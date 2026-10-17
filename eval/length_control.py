"""Descriptive trace-length confound control for H2 (outside the confirmatory freeze)."""

from __future__ import annotations

import math
from collections.abc import Sequence
from typing import Any

from baselines.score import mann_whitney_auroc


def length_matched_control(
    scores: Sequence[float],
    labels: Sequence[int],
    lengths: Sequence[float],
    *,
    tolerance: float = 3.0,
    min_pairs: int = 10,
) -> dict[str, Any]:
    """Offline control for the trace-length confound (descriptive, never a claim).

    Reports the length-only AUROC on all episodes and the score AUROC on
    positive/negative pairs matched within ``tolerance`` steps. Matching is
    deterministic (sorted by length then index, nearest unused negative) and
    uses no outcome information beyond the label itself. Fewer than
    ``min_pairs`` pairs marks the result ``insufficient_pairs``.

    Scores must be finite numbers; trace lengths and tolerance must also be
    nonnegative. Labels are integer 0/1 and min_pairs is a positive integer.
    Boolean aliases and malformed inputs raise ValueError before scoring.
    """
    if not (len(scores) == len(labels) == len(lengths)):
        raise ValueError("scores, labels, and lengths must have equal length")
    if any(type(label) is not int or label not in (0, 1) for label in labels):
        raise ValueError("labels must be binary integers")
    if any(type(score) not in (int, float) or not math.isfinite(score) for score in scores):
        raise ValueError("scores must be finite numbers")
    if any(type(length) not in (int, float) or not math.isfinite(length) or length < 0 for length in lengths):
        raise ValueError("lengths must be finite nonnegative numbers")
    if type(tolerance) not in (int, float) or not math.isfinite(tolerance) or tolerance < 0:
        raise ValueError("tolerance must be a finite nonnegative number")
    if type(min_pairs) is not int or min_pairs < 1:
        raise ValueError("min_pairs must be a positive integer")
    positives = sorted((lengths[i], i) for i, label in enumerate(labels) if label == 1)
    negatives = sorted((lengths[i], i) for i, label in enumerate(labels) if label == 0)
    used: set[int] = set()
    pairs: list[tuple[int, int]] = []
    for length, pos in positives:
        candidates = [
            (abs(neg_length - length), neg_length, neg)
            for neg_length, neg in negatives
            if neg not in used and abs(neg_length - length) <= tolerance
        ]
        if candidates:
            _, _, neg = min(candidates)
            used.add(neg)
            pairs.append((pos, neg))
    matched_scores = [scores[i] for pair in pairs for i in pair]
    matched_labels = [label for _ in pairs for label in (1, 0)]
    matched_auroc = mann_whitney_auroc(matched_scores, matched_labels) if pairs else None
    return {
        "control": "length_matched",
        "tolerance": tolerance,
        "length_only_auroc": mann_whitney_auroc([float(v) for v in lengths], list(labels)),
        "n_pairs": len(pairs),
        "n_positive": len(positives),
        "n_negative": len(negatives),
        "matched_auroc": matched_auroc,
        "status": "ok" if len(pairs) >= min_pairs else "insufficient_pairs",
        "claim": "descriptive_only",
    }


__all__ = ("length_matched_control",)
