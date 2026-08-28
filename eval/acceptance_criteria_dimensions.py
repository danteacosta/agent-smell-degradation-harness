"""Independent label-plane dimensions for generated acceptance criteria.

These outcomes deliberately do not enter T1--T3 feature construction. They
make a final artifact review explain *how* it failed, rather than reducing all
failures to a single score.
"""
from __future__ import annotations
from typing import Any, Mapping, Sequence

DIMENSIONS = ("structural_validity", "testable_condition_coverage", "semantic_omission", "spurious_criteria", "external_traceability")

def evaluate_dimensions(*, artifact: Mapping[str, Any], reference_constraints: Sequence[str], traceability_valid: bool | None = None) -> dict[str, int]:
    criteria = [str(value).lower() for value in artifact.values() if isinstance(value, (str, int, float))]
    text = " ".join(criteria)
    constraints = [str(value).lower() for value in reference_constraints if str(value).strip()]
    covered = sum(1 for value in constraints if value in text)
    return {
        "structural_validity": int(bool(criteria)),
        "testable_condition_coverage": covered,
        "semantic_omission": len(constraints) - covered,
        "spurious_criteria": max(0, len(criteria) - covered),
        "external_traceability": int(traceability_valid is True),
    }

__all__ = ("DIMENSIONS", "evaluate_dimensions")
