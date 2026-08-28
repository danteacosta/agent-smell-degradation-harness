from __future__ import annotations

import pytest

from label_plane.llm_panel import (
    PANEL_PROVIDERS,
    build_consensus,
    build_panel_prompt,
    build_panel_tasks,
    select_human_audit_subset,
    summarize_panel_agreement,
    validate_panel_annotation,
)
from label_plane.control_matrix import CONTROL_CONDITIONS, validate_control_matrix


def _annotation(provider: str, label: str, item_id: str = "item-1") -> dict[str, object]:
    return {
        "item_id": item_id,
        "provider_id": provider,
        "model_id": f"{provider}-model-1",
        "target_family": "vague_pronoun",
        "label": label,
        "evidence_span": "it",
        "rationale": "The referent is not uniquely identifiable.",
        "confidence": 0.8,
    }


def test_panel_prompt_blinds_source_and_experiment_metadata() -> None:
    prompt = build_panel_prompt(
        item_id="opaque-1",
        requirement_text="The system shall process it.",
        target_family="vague_pronoun",
    )

    assert "opaque-1" in prompt
    assert "vague_pronoun" in prompt
    assert "source_label" in prompt
    assert "project_id" in prompt
    assert "oracle_result" in prompt


def test_panel_task_identifier_does_not_reveal_sampling_kind() -> None:
    tasks = build_panel_tasks([
        {
            "candidate_id": "unified-v1-item-opaque",
            "requirement_text": "The system shall process the request.",
            "target_family": "polysemy",
            "candidate_kind": "hard_clean_candidate",
        }
    ])

    assert len(tasks) == 3
    assert all("candidate_kind" not in task for task in tasks)
    assert all("hard_clean" not in task["item_id"] for task in tasks)


def test_control_condition_is_private_task_metadata_and_not_in_prompt() -> None:
    tasks = build_panel_tasks(
        [
            {
                "candidate_id": "opaque-control",
                "requirement_text": "The system shall process the request.",
                "target_family": "polysemy",
                "control_condition": "surface_only_control",
            }
        ],
        judge_ids=("judge-a",),
    )

    assert tasks[0]["control_condition"] == "surface_only_control"
    assert "surface_only_control" not in tasks[0]["prompt"]


def test_panel_annotation_rejects_leaked_fields() -> None:
    with pytest.raises(ValueError, match="forbidden"):
        validate_panel_annotation({**_annotation("gpt", "smelly"), "source_label": "smelly"})


def test_two_of_three_is_consensus_and_conflict_is_uncertain() -> None:
    annotations = [
        _annotation("kimi", "smelly"),
        _annotation("gpt", "smelly"),
        _annotation("claude", "clean"),
    ]
    result = build_consensus(annotations)
    assert result["label"] == "smelly"
    assert result["status"] == "panel_consensus"
    assert result["agreement"] == 2 / 3

    conflict = build_consensus([
        _annotation("kimi", "smelly"),
        _annotation("gpt", "clean"),
        _annotation("claude", "uncertain"),
    ])
    assert conflict["label"] == "uncertain"
    assert conflict["status"] == "uncertain"
    assert conflict["human_review_required"] is True


def test_consensus_requires_exactly_one_annotation_per_panel_provider() -> None:
    with pytest.raises(ValueError, match="providers"):
        build_consensus([_annotation(provider, "clean") for provider in PANEL_PROVIDERS[:2]])


def test_human_audit_subset_is_reproducible_and_nonempty() -> None:
    item_ids = [f"item-{index}" for index in range(10)]
    first = select_human_audit_subset(item_ids, fraction=0.2, seed=4)
    second = select_human_audit_subset(item_ids, fraction=0.2, seed=4)

    assert first == second
    assert len(first) == 2


def test_panel_supports_arbitrary_judge_ids_without_provider_branding() -> None:
    tasks = build_panel_tasks(
        [
            {
                "candidate_id": "opaque-1",
                "requirement_text": "The system shall process the request.",
                "target_family": "polysemy",
            }
        ],
        judge_ids=("judge-a", "judge-b", "judge-c"),
    )

    assert [task["provider_id"] for task in tasks] == ["judge-a", "judge-b", "judge-c"]


def test_consensus_accepts_configured_judges() -> None:
    annotations = [
        _annotation("judge-a", "smelly"),
        _annotation("judge-b", "smelly"),
        _annotation("judge-c", "clean"),
    ]

    result = build_consensus(
        annotations,
        expected_providers=("judge-a", "judge-b", "judge-c"),
        consensus_required=2,
    )

    assert result["label"] == "smelly"
    assert result["status"] == "panel_consensus"


def test_control_matrix_requires_all_four_conditions_without_gold_labels() -> None:
    records = [
        {
            "item_id": f"control-{index}",
            "target_family": "polysemy",
            "control_condition": condition,
        }
        for index, condition in enumerate(CONTROL_CONDITIONS)
    ]

    summary = validate_control_matrix(records)

    assert summary["item_count"] == 4
    assert summary["counts_by_family"]["polysemy"] == {
        condition: 1 for condition in CONTROL_CONDITIONS
    }


def test_control_matrix_rejects_incomplete_oracle_leaking_conditions() -> None:
    records = [
        {
            "item_id": f"control-{index}",
            "target_family": "polysemy",
            "control_condition": condition,
        }
        for index, condition in enumerate(CONTROL_CONDITIONS[:-1])
    ]
    records[0]["expected_label"] = "clean"

    with pytest.raises(ValueError, match="label-like"):
        validate_control_matrix(records)

    records[0].pop("expected_label")
    with pytest.raises(ValueError, match="incomplete"):
        validate_control_matrix(records)


def test_panel_agreement_is_reported_without_becoming_ground_truth() -> None:
    annotations = [
        _annotation("judge-a", "smelly"),
        _annotation("judge-b", "smelly"),
        _annotation("judge-c", "clean"),
    ]
    consensus = [
        build_consensus(
            annotations,
            expected_providers=("judge-a", "judge-b", "judge-c"),
        )
    ]

    summary = summarize_panel_agreement(
        consensus,
        annotations=annotations,
        item_metadata={"item-1": {"project_id": "project-1", "intent_id": "intent-1"}},
    )

    assert summary["agreement_rate"] == 2 / 3
    assert summary["model_disagreement"] == {
        "count": 1,
        "rate": 1.0,
        "items": ["item-1"],
    }
    assert summary["human_model_disagreement"]["status"] == "not_available"
    assert summary["interpretation"] == "triage_and_robustness_only"
    assert summary["by_project"]["project-1"]["model_disagreement_count"] == 1
    assert summary["by_intent"]["intent-1"]["item_count"] == 1


def test_human_model_disagreement_is_separate_when_adjudication_exists() -> None:
    annotations = [
        _annotation("judge-a", "smelly"),
        _annotation("judge-b", "smelly"),
        _annotation("judge-c", "clean"),
    ]
    consensus = [
        build_consensus(
            annotations,
            expected_providers=("judge-a", "judge-b", "judge-c"),
        )
    ]

    summary = summarize_panel_agreement(
        consensus,
        annotations=annotations,
        human_labels={"item-1": "clean"},
    )

    assert summary["human_model_disagreement"]["status"] == "available"
    assert summary["human_model_disagreement"]["consensus_count"] == 1
    assert summary["human_model_disagreement"]["consensus_rate"] == 1.0
    assert summary["human_model_disagreement"]["judge_count"] == 2
    assert summary["human_model_disagreement"]["judge_rate"] == 2 / 3
