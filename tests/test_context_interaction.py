from __future__ import annotations

import pytest

from eval.context_interaction import analyze_context_interaction


def _episode(
    intent_id: str,
    replication_id: int,
    variant: str,
    condition: str,
    severity: int,
) -> dict:
    return {
        "intent_id": intent_id,
        "task_family": "acceptance_criteria",
        "replication_id": replication_id,
        "variant": variant,
        "degradation_severity": severity,
        "provider_meta": {
            "context_management": {"condition": condition},
        },
    }


def test_context_interaction_is_a_difference_in_differences() -> None:
    episodes = [
        _episode("I-1", 0, "clean", "no_compaction", 2),
        _episode("I-1", 0, "smelly", "no_compaction", 1),
        _episode("I-1", 0, "clean", "compaction_stress_test", 3),
        _episode("I-1", 0, "smelly", "compaction_stress_test", 1),
    ]

    report = analyze_context_interaction(episodes)

    assert report["schema_version"] == "context-interaction/v1"
    assert report["confirmatory"] is False
    assert report["primary_estimand_changed"] is False
    assert report["complete_case_count"] == 1
    assert report["interaction_mean"] == 1.0
    assert report["cell_means"]["clean/no_compaction"]["count"] == 1
    assert report["cluster_interactions"][0]["interaction"] == 1.0


def test_context_interaction_clusters_repeated_replications_by_intent() -> None:
    episodes = []
    for replication_id in (0, 1):
        episodes.extend(
            [
                _episode("I-1", replication_id, "clean", "no_compaction", 1),
                _episode("I-1", replication_id, "smelly", "no_compaction", 1),
                _episode("I-1", replication_id, "clean", "compaction_stress_test", 2),
                _episode("I-1", replication_id, "smelly", "compaction_stress_test", 1),
            ]
        )

    report = analyze_context_interaction(episodes)

    assert report["input_episode_count"] == 8
    assert report["complete_case_count"] == 2
    assert report["complete_cluster_count"] == 1
    assert report["cluster_interactions"][0]["replication_count"] == 2
    assert report["interaction_mean"] == 1.0


def test_context_interaction_requires_all_four_cells() -> None:
    episodes = [
        _episode("I-1", 0, "clean", "no_compaction", 1),
        _episode("I-1", 0, "smelly", "no_compaction", 1),
    ]

    with pytest.raises(ValueError, match="four cells"):
        analyze_context_interaction(episodes)


def test_context_interaction_can_report_incomplete_cases_without_using_them() -> None:
    episodes = [
        _episode("I-1", 0, "clean", "no_compaction", 1),
        _episode("I-1", 0, "smelly", "no_compaction", 1),
    ]

    report = analyze_context_interaction(episodes, require_complete=False)

    assert report["complete_case_count"] == 0
    assert report["incomplete_case_count"] == 1
    assert report["interaction_mean"] == 0.0
