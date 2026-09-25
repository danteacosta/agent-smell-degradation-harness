from __future__ import annotations

import copy
import hashlib
import json

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


def test_runtime_intent_id_is_canonicalized_to_source_intent_id():
    episodes = _episodes()
    for row in episodes:
        row.pop("source_intent_id")
    manifest = build_grouped_split_manifest(episodes)
    assert all("source_intent_id" in row for row in manifest["assignments"])
    assert sum(len(rows) for rows in apply_split_manifest(episodes, manifest).values()) == len(episodes)


def test_manifest_rejects_insufficient_disjoint_groups():
    episodes = _episodes()
    for row in episodes:
        row["project_id"] = "one-project"
    with pytest.raises(ValueError, match="three"):
        build_grouped_split_manifest(episodes)


def test_applying_manifest_rejects_tampered_assignment_even_if_all_splits_exist():
    episodes = _episodes()
    manifest = copy.deepcopy(build_grouped_split_manifest(episodes))
    manifest["assignments"][0]["source_intent_id"] = "different-intent"
    with pytest.raises(ValueError, match="hash mismatch"):
        apply_split_manifest(episodes, manifest)


def test_applying_manifest_rejects_cross_project_leakage_with_recomputed_hash():
    episodes = _episodes()
    manifest = copy.deepcopy(build_grouped_split_manifest(episodes))
    first = manifest["assignments"][0]
    sibling = next(row for row in manifest["assignments"] if row["project_id"] == first["project_id"] and row is not first)
    sibling["split"] = next(split for split in ("train", "calibration", "test") if split != first["split"])
    manifest["provenance"]["assignment_hash"] = hashlib.sha256(
        json.dumps(manifest["assignments"], sort_keys=True, separators=(",", ":")).encode("utf-8")
    ).hexdigest()
    with pytest.raises(ValueError, match="project_id crosses split boundary"):
        apply_split_manifest(episodes, manifest)


def test_applying_manifest_rejects_duplicate_assignment_instead_of_overwriting_it():
    episodes = _episodes()
    manifest = copy.deepcopy(build_grouped_split_manifest(episodes))
    manifest["assignments"].append(dict(manifest["assignments"][0]))
    with pytest.raises(ValueError, match="duplicate split assignment"):
        apply_split_manifest(episodes, manifest)


def test_applying_manifest_rejects_intent_leakage_across_projects():
    episodes = [
        {"source_intent_id": source, "project_id": project}
        for source, project in (("shared", "p1"), ("shared", "p2"), ("other", "p3"), ("third", "p4"))
    ]
    manifest = copy.deepcopy(build_grouped_split_manifest(episodes))
    shared = [row for row in manifest["assignments"] if row["source_intent_id"] == "shared"]
    shared[1]["split"] = next(split for split in ("train", "calibration", "test") if split != shared[0]["split"])
    manifest["provenance"]["assignment_hash"] = hashlib.sha256(
        json.dumps(manifest["assignments"], sort_keys=True, separators=(",", ":")).encode("utf-8")
    ).hexdigest()
    with pytest.raises(ValueError, match="source_intent_id crosses split boundary"):
        apply_split_manifest(episodes, manifest)
