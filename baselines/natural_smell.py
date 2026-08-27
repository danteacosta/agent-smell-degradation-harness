"""Frozen text-only baseline for natural requirements-smell screening.

This module is intentionally a weak comparator.  It uses only normalized
requirement text and a versioned lexicon; source labels and source marker
columns are never consulted by scoring code.
"""

from __future__ import annotations

import re
from collections.abc import Mapping, Sequence
from typing import Any

from eval.uncertainty import wilson_interval

BASELINE_VERSION = "natural-lexicon/v1"
NORMALIZATION_VERSION = "unicode-casefold/v1"
SUPPORTED_FAMILIES = (
    "subjective_language",
    "ambiguous_adjective_adverb",
    "nonverifiable_term",
    "vague_pronoun",
    "uncertain_verb",
    "polysemy",
)

# The lexicon is frozen for this screening round. It is a transparent
# comparator, not a claim that a term is always a defect in context.
LEXICON: dict[str, tuple[str, ...]] = {
    "subjective_language": (
        "easy",
        "suitable",
        "appropriate",
        "safe",
        "adequate",
        "proper",
        "convenient",
        "user-friendly",
    ),
    "ambiguous_adjective_adverb": (
        "quickly",
        "easily",
        "appropriately",
        "normally",
        "usually",
        "regularly",
        "significant",
        "reasonable",
        "timely",
    ),
    "nonverifiable_term": (
        "possible",
        "likely",
        "sufficient",
        "acceptable",
        "as needed",
        "and so on",
        "etc",
    ),
    "vague_pronoun": ("it", "this", "that", "they", "them", "their"),
    "uncertain_verb": ("may", "might", "could", "should"),
    "polysemy": ("support", "handle", "process", "manage", "control", "provide"),
}


def _pattern(term: str) -> re.Pattern[str]:
    escaped = re.escape(term)
    return re.compile(rf"(?<![a-z0-9]){escaped}(?![a-z0-9])", re.IGNORECASE)


_PATTERNS = {
    family: tuple((term, _pattern(term)) for term in terms)
    for family, terms in LEXICON.items()
}


def matched_terms(text: str, family: str) -> tuple[str, ...]:
    """Return lexicon hits for one family using requirement text only."""

    if family not in SUPPORTED_FAMILIES:
        raise ValueError(f"unsupported natural-smell family: {family}")
    normalized = str(text).casefold()
    return tuple(term for term, pattern in _PATTERNS[family] if pattern.search(normalized))


def score_family(text: str, family: str) -> float:
    """Return a binary lexicon score for one family."""

    return 1.0 if matched_terms(text, family) else 0.0


def predict_family(text: str, family: str) -> bool:
    """Predict whether text contains a signal for ``family``."""

    return score_family(text, family) >= 1.0


def _rate(successes: int, trials: int) -> dict[str, Any]:
    return wilson_interval(successes, trials)


def _metric_bundle(tp: int, fp: int, tn: int, fn: int) -> dict[str, Any]:
    positives = tp + fn
    negatives = tn + fp
    predicted_positive = tp + fp
    total = positives + negatives
    precision = tp / predicted_positive if predicted_positive else None
    recall = tp / positives if positives else None
    specificity = tn / negatives if negatives else None
    f1 = (
        2 * precision * recall / (precision + recall)
        if precision is not None and recall is not None and precision + recall
        else None
    )
    return {
        "precision": precision,
        "recall": recall,
        "specificity": specificity,
        "f1": f1,
        "accuracy": (tp + tn) / total if total else None,
        "wilson_interval": {
            "precision": _rate(tp, predicted_positive),
            "recall": _rate(tp, positives),
            "specificity": _rate(tn, negatives),
        },
    }


def evaluate_source_label_screening(
    cases: Sequence[Mapping[str, Any]], *, split: str = "test"
) -> dict[str, dict[str, Any]]:
    """Evaluate the baseline against source labels for descriptive screening.

    ``split`` is optional for small unit fixtures. In a real corpus, records
    are expected to carry the runner's private ``_split`` field.
    """

    results: dict[str, dict[str, Any]] = {}
    for family in SUPPORTED_FAMILIES:
        selected = [
            case
            for case in cases
            if case.get("target_family") == family
            and (case.get("_split") is None or case.get("_split") == split)
        ]
        tp = fp = tn = fn = 0
        for case in selected:
            source_label = str(case.get("source_label", "")).casefold()
            if source_label not in {"clean", "smelly"}:
                raise ValueError("screening cases must have clean or smelly source labels")
            actual = source_label == "smelly"
            predicted = predict_family(str(case.get("requirement_text", "")), family)
            if predicted and actual:
                tp += 1
            elif predicted and not actual:
                fp += 1
            elif not predicted and not actual:
                tn += 1
            else:
                fn += 1
        results[family] = {
            "baseline_version": BASELINE_VERSION,
            "normalization_version": NORMALIZATION_VERSION,
            "split": split,
            "case_count": len(selected),
            "confusion": {"tp": tp, "fp": fp, "tn": tn, "fn": fn},
            "metrics": _metric_bundle(tp, fp, tn, fn),
        }
    return results


__all__ = (
    "BASELINE_VERSION",
    "LEXICON",
    "NORMALIZATION_VERSION",
    "SUPPORTED_FAMILIES",
    "evaluate_source_label_screening",
    "matched_terms",
    "predict_family",
    "score_family",
)
