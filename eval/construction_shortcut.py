"""Construction-only shortcut control for H2 (descriptive, outside the confirmatory freeze)."""

from __future__ import annotations

import math
from collections.abc import Mapping, Sequence
from typing import Any

from baselines.score import mann_whitney_auroc


def construction_shortcut_control(
    labels: Sequence[int],
    construction_features: Mapping[str, Sequence[float]],
    *,
    threshold: float = 0.9,
) -> dict[str, Any]:
    """Flag corpus-construction artifacts that predict labels without any trace content.

    Each named feature (for example episode order, identifier length, or a
    variant-arm marker) must be derivable from how the corpus was built, not
    from agent behavior. The control reports a direction-free AUROC per
    feature, ``max(auroc, 1 - auroc)``, and marks ``shortcut_detected`` when any
    feature reaches ``threshold``. A detected shortcut means the corpus or its
    exposed fields must be repaired before a detector score is interpreted; it
    is never a scientific label or claim.

    Labels are integer 0/1 with both classes present; features must be finite
    numbers of the same length as labels. Malformed input raises ValueError.
    """
    if any(type(label) is not int or label not in (0, 1) for label in labels):
        raise ValueError("labels must be binary integers")
    if len(set(labels)) < 2:
        raise ValueError("labels must contain both classes")
    if not construction_features:
        raise ValueError("construction_features must not be empty")
    if type(threshold) not in (int, float) or not math.isfinite(threshold) or not 0.5 <= threshold <= 1:
        raise ValueError("threshold must be a finite number in [0.5, 1]")
    per_feature: dict[str, float] = {}
    for name in sorted(construction_features):
        values = construction_features[name]
        if len(values) != len(labels):
            raise ValueError(f"feature {name!r} must match labels in length")
        if any(type(v) not in (int, float) or not math.isfinite(v) for v in values):
            raise ValueError(f"feature {name!r} must contain finite numbers")
        auroc = mann_whitney_auroc([float(v) for v in values], list(labels))
        per_feature[name] = max(auroc, 1.0 - auroc)
    flagged = sorted(name for name, value in per_feature.items() if value >= threshold)
    return {
        "control": "construction_only_shortcut",
        "threshold": threshold,
        "directionless_auroc": per_feature,
        "flagged_features": flagged,
        "shortcut_detected": bool(flagged),
        "claim": "descriptive_only",
    }


__all__ = ("construction_shortcut_control",)
