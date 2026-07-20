"""C5 overlay — activated in Tier 3."""

from mitigation.clarify import (
    Clarification,
    ClarifiedRequirement,
    apply_clarification_answer,
    build_clarification,
)
from mitigation.detect import SmellDetection, detect_smell
from mitigation.pipeline import PreparedRequirement, prepare_requirement
from mitigation.rewrite import RewriteResult, rewrite_requirement

__all__ = [
    "Clarification",
    "ClarifiedRequirement",
    "PreparedRequirement",
    "RewriteResult",
    "SmellDetection",
    "apply_clarification_answer",
    "build_clarification",
    "detect_smell",
    "prepare_requirement",
    "rewrite_requirement",
]

