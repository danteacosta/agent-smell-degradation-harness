from __future__ import annotations

from baselines.contextual_smell import analyze_family
from baselines.natural_smell import matched_terms
from eval.error_analysis import build_error_audit


def test_error_audit_is_redacted_and_marks_disagreements_for_review() -> None:
    cases = [
        {
            "case_id": "case-fn",
            "target_family": "subjective_language",
            "_split": "test",
            "requirement_text": "The system shall perform recurring backups.",
            "source_label": "smelly",
        },
        {
            "case_id": "case-tn",
            "target_family": "subjective_language",
            "_split": "test",
            "requirement_text": "The system shall respond within 5 seconds.",
            "source_label": "clean",
        },
    ]

    result = build_error_audit(
        cases,
        split="test",
        families=("subjective_language",),
        predictor=analyze_family,
        lexical_matcher=matched_terms,
    )

    assert result["raw_requirement_text_included"] is False
    assert result["case_count"] == 2
    assert all("requirement_text" not in row for row in result["rows"])
    assert result["rows"][0]["expert_review"] == "pending"
    assert result["rows"][0]["lexical_outcome"] == "FN"
    assert result["rows"][1]["outcome"] == "TN"
