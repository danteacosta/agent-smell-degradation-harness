"""Shared, threshold-based binary ranking metrics."""
from __future__ import annotations

import math
from collections.abc import Sequence
from itertools import groupby


def average_precision(scores: Sequence[float], labels: Sequence[int]) -> float:
    """Non-interpolated AP; tied scores enter the same threshold together.

    Empty/no-positive inputs return zero by convention, not evidence of
    discrimination. Callers making inferential claims must require both classes.
    """
    if len(scores) != len(labels):
        raise ValueError("scores and labels must have equal length")
    if any(label not in (0, 1) for label in labels):
        raise ValueError("labels must be binary (0 or 1)")
    try:
        numeric_scores = [float(score) for score in scores]
    except (TypeError, ValueError, OverflowError) as exc:
        raise ValueError("scores must be finite numbers") from exc
    if any(not math.isfinite(score) for score in numeric_scores):
        raise ValueError("scores must be finite numbers")
    positives = sum(labels)
    if positives == 0:
        return 0.0
    ranked = sorted(zip(numeric_scores, labels), key=lambda item: item[0], reverse=True)
    hits = seen = 0
    area = 0.0
    for _, group in groupby(ranked, key=lambda item: item[0]):
        group_labels = [label for _, label in group]
        added_hits = sum(group_labels)
        hits += added_hits
        seen += len(group_labels)
        area += (added_hits / positives) * (hits / seen)
    return area
