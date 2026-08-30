"""Independent T4 label-plane dimensions for acceptance criteria.

The confirmatory outcome is supplied as an independently reviewed decision for
each ``constraint_id``.  Textual substring matching is intentionally not used
as a semantic oracle: it is available to callers as a separate diagnostic
baseline, never as a human outcome substitute.
"""
from __future__ import annotations
from typing import Any, Iterable, Mapping, Sequence

DIMENSIONS = (
    "structural_validity",
    "testable_condition_coverage",
    "semantic_omission",
    "spurious_criteria",
    "external_traceability",
)

_STATUSES = frozenset({"covered", "omitted", "uncertain"})


def validate_constraint_outcomes(
    outcomes: Iterable[Mapping[str, Any]],
    reference_constraints: Sequence[str],
) -> list[dict[str, Any]]:
    """Validate the adjudicated T4 outcome table without deriving labels.

    Each reference constraint must have exactly one independent label-plane
    row.  The function validates the contract only; humans or an approved
    adjudication process must provide the status.
    """

    expected = tuple(str(value).strip() for value in reference_constraints if str(value).strip())
    if len(set(expected)) != len(expected):
        raise ValueError("reference constraints require unique non-empty IDs")
    rows = [dict(row) for row in outcomes]
    ids = [str(row.get("constraint_id", "")).strip() for row in rows]
    if any(not value for value in ids) or len(set(ids)) != len(ids):
        raise ValueError("constraint outcomes require unique non-empty constraint_id values")
    if set(ids) != set(expected):
        raise ValueError("constraint outcomes must cover exactly the reference constraint IDs")
    for row in rows:
        status = str(row.get("status", "")).strip()
        if status not in _STATUSES:
            raise ValueError(f"constraint outcome status must be one of {sorted(_STATUSES)}")
        if row.get("plane", "label") != "label":
            raise ValueError("constraint outcomes must remain in the label plane")
        row["constraint_id"] = str(row["constraint_id"]).strip()
        row["status"] = status
        row["plane"] = "label"
    return sorted(rows, key=lambda row: row["constraint_id"])


def evaluate_dimensions(
    *,
    artifact: Mapping[str, Any],
    reference_constraints: Sequence[str],
    constraint_outcomes: Iterable[Mapping[str, Any]],
    spurious_criteria_count: int = 0,
    traceability_valid: bool | None = None,
) -> dict[str, int]:
    """Return separate T4 dimensions from reviewed per-constraint outcomes.

    ``constraint_outcomes`` is deliberately mandatory.  This prevents a
    convenient lexical heuristic from silently becoming the confirmatory
    semantic metric.
    """

    outcomes = validate_constraint_outcomes(constraint_outcomes, reference_constraints)
    if spurious_criteria_count < 0:
        raise ValueError("spurious_criteria_count cannot be negative")
    return {
        "structural_validity": int(bool(artifact)),
        "testable_condition_coverage": sum(row["status"] == "covered" for row in outcomes),
        "semantic_omission": sum(row["status"] == "omitted" for row in outcomes),
        "spurious_criteria": int(spurious_criteria_count),
        "external_traceability": int(traceability_valid is True),
    }

__all__ = ("DIMENSIONS", "evaluate_dimensions", "validate_constraint_outcomes")
