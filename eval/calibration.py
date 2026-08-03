"""Train-only model-family selection and calibration-only threshold fitting."""

from __future__ import annotations

from typing import Any, Mapping, Sequence


class CalibrationError(ValueError):
    """Raised when calibration data cannot identify a binary threshold."""


def _validate(scores: Sequence[float], labels: Sequence[int], *, split: str) -> None:
    if len(scores) != len(labels):
        raise CalibrationError(f"{split} scores and labels must have equal length")
    if not scores:
        raise CalibrationError(f"{split} group is empty")
    if not all(label in (0, 1) for label in labels):
        raise CalibrationError(f"{split} labels must be binary")


def _predictions(scores: Sequence[float], threshold: float) -> list[int]:
    return [int(float(score) >= threshold) for score in scores]


def _confusion(scores: Sequence[float], labels: Sequence[int], threshold: float) -> tuple[int, int, int, int]:
    predictions = _predictions(scores, threshold)
    tp = sum(pred == 1 and label == 1 for pred, label in zip(predictions, labels))
    fp = sum(pred == 1 and label == 0 for pred, label in zip(predictions, labels))
    tn = sum(pred == 0 and label == 0 for pred, label in zip(predictions, labels))
    fn = sum(pred == 0 and label == 1 for pred, label in zip(predictions, labels))
    return tp, fp, tn, fn


def fit_threshold(
    scores: Sequence[float],
    labels: Sequence[int],
    *,
    split: str = "calibration",
    strategy: str = "f1",
) -> dict[str, Any]:
    """Fit a deterministic threshold using calibration labels only.

    The threshold maximizing F1 is selected; ties prefer the largest threshold,
    which is conservative for a warning gate.  No train or test observations
    are consulted by this function.
    """

    _validate(scores, labels, split=split)
    if not {0, 1}.issubset(set(labels)):
        raise CalibrationError(f"{split} group must contain both positive and negative labels")
    if strategy != "f1":
        raise CalibrationError(f"unsupported calibration strategy {strategy!r}")
    candidates = sorted({float(score) for score in scores}, reverse=True)
    best: tuple[float, float, float, int] | None = None
    for threshold in candidates:
        tp, fp, _tn, fn = _confusion(scores, labels, threshold)
        precision = tp / (tp + fp) if tp + fp else 0.0
        recall = tp / (tp + fn) if tp + fn else 0.0
        f1 = 2 * precision * recall / (precision + recall) if precision + recall else 0.0
        # max f1, then max threshold, then max recall, then max precision.
        key = (f1, threshold, recall, precision)
        if best is None or key > best:
            best = key
    assert best is not None
    threshold = best[1]
    return {
        "fit_split": split,
        "strategy": strategy,
        "threshold": threshold,
        "n": len(scores),
        "positive_n": sum(labels),
        "negative_n": len(labels) - sum(labels),
        "f1": best[0],
    }


def select_family(
    family_scores: Mapping[str, Sequence[float]],
    labels: Sequence[int],
    *,
    split: str = "train",
) -> dict[str, Any]:
    """Select the feature family on train groups only using average precision."""

    if not family_scores:
        raise CalibrationError("no candidate feature families")
    if not labels or not {0, 1}.issubset(set(labels)):
        raise CalibrationError(f"{split} group must contain both positive and negative labels")
    from baselines.score import mann_whitney_auroc

    def average_precision(scores: Sequence[float]) -> float:
        positives = sum(labels)
        if positives == 0:
            return 0.0
        ranked = sorted(zip(scores, labels), key=lambda item: float(item[0]), reverse=True)
        hits = area = 0.0
        for rank, (_, label) in enumerate(ranked, start=1):
            if label:
                hits += 1
                area += hits / rank
        return area / positives

    reports: dict[str, dict[str, float]] = {}
    for family, scores in sorted(family_scores.items()):
        _validate(scores, labels, split=split)
        reports[family] = {
            "pr_auc": average_precision(scores),
            "auroc": mann_whitney_auroc(list(scores), list(labels)),
        }
    selected = max(sorted(reports), key=lambda family: (reports[family]["pr_auc"], reports[family]["auroc"], family))
    return {"fit_split": split, "selected_family": selected, "candidates": reports}


def evaluate_threshold(
    scores: Sequence[float],
    labels: Sequence[int],
    threshold: float,
    *,
    split: str = "test",
) -> dict[str, Any]:
    """Evaluate a frozen threshold on a held-out group."""

    _validate(scores, labels, split=split)
    tp, fp, tn, fn = _confusion(scores, labels, threshold)
    positives = tp + fn
    negatives = fp + tn
    ranked = sorted(zip(scores, labels), key=lambda item: float(item[0]), reverse=True)
    hits = area = 0.0
    for rank, (_, label) in enumerate(ranked, start=1):
        if label:
            hits += 1
            area += hits / rank
    pr_auc = area / positives if positives else 0.0
    return {
        "split": split,
        "n": len(scores),
        "threshold": float(threshold),
        "tp": tp,
        "fp": fp,
        "tn": tn,
        "fn": fn,
        "false_alert_rate": fp / negatives if negatives else 0.0,
        "warning_coverage": tp / positives if positives else 0.0,
        "alert_rate": (tp + fp) / len(scores) if scores else 0.0,
        "pr_auc": pr_auc,
    }


__all__ = ("CalibrationError", "evaluate_threshold", "fit_threshold", "select_family")
