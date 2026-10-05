"""Mutation adequacy: do generated test suites notice that a rule was lost?

Extends the three-case test-anchor diagnostic to every eligible requirement of
the 46-case collection, without generating any new implementation.

Mutants are confirmed by the frozen oracle: an arm-C implementation whose
oracle verdict is ``target_only_failure`` is a version of the feature that
lost the rule. Arm-C implementations that passed are *recovered*: the agent
kept the rule although the request omitted it, so no test should fail on
them. Arm-A implementations that passed are *correct* implementations.

For every eligible requirement (at least one correct A and one confirmed
mutant) a tester model writes suites from three sources, SUITES_PER_SOURCE
each, generated once:

  spec_complete    the complete requirement (arm A) and the page scaffold
  spec_incomplete  the incomplete request (arm C) and the page scaffold
  code_incomplete  the incomplete request and one correct implementation
                   (the seeded reference), as a reviewer of that PR would see

Every suite runs against every correct, mutant and recovered implementation of
its requirement in the qualified, network-disabled image. A suite is *sound*
when it is quiet on the reference implementation; a mutant is *killed* by a
sound suite that raises an alarm on it. Unusable suites (generation failure,
invalid suite, runner error) stay in the denominator as unsound
(intention-to-test).

Modes: locate, prepare, generate, execute, analyse. Ground truth comes from
the published results of the 46-case collection; the tester never sees it.
"""
from __future__ import annotations

import argparse
from collections import Counter, defaultdict
import hashlib
from itertools import product
import json
from pathlib import Path
import random
import sys

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts import test_anchor_experiment as ta  # noqa: E402

SCHEMA = "mutation-adequacy/v1"
SEED = 2026100507
SOURCES = ("spec_complete", "spec_incomplete", "code_incomplete")
SUITES_PER_SOURCE = 2
RESULTS_ROOT = ROOT / "data/selection-abc-results/20261003"
CASES_DIR = ROOT / "data/abc-cases"
ALARMS = ("assertion_alarm", "error_alarm")


# ---------------------------------------------------------------- eligibility

def roles(rows: list[dict]) -> dict[str, list[str]]:
    out = {"correct": [], "mutant": [], "recovered": []}
    for r in sorted(rows, key=lambda r: r["slot_id"]):
        if r["arm"] == "A" and r.get("category") == "pass":
            out["correct"].append(r["slot_id"])
        elif r["arm"] == "C" and r.get("category") == "target_only_failure":
            out["mutant"].append(r["slot_id"])
        elif r["arm"] == "C" and r.get("category") == "pass":
            out["recovered"].append(r["slot_id"])
    return out


def eligible_cases(results_root: Path = RESULTS_ROOT, cases_dir: Path = CASES_DIR) -> list[dict]:
    """Mechanical, from published results: >=1 correct A and >=1 confirmed mutant."""
    from scripts import selected46_report as rep
    configs = rep.load_configs(cases_dir)
    runs = rep.load_results(results_root, configs)
    out = []
    for case in sorted(runs):
        r = roles(runs[case])
        if r["correct"] and r["mutant"]:
            config = configs[case]
            reference = random.Random(f"{SEED}:{case}").choice(r["correct"])
            out.append({"case": case, "project_id": config["project_id"], "roles": r, "reference": reference,
                        "results_sha256": ta.sha256_file(results_root / case / "results.json")})
    return out


# ---------------------------------------------------------------- locate

def locate(evidence_root: Path, cases: list[dict]) -> dict[str, str]:
    """Bind each case to the private packet whose results.json is byte-identical to the published one."""
    wanted = {c["results_sha256"]: c["case"] for c in cases}
    found: dict[str, list[str]] = defaultdict(list)
    for depth in ("*/results.json", "*/*/results.json", "*/*/*/results.json"):
        for path in sorted(evidence_root.glob(depth)):
            case = wanted.get(ta.sha256_file(path))
            if case and (path.parent / "frozen/manifest.json").is_file():
                found[case].append(str(path.parent))
    missing = sorted(c["case"] for c in cases if len(set(found.get(c["case"], []))) != 1)
    if missing:
        raise SystemExit(f"could not identify exactly one packet for: {', '.join(missing)}")
    return {case: sorted(set(paths))[0] for case, paths in found.items()}


# ---------------------------------------------------------------- prepare

