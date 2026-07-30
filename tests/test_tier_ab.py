from __future__ import annotations

import ast
import json
from pathlib import Path

import pytest

import baselines.features as baseline_features
from eval.runner import run_eval
from observability.features import extract_tier_a_features
from observability.feature_plane import FeatureEpisodeInput, extract_pre_final_features
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
    }
    features = extract_tier_a_features(episode, trace_path)
    assert features["operational"]["event_count"] == 2


def test_legacy_tier_a_compatibility_contract_delegates_to_pre_final_features(
    tmp_path: Path,
):
    trace_path = tmp_path / "trace.jsonl"
    trace_path.write_text(
        json.dumps(
            {
                "kind": "operational",
                "name": "latency",
                "tier": "A",
                "payload": {"ms": 1},
            }
        )
        + "\n",
        encoding="utf-8",
    )
    episode = {
        "intent_id": "RF-09",
        "task_family": "codegen",
        "variant": "smelly",
        "smell": {"type": "vague_threshold"},
        "requirement_text": "delayed after significant time",
    }

    assert extract_tier_a_features(episode, trace_path) == extract_pre_final_features(
        FeatureEpisodeInput.from_episode(episode), trace_path
    )


class _EpisodeMappingReads(ast.NodeVisitor):
    def __init__(self) -> None:
        self.current_function: str | None = None
        self.reads: dict[str, set[str]] = {}

    def visit_FunctionDef(self, node: ast.FunctionDef) -> None:
        previous = self.current_function
        self.current_function = node.name
        self.reads.setdefault(node.name, set())
        self.generic_visit(node)
        self.current_function = previous

    def visit_Subscript(self, node: ast.Subscript) -> None:
        if (
            self.current_function is not None
            and isinstance(node.value, ast.Name)
            and node.value.id == "episode"
            and isinstance(node.slice, ast.Constant)
            and isinstance(node.slice.value, str)
        ):
            self.reads[self.current_function].add(node.slice.value)
        self.generic_visit(node)

    def visit_Call(self, node: ast.Call) -> None:
        if (
            self.current_function is not None
            and isinstance(node.func, ast.Attribute)
            and isinstance(node.func.value, ast.Name)
            and node.func.value.id == "episode"
            and node.func.attr == "get"
            and node.args
            and isinstance(node.args[0], ast.Constant)
            and isinstance(node.args[0].value, str)
        ):
            self.reads[self.current_function].add(node.args[0].value)
        self.generic_visit(node)


def test_baseline_never_reads_non_output_terminal_episode_fields():
    source = Path(baseline_features.__file__).read_text(encoding="utf-8")
    reads = _EpisodeMappingReads()
    reads.visit(ast.parse(source))
    forbidden_terminal_names = {
        "artifact",
        "oracle_spec",
        "semantic_label",
        "mutation_score",
    }

    for function_name, fields in reads.reads.items():
        assert not fields & forbidden_terminal_names, function_name


def test_baseline_oracle_passed_can_affect_only_output_only(tmp_path: Path):
    trace_path = tmp_path / "trace.jsonl"
    trace_path.write_text("", encoding="utf-8")
    base_episode = {
        "intent_id": "RF-09",
        "task_family": "codegen",
        "variant": "smelly",
        "smell": {"type": "vague_threshold"},
        "requirement_text": "delayed after significant time",
    }

    failed_features = baseline_features.extract_features(
        {**base_episode, "oracle_passed": False}, trace_path
    )
    passed_features = baseline_features.extract_features(
        {**base_episode, "oracle_passed": True}, trace_path
    )

    assert failed_features["output_only"] != passed_features["output_only"]
    assert {
        family: values
        for family, values in failed_features.items()
        if family != "output_only"
    } == {
        family: values
        for family, values in passed_features.items()
        if family != "output_only"
    }


def test_baseline_delegates_pre_final_families_through_feature_plane(monkeypatch: pytest.MonkeyPatch):
    delegated_input = FeatureEpisodeInput.from_episode(
        {
            "intent_id": "RF-09",
            "task_family": "codegen",
            "variant": "smelly",
            "smell": {"type": "vague_threshold"},
            "requirement_text": "delayed after significant time",
        },
    )
    expected_pre_final = {"delegated": {"value": 1}}

    def fake_extract(
        feature_input: FeatureEpisodeInput, provenance_path: str
    ) -> dict[str, dict[str, int]]:
        assert feature_input == delegated_input
        assert provenance_path == ""
        return expected_pre_final

    monkeypatch.setattr(baseline_features, "extract_pre_final_features", fake_extract)

    assert baseline_features.extract_features(
        {
            "intent_id": "RF-09",
            "task_family": "codegen",
            "variant": "smelly",
            "smell": {"type": "vague_threshold"},
            "requirement_text": "delayed after significant time",
            "oracle_passed": True,
        },
        "",
    ) == {"delegated": {"value": 1}, "output_only": {"oracle_passed": 1}}
