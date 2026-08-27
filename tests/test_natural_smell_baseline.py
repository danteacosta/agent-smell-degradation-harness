from __future__ import annotations

from baselines.natural_smell import (
    SUPPORTED_FAMILIES,
    evaluate_source_label_screening,
    predict_family,
)


def _case(case_id: str, text: str, family: str, label: str) -> dict[str, object]:
    return {
        "case_id": case_id,
        "project_id": "project-a",
        "requirement_text": text,
        "target_family": family,
        "source_label": label,
        "source_label_type": "arta_dataset_marker",
        "source_smell_markers": [family] if label == "smelly" else [],
    }


def test_baseline_uses_text_only_not_source_markers() -> None:
    case = _case("c1", "The system shall respond quickly.", "ambiguous_adjective_adverb", "smelly")
    changed = dict(case, source_smell_markers=["unrelated"], source_label="clean")

    assert predict_family(case["requirement_text"], "ambiguous_adjective_adverb") is True
    assert predict_family(changed["requirement_text"], "ambiguous_adjective_adverb") is True


def test_screening_reports_all_supported_families_and_confusion_counts() -> None:
    cases = []
    for family in SUPPORTED_FAMILIES:
        cases.extend(
            [
                _case(f"{family}-positive", "The service shall respond quickly.", family, "smelly"),
                _case(f"{family}-clean", "The service shall respond within 5 seconds.", family, "clean"),
            ]
        )

    result = evaluate_source_label_screening(cases, split="test")

    assert set(result) == set(SUPPORTED_FAMILIES)
    assert all("confusion" in result[family] for family in SUPPORTED_FAMILIES)
    assert all("wilson_interval" in result[family]["metrics"] for family in SUPPORTED_FAMILIES)