def plan(cases: list[dict], packets: dict[str, Path]) -> tuple[list[dict], list[dict]]:
    calls, records = [], []
    for c in cases:
        config = json.loads((CASES_DIR / f"{c['case']}.json").read_text())
        scaffold = (ROOT / config["fixture"] / "page.html").read_text()
        packet = Path(packets[c["case"]])
        artifacts = {}
        for role, slots in c["roles"].items():
            for slot in slots:
                path = packet / "artifacts" / slot / "app.html"
                artifacts[slot] = {"role": role, "artifact_path": str(path.resolve()),
                                   "artifact_sha256": ta.sha256_file(path)}
        reference_code = Path(artifacts[c["reference"]]["artifact_path"]).read_text()
        texts = {"spec_complete": ta.tester_prompt("spec_only", config["arms"]["A"], scaffold),
                 "spec_incomplete": ta.tester_prompt("spec_only", config["arms"]["C"], scaffold),
                 "code_incomplete": ta.tester_prompt("code_request", config["arms"]["C"], reference_code)}
        records.append({**c, "packet": str(packet.resolve()), "artifacts": artifacts})
        for source in SOURCES:
            for k in range(1, SUITES_PER_SOURCE + 1):
                key = json.dumps([c["case"], source, k, SEED])
                calls.append({"call_id": "ma-" + hashlib.sha256(key.encode()).hexdigest()[:20], "case": c["case"],
                              "project_id": c["project_id"], "source": source, "suite_index": k,
                              "prompt": texts[source], "targets": sorted(artifacts)})
    random.Random(SEED).shuffle(calls)
    return calls, records


def prepare(out: Path, packets: dict[str, Path], model: str, executable: Path) -> dict:
    if out.exists():
        raise FileExistsError("fresh output directory required")
    cases = eligible_cases()
    if set(packets) != {c["case"] for c in cases}:
        raise ValueError("packets must cover exactly the eligible cases")
    calls, records = plan(cases, packets)
    out.mkdir(mode=0o700, parents=True)
    for call in calls:
        ta.put(out / "frozen/prompts" / f"{call['call_id']}.txt", call["prompt"])
    manifest = {
        "schema_version": SCHEMA, "seed": SEED, "model": model, "executable": str(executable), "image": ta.IMAGE,
        "sources": SOURCES, "suites_per_source": SUITES_PER_SOURCE,
        "runner_sha256": ta.sha256_file(ta.RUNNER), "script_sha256": ta.sha256_file(Path(__file__)),
        "test_anchor_script_sha256": ta.sha256_file(Path(ta.__file__)),
        "cases": records, "schedule": [{k: v for k, v in c.items() if k != "prompt"} for c in calls],
        "retry_policy": "no_retry_no_repair", "confirmatory_eligible": False,
        "ground_truth": "published oracle categories of data/selection-abc-results/20261003 (hash-bound)",
    }
    ta.put(out / "frozen/manifest.json", manifest)
    ta.put(out / "frozen/receipt.json", {"files": ta.inventory(out / "frozen")})
    return {"calls": len(calls), "cases": len(records),
            "executions": sum(len(c["targets"]) for c in calls),
            "artifacts": dict(Counter(a["role"] for r in records for a in r["artifacts"].values()))}


def verify(out: Path) -> dict:
    receipt = json.loads((out / "frozen/receipt.json").read_text())["files"]
    if {k: v for k, v in ta.inventory(out / "frozen").items() if k != "receipt.json"} != receipt:
        raise ValueError("frozen packet drift")
    manifest = json.loads((out / "frozen/manifest.json").read_text())
    if manifest["runner_sha256"] != ta.sha256_file(ta.RUNNER):
        raise ValueError("runner drift since freeze")
    for case in manifest["cases"]:
        for slot, a in case["artifacts"].items():
            if ta.sha256_file(Path(a["artifact_path"])) != a["artifact_sha256"]:
                raise ValueError(f"artifact drift: {slot}")
    return manifest


# ---------------------------------------------------------------- generate / execute

def generate(out: Path, provider_factory=None) -> dict:
    manifest = verify(out)
    if (out / "generation-started.json").exists():
        raise FileExistsError("no resume or retry")
    ta.put(out / "generation-started.json", {"frozen_receipt_sha256": ta.sha256_file(out / "frozen/receipt.json")})
    if provider_factory is None:
        from agents.codex_cli import CodexCLIProvider
        provider_factory = lambda evidence: CodexCLIProvider(  # noqa: E731
            executable=manifest["executable"], model=manifest["model"], timeout_seconds=300,
            evidence_directory=evidence)
    from agents.providers import ProviderRequest
    status = Counter()
    for call in manifest["schedule"]:
        directory = out / "calls" / call["call_id"]
        ta.put(directory / "attempt.json", {"call_id": call["call_id"]})
        try:
            raw = provider_factory(directory / "capture").complete(
                ProviderRequest((out / "frozen/prompts" / f"{call['call_id']}.txt").read_text(), {}, "opaque", "code"))
        except Exception as error:  # an outcome, never retried
            ta.put(directory / "result.json", {"status": "generation_failed", "error_type": type(error).__name__})
            status["generation_failed"] += 1
            continue
        ta.put(directory / "response.txt", raw)
        try:
            suite = ta.extract_suite(raw)
        except ValueError as error:
            ta.put(directory / "result.json", {"status": "suite_invalid", "reason": str(error)})
            status["suite_invalid"] += 1
        else:
            ta.put(directory / "suite.cjs", suite)
            ta.put(directory / "result.json", {"status": "suite_ready", "suite_sha256": ta.sha256_bytes(suite.encode())})
            status["suite_ready"] += 1
        print(json.dumps({"phase": "generation", "done": sum(status.values()), "of": len(manifest["schedule"])}),
              flush=True)
    ta.put(out / "generation.json", dict(status))
    return dict(status)


