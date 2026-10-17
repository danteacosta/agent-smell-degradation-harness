"""Prepare a proposed product-only semantic review view, never scientific labels."""
from __future__ import annotations

import copy


VISIBLE = ("original_rule", "scenario", "trajectory")
IDENTITY = ("run_id", "replication_id", "constraint_id")


def prepare_blind_review(records: list[dict]) -> dict:
    """Preserve every supplied row in order; keep joins outside the review view.

    Text is not automatically de-identified. A human must inspect it for model,
    treatment and reward disclosures before sharing. No reward-based sampling
    or semantic verdict is performed here.
    """
    if not isinstance(records, list) or not records:
        raise ValueError("non-empty records required")
    review, join_key, seen = [], [], set()
    for index, row in enumerate(records):
        if not isinstance(row, dict):
            raise ValueError("record must be an object")
        for field in IDENTITY + VISIBLE:
            if not isinstance(row.get(field), str) or not row[field].strip():
                raise ValueError(f"non-empty {field} required; do not silently drop incomplete rows")
        identity = tuple(row[field] for field in IDENTITY)
        if identity in seen:
            raise ValueError("duplicate review identity")
        seen.add(identity)
        blind_id = f"item-{index + 1:04d}"
        review.append({"blind_id": blind_id, **{field: row[field] for field in VISIBLE}})
        join_key.append({"blind_id": blind_id, "source": copy.deepcopy(row)})
    return {
        "schema_version": "blind-semantic-review-draft/v1",
        "confirmatory_eligible": False,
        "scheduled_denominator": len(records),
        "review_view": review,
        "private_join_key": join_key,
        "release_gate": "Human disclosure screening and rubric approval required before reviewer release.",
    }
