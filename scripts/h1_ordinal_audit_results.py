"""Audit blinded ordinal votes and retain missingness bounds for a saved pilot."""
from __future__ import annotations

import argparse
from collections import Counter, defaultdict
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from label_plane.exploratory_judge import parse_judge_response, validate_judge_request
from scripts.h1_existing_artifacts_ordinal_audit import RUBRIC, judge_prompt, source_rows
from scripts.criteria_consensus import verify
from scripts.persistence_collection import hash_file

SEVERITY = {"clean": 0, "minor": 1, "moderate": 2, "severe": 3}


def interval(arms: dict[str, int | None]) -> tuple[int, int]:
    """Sharp per-cell A-minus-C range when missing ordinal scores are 0..3."""
    a, c = arms["A"], arms["C"]
    return (a if a is not None else 0) - (c if c is not None else 3), (
        a if a is not None else 3) - (c if c is not None else 0)


def citation_valid(assessments, criteria: str) -> bool:
    """Reject unsupported quotes without changing any model response."""
    for item in assessments:
        if item.status in ("covered", "uncertain"):
            if not item.evidence or item.evidence not in criteria:
                return False
        elif item.status == "omitted" and item.evidence:
            return False
    return True


def derive(packet: Path, parent: Path) -> tuple[dict, dict]:
    manifest = json.loads((packet / "manifest.json").read_text())
    for key, path in (
        ("parent_receipt_sha256", parent / "receipt.json"),
        ("parent_results_sha256", parent / "results.json"),
        ("parent_schedule_sha256", parent / "frozen/schedule.json"),
        ("parent_corpus_sha256", parent / "frozen/corpus.json"),
        ("script_sha256", packet / "frozen-runtime.py"),
        ("rubric_sha256", RUBRIC),
    ):
        if manifest[key] != hash_file(path):
            raise ValueError("source or runtime drift: " + key)
    if manifest.get("planned_artifacts") != 48 or manifest.get("confirmatory_eligible") is not False:
        raise ValueError("unexpected study contract")
    source, _ = source_rows(parent)
    eligible = {row["artifact_id"]: row for row in source if row["request"] is not None}
    if len(eligible) != manifest["valid_artifacts"] or len(manifest["slots"]) != 2 * len(eligible):
        raise ValueError("sample inventory drift")
    rubric = json.loads(RUBRIC.read_text())

    votes: dict[str, dict[str, dict]] = defaultdict(dict)
    citation_invalid = Counter()
    label_counts: dict[str, Counter] = {judge: Counter() for judge in manifest["judges"]}
    for slot in manifest["slots"]:
        sid, aid, judge = (slot[key] for key in ("slot_id", "artifact_id", "judge"))
        if judge in votes[aid]:
            raise ValueError("duplicate judge slot")
        request = validate_judge_request(json.loads((packet / "requests" / (sid + ".json")).read_text()))
        call = packet / "calls" / sid
        if not (call / "attempt.json").is_file() or not (call / "result.json").is_file():
            raise ValueError("incomplete call slot")
        if aid not in eligible or request != validate_judge_request(eligible[aid]["request"]):
            raise ValueError("blind request differs from saved artifact")
        prompt_path = packet / "prompts" / (sid + ".txt")
        if (prompt_path.read_text() != judge_prompt(eligible[aid]["request"], rubric)
                or json.loads((call / "attempt.json").read_text())["prompt_sha256"] != hash_file(prompt_path)):
            raise ValueError("attempted prompt differs from frozen input")
        result = json.loads((call / "result.json").read_text())
        if result.get("status") != "valid":
            votes[aid][judge] = {"status": result.get("status", "unknown")}
            continue
        parsed = parse_judge_response((call / "response.txt").read_text(), request)
        assessments = {item.constraint_id: item.status for item in parsed.constraint_assessments}
        if parsed.label != result.get("label") or assessments != result.get("assessments"):
            raise ValueError("saved result differs from raw vote")
        evidence_ok = citation_valid(parsed.constraint_assessments, request.generated_acceptance_criteria)
        for item in parsed.constraint_assessments:
            if item.status in ("covered", "uncertain"):
                valid = bool(item.evidence) and item.evidence in request.generated_acceptance_criteria
            else:
                valid = item.evidence == ""
            if not valid:
                citation_invalid[judge] += 1
        label_counts[judge][parsed.label] += 1
        votes[aid][judge] = {"status": "valid", "label": parsed.label,
                             "assessments": assessments, "citation_valid": evidence_ok}

    score: dict[str, int] = {}
    label_agreement = 0
    full_agreement = 0
    for aid, pair in votes.items():
        if set(pair) != set(manifest["judges"]):
            raise ValueError("unbalanced judge pair")
        a, b = (pair[judge] for judge in manifest["judges"])
        if a.get("status") == b.get("status") == "valid" and a["label"] == b["label"]:
            label_agreement += 1
            if a["assessments"] == b["assessments"] and a["label"] in SEVERITY:
                full_agreement += 1
                if a["citation_valid"] and b["citation_valid"]:
                    score[aid] = SEVERITY[a["label"]]

    schedule = json.loads((parent / "frozen/schedule.json").read_text())["generations"]
    selected = [row for row in schedule if row["replication"] == 1 and row["variant"] in ("A", "C")]
    cells: dict[tuple[str, str, str], dict[str, int | None]] = defaultdict(dict)
    for row in selected:
        cells[(row["intent_id"], row["project_id"], row["model"])][row["variant"]] = score.get(row["artifact_id"])
    if len(selected) != 48 or len(cells) != 24 or any(set(arms) != {"A", "C"} for arms in cells.values()):
        raise ValueError("sample frame drift")
    ranges = [interval(arms) for arms in cells.values()]
    paired = [arms["A"] - arms["C"] for arms in cells.values()
              if arms["A"] is not None and arms["C"] is not None]
    projects = {}
    for project in sorted({key[1] for key in cells}):
        selected_ranges = [interval(arms) for key, arms in cells.items() if key[1] == project]
        projects[project] = {"cells": len(selected_ranges),
                             "lower": sum(x[0] for x in selected_ranges) / len(selected_ranges),
                             "upper": sum(x[1] for x in selected_ranges) / len(selected_ranges),
                             "complete_pairs": sum(arms["A"] is not None and arms["C"] is not None
                                                   for key, arms in cells.items() if key[1] == project)}
    summary = {
        "schema_version": "h1-existing-ordinal-audit-results/v1",
        "status": "secondary_exploratory", "confirmatory_eligible": False,
        "human_approvals": 0, "parent_receipt_sha256": manifest["parent_receipt_sha256"],
        "planned_artifacts": 48, "invalid_original_generations": 48 - len(votes),
        "valid_artifacts": len(votes), "judge_calls": len(manifest["slots"]),
        "valid_judge_calls": sum(x.get("status") == "valid" for pair in votes.values() for x in pair.values()),
        "label_agreement_artifacts": label_agreement,
        "full_label_and_constraint_agreement_artifacts": full_agreement,
        "citation_invalid_assessments_by_judge": dict(citation_invalid),
        "strict_consensus_artifacts": len(score),
        "strict_consensus_labels": dict(Counter(next(label for label, value in SEVERITY.items() if value == item)
                                              for item in score.values())),
        "complete_a_c_cells": len(paired), "planned_a_c_cells": len(cells),
        "complete_cell_mean_a_minus_c": sum(paired) / len(paired) if paired else None,
        "complete_cell_delta_distribution": dict(Counter(str(item) for item in paired)),
        "planned_denominator_bounds_a_minus_c": {
            "lower": sum(item[0] for item in ranges) / len(ranges),
            "upper": sum(item[1] for item in ranges) / len(ranges),
        },
        "project_bounds": projects,
        "interpretation": "Missingness bounds and LLM consensus are descriptive; not an H1 confidence interval or human adjudication.",
    }
    private = {**summary, "artifact_scores": score,
               "cells": [{"intent_id": key[0], "project_id": key[1], "model": key[2],
                          "A": arms["A"], "C": arms["C"], "bounds": interval(arms)}
                         for key, arms in sorted(cells.items())]}
    return summary, private


