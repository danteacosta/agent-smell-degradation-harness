"""Post-hoc assertion/error sensitivity; never modifies frozen study files.

An assertion alarm is not proof that the assertion checks the target condition.
Keep the original reference-quiet/usability gate and planned denominators.
"""
from __future__ import annotations

import argparse
from collections import Counter, defaultdict
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
from scripts import mutation_adequacy as ma

VERDICTS = {"quiet", "assertion_alarm", "error_alarm", "runner_error",
            "generation_failed", "suite_invalid"}


def validate(rows: list[dict], manifest: dict) -> None:
    """Require the exact frozen schedule/role grid, including failed slots."""
    cases = {c["case"]: c for c in manifest["cases"]}
    if not cases or len(cases) != len(manifest["cases"]):
        raise ValueError("empty or duplicate cases")
    expected = {}
    design = Counter()
    calls = set()
    for call in manifest["schedule"]:
        cid = call["call_id"]
        if cid in calls:
            raise ValueError("duplicate scheduled call")
        calls.add(cid)
        case = cases[call["case"]]
        roles = {slot: role for role, slots in case["roles"].items() for slot in slots}
        if len(roles) != sum(map(len, case["roles"].values())):
            raise ValueError("overlapping roles")
        if (case["reference"] not in case["roles"]["correct"]
                or not case["roles"]["mutant"]):
            raise ValueError("missing correct reference or confirmed mutant")
        if (len(call["targets"]) != len(roles) or set(call["targets"]) != set(roles)
                or call["project_id"] != case["project_id"]):
            raise ValueError("schedule targets or project mismatch")
        design[(call["case"], call["source"], call["suite_index"])] += 1
        for slot in call["targets"]:
            expected[(cid, slot)] = dict(call_id=cid, slot_id=slot, case=call["case"],
                project_id=case["project_id"], source=call["source"],
                suite_index=call["suite_index"], role=roles[slot],
                is_reference=slot == case["reference"])
    intended = Counter({(case, source, index): 1 for case in cases
                        for source in ma.SOURCES for index in (1, 2)})
    if design != intended:
        raise ValueError("incomplete or duplicate source/replication design")
    seen = set()
    by_call = defaultdict(set)
    for row in rows:
        key = (row["call_id"], row["slot_id"])
        if key in seen or key not in expected:
            raise ValueError("duplicate or unexpected pair")
        seen.add(key)
        if (type(row["is_reference"]) is not bool
                or any(row.get(k) != v for k, v in expected[key].items())):
            raise ValueError("row identity or role mismatch")
        if row["verdict"] not in VERDICTS:
            raise ValueError("unknown verdict")
        by_call[row["call_id"]].add(row["verdict"])
    if seen != set(expected):
        raise ValueError("missing planned pairs (retain failure placeholders)")
    for verdicts in by_call.values():
        if verdicts & {"generation_failed", "suite_invalid"} and len(verdicts) != 1:
            raise ValueError("generation failure mixed with execution outcomes")


def analyse(data: dict, manifest: dict) -> dict:
    rows = data["rows"]
    validate(rows, manifest)
    original = ma.analyse(rows)
    if original != data["analysis"]:
        raise ValueError("published analysis differs from frozen recomputation")
    suites = original["suites"]
    by_call = defaultdict(list)
    for row in rows:
        by_call[row["call_id"]].append(row)
    assertion_suites = []
    for suite in suites:
        killed = sum(suite["sound"] and r["role"] == "mutant"
                     and r["verdict"] == "assertion_alarm"
                     for r in by_call[suite["call_id"]])
        assertion_suites.append({**suite, "killed": killed,
                                 "mutation_score": killed / suite["mutants"]})
    req = ma.requirement_scores(assertion_suites)
    by_source = {}
    for source in ma.SOURCES:
        ss = [s for s in suites if s["source"] == source]
        eligible_ids = {s["call_id"] for s in ss if s["sound"]}
        mutants = [r for r in rows if r["source"] == source and r["role"] == "mutant"]
        eligible = [r for r in mutants if r["call_id"] in eligible_ids]
        counts = Counter(r["verdict"] for r in eligible)
        scores = [v for (case, project, s), v in req.items() if s == source]
        by_source[source] = {
            "planned_suites": len(ss), "eligible_suites": len(eligible_ids),
            "planned_mutant_pairs": len(mutants), "eligible_mutant_pairs": len(eligible),
            "eligible_mutant_verdicts": dict(sorted(counts.items())),
            "registered_score": original["by_source"][source]["mean_requirement_mutation_score"],
            "assertion_only_score": sum(scores) / len(scores),
            "assertion_kills": counts["assertion_alarm"], "error_kills": counts["error_alarm"],
        }
    return {"schema_version": "mutation-alarm-sensitivity/v1", "post_hoc": True,
            "confirmatory_eligible": False, "model": manifest["model"],
            "requirements": len(manifest["cases"]),
            "projects": len({c["project_id"] for c in manifest["cases"]}),
            "by_source": by_source,
            "assertion_score_by_requirement": [
                {"case": case, "project_id": project, "source": source, "score": score}
                for (case, project, source), score in sorted(req.items())],
            "target_specificity": "not_established_by_aggregate_verdicts"}


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("packet", type=Path)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    data = json.loads((args.packet / "results.json").read_text())
    manifest = json.loads((args.packet / "frozen-manifest-public.json").read_text())
    report = analyse(data, manifest)
    report["inputs_sha256"] = {name: ma.ta.sha256_file(args.packet / name)
                              for name in ("results.json", "frozen-manifest-public.json")}
    ma.ta.put(args.output, report)


if __name__ == "__main__":
    main()