def execute(out: Path, executor=ta.docker_execute) -> dict:
    manifest = verify(out)
    if (out / "execution-started.json").exists():
        raise FileExistsError("no resume or retry")
    ta.put(out / "execution-started.json", {"generation_sha256": ta.sha256_file(out / "generation.json")})
    cases = {c["case"]: c for c in manifest["cases"]}
    rows = []
    for call in manifest["schedule"]:
        directory = out / "calls" / call["call_id"]
        result = json.loads((directory / "result.json").read_text())
        case = cases[call["case"]]
        for slot in call["targets"]:
            a = case["artifacts"][slot]
            row = {"call_id": call["call_id"], "case": call["case"], "project_id": call["project_id"],
                   "source": call["source"], "suite_index": call["suite_index"], "slot_id": slot,
                   "role": a["role"], "is_reference": slot == case["reference"]}
            if result["status"] != "suite_ready":
                row["verdict"] = result["status"]
            else:
                try:
                    report = executor(Path(a["artifact_path"]), directory / "suite.cjs",
                                      out / "execution" / call["call_id"] / slot)
                except Exception as error:
                    report = {"status": "runner_error", "error": f"{type(error).__name__}: {error}"[:500]}
                row["verdict"] = ta.classify(report)
            rows.append(row)
        print(json.dumps({"phase": "execution", "call": call["call_id"]}), flush=True)
    results = {"schema_version": SCHEMA + "-results", "rows": rows, "analysis": analyse(rows),
               "confirmatory_eligible": False}
    ta.put(out / "results.json", results)
    ta.put(out / "receipt.json", {"files": ta.inventory(out)})
    return results["analysis"]


# ---------------------------------------------------------------- analysis

def suite_scores(rows: list[dict]) -> list[dict]:
    """One record per suite: soundness, kills, naive kills and false alarms."""
    by_suite: dict[str, list[dict]] = defaultdict(list)
    for r in rows:
        by_suite[r["call_id"]].append(r)
    out = []
    for call_id, rs in sorted(by_suite.items()):
        ref = [r for r in rs if r["is_reference"]]
        sound = len(ref) == 1 and ref[0]["verdict"] == "quiet"
        alarm = {r["slot_id"]: r["verdict"] in ALARMS for r in rs}
        mutants = [r for r in rs if r["role"] == "mutant"]
        recovered = [r for r in rs if r["role"] == "recovered"]
        others = [r for r in rs if r["role"] == "correct" and not r["is_reference"]]
        killed = sum(sound and alarm[r["slot_id"]] for r in mutants)
        out.append({
            "call_id": call_id, "case": rs[0]["case"], "project_id": rs[0]["project_id"], "source": rs[0]["source"],
            "sound": sound, "mutants": len(mutants), "killed": killed,
            "mutation_score": killed / len(mutants) if mutants else None,
            "naive_mutants": len(mutants) + len(recovered),
            "naive_killed": killed + sum(sound and alarm[r["slot_id"]] for r in recovered),
            "recovered": len(recovered), "recovered_alarms": sum(alarm[r["slot_id"]] for r in recovered),
            "correct_other": len(others), "correct_other_alarms": sum(alarm[r["slot_id"]] for r in others),
            "unusable": all(r["verdict"] in ("generation_failed", "suite_invalid", "runner_error") for r in rs),
        })
    return out


def requirement_scores(suites: list[dict]) -> dict[tuple, float]:
    acc: dict[tuple, list[float]] = defaultdict(list)
    for s in suites:
        acc[(s["case"], s["project_id"], s["source"])].append(s["mutation_score"])
    return {k: sum(v) / len(v) for k, v in acc.items()}


