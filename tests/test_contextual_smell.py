from __future__ import annotations

from baselines.contextual_smell import analyze_family, extract_context_features


def test_contextual_comparator_exposes_evidence_and_structure() -> None:
    result = analyze_family(
        "The driver shall safely acknowledge the signal within 5 seconds.",
        "subjective_language",
    )

    assert result["predicted"] is True
    assert "safely" in result["evidence"]
    assert result["features"]["has_measurement"] is True
    assert result["features"]["has_normative_modal"] is True


def test_context_can_suppress_ambiguous_cue_when_requirement_is_quantified() -> None:
    result = analyze_family(
        "The system shall respond within 5 seconds.",
        "ambiguous_adjective_adverb",
    )

    assert result["features"]["has_measurement"] is True
    assert result["predicted"] is False


def test_vague_pronoun_signal_checks_for_a_local_antecedent() -> None:
    with_referent = extract_context_features(
        "The functional identity shall be displayed; this shall also be logged.",
        "vague_pronoun",
    )
    without_referent = extract_context_features(
        "This shall also be displayed.",
        "vague_pronoun",
    )

    assert with_referent["local_antecedent"] is True
    assert without_referent["local_antecedent"] is False
