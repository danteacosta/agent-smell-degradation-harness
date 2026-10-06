"""Frozen analysis for the confirmatory H1a collection, tested on synthetic data.

Written and tested before any confirmatory output exists, so the analysis
cannot be tuned to the data. It reads two inputs:

  selection  the output of `confirmatory_selection.py walk` (PR #177): the
             analysis runs only when its status is "complete"; otherwise it
             returns that status and no estimate (stop rule).
  outcomes   one row per generated output: intent_id, project_id, model,
             replication, arm (A, B or C), outcome (pass, fail or unknown) and,
             optionally, frame_option (reserve or w2024).

Reported, following the pre-registration and the corrected planning note:

  H1a       paired probability of superiority of C against A (requirement
            weights, repetitions averaged), project-cluster bootstrap interval
            and exact two-sided project-level sign-flip p-value. Decision:
            supported if the lower bound is above 0.5 and p < 0.05; reversal if
            the upper bound is below 0.5 and p < 0.05; otherwise inconclusive.
  B control the same estimand for B against A; a wording effect is flagged when
            its interval excludes 0.5.
  unknowns  observed pairs (primary) and worst/best-case assignment (bounds).
  exploratory per model, leave-one-project-out, per frame option, and the
            sensitivity without the 2024 window (which does not keep the design).

No model call. The `dry-run` mode writes the three synthetic scenarios.
"""
from __future__ import annotations

import argparse
from collections import Counter, defaultdict
import json
from pathlib import Path
import random
import sys

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from protocol.paired_stats import paired_probability_of_superiority  # noqa: E402
from scripts.confirmatory_power import project_sign_flip_pvalue  # noqa: E402

SCHEMA = "confirmatory-h1a-analysis/v1"
ARMS = ("A", "B", "C")
OUTCOMES = {"pass": 0, "fail": 1, "unknown": None}
SEED = 2026100611
N_BOOT = 4000
ALPHA = 0.05


# ---------------------------------------------------------------- validation

def validate(rows: list[dict], selection: dict) -> dict:
    """Every selected requirement has every planned slot exactly once; nothing else."""
    selected = {c for ids in selection["selected"].values() for c in ids}
    project_of = {c: p for p, ids in selection["selected"].items() for c in ids}
    seen: dict[tuple, dict] = {}
    for n, r in enumerate(rows):
        for field in ("intent_id", "project_id", "model", "replication", "arm", "outcome"):
            if field not in r:
                raise ValueError(f"row {n}: missing {field}")
        if r["intent_id"] not in selected:
            raise ValueError(f"row {n}: {r['intent_id']} was not selected")
        if project_of[r["intent_id"]] != r["project_id"]:
            raise ValueError(f"row {n}: {r['intent_id']} belongs to {project_of[r['intent_id']]}")
        if r["arm"] not in ARMS:
            raise ValueError(f"row {n}: arm must be one of {ARMS}")
        if r["outcome"] not in OUTCOMES:
            raise ValueError(f"row {n}: outcome must be one of {sorted(OUTCOMES)}")
        key = (r["intent_id"], r["model"], r["replication"], r["arm"])
        if key in seen:
            raise ValueError(f"row {n}: duplicate slot {key}")
        seen[key] = r
    models = sorted({r["model"] for r in rows})
    reps = sorted({r["replication"] for r in rows})
    missing = [(i, m, k, a) for i in sorted(selected) for m in models for k in reps for a in ARMS
               if (i, m, k, a) not in seen]
    if missing:
        raise ValueError(f"{len(missing)} planned slots missing, first {missing[0]}")
    return {"requirements": len(selected), "projects": len(selection["selected"]),
            "models": models, "replications": reps, "slots": len(seen)}


