"""Prepare reviewer evidence for prospective omission-manipulation admission."""
from __future__ import annotations

import copy


REQUIRED = (
    "candidate_id",
    "reviewer_id",
    "removed_span",
    "target_constraint_id",
    "dependent_constraint_ids",
    "non_target_obligations_preserved",
    "plausible_remainder",
    "decision",
    "reason",
)
FORBIDDEN = {
    "reward",
    "terminal_defect",
    "generated_output",
    "oracle_verdict",
    "model",
    "provider",
    "arm",
    "treatment",
}
DECISIONS = {"admit", "exclude", "uncertain"}
AGREEMENT_FIELDS = (
    "removed_span",
    "target_constraint_id",
    "dependent_constraint_ids",
    "non_target_obligations_preserved",
    "plausible_remainder",
    "decision",
)


def _candidate_summary(candidate_id: str, reviews: list[dict]) -> dict:
    agreement = {}
    for field in AGREEMENT_FIELDS:
        values = [
            tuple(row[field]) if field == "dependent_constraint_ids" else row[field]
            for row in reviews
        ]
        agreement[field] = len(set(values)) == 1

    has_blocking_judgment = any(
        row["decision"] != "admit"
        or row["dependent_constraint_ids"]
        or not row["non_target_obligations_preserved"]
        or not row["plausible_remainder"]
        for row in reviews
    )
    return {
        "candidate_id": candidate_id,
        "review_count": len(reviews),
        "agreement": agreement,
        "requires_adjudication": has_blocking_judgment or not all(agreement.values()),
        "reviews": reviews,
    }


def prepare_manipulation_admission(
    reviews: list[dict], *, expected_candidate_ids: list[str]
) -> dict:
    """Validate complete, outcome-blind independent reviews for adjudication.

    This function does not decide whether a manipulation is scientifically valid.
    It only ensures that every frozen candidate has at least two distinct reviews
    with the evidence required by the proposed dependency checklist.
    """
    if not isinstance(expected_candidate_ids, list) or not expected_candidate_ids:
        raise ValueError("non-empty expected candidate inventory required")
    if any(not isinstance(value, str) or not value.strip() for value in expected_candidate_ids):
        raise ValueError("non-empty expected candidate ids required")
    if len(set(expected_candidate_ids)) != len(expected_candidate_ids):
        raise ValueError("duplicate expected candidate id")
    if not isinstance(reviews, list) or not reviews:
        raise ValueError("non-empty reviews required")

    grouped: dict[str, list[dict]] = {value: [] for value in expected_candidate_ids}
    seen: set[tuple[str, str]] = set()
    for review in reviews:
        if not isinstance(review, dict):
            raise ValueError("review must be an object")
        leaked = FORBIDDEN.intersection(review)
        if leaked:
            raise ValueError(f"outcome or treatment fields forbidden: {sorted(leaked)}")
        missing = [field for field in REQUIRED if field not in review]
        if missing:
            raise ValueError(f"missing review fields: {missing}")
        for field in ("candidate_id", "reviewer_id", "removed_span", "target_constraint_id", "reason"):
            if not isinstance(review[field], str) or not review[field].strip():
                raise ValueError(f"non-empty {field} required")
        if review["candidate_id"] not in grouped:
            raise ValueError("review candidate is outside expected inventory")
        if review["decision"] not in DECISIONS:
            raise ValueError("invalid review decision")
        if not isinstance(review["dependent_constraint_ids"], list) or any(
            not isinstance(value, str) or not value.strip()
            for value in review["dependent_constraint_ids"]
        ):
            raise ValueError("dependent_constraint_ids must be a list of non-empty strings")
        if len(set(review["dependent_constraint_ids"])) != len(review["dependent_constraint_ids"]):
            raise ValueError("duplicate dependent constraint id")
        for field in ("non_target_obligations_preserved", "plausible_remainder"):
            if not isinstance(review[field], bool):
                raise ValueError(f"boolean {field} required")
        identity = (review["candidate_id"], review["reviewer_id"])
        if identity in seen:
            raise ValueError("duplicate candidate-reviewer identity")
        seen.add(identity)
        grouped[review["candidate_id"]].append(copy.deepcopy(review))

    incomplete = [candidate_id for candidate_id, rows in grouped.items() if len(rows) < 2]
    if incomplete:
        raise ValueError(f"at least two independent reviews required for: {incomplete}")

    return {
        "schema_version": "manipulation-admission-review/v1",
        "confirmatory_eligible": False,
        "inventory_coverage_checked": True,
        "candidate_count": len(grouped),
        "review_count": len(reviews),
        "candidates": [
            _candidate_summary(candidate_id, grouped[candidate_id])
            for candidate_id in expected_candidate_ids
        ],
        "next_gate": "Human adjudication and rubric approval required before admission.",
    }
