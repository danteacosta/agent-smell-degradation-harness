from __future__ import annotations

import pytest

from label_plane.llm_panel import (
    PANEL_PROVIDERS,
    build_consensus,
    build_panel_prompt,
    build_panel_tasks,
    select_human_audit_subset,
    select_stratified_human_audit_subset,
    validate_panel_annotation,
)


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


def test_stratified_audit_keeps_mandatory_review_and_covers_outcomes() -> None:
    rows = [
        {"item_id": "a", "target_family": "polysemy", "status": "panel_consensus", "agreement": 1.0, "human_review_required": False},
        {"item_id": "b", "target_family": "polysemy", "status": "panel_consensus", "agreement": 2 / 3, "human_review_required": True},
        {"item_id": "c", "target_family": "vague_pronoun", "status": "uncertain", "agreement": 1 / 3, "human_review_required": True},
        {"item_id": "d", "target_family": "vague_pronoun", "status": "panel_consensus", "agreement": 1.0, "human_review_required": False},
    ]
    audit = select_stratified_human_audit_subset(rows, fraction=0.25, seed=7)
    selected = {row["item_id"]: row["audit_reason"] for row in audit}
    assert selected["b"] == "mandatory_disagreement_or_uncertainty"
    assert selected["c"] == "mandatory_disagreement_or_uncertainty"
    assert audit == select_stratified_human_audit_subset(rows, fraction=0.25, seed=7)


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