def verify_sealed(packet: Path, parent: Path, public_output: Path, receipt_sha256: str) -> dict:
    """Recompute a sealed result and compare both outputs without changing the packet."""
    verify(packet, expected=receipt_sha256)
    summary, private = derive(packet, parent)
    if json.loads(public_output.read_text()) != json.loads(json.dumps(summary)):
        raise ValueError("public result differs from sealed packet")
    if json.loads((packet / "analysis.json").read_text()) != json.loads(json.dumps(private)):
        raise ValueError("private analysis differs from sealed packet")
    return summary


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--packet", required=True, type=Path)
    parser.add_argument("--parent", required=True, type=Path)
    parser.add_argument("--public-output", required=True, type=Path)
    parser.add_argument("--verify-sealed-receipt-sha256")
    args = parser.parse_args()
    if args.verify_sealed_receipt_sha256:
        print(json.dumps(verify_sealed(args.packet, args.parent, args.public_output,
                                       args.verify_sealed_receipt_sha256), sort_keys=True))
        return
    summary, private = derive(args.packet, args.parent)
    args.public_output.parent.mkdir(parents=True, exist_ok=True)
    args.public_output.write_text(json.dumps(summary, sort_keys=True, indent=2) + "\n")
    (args.packet / "analysis.json").write_text(json.dumps(private, sort_keys=True, indent=2) + "\n")
    print(json.dumps(summary, sort_keys=True))


if __name__ == "__main__":
    main()