def pairs(rows: list[dict], clean: str, defective: str, unknown: str = "drop") -> list[dict]:
    """Matched (model, replication) pairs; unknown: drop, worst or best."""
    by = {(r["intent_id"], r["model"], r["replication"], r["arm"]): r for r in rows}
    out = []
    for (intent, model, rep, arm), r in sorted(by.items()):
        if arm != clean:
            continue
        d = by[(intent, model, rep, defective)]
        c_sev, d_sev = OUTCOMES[r["outcome"]], OUTCOMES[d["outcome"]]
        if c_sev is None or d_sev is None:
            if unknown == "drop":
                continue
            if c_sev is None:
                c_sev = 0 if unknown == "worst" else 1
            if d_sev is None:
                d_sev = 1 if unknown == "worst" else 0
        out.append({"intent_id": intent, "project_id": r["project_id"], "model": model, "replication": rep,
                    "clean_severity": c_sev, "defective_severity": d_sev})
    return out


# ---------------------------------------------------------------- estimation

def estimate(pair_rows: list[dict], seed: int = SEED, n_boot: int = N_BOOT, inference: bool = True) -> dict:
    if not pair_rows:
        return {"estimate": None, "n_pairs": 0}
    r = paired_probability_of_superiority(pair_rows, n_boot=n_boot, n_perm=1, seed=seed)
    out = {"estimate": round(r["estimate"], 4), "n_pairs": r["n_pairs"], "n_requirements": r["n_intents"],
           "n_projects": r["n_projects"], "pair_outcomes": r["pair_outcomes"]}
    if inference:
        ci = r["ci95_project_cluster"]
        out["ci95_project_bootstrap"] = [None if ci["low"] is None else round(ci["low"], 4),
                                         None if ci["high"] is None else round(ci["high"], 4)]
        out["p_exact_project_sign_flip"] = project_sign_flip_pvalue(pair_rows)
    return out


def decide(result: dict, alpha: float = ALPHA) -> str:
    low, high = result["ci95_project_bootstrap"]
    p = result["p_exact_project_sign_flip"]
    if low is not None and low > 0.5 and p < alpha:
        return "supported"
    if high is not None and high < 0.5 and p < alpha:
        return "reversal"
    return "inconclusive"


def analyse(rows: list[dict], selection: dict, seed: int = SEED, n_boot: int = N_BOOT) -> dict:
    if selection.get("status") != "complete":
        return {"schema_version": SCHEMA, "status": selection.get("status", "missing"),
                "note": "selection did not complete; the stop rule forbids estimation", "h1a": None}
    design = validate(rows, selection)
    primary = estimate(pairs(rows, "A", "C"), seed, n_boot)
    primary["decision"] = decide(primary)
    if 2 / 2 ** primary["n_projects"] >= ALPHA:
        primary["note"] = "too few projects for the exact test to reach p < 0.05"
    b = estimate(pairs(rows, "A", "B"), seed, n_boot)
    low, high = b["ci95_project_bootstrap"]
    b["wording_effect_flag"] = bool((low is not None and low > 0.5) or (high is not None and high < 0.5))

    unknown = Counter((r["arm"], r["outcome"] == "unknown") for r in rows)
    result = {
        "schema_version": SCHEMA, "status": "complete", "seed": seed, "n_boot": n_boot,
        "decision_rule": ("supported: project-bootstrap lower bound > 0.5 and exact project sign-flip p < 0.05; "
                          "reversal: upper bound < 0.5 and p < 0.05; otherwise inconclusive"),
        "design": design,
        "unknown_rate": {arm: round(unknown[(arm, True)] / (unknown[(arm, True)] + unknown[(arm, False)]), 4)
                         for arm in ARMS},
        "h1a": primary,
        "h1a_unknown_bounds": {k: estimate(pairs(rows, "A", "C", k), seed, n_boot, inference=False)
                               for k in ("worst", "best")},
        "b_control": b,
        "exploratory": exploratory(rows, seed, n_boot),
        "confirmatory_eligible": True,
    }
    return result


def exploratory(rows: list[dict], seed: int, n_boot: int) -> dict:
    ac = pairs(rows, "A", "C")
    out = {"per_model": {m: estimate([p for p in ac if p["model"] == m], seed, n_boot)
                         for m in sorted({p["model"] for p in ac})}}
    projects = sorted({p["project_id"] for p in ac})
    out["leave_one_project_out"] = {p: estimate([x for x in ac if x["project_id"] != p], seed, n_boot,
                                                inference=False)["estimate"] for p in projects}
    option = {r["intent_id"]: r.get("frame_option") for r in rows}
    if any(option.values()):
        out["per_frame_option"] = {o: estimate([p for p in ac if option[p["intent_id"]] == o], seed, n_boot,
                                               inference=False)
                                   for o in sorted({v for v in option.values() if v})}
        without = [p for p in ac if option[p["intent_id"]] != "w2024"]
        out["without_w2024"] = {**estimate(without, seed, n_boot),
                                "note": "sensitivity only: drops requirements unevenly by project and does not "
                                        "keep the 8x5 design or its estimated power"}
    return out


