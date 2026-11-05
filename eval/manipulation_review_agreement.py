"""Describe pre-adjudication decisions; never infer validity or authorize admission."""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

from eval.manipulation_admission import (
    AGREEMENT_FIELDS, _reviewer_key, prepare_manipulation_admission,
)

DECISION_ORDER = ("admit", "exclude", "uncertain")


def summarize_agreement(reviews: list[dict], *, expected_candidate_ids: list[str]) -> dict:
    """Require the same two reviewers for every planned candidate; no case deletion.

    Reviewer IDs only establish recorded identity, not independent human custody.
    Decisions are nominal. Kappa is descriptive, without a cutoff or interval.
    """
    packet = prepare_manipulation_admission(
        reviews, expected_candidate_ids=expected_candidate_ids)
    candidates = packet["candidates"]
    identities = sorted({_reviewer_key(row["reviewer_id"]) for row in reviews})
    if len(identities) != 2 or any(item["review_count"] != 2 for item in candidates):
        raise ValueError("the same two reviewers must cover every candidate")
    table = [[0 for _ in DECISION_ORDER] for _ in DECISION_ORDER]
    for item in candidates:
        by_reviewer = {_reviewer_key(row["reviewer_id"]): row for row in item["reviews"]}
        left, right = [by_reviewer[identity]["decision"] for identity in identities]
        table[DECISION_ORDER.index(left)][DECISION_ORDER.index(right)] += 1
    n = len(candidates)
    diagonal = sum(table[i][i] for i in range(len(DECISION_ORDER)))
    row_totals = [sum(row) for row in table]
    column_totals = [sum(row[i] for row in table) for i in range(len(DECISION_ORDER))]
    marginal_product = sum(a * b for a, b in zip(row_totals, column_totals))
    denominator = n * n - marginal_product
    # Bind every validated response, including reasons, not just aggregate counts.
    # Canonical order ignores input row/key order while retaining original text.
    snapshot = [row for item in candidates for row in sorted(
        item["reviews"], key=lambda row: _reviewer_key(row["reviewer_id"]))]
    payload = json.dumps(snapshot, sort_keys=True, ensure_ascii=False,
                         separators=(",", ":")).encode("utf-8")
    return {
        "schema_version": "manipulation-review-agreement/v1",
        "status": "descriptive_pre_adjudication_only",
        "confirmatory_eligible": False,
        "candidate_count": n,
        "review_count": len(reviews),
        "candidate_inventory_sha256": packet["candidate_inventory_sha256"],
        "review_content_sha256": hashlib.sha256(payload).hexdigest(),
        "review_content_digest_scope": (
            "Validated review objects in supplied candidate-inventory order, then "
            "NFKC/casefold reviewer sort order; JSON sorted keys, ensure_ascii=false, "
            "compact separators, UTF-8. Original values/list order retained. "
            "Not a raw-file checksum, custody attestation or rubric/source commitment."),
        "reviewer_order": identities,
        "field_agreement": {
            field: {
                "agreeing_candidates": sum(item["agreement"][field] for item in candidates),
                "candidate_denominator": n,
                "agreement_rate": sum(item["agreement"][field] for item in candidates) / n,
            } for field in AGREEMENT_FIELDS
        },
        "decision_agreement": {
            "categories": list(DECISION_ORDER),
            "matrix_rows_reviewer_0_columns_reviewer_1": table,
            "row_totals": row_totals,
            "column_totals": column_totals,
            "observed_agreement": diagonal / n,
            "expected_agreement_from_marginals": marginal_product / (n * n),
            "cohen_kappa_unweighted_nominal": (
                (n * diagonal - marginal_product) / denominator if denominator else None),
            "kappa_undefined_reason": "degenerate_marginals" if not denominator else None,
        },
        "limitations": [
            "Descriptive agreement on the supplied pre-adjudication reviews, not label validity.",
            "Identity strings cannot establish human status, blinding or independence.",
            "The review-content digest binds supplied responses, not authorship or collection time.",
            "No acceptance cutoff, project-clustered interval or population inference is supplied.",
            "Retain disagreements and original responses for human adjudication; do not overwrite them.",
        ],
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--reviews", type=Path, required=True,
                        help="private JSON array of original independent reviews")
    parser.add_argument("--expected-candidate-ids", type=Path, required=True,
                        help="JSON array from the separately approved review inventory")
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    try:
        report = summarize_agreement(
            json.loads(args.reviews.read_text(encoding="utf-8")),
            expected_candidate_ids=json.loads(args.expected_candidate_ids.read_text(encoding="utf-8")))
        with args.output.open("x", encoding="utf-8") as stream:
            stream.write(json.dumps(report, ensure_ascii=False, indent=2) + "\n")
    except (OSError, ValueError, KeyError, TypeError) as error:
        parser.exit(1, f"error: {error}\n")
    print(json.dumps({"status": report["status"], "candidate_count": report["candidate_count"],
                      "confirmatory_eligible": False}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

