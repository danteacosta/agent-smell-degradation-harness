"""C1 overlay — taxonomy catalog and degradation labeler."""

from taxonomy.catalog import DEGRADATION_MODES, INTENT_TO_MODE
from taxonomy.label import DegradationLabel, label_degradation

__all__ = [
    "DEGRADATION_MODES",
    "INTENT_TO_MODE",
    "DegradationLabel",
    "label_degradation",
]