# ---------------------------------------------------------------- synthetic data

def synthetic(fail_a: float, fail_b: float, fail_c: float, unknown: float = 0.03, projects: int = 8,
              per_project: int = 5, models: tuple = ("model-1", "model-2"), reps: int = 2,
              w2024_per_project: int = 0, seed: int = 1) -> tuple[list[dict], dict]:
    """Rows and a complete selection; failure probabilities per arm, requirement-level heterogeneity."""
    rng = random.Random(seed)
    selected, rows = {}, []
    for p in range(projects):
        project = f"proj{p}"
        selected[project] = [f"{project}-req{k}" for k in range(per_project)]
        for k, intent in enumerate(selected[project]):
            shift = rng.uniform(-0.1, 0.1)
            for m in models:
                for rep in range(1, reps + 1):
                    for arm, base in (("A", fail_a), ("B", fail_b), ("C", fail_c)):
                        prob = min(1.0, max(0.0, base + shift))
                        outcome = ("unknown" if rng.random() < unknown else
                                   "fail" if rng.random() < prob else "pass")
                        rows.append({"intent_id": intent, "project_id": project, "model": m, "replication": rep,
                                     "arm": arm, "outcome": outcome,
                                     "frame_option": "w2024" if k >= per_project - w2024_per_project else "reserve"})
    selection = {"status": "complete", "selected": selected,
                 "project_status": {p: "complete" for p in selected}}
    return rows, selection


SCENARIOS = {
    "effect": dict(fail_a=0.08, fail_b=0.10, fail_c=0.55, w2024_per_project=1),
    "null": dict(fail_a=0.20, fail_b=0.20, fail_c=0.20),
    "reversal": dict(fail_a=0.55, fail_b=0.55, fail_c=0.10),
}


def dry_run(out_dir: Path) -> dict:
    out_dir.mkdir(parents=True, exist_ok=True)
    summary = {}
    for name, params in SCENARIOS.items():
        rows, selection = synthetic(**params)
        result = analyse(rows, selection)
        result["synthetic"] = {"scenario": name, "parameters": params}
        result["confirmatory_eligible"] = False
        (out_dir / f"{name}.json").write_text(json.dumps(result, indent=2) + "\n")
        summary[name] = {"estimate": result["h1a"]["estimate"], "ci": result["h1a"]["ci95_project_bootstrap"],
                         "p": result["h1a"]["p_exact_project_sign_flip"], "decision": result["h1a"]["decision"]}
    stopped = analyse([], {"status": "stopped_insufficient", "selected": {}})
    (out_dir / "stopped_insufficient.json").write_text(json.dumps(stopped, indent=2) + "\n")
    summary["stopped_insufficient"] = {"status": stopped["status"], "h1a": stopped["h1a"]}
    return summary


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    sub = parser.add_subparsers(dest="mode", required=True)
    d = sub.add_parser("dry-run")
    d.add_argument("--out", type=Path, default=ROOT / "data/confirmatory-planning/analysis-dry-run")
    a = sub.add_parser("analyse")
    a.add_argument("--selection", type=Path, required=True)
    a.add_argument("--outcomes", type=Path, required=True, help="JSON list of outcome rows")
    a.add_argument("--out", type=Path)
    args = parser.parse_args(argv)
    if args.mode == "dry-run":
        print(json.dumps(dry_run(args.out), indent=2))
        return
    result = analyse(json.loads(args.outcomes.read_text()), json.loads(args.selection.read_text()))
    text = json.dumps(result, indent=2)
    if args.out:
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_text(text + "\n")
    print(text)


if __name__ == "__main__":
    main()
