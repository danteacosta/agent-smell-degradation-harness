"""Context-aware linguistic comparator for natural requirements-smell screening.

This is a stronger offline comparator than :mod:`baselines.natural_smell`, but
it is deliberately not presented as a semantic model.  It combines a broader
set of linguistic cues with lightweight structural features that are
observable in the requirement itself.  It emits evidence and a score so that a
future provider-backed adjudicator can inspect disagreements instead of
silently converting them into labels.

The comparator does not read source labels, marker columns, project names, or
oracle outcomes.
"""

from __future__ import annotations

import re
from collections.abc import Mapping, Sequence
from typing import Any

from baselines.natural_smell import SUPPORTED_FAMILIES
from eval.uncertainty import wilson_interval

BASELINE_VERSION = "contextual-linguistic/v1"
NORMALIZATION_VERSION = "unicode-casefold-whitespace/v1"

# These are transparent candidate cues assembled from the smell families used
# by Smella/ARTA/Paska-like approaches.  They are intentionally broader than
# the frozen keyword comparator, but the decision also depends on structure.
CONTEXT_CUES: dict[str, tuple[str, ...]] = {
    "subjective_language": (
        "adequate",
        "appropriate",
        "appropriately",
        "automatic",
        "automatically",
        "clear",
        "convenient",
        "easy",
        "easier",
        "easily",
        "effective",
        "normal",
        "normally",
        "proper",
        "safe",
        "safely",
        "sensitive",
        "something",
        "suitable",
        "user-friendly",
    ),
    "ambiguous_adjective_adverb": (
        "already",
        "at least",
        "automatically",
        "correctly",
        "each",
        "extremely",
        "maximum",
        "minimum",
        "normally",
        "appropriately",
        "quickly",
        "reasonable",
        "regularly",
        "similar",
        "significant",
        "timely",
        "usually",
        "upon",
        "up to",
    ),
    "nonverifiable_term": (
        "acceptable",
        "and so on",
        "as needed",
        "consistent",
        "defined",
        "detail",
        "etc",
        "interchangeable",
        "limit",
        "long-term",
        "minimum",
        "possible",
        "several",
        "sufficient",
        "too large",
        "validate",
    ),
    "vague_pronoun": (
        "another",
        "it",
        "that",
        "their",
        "them",
        "this",
        "they",
        "which",
    ),
    "uncertain_verb": (
        "can",
        "could",
        "may",
        "might",
        "should",
        "will",
    ),
    "polysemy": (
        "action",
        "application",
        "call",
        "control",
        "handle",
        "information",
        "interface",
        "log",
        "manage",
        "name",
        "process",
        "provide",
        "site",
        "store",
        "support",
    ),
}

_STOPWORDS = {
    "a",
    "an",
    "and",
    "are",
    "as",
    "be",
    "by",
    "can",
    "for",
    "from",
    "if",
    "in",
    "is",
    "it",
    "must",
    "of",
    "on",
    "or",
    "shall",
    "that",
    "the",
    "their",
    "them",
    "then",
    "this",
    "to",
    "under",
    "was",
    "when",
    "which",
    "will",
    "with",
}
_TOKEN_RE = re.compile(r"[a-z0-9]+(?:[-'][a-z0-9]+)?", re.IGNORECASE)
_MEASUREMENT_RE = re.compile(
    r"\b\d+(?:[.,]\d+)?\s*(?:ms|s|sec|secs|second|seconds|m|min|minute|minutes|"
    r"h|hour|hours|kb|kbit/s|mb|gb|km/h|mph|percent|%)\b",
    re.IGNORECASE,
)
_NUMBER_RE = re.compile(r"\b\d+(?:[.,]\d+)?\b")
_COMPARATOR_RE = re.compile(r"(?:<=|>=|<|>|at least|at most|no more than|no less than|"
                             r"less than|more than|from .+ to .+)", re.IGNORECASE)
_CONDITION_RE = re.compile(r"\b(?:if|when|unless|only if|after|before|until)\b", re.IGNORECASE)
_ACTOR_RE = re.compile(r"\b(?:system|service|user|driver|operator|administrator|client|server)\b", re.IGNORECASE)
_NORMATIVE_RE = re.compile(r"\b(?:shall|must|required to)\b", re.IGNORECASE)
_RESPONSE_RE = re.compile(r"\b(?:reject|deny|block|log|display|notify|return|apply|release|"
                           r"store|send|prompt|terminate|expire)\w*\b", re.IGNORECASE)


def _pattern(term: str) -> re.Pattern[str]:
    return re.compile(rf"(?<![a-z0-9]){re.escape(term)}(?![a-z0-9])", re.IGNORECASE)


_CUE_PATTERNS = {
    family: tuple((cue, _pattern(cue)) for cue in cues)
    for family, cues in CONTEXT_CUES.items()
}


