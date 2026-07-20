"""C5 overlay — activated in Tier 3."""

from mitigation.clarify import (
    Clarification,
    ClarifiedRequirement,
    apply_clarification_answer,
    build_clarification,
)
from mitigation.detect import SmellDetection, detect_smell
from mitigation.rewrite import RewriteResult, rewrite_requirement

__all__ = [
    "Clarification",
    "ClarifiedRequirement",
    "RewriteResult",
    "SmellDetection",
    "apply_clarification_answer",
    "build_clarification",
    "detect_smell",
    "rewrite_requirement",
]

