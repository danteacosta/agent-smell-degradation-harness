from __future__ import annotations

import json
from pathlib import Path

import pytest

from eval.runner import run_eval
from observability.features import extract_tier_a_features
from observability.tracing import ProvenanceRecorder


def test_provenance_events_include_tier(tmp_path: Path):
    trace_path = tmp_path / "trace.jsonl"
    rec = ProvenanceRecorder(trace_path)
    rec.operational("latency", {"ms": 1}, tier="A")
    rec.semantic("constraint_extract", {"x": 1}, tier="A")
    rec.oracle_verdict({"passed": True}, tier="B")
    rec.close()

    events = [json.loads(line) for line in trace_path.read_text().splitlines()]
    assert events[0]["tier"] == "A"
    assert events[1]["tier"] == "A"
    assert events[2]["tier"] == "B"
    assert events[2]["name"] == "oracle_verdict"


def test_extract_tier_a_features_excludes_oracle_verdict(tmp_path: Path):
    episodes_path = tmp_path / "episodes.jsonl"
    traces_dir = tmp_path / "traces"
    run_eval(
        failure_mode="smell-blind",
        output_path=tmp_path / "metrics.json",
        traces_dir=traces_dir,
        episodes_path=episodes_path,
    )

    episode = json.loads(episodes_path.read_text().splitlines()[0])
    features = extract_tier_a_features(episode, episode["provenance_path"])

    flattened = {
        key: value
        for family in features.values()
        for key, value in family.items()
    }
    assert "oracle_passed" not in flattened
    assert "oracle_verdict" not in flattened
    assert "mutation_score" not in flattened
    assert set(features) == {"static_smell", "operational", "provenance_semantic"}


def test_tier_a_event_count_excludes_tier_b(tmp_path: Path):
    trace_path = tmp_path / "trace.jsonl"
    rec = ProvenanceRecorder(trace_path)
    rec.operational("latency", {"ms": 1})
    rec.semantic("constraint_extract", {"delay_threshold_minutes": 5, "comparator": ">"})
    rec.oracle_verdict({"passed": False})
    rec.close()

    episode = {
        "intent_id": "RF-09",
        "task_family": "codegen",
        "variant": "smelly",
        "smell": {"type": "vague_threshold"},
        "requirement_text": "delayed after significant time",
        "artifact": {"delay_threshold_minutes": 5, "comparator": ">="},
    }
    features = extract_tier_a_features(episode, trace_path)
    assert features["operational"]["event_count"] == 2
