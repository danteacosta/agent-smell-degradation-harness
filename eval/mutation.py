"""Compatibility imports for reference-based label checks."""

from label_plane.reference_based import (
    MUTANTS_BY_INTENT,
    artifact_detects_mutant,
    score_test_gen_mutation,
)

__all__ = ["MUTANTS_BY_INTENT", "artifact_detects_mutant", "score_test_gen_mutation"]
