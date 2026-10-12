"""One descriptive table across every tester of the shared-omission study.

Written before the results of later testers exist, so that adding a run cannot
change how runs are summarised. Reads the registry
(data/shared-omission-e2e/testers.json), checks that every evaluated run used
the same 25 requirements, the same pages and the same shown mutants as the
first run, recomputes each run with the frozen analysis (no reliance on the
stored numbers) and reports, per tester:

  - the equal-requirement score per source and the number of sound suites;
  - MA1 (complete - incomplete) and MA2 (complete - incomplete + mutant code):
    mean difference, project-bootstrap interval, exact project p, and the
    requirements higher / lower / tied;
  - the reference-versus-shown-mutant pattern: suites that fail the correct
    reference by assertion while passing the mutant they were shown, per source;
  - detection among sound suites on confirmed mutants.

It also counts, per requirement, in how many evaluated testers the complete
source scored higher than the incomplete one. Testers are never pooled and no
test is computed across them: they share pages, requirements and, within a
provider, model families, so they are not independent replications.
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

from scripts import mutation_adequacy as ma  # noqa: E402

REGISTRY = ROOT / "data/shared-omission-e2e/testers.json"
SOURCES = ("spec_complete", "spec_incomplete", "code_incomplete")
SCHEMA = "shared-omission-testers-summary/v1"


def load(path: str) -> dict:
    return json.loads((ROOT / path).read_text())


def design_key(manifest: dict) -> dict:
    cases = {c["case"]: {"reference": c["reference"],
                         "roles": {k: sorted(v) for k, v in c["roles"].items()}} for c in manifest["cases"]}
    return {"cases": cases, "selected_mutants": manifest["selected_mutants"]}


def reversal(rows: list[dict], selected: dict) -> dict:
    """Per source: suites failing the correct reference by assertion and quiet on the shown mutant."""
    by = defaultdict(dict)
    for r in rows:
        if r["is_reference"]:
            by[r["call_id"]].update(source=r["source"], ref=r["verdict"])
        if r["slot_id"] == selected[r["case"]]:
            by[r["call_id"]]["shown"] = r["verdict"]
    out = {}
    for s in SOURCES:
        suites = [v for v in by.values() if v.get("source") == s]
        out[s] = {"suites": len(suites),
                  "reference_assertion_and_shown_quiet": sum(v.get("ref") == "assertion_alarm"
                                                             and v.get("shown") == "quiet" for v in suites)}
    return out


def sound_detection(rows: list[dict]) -> dict:
    sound = {s["call_id"] for s in ma.suite_scores(rows) if s["sound"]}
    out = {}
    for s in SOURCES:
        pairs = [r for r in rows if r["source"] == s and r["call_id"] in sound and r["role"] == "mutant"]
        out[s] = {"alarms": sum(r["verdict"] in ma.ALARMS for r in pairs), "pairs": len(pairs)}
    return out


def requirement_scores(rows: list[dict]) -> dict[str, dict[str, float]]:
    per = defaultdict(lambda: defaultdict(list))
    for s in ma.suite_scores(rows):
        per[s["source"]][s["case"]].append(s["mutation_score"] or 0.0)
    return {src: {case: sum(v) / len(v) for case, v in cases.items()} for src, cases in per.items()}


def summarise(registry: dict) -> dict:
    for r in registry["runs"]:
        if r["status"] not in ("evaluated", "failed_evaluation"):
            raise ValueError(f"unknown status {r['status']!r}")
        if r["status"] == "failed_evaluation" and not r.get("reason"):
            raise ValueError(f"{r['tester']}: a failed evaluation needs a reason")
    evaluated = [r for r in registry["runs"] if r["status"] == "evaluated"]
    excluded = [{k: r[k] for k in ("tester", "status", "reason", "pr")} for r in registry["runs"]
                if r["status"] != "evaluated"]
    if not evaluated:
        raise ValueError("no evaluated run")
    reference = design_key(load(evaluated[0]["manifest"]))
    testers, req_higher = [], Counter()
    for run in evaluated:
        manifest, results = load(run["manifest"]), load(run["results"])
        if design_key(manifest) != reference:
            raise ValueError(f"{run['tester']}: different requirements, pages or shown mutants than the first run")
        rows = results["rows"]
        analysis = ma.analyse(rows)
        stored = {k: v for k, v in results["analysis"].items() if k != "suites"}
        if {k: v for k, v in analysis.items() if k != "suites"} != stored:
            raise ValueError(f"{run['tester']}: stored analysis differs from the frozen recomputation")
        req = requirement_scores(rows)
        for case in req["spec_complete"]:
            req_higher[case] += req["spec_complete"][case] > req["spec_incomplete"][case]

        def contrast(c):
            return {"mean_difference": round(c["mean_difference"], 4),
                    "ci95_project_bootstrap": [round(x, 4) for x in c["ci95_project_bootstrap"]],
                    "p_exact_project_sign_flip": c["p_exact_project_sign_flip"],
                    "requirements_higher_lower_tied": [c["requirements_higher"], c["requirements_lower"],
                                                       c["requirements"] - c["requirements_higher"]
                                                       - c["requirements_lower"]]}
        testers.append({
            "tester": run["tester"], "provider": run["provider"], "pr": run["pr"],
            "score": {s: round(analysis["by_source"][s]["mean_requirement_mutation_score"], 4) for s in SOURCES},
            "sound_suites": {s: analysis["by_source"][s]["sound"] for s in SOURCES},
            "MA1_complete_minus_incomplete": contrast(analysis["primary"]),
            "MA2_complete_minus_incomplete_code": contrast(analysis["secondary"]),
            "reference_assertion_and_shown_mutant_quiet": reversal(rows, manifest["selected_mutants"]),
            "sound_suite_detection_of_confirmed_mutants": sound_detection(rows),
        })
    n = len(evaluated)
    return {"schema_version": SCHEMA, "exploratory": True, "rule": registry["rule"],
            "evaluated_runs": n, "excluded_runs": excluded,
            "requirements": len(reference["cases"]), "testers": testers,
            "requirements_complete_higher_in_k_of_n_testers": {
                "n_testers": n,
                "distribution": {str(k): sum(1 for c in reference["cases"] if req_higher[c] == k)
                                 for k in range(n + 1)}},
            "note": ("Testers share pages, requirements and implementations; within a provider they may share "
                     "model families. The table is descriptive; no test is computed across testers.")}


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--registry", type=Path, default=REGISTRY)
    parser.add_argument("--out", type=Path, default=ROOT / "data/shared-omission-e2e/testers-summary.json")
    args = parser.parse_args(argv)
    result = summarise(json.loads(args.registry.read_text()))
    args.out.write_text(json.dumps(result, indent=2) + "\n")
    for t in result["testers"]:
        print(t["tester"], t["score"], "MA1", t["MA1_complete_minus_incomplete"]["mean_difference"])


if __name__ == "__main__":
    main()
