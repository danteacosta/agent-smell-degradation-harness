"""Redacted, auditable error triage for natural-smell screening.

The source-label outcome is retained only as a derived diagnostic.  Raw
requirement text and marker values are never emitted.  FN/FP rows are marked
for expert review because lexical disagreement alone cannot establish a true
semantic error.
"""

from __future__ import annotations

import hashlib
from collections import Counter, defaultdict
from collections.abc import Mapping, Sequence
from typing import Any, Callable


ERROR_ANALYSIS_VERSION = "natural-screening-error-audit/v1"


def _outcome(actual: bool, predicted: bool) -> str:
    if actual and predicted:
        return "TP"
    if actual:
        return "FN"
    if predicted:
        return "FP"
    return "TN"


def build_error_audit(
    cases: Sequence[Mapping[str, Any]],
    *,
    split: str,
    families: Sequence[str],
    predictor: Callable[[str, str], Mapping[str, Any]],
    lexical_matcher: Callable[[str, str], Sequence[str]],
) -> dict[str, Any]:
    """Build per-case diagnostic rows without exposing source text."""

    rows: list[dict[str, Any]] = []
    for case in cases:
        if case.get("_split") != split or case.get("target_family") not in families:
            continue
        family = str(case["target_family"])
        text = str(case["requirement_text"])
        actual = str(case.get("source_label", "")).casefold() == "smelly"
        contextual = dict(predictor(text, family))
        predicted = bool(contextual.get("predicted"))
        outcome = _outcome(actual, predicted)
        lexical_evidence = list(lexical_matcher(text, family))
        lexical_predicted = bool(lexical_evidence)
        lexical_outcome = _outcome(actual, lexical_predicted)
        rows.append(
            {
                "case_id": str(case["case_id"]),
                "target_family": family,
                "split": split,
                "requirement_text_sha256": hashlib.sha256(text.encode("utf-8")).hexdigest(),
                "outcome": outcome,
                "prediction": predicted,
                "lexical_outcome": lexical_outcome,
                "lexical_prediction": lexical_predicted,
                "score": contextual.get("score"),
                "contextual_evidence": list(contextual.get("evidence", [])),
                "contextual_features": contextual.get("features", {}),
                "lexical_evidence": lexical_evidence,
                "automatic_triage": (
                    "contextual_hit" if outcome == "TP" else
                    "contextual_nonhit" if outcome == "TN" else
                    "contextual_overreach" if outcome == "FP" else
                    "uncovered_or_contextual_miss"
                ),
                "expert_review": "not_required_for_classification" if outcome in {"TP", "TN"} else "pending",
                "semantic_error_category": None,
            }
        )
    by_family: dict[str, dict[str, int]] = defaultdict(lambda: Counter())
    lexical_by_family: dict[str, dict[str, int]] = defaultdict(lambda: Counter())
    triage_counts: Counter[str] = Counter()
    for row in rows:
        by_family[row["target_family"]][row["outcome"]] += 1
        lexical_by_family[row["target_family"]][row["lexical_outcome"]] += 1
        triage_counts[row["automatic_triage"]] += 1
    return {
        "status": "automatic_triage_pending_expert_review",
        "version": ERROR_ANALYSIS_VERSION,
        "split": split,
        "case_count": len(rows),
        "source_label_use": "derived_diagnostic_only",
        "raw_requirement_text_included": False,
        "semantic_categories_require_expert_review": True,
        "outcome_counts_by_family": {family: dict(counts) for family, counts in sorted(by_family.items())},
        "lexical_outcome_counts_by_family": {
            family: dict(counts) for family, counts in sorted(lexical_by_family.items())
        },
        "automatic_triage_counts": dict(sorted(triage_counts.items())),
        "rows": rows,
    }


__all__ = ("ERROR_ANALYSIS_VERSION", "build_error_audit")
