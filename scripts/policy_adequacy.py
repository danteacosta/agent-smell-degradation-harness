"""Does an agent's existing evaluation suite notice when one policy rule is lost?

Exploratory extension of the shared-omission study to a conversational agent with
a written policy (tau2-bench airline). Nothing here calls a model: the script
validates the frozen rule inventory against a pinned tau2-bench checkout, builds
one data directory per policy variant (selected with TAU2_DATA_DIR, so tau2-bench
code is untouched), writes a seeded run plan, and analyses results with rules
fixed before any run.

Variants
  A    the policy as published.
  Dxx  rule xx deleted (whole lines), the omission a ticket or prompt can suffer.
  Nxx  rule xx replaced by its inversion, which tells the agent to violate it;
       measures whether any task can fail when the rule is broken.
  Byy  a meaning-preserving rewording of one rule (noise control).

Analysis (pre-specified, see the draft preregistration)
  - A runs BASELINE_TRIALS times on every task; a task is eligible when it passes
    at least ELIGIBLE_PASSES of them.
  - Every other variant runs once on every task. A failure on an eligible task is
    a candidate; each candidate is re-run CONFIRM_RERUNS more times and counts as
    a confirmed detection when it fails in at least CONFIRM_FAILS of the
    1 + CONFIRM_RERUNS runs.
  - A rule is covered under an operator when at least one task confirms it.
  - Confirmed detections under B controls estimate how often noise alone passes
    the confirmation rule.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import math
import os
from pathlib import Path
import random
import sys

ROOT = Path(__file__).resolve().parents[1]
RULES = ROOT / "data/policy-adequacy/tau2-airline/rules-draft.json"
BASELINE_TRIALS = 4
ELIGIBLE_PASSES = 3
CONFIRM_RERUNS = 2
CONFIRM_FAILS = 2
SEED = 2026100701


def sha256(text: str) -> str:
    return hashlib.sha256(text.encode()).hexdigest()


def load_rules(path: Path = RULES) -> dict:
    return json.loads(path.read_text())


def validate(inv: dict, policy: str) -> None:
    if sha256(policy) != inv["source"]["policy_sha256"]:
        raise ValueError("policy drift: sha256 differs from the pinned policy")
    lines = policy.split("\n")
    taken = set()
    for item in inv["rules"] + inv["controls"]:
        a, b = item["lines"]
        if "\n".join(lines[a - 1:b]) != item["text"]:
            raise ValueError(f"{item['id']}: text does not match policy lines {a}-{b}")
    for r in inv["rules"]:
        a, b = r["lines"]
        span = set(range(a, b + 1))
        if span & taken:
            raise ValueError(f"{r['id']}: overlaps another rule")
        taken |= span
        if not r["negation"].strip() or r["negation"] == r["text"]:
            raise ValueError(f"{r['id']}: negation missing or identical")
    ids = [x["id"] for x in inv["rules"] + inv["controls"]]
    if len(ids) != len(set(ids)):
        raise ValueError("duplicate ids")
    for c in inv["controls"]:
        if c["rewording"] == c["text"]:
            raise ValueError(f"{c['id']}: rewording identical to the rule")


def replace_lines(policy: str, a: int, b: int, new: str | None) -> str:
    lines = policy.split("\n")
    if new is None:
        rest = lines[:a - 1] + lines[b:]
        i = a - 1  # collapse one blank line if the deletion left two in a row
        if 0 < i < len(rest) and rest[i - 1] == "" and rest[i] == "":
            del rest[i]
        return "\n".join(rest)
    return "\n".join(lines[:a - 1] + new.split("\n") + lines[b:])


def variants(inv: dict, policy: str) -> dict[str, str]:
    out = {"A": policy}
    for r in inv["rules"]:
        a, b = r["lines"]
        n = r["id"][1:]
        out["D" + n] = replace_lines(policy, a, b, None)
        out["N" + n] = replace_lines(policy, a, b, r["negation"])
    for c in inv["controls"]:
        a, b = c["lines"]
        out[c["id"]] = replace_lines(policy, a, b, c["rewording"])
    for name, text in out.items():
        if name != "A" and text == policy:
            raise ValueError(f"{name}: variant equals the original policy")
    return out


def build(tau2_dir: Path, out: Path, inv: dict) -> dict:
    data = tau2_dir / "data"
    policy_path = data / "tau2/domains/airline/policy.md"
    policy = policy_path.read_text()
    validate(inv, policy)
    texts = variants(inv, policy)
    if out.exists():
        raise FileExistsError(out)
    manifest = {}
    for name, text in texts.items():
        root = out / name
        (root / "tau2/domains/airline").mkdir(parents=True)
        for entry in data.iterdir():
            if entry.name != "tau2":
                os.symlink(entry.resolve(), root / entry.name)
        for entry in (data / "tau2").iterdir():
            if entry.name != "domains":
                os.symlink(entry.resolve(), root / "tau2" / entry.name)
        for entry in (data / "tau2/domains").iterdir():
            if entry.name != "airline":
                os.symlink(entry.resolve(), root / "tau2/domains" / entry.name)
        for entry in (data / "tau2/domains/airline").iterdir():
            if entry.name != "policy.md":
                os.symlink(entry.resolve(), root / "tau2/domains/airline" / entry.name)
        (root / "tau2/domains/airline/policy.md").write_text(text)
        manifest[name] = sha256(text)
    (out / "variants-manifest.json").write_text(json.dumps(
        {"source": inv["source"], "policy_sha256": manifest}, indent=2) + "\n")
    return manifest


def plan(inv: dict, seed: int = SEED) -> list[dict]:
    """Stage 1: baseline, inversions and controls. Stage 2: deletions, run only if stage 1
    is complete and the budget allows; the stage-2 order is fixed now, before any result."""
    rng = random.Random(seed)
    baseline = [{"variant": "A", "trial": t, "stage": 1} for t in range(1, BASELINE_TRIALS + 1)]
    stage1 = [{"variant": "N" + r["id"][1:], "trial": 1, "stage": 1} for r in inv["rules"]]
    stage1 += [{"variant": c["id"], "trial": 1, "stage": 1} for c in inv["controls"]]
    stage2 = [{"variant": "D" + r["id"][1:], "trial": 1, "stage": 2} for r in inv["rules"]]
    rng.shuffle(stage1)
    rng.shuffle(stage2)
    order = baseline + stage1 + stage2  # baseline first: eligibility must exist before confirmations
    for i, b in enumerate(order, 1):
        b["order"] = i
        b["run_seed"] = seed + i
        b["save_to"] = f"policy-adequacy-{b['variant']}-t{b['trial']}"
    return order


def read_tau2_results(path: Path, variant: str, *, trial: int) -> list[dict]:
    data = json.loads(Path(path).read_text())
    rows = []
    for sim in data["simulations"]:
        info = sim.get("reward_info") or {}
        rows.append({"variant": variant, "task_id": str(sim["task_id"]),
                     "trial": trial, "reward": info.get("reward"), "termination_reason": sim.get("termination_reason")})
    return rows


def passed(row: dict) -> bool:
    return row["reward"] is not None and row["reward"] >= 1.0


def analyse(inv: dict, rows: list[dict], tasks: list[str]) -> dict:
    if not tasks or len(tasks) != len(set(tasks)):
        raise ValueError("tasks must be nonempty and unique")
    valid_variants = {"A"} | {
        op + r["id"][1:] for r in inv["rules"] for op in ("N", "D")
    } | {c["id"] for c in inv["controls"]}
    by = {}
    for row in rows:
        variant, task = row["variant"], row["task_id"]
        if variant not in valid_variants or task not in tasks:
            raise ValueError("unknown variant/task slot")
        trial = row.get("trial")
        limit = BASELINE_TRIALS if variant == "A" else 1 + CONFIRM_RERUNS
        if type(trial) is not int or not 1 <= trial <= limit:
            raise ValueError("invalid or missing trial identity")
        reward = row.get("reward")
        if reward is not None and (
            type(reward) not in (int, float) or not math.isfinite(reward)
            or not 0 <= reward <= 1
        ):
            raise ValueError("reward must be absent or a finite number in [0, 1]")
        runs = by.setdefault((variant, task), {})
        if trial in runs:
            raise ValueError("duplicate variant/task/trial slot")
        runs[trial] = row
    for (variant, task), runs in by.items():
        if variant != "A" and 1 not in runs:
            raise ValueError("confirmation requires an initial slot")
    if any(set(by.get(("A", t), {})) != set(range(1, BASELINE_TRIALS + 1)) for t in tasks):
        raise ValueError("every task needs exactly BASELINE_TRIALS baseline runs")
    unresolved = sorted(t for t in tasks if any(
        r.get("reward") is None for r in by[("A", t)].values()))
    eligible = sorted(t for t in tasks if t not in unresolved and sum(
        passed(r) for r in by[("A", t)].values()) >= ELIGIBLE_PASSES)

    def status(variant: str, task: str) -> str:
        runs = by.get((variant, task), {})
        if 1 not in runs:
            return "missing"
        if any(r.get("reward") is None for r in runs.values()):
            return "technical_failure"
        if passed(runs[1]):
            return "pass"
        if len(runs) < 1 + CONFIRM_RERUNS:
            return "unconfirmed"
        fails = sum(not passed(r) for r in runs.values())
        return "confirmed" if fails >= CONFIRM_FAILS else "not_confirmed"

    def summary(variant: str) -> dict:
        st = {t: status(variant, t) for t in eligible}
        confirmations = []
        for task in eligible:
            runs = by.get((variant, task), {})
            initial = runs.get(1)
            if initial is not None and initial.get("reward") is not None and not passed(initial):
                remaining = [t for t in range(2, 2 + CONFIRM_RERUNS) if t not in runs]
                if remaining:
                    confirmations.append({"task_id": task, "trials": remaining})
        return {"confirmed_tasks": sorted(t for t, s in st.items() if s == "confirmed"),
                "pending": sorted(t for t, s in st.items() if s in (
                    "unconfirmed", "missing", "technical_failure")),
                "missing_initial_tasks": sorted(t for t, s in st.items() if s == "missing"),
                "technical_failure_tasks": sorted(t for t, s in st.items() if s == "technical_failure"),
                "confirmation_pending": confirmations}

    per_rule = []
    for r in inv["rules"]:
        n = r["id"][1:]
        d, g = summary("D" + n), summary("N" + n)
        covered_n = bool(g["confirmed_tasks"])
        covered_d = bool(d["confirmed_tasks"])
        if not eligible:
            cls = "not_estimable"
        elif g["pending"] or d["pending"]:
            cls = "incomplete"
        elif covered_n and covered_d:
            cls = "omission_detected"
        elif covered_n:
            cls = "covered_but_omission_silent"
        elif covered_d:
            cls = "omission_detected_violation_not"
        else:
            cls = "uncovered"
        per_rule.append({"id": r["id"], "name": r["name"], "section": r["section"],
                         "deletion": d, "negation": g, "class": cls})
    controls = [{"id": c["id"], **summary(c["id"])} for c in inv["controls"]]
    noise = sum(len(c["confirmed_tasks"]) for c in controls)
    classes = {}
    for p in per_rule:
        classes[p["class"]] = classes.get(p["class"], 0) + 1
    return {"schema_version": "policy-suite-adequacy-analysis/v2", "exploratory": True,
            "baseline_unresolved_tasks": unresolved,
            "tasks": len(tasks), "eligible_tasks": len(eligible),
            "rules": len(per_rule), "classes": classes,
            "covered_under_negation": sum(bool(p["negation"]["confirmed_tasks"]) for p in per_rule),
            "detected_under_deletion": sum(bool(p["deletion"]["confirmed_tasks"]) for p in per_rule),
            "control_confirmed_detections": noise,
            "control_task_pairs": len(controls) * len(eligible),
            "per_rule": per_rule, "controls": controls}


def candidates(inv: dict, rows: list[dict], tasks: list[str]) -> list[dict]:
    """Eligible (variant, task) pairs that failed once and still need confirmation re-runs."""
    result = analyse(inv, rows, tasks)
    out = []
    summaries = [(op + p["id"][1:], p[key]) for p in result["per_rule"]
                 for op, key in (("D", "deletion"), ("N", "negation"))]
    summaries += [(c["id"], c) for c in result["controls"]]
    for variant, summary in summaries:
        for item in summary["confirmation_pending"]:
            out.append({"variant": variant, "task_id": item["task_id"],
                        "reruns": len(item["trials"]), "trials": item["trials"]})
    return out


def main(argv: list[str] | None = None) -> None:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    sub = ap.add_subparsers(dest="cmd", required=True)
    v = sub.add_parser("validate"); v.add_argument("--tau2", type=Path, required=True)
    b = sub.add_parser("build"); b.add_argument("--tau2", type=Path, required=True); b.add_argument("--out", type=Path, required=True)
    sub.add_parser("plan")
    args = ap.parse_args(argv)
    inv = load_rules()
    if args.cmd == "validate":
        policy = (args.tau2 / "data/tau2/domains/airline/policy.md").read_text()
        validate(inv, policy)
        texts = variants(inv, policy)
        print(f"ok: {len(inv['rules'])} rules, {len(inv['controls'])} controls, {len(texts)} variants")
    elif args.cmd == "build":
        print(json.dumps(build(args.tau2, args.out, inv), indent=2))
    else:
        print(json.dumps(plan(inv), indent=2))


if __name__ == "__main__":
    main()
