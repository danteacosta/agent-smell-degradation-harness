from __future__ import annotations

import pytest

from eval.splits import apply_split_manifest, build_grouped_split_manifest


def _episodes() -> list[dict[str, object]]:
    rows: list[dict[str, object]] = []
    for intent_index in range(6):
        project = f"project-{intent_index % 3}"
        for variant in ("clean", "smelly"):
            for replication in range(2):
                rows.append(
                    {
                        "intent_id": f"I-{intent_index}",
                        "source_intent_id": f"I-{intent_index}",
                        "project_id": project,
                        "variant": variant,
                        "replication_id": replication,
                    }
                )
    return rows


def test_confirmatory_manifest_is_deterministic_and_keeps_groups_together():
    episodes = _episodes()
    first = build_grouped_split_manifest(episodes, seed=17)
    second = build_grouped_split_manifest(episodes, seed=17)
    assert first == second
    partitions = apply_split_manifest(episodes, first)
    assignment_by_intent = {
        episode["source_intent_id"]: split
        for split, rows in partitions.items()
        for episode in rows
    }
    assert len(set(assignment_by_intent.values())) >= 2
    for split, rows in partitions.items():
        assert {row["project_id"] for row in rows}
        assert all(assignment_by_intent[row["source_intent_id"]] == split for row in rows)
    assert first["provenance"]["assignment_hash"]


def test_manifest_rejects_missing_project_group():
    episodes = _episodes()
    episodes[0].pop("project_id")
    with pytest.raises(ValueError, match="project_id"):
        build_grouped_split_manifest(episodes)


def test_manifest_rejects_insufficient_disjoint_groups():
    episodes = _episodes()
    for row in episodes:
        row["project_id"] = "one-project"
    with pytest.raises(ValueError, match="three"):
        build_grouped_split_manifest(episodes)
