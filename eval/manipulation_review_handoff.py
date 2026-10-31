"""Export one unfilled manipulation-review assignment without sharing peer forms."""
from __future__ import annotations

import argparse
import copy
import hashlib
import json
from pathlib import Path

from eval.manipulation_admission import REQUIRED, candidate_inventory_sha256


def prepare_assignment(template: dict, candidates: dict, slot: str) -> dict:
    """Check the complete template, then project only the requested blank slot.

    This prepares routing, not a corpus freeze, a rubric approval or human review.
    Caller-supplied material hashes are not independent custody attestations.
    """
    if template.get("schema_version") != "manipulation-review-authoring-template/v1":
        raise ValueError("unsupported authoring template schema")
    if template.get("status") != "unfilled_not_admission_evidence":
        raise ValueError("unfilled template required")
    if template.get("confirmatory_eligible") is not False:
        raise ValueError("template must not claim confirmatory eligibility")
    raw = json.dumps(candidates, sort_keys=True, ensure_ascii=False,
                     separators=(",", ":")).encode("utf-8")
    digest = hashlib.sha256(raw).hexdigest()
    if template.get("candidate_content_sha256") != digest:
        raise ValueError("candidate content digest mismatch")
    ids = [row["intent_id"] for row in candidates["records"]]
    if not ids or len(ids) != len(set(ids)) or template.get("expected_candidate_ids") != ids:
        raise ValueError("candidate inventory mismatch")
    slots = template.get("review_slots")
    if not isinstance(slots, list) or len(slots) != 2:
        raise ValueError("exactly two review slots required")
    names = [item.get("slot") for item in slots]
    if names != ["reviewer_A", "reviewer_B"] or slot not in names:
        raise ValueError("distinct reviewer_A/reviewer_B slots required")
    for item in slots:
        rows = item.get("reviews")
        if not isinstance(rows, list) or len(rows) != len(ids):
            raise ValueError("complete review coverage required")
        for expected_id, row in zip(ids, rows):
            if not isinstance(row, dict) or set(row) != set(REQUIRED):
                raise ValueError("unexpected review fields")
            if row["candidate_id"] != expected_id:
                raise ValueError("review candidate order mismatch")
            if any(row[key] is not None for key in REQUIRED if key != "candidate_id"):
                raise ValueError("only blank review forms may be exported")
    return {
        "schema_version": "manipulation-review-assignment/v1",
        "status": "unfilled_not_admission_evidence",
        "slot": slot,
        "candidate_content_sha256": digest,
        "candidate_inventory_sha256": candidate_inventory_sha256(ids),
        "expected_candidate_ids": list(ids),
        "reviews": copy.deepcopy(slots[names.index(slot)]["reviews"]),
        "confirmatory_eligible": False,
        "instructions": [
            "The custodian must separately provide the same pinned source materials and approved rubric.",
            "Slots are routing labels, not human identities or proof of independence.",
            "Complete only your own forms without generated outputs, provider identities or peer judgments.",
            "Keep completed responses private; adjudication and human approval remain required.",
        ],
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--template", type=Path, required=True)
    parser.add_argument("--candidates", type=Path, required=True)
    parser.add_argument("--slot", choices=("reviewer_A", "reviewer_B"), required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    try:
        packet = prepare_assignment(
            json.loads(args.template.read_text(encoding="utf-8")),
            json.loads(args.candidates.read_text(encoding="utf-8")), args.slot)
        # Exclusive creation keeps an earlier assignment or completed response intact.
        with args.output.open("x", encoding="utf-8") as stream:
            stream.write(json.dumps(packet, ensure_ascii=False, indent=2) + "\n")
    except (OSError, ValueError, KeyError, TypeError) as error:
        parser.exit(1, f"error: {error}\n")
    print(json.dumps({"status": "prepared_unfilled", "slot": args.slot,
                      "candidate_count": len(packet["reviews"]),
                      "confirmatory_eligible": False}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
