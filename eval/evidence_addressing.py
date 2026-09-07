"""Bounded offline audit. No provider dispatch, budget mutation, or launch path."""
from __future__ import annotations

import argparse
from collections import Counter
import json
from pathlib import Path
from typing import Any

from label_plane.addressed_judge import PROMPT_VERSION, checked_item, parse_response
from label_plane.artifact_segments import EvidenceContractError, build_snapshot
from label_plane.evidence_json import load_json
from label_plane.scoped_judge import STATUSES

MAX_RECORDS = 1000
MAX_INPUT_BYTES = 1_048_576


def _record_input(record: Any) -> tuple[dict[str, Any], list[str] | None]:
    required = {"item", "raw_response"}
    if (not isinstance(record, dict) or not required <= set(record)
            or set(record) - required - {"expected_checks"}):
        raise EvidenceContractError("invalid_record")
    item = checked_item(record["item"])
    expected = record.get("expected_checks")
    if "expected_checks" in record:
        if (not isinstance(expected, list) or len(expected) != len(item["obligations"])
                or any(not isinstance(s, str) or s not in STATUSES for s in expected)):
            raise EvidenceContractError("invalid_answers")
    return item, expected


def summarize(records: list[dict[str, Any]]) -> dict[str, Any]:
    """Aggregate supplied records only; the independent study plan is not known."""
    if not isinstance(records, list) or not 1 <= len(records) <= MAX_RECORDS:
        raise EvidenceContractError("invalid_audit")
    errors: Counter[str] = Counter()
    statuses = dict.fromkeys(sorted(STATUSES), 0)
    answer_records = valid_with_answers = matches = records_without_answers = 0
    valid = 0
    for record in records:
        try:
            item, expected = _record_input(record)
            if expected is None:
                records_without_answers += 1
            else:
                answer_records += 1
            if record["raw_response"] is None:
                raise EvidenceContractError("missing_response")
            result = parse_response(record["raw_response"], item)
        except EvidenceContractError as exc:
            # Only fixed contract codes cross the aggregate boundary. Do not
            # catch and print arbitrary exceptions or raw provider messages.
            errors[str(exc)] += 1
            continue
        valid += 1
        statuses[result["status"]] += 1
        if expected is not None:
            valid_with_answers += 1
            matches += [c["status"] for c in result["checks"]] == expected
    return {"schema_version": "addressed-evidence-audit/v1", "mode": "offline_audit",
            "prompt_version": PROMPT_VERSION, "attempted_records": len(records),
            "valid_responses": valid, "invalid_records": len(records) - valid,
            "first_error_counts": dict(sorted(errors.items())),
            "valid_response_status_counts": statuses,
            "construction_agreement": {
                "answer_records": answer_records, "valid_responses": valid_with_answers,
                "matching": matches, "mismatching": valid_with_answers - matches,
                "unscored": answer_records - valid_with_answers,
                "records_without_answers": records_without_answers},
            "semantic_validity": "not_measured", "main_collection_released": False,
            "provider_calls_dispatched": 0, "planned_provider_calls": None}


def demo_records() -> list[dict[str, Any]]:
    """Authored toy responses, including a real citation that supports no claim."""
    item = {"criteria": "The record is stored.", "reference": "Store the record.",
            "scope": "complete", "obligations": [{"id": "c1", "text": "Store the record."}]}

    def row(value, ids, expected="covered"):
        return {"item": value, "expected_checks": [expected], "raw_response": json.dumps({
            "checks": [{"id": "c1", "status": "covered", "evidence_ids": ids}]})}

    correct = row(item, [build_snapshot(item["criteria"])["segments"][0]["id"]])
    invented = row(item, ["reference-only-id"])
    missing = {"item": item, "expected_checks": ["covered"], "raw_response": None}
    unrelated = {"criteria": "The heading mentions encryption.",
                 "reference": "Encrypt stored records.", "scope": "complete",
                 "obligations": [{"id": "c1", "text": "Encrypt stored records."}]}
    irrelevant = row(unrelated, [build_snapshot(unrelated["criteria"])["segments"][0]["id"]],
                     expected="omitted")
    return [correct, invented, missing, irrelevant]


def read_records(path: Path) -> list[dict[str, Any]]:
    """Read one bounded local file, with no raw values or paths in failures."""
    try:
        if not path.is_file():
            raise ValueError
        with path.open("rb") as stream:
            data = stream.read(MAX_INPUT_BYTES + 1)
        if len(data) > MAX_INPUT_BYTES:
            raise ValueError
        return load_json(data.decode("utf-8"))
    except (OSError, ValueError, RecursionError) as exc:
        raise EvidenceContractError("invalid_audit_file") from exc


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    source = parser.add_mutually_exclusive_group(required=True)
    source.add_argument("--demo", action="store_true", help="Run authored toy responses, not models")
    source.add_argument("--input", type=Path, help="Local private JSON array, at most 1 MiB")
    args = parser.parse_args(argv)
    try:
        report = summarize(demo_records() if args.demo else read_records(args.input))
    except EvidenceContractError as exc:
        print(json.dumps({"error": str(exc), "provider_calls_dispatched": 0,
                          "main_collection_released": False}))
        return 2
    if args.demo:
        report["mode"] = "toy_demo"
    print(json.dumps(report, indent=2, sort_keys=True))
    return 0 if args.demo or report["invalid_records"] == 0 else 2


if __name__ == "__main__":
    raise SystemExit(main())