def _normalize(text: str) -> str:
    return " ".join(str(text).casefold().split())


def _has_local_antecedent(text: str, cue: str) -> bool:
    """Approximate a local antecedent check for vague pronouns.

    This intentionally avoids claiming full coreference resolution.  It only
    treats a nearby content word before a pronoun as a possible referent; the
    result is therefore a review signal, not ground truth.
    """

    tokens = [token.casefold() for token in _TOKEN_RE.findall(text)]
    try:
        index = tokens.index(cue)
    except ValueError:
        return False
    window = tokens[max(0, index - 8):index]
    return any(token not in _STOPWORDS and not token.isdigit() for token in window)


def extract_context_features(text: str, family: str) -> dict[str, Any]:
    """Extract explainable text-only signals for one smell family."""

    if family not in SUPPORTED_FAMILIES:
        raise ValueError(f"unsupported natural-smell family: {family}")
    normalized = _normalize(text)
    cue_hits = tuple(cue for cue, pattern in _CUE_PATTERNS[family] if pattern.search(normalized))
    has_measurement = bool(_MEASUREMENT_RE.search(normalized))
    has_number = bool(_NUMBER_RE.search(normalized))
    has_comparator = bool(_COMPARATOR_RE.search(normalized))
    has_condition = bool(_CONDITION_RE.search(normalized))
    has_actor = bool(_ACTOR_RE.search(normalized))
    has_normative_modal = bool(_NORMATIVE_RE.search(normalized))
    has_explicit_response = bool(_RESPONSE_RE.search(normalized))
    local_antecedent = None
    if family == "vague_pronoun":
        for cue in cue_hits:
            if cue in {"it", "that", "their", "them", "this", "they", "which"}:
                local_antecedent = _has_local_antecedent(normalized, cue)
                break
    return {
        "cue_hits": cue_hits,
        "has_measurement": has_measurement,
        "has_number": has_number,
        "has_comparator": has_comparator,
        "has_condition": has_condition,
        "has_actor": has_actor,
        "has_normative_modal": has_normative_modal,
        "has_explicit_response": has_explicit_response,
        "local_antecedent": local_antecedent,
    }


def _score(features: Mapping[str, Any], family: str) -> float:
    if not features["cue_hits"]:
        return 0.0
    score = 0.65
    if family == "ambiguous_adjective_adverb":
        # A quantified threshold is evidence against an untestable vagueness
        # interpretation.  The cue remains visible for human review.
        if features["has_measurement"] or features["has_comparator"]:
            score -= 0.35
    elif family == "nonverifiable_term":
        if features["has_measurement"] and features["has_explicit_response"]:
            score -= 0.25
        if features["has_condition"] and features["has_actor"]:
            score -= 0.10
    elif family == "vague_pronoun":
        if features["local_antecedent"] is True:
            score -= 0.45
        elif features["local_antecedent"] is False:
            score += 0.20
        if "another" in features["cue_hits"] and features["has_actor"]:
            score -= 0.10
    elif family == "uncertain_verb":
        if features["has_normative_modal"] and set(features["cue_hits"]) <= {"will"}:
            score -= 0.20
    elif family == "polysemy":
        if features["has_explicit_response"] and features["has_actor"]:
            score -= 0.10
        if features["has_condition"]:
            score -= 0.10
    return max(0.0, min(1.0, score))


def analyze_family(text: str, family: str) -> dict[str, Any]:
    """Return a contextual score, decision and auditable text-only signals."""

    features = extract_context_features(text, family)
    score = _score(features, family)
    return {
        "baseline_version": BASELINE_VERSION,
        "normalization_version": NORMALIZATION_VERSION,
        "family": family,
        "score": round(score, 4),
        "predicted": score >= 0.5,
        "evidence": list(features["cue_hits"]),
        "features": features,
    }


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
            "precision": wilson_interval(tp, predicted_positive),
            "recall": wilson_interval(tp, positives),
            "specificity": wilson_interval(tn, negatives),
        },
    }


def evaluate_contextual_screening(
    cases: Sequence[Mapping[str, Any]],
    *,
    split: str = "test",
    families: Sequence[str] = SUPPORTED_FAMILIES,
) -> dict[str, dict[str, Any]]:
    """Evaluate the contextual comparator against source labels descriptively."""

    requested_families = tuple(families)
    unknown_families = set(requested_families) - set(SUPPORTED_FAMILIES)
    if unknown_families:
        raise ValueError(f"unsupported natural-smell families: {sorted(unknown_families)}")
    results: dict[str, dict[str, Any]] = {}
    for family in requested_families:
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
            predicted = bool(analyze_family(str(case.get("requirement_text", "")), family)["predicted"])
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
    "CONTEXT_CUES",
    "NORMALIZATION_VERSION",
    "analyze_family",
    "evaluate_contextual_screening",
    "extract_context_features",
)
