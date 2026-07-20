"""C5 overlay — activated in Tier 3."""

from mitigation.detect import SmellDetection, detect_smell
from mitigation.rewrite import RewriteResult, rewrite_requirement

__all__ = [
    "RewriteResult",
    "SmellDetection",
    "detect_smell",
    "rewrite_requirement",
]

