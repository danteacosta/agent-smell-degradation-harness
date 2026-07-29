from __future__ import annotations

import dataclasses
import inspect
import json
from pathlib import Path

import pytest

from observability.feature_plane import FeatureEpisodeInput, extract_pre_final_features
from observability.tracing import ProvenanceRecorder


def _episode(**overrides: object) -> dict[str, object]:
    episode: dict[str, object] = {
        "intent_id": "RF-09",
        "task_family": "codegen",
        "variant": "smelly",
        "smell": {"type": "vague_threshold"},
        "requirement_text": "Refund delayed orders after 15 minutes.",
        "artifact": {"delay_threshold_minutes": 15, "comparator": ">="},
        "oracle_spec": {"delay_threshold_minutes": 15, "comparator": ">"},
        "oracle_passed": False,
        "semantic_label": "incorrect",
        "mutation_score": 0.0,
    }
    episode.update(overrides)
    return episode


def _write_trace(path: Path, constraint_payload: dict[str, object] | None) -> str:
    recorder = ProvenanceRecorder(path)
    recorder.operational("latency", {"ms": 1}, tier="A")
    if constraint_payload is not None:
        recorder.semantic("constraint_extract", constraint_payload, tier="A")
    recorder.oracle_verdict({"passed": False}, tier="B")
    recorder.close()
    return path.read_text(encoding="utf-8")


def test_feature_episode_input_copies_only_pre_final_episode_fields(tmp_path: Path):
    input_episode = FeatureEpisodeInput.from_episode(
        _episode(), _write_trace(tmp_path / "trace.jsonl", {"first": 1})
    )

    assert set(input_episode.__dict__) == {
        "intent_id",
        "task_family",
        "variant",
        "smell",
        "requirement_text",
        "provenance_jsonl",
    }
    assert {field.name for field in dataclasses.fields(FeatureEpisodeInput)} == set(
        input_episode.__dict__
    )
    assert not hasattr(input_episode, "artifact")


def test_pre_final_features_use_tier_a_trace_and_ignore_tier_b(tmp_path: Path):
    feature_input = FeatureEpisodeInput.from_episode(
        _episode(),
        _write_trace(
            tmp_path / "trace.jsonl", {"first": 1, "comparator": ">"}
        ),
    )

    features = extract_pre_final_features(feature_input)

    assert features["operational"]["event_count"] == 2
    assert features["provenance_semantic"] == {
        "constraint_event_present": 1,
        "constraint_field_count": 2,
        "constraint_has_comparator": 1,
        "constraint_risk": 0.0,
        "semantic_event_count": 1,
    }


def test_pre_final_features_are_invariant_to_final_episode_data(tmp_path: Path):
    provenance_jsonl = _write_trace(tmp_path / "trace.jsonl", {"first": 1})
    source = _episode()
    changed_only_final_data = _episode(
        artifact={"unrelated": "replacement"},
        oracle_spec={"expected": "replacement"},
        oracle_passed=True,
        semantic_label="correct",
        mutation_score=1.0,
    )

    source_features = extract_pre_final_features(
        FeatureEpisodeInput.from_episode(source, provenance_jsonl)
    )
    changed_features = extract_pre_final_features(
        FeatureEpisodeInput.from_episode(changed_only_final_data, provenance_jsonl)
    )

    assert source_features == changed_features


@pytest.mark.parametrize(
    ("constraint_payload", "expected_risk"),
    [
        (None, 1.0),
        ({}, 0.5),
        ({"first": 1}, 0.0),
    ],
)
def test_constraint_risk_is_neutral_and_trace_derived(
    tmp_path: Path,
    constraint_payload: dict[str, object] | None,
    expected_risk: float,
):
    feature_input = FeatureEpisodeInput.from_episode(
        _episode(), _write_trace(tmp_path / "trace.jsonl", constraint_payload)
    )

    features = extract_pre_final_features(feature_input)

    assert features["provenance_semantic"]["constraint_risk"] == expected_risk


def test_feature_plane_source_has_no_final_label_or_oracle_dependencies():
    import observability.feature_plane as feature_plane

    source = inspect.getsource(feature_plane)

    for forbidden_dependency in (
        "label_plane",
        "eval.oracles",
        "pairs.loader",
        "oracle_spec",
        "artifact",
        "oracle_passed",
        "semantic_label",
        "mutation_score",
    ):
        assert forbidden_dependency not in source