def project_sign_flip(diffs: dict[str, list[float]]) -> float | None:
    """Exact two-sided test: flip the signs of all requirement differences of a project together."""
    projects = sorted(diffs)
    values = [v for p in projects for v in diffs[p]]
    if not values:
        return None
    observed = abs(sum(values) / len(values))
    if observed == 0:
        return 1.0
    extreme = total = 0
    for signs in product((1, -1), repeat=len(projects)):
        stat = abs(sum(s * v for s, p in zip(signs, projects) for v in diffs[p]) / len(values))
        extreme += stat >= observed - 1e-12
        total += 1
    return extreme / total


def project_bootstrap(diffs: dict[str, list[float]], seed: int = SEED, n: int = 4000) -> list[float] | None:
    projects = sorted(diffs)
    if len(projects) < 2:
        return None
    rng = random.Random(seed)
    draws = []
    for _ in range(n):
        vals = [v for p in (rng.choice(projects) for _ in projects) for v in diffs[p]]
        draws.append(sum(vals) / len(vals))
    draws.sort()
    return [draws[int(0.025 * (n - 1))], draws[int(0.975 * (n - 1))]]


def paired(req: dict[tuple, float], better: str, worse: str) -> dict:
    diffs: dict[str, list[float]] = defaultdict(list)
    for (case, project, source), score in req.items():
        if source == better and (case, project, worse) in req:
            diffs[project].append(score - req[(case, project, worse)])
    values = [v for vs in diffs.values() for v in vs]
    return {"comparison": f"{better} - {worse}", "requirements": len(values), "projects": len(diffs),
            "mean_difference": sum(values) / len(values) if values else None,
            "requirements_higher": sum(v > 0 for v in values), "requirements_lower": sum(v < 0 for v in values),
            "ci95_project_bootstrap": project_bootstrap(diffs), "p_exact_project_sign_flip": project_sign_flip(diffs)}


def analyse(rows: list[dict]) -> dict:
    suites = suite_scores(rows)
    req = requirement_scores(suites)
    by_source = {}
    for source in SOURCES:
        ss = [s for s in suites if s["source"] == source]
        scores = [v for (c, p, s), v in req.items() if s == source]
        by_source[source] = {
            "suites": len(ss), "sound": sum(s["sound"] for s in ss), "unusable": sum(s["unusable"] for s in ss),
            "mean_requirement_mutation_score": sum(scores) / len(scores) if scores else None,
            "requirements_all_mutants_killed": sum(v == 1 for v in scores),
            "requirements_no_mutant_killed": sum(v == 0 for v in scores),
            "naive_score_pooled": (sum(s["naive_killed"] for s in ss) / sum(s["naive_mutants"] for s in ss))
            if ss else None,
            "recovered_alarm_rate": (sum(s["recovered_alarms"] for s in ss) / sum(s["recovered"] for s in ss))
            if sum(s["recovered"] for s in ss) else None,
            "correct_other_alarm_rate": (sum(s["correct_other_alarms"] for s in ss) / sum(s["correct_other"] for s in ss))
            if sum(s["correct_other"] for s in ss) else None,
        }
    return {"by_source": by_source,
            "primary": paired(req, "spec_complete", "spec_incomplete"),
            "secondary": paired(req, "spec_complete", "code_incomplete"),
            "suites": suites}


# ---------------------------------------------------------------- CLI

def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    sub = parser.add_subparsers(dest="mode", required=True)
    sub.add_parser("eligible")
    sub.add_parser("locate").add_argument("--evidence-root", type=Path, required=True)
    p = sub.add_parser("prepare")
    p.add_argument("--out", type=Path, required=True)
    p.add_argument("--packets", type=Path, required=True, help="JSON from locate")
    p.add_argument("--model", required=True)
    p.add_argument("--executable", type=Path, default=Path("/opt/homebrew/bin/codex"))
    for mode in ("generate", "execute", "analyse"):
        sub.add_parser(mode).add_argument("--out", type=Path, required=True)
    args = parser.parse_args(argv)
    if args.mode == "eligible":
        cases = eligible_cases()
        result = {"cases": len(cases), "projects": len({c["project_id"] for c in cases}),
                  "artifacts": dict(Counter(role for c in cases for role, s in c["roles"].items() for _ in s))}
    elif args.mode == "locate":
        result = locate(args.evidence_root, eligible_cases())
    elif args.mode == "prepare":
        packets = json.loads(args.packets.read_text())
        result = prepare(args.out, {k: Path(v) for k, v in packets.items()}, args.model, args.executable)
    elif args.mode == "generate":
        result = generate(args.out)
    elif args.mode == "execute":
        result = {k: v for k, v in execute(args.out).items() if k != "suites"}
    else:
        rows = json.loads((args.out / "results.json").read_text())["rows"]
        result = {k: v for k, v in analyse(rows).items() if k != "suites"}
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
