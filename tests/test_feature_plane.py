from __future__ import annotations

import ast
import dataclasses
from pathlib import Path

import pytest

from observability.feature_plane import (
    FeatureEpisodeInput,
    extract_pre_final_features,
    semantic_risk,
)
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


def _write_trace(
    path: Path,
    constraint_payload: dict[str, object] | None,
    oracle_payload: dict[str, object] | None = None,
) -> str:
    recorder = ProvenanceRecorder(path)
    recorder.operational("latency", {"ms": 1}, tier="A")
    if constraint_payload is not None:
        recorder.semantic("constraint_extract", constraint_payload, tier="A")
    recorder.oracle_verdict(oracle_payload or {"passed": False}, tier="B")
    recorder.close()
    return path.read_text(encoding="utf-8")


def test_feature_episode_input_copies_only_pre_final_episode_fields(tmp_path: Path):
    _write_trace(tmp_path / "trace.jsonl", {"first": 1})
    input_episode = FeatureEpisodeInput.from_episode(
        _episode(hidden_terminal_sentinel={"must_not_cross": "feature_plane"})
    )

    assert input_episode.intent_id == "RF-09"
    assert input_episode.task_family == "codegen"
    assert input_episode.variant == "smelly"
    assert input_episode.smell == {"type": "vague_threshold"}
    assert input_episode.requirement_text == "Refund delayed orders after 15 minutes."
    assert {field.name for field in dataclasses.fields(FeatureEpisodeInput)} == {
        "intent_id",
        "task_family",
        "variant",
        "smell",
        "requirement_text",
    }
    for terminal_attribute in (
        "artifact",
        "oracle_spec",
        "oracle_passed",
        "semantic_label",
        "mutation_score",
        "hidden_terminal_sentinel",
    ):
        assert not hasattr(input_episode, terminal_attribute)


def test_feature_episode_input_is_immune_to_caller_smell_mutation(tmp_path: Path):
    trace_path = tmp_path / "trace.jsonl"
    _write_trace(trace_path, {"first": 1})
    smell = {"type": "vague_threshold", "details": {"window": 15}}
    feature_input = FeatureEpisodeInput.from_episode(_episode(smell=smell))
    original_features = extract_pre_final_features(feature_input, trace_path)

    smell["type"] = "replacement"
    smell["details"]["window"] = 30

    assert feature_input.smell == {
        "type": "vague_threshold",
        "details": {"window": 15},
    }
    assert extract_pre_final_features(feature_input, trace_path) == original_features


def test_direct_feature_episode_input_freezes_smell_metadata():
    smell = {"type": "vague_threshold", "details": {"window": 15}}
    feature_input = FeatureEpisodeInput(
        intent_id="RF-09",
        task_family="codegen",
        variant="smelly",
        smell=smell,
        requirement_text="Refund delayed orders after 15 minutes.",
    )

    with pytest.raises(TypeError):
        feature_input.smell["type"] = "replacement"  # type: ignore[index]
    with pytest.raises(TypeError):
        feature_input.smell["details"]["window"] = 30  # type: ignore[index]


def test_pre_final_features_use_tier_a_trace_and_ignore_tier_b(tmp_path: Path):
    trace_path = tmp_path / "trace.jsonl"
    _write_trace(trace_path, {"first": 1, "comparator": ">"})
    feature_input = FeatureEpisodeInput.from_episode(_episode())

    features = extract_pre_final_features(feature_input, trace_path)

    assert features["operational"]["event_count"] == 2
    assert features["provenance_semantic"] == {
        "constraint_event_present": 1,
        "constraint_field_count": 2,
        "constraint_has_comparator": 1,
        "semantic_event_count": 1,
    }


def test_pre_final_semantic_features_ignore_lifecycle_metadata_events(tmp_path: Path):
    trace_path = tmp_path / "trace.jsonl"
    recorder = ProvenanceRecorder(trace_path)
    recorder.semantic("interpretation.completed", {"requirement_text": "Refund."}, tier="A")
    recorder.semantic("constraint_extract", {"first": 1}, tier="A")
    recorder.semantic("plan.completed", {"task_family": "codegen"}, tier="A")
    recorder.close()

    features = extract_pre_final_features(
        FeatureEpisodeInput.from_episode(_episode()), trace_path
    )

    assert features["provenance_semantic"] == {
        "constraint_event_present": 1,
        "constraint_field_count": 1,
        "constraint_has_comparator": 0,
        "semantic_event_count": 1,
    }


def test_pre_final_features_are_invariant_to_tier_b_oracle_payload(tmp_path: Path):
    tier_a_payload = {"first": 1, "comparator": ">"}
    passing_path = tmp_path / "passing.jsonl"
    failing_path = tmp_path / "failing.jsonl"
    _write_trace(passing_path, tier_a_payload, {"passed": True, "score": 1})
    _write_trace(failing_path, tier_a_payload, {"passed": False, "score": 0})
    passing_input = FeatureEpisodeInput.from_episode(_episode())
    failing_input = FeatureEpisodeInput.from_episode(_episode())

    assert extract_pre_final_features(
        passing_input, passing_path
    ) == extract_pre_final_features(
        failing_input, failing_path
    )


def test_pre_final_features_are_invariant_to_final_episode_data(tmp_path: Path):
    trace_path = tmp_path / "trace.jsonl"
    _write_trace(trace_path, {"first": 1})
    source = _episode()
    changed_only_final_data = _episode(
        artifact={"unrelated": "replacement"},
        oracle_spec={"expected": "replacement"},
        oracle_passed=True,
        semantic_label="correct",
        mutation_score=1.0,
    )

    source_features = extract_pre_final_features(
        FeatureEpisodeInput.from_episode(source), trace_path
    )
    changed_features = extract_pre_final_features(
        FeatureEpisodeInput.from_episode(changed_only_final_data), trace_path
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
def test_semantic_risk_is_neutral_and_trace_derived(
    tmp_path: Path,
    constraint_payload: dict[str, object] | None,
    expected_risk: float,
):
    trace_path = tmp_path / "trace.jsonl"
    _write_trace(trace_path, constraint_payload)
    feature_input = FeatureEpisodeInput.from_episode(_episode())

    features = extract_pre_final_features(feature_input, trace_path)

    assert semantic_risk(features["provenance_semantic"]) == expected_risk


def _is_forbidden_module(module_name: str) -> bool:
    return module_name in {"label_plane", "eval.oracles", "pairs.loader"} or module_name.endswith(
        ".label_plane"
    )


class _FeaturePlaneForbiddenReferences(ast.NodeVisitor):
    def __init__(self) -> None:
        self.forbidden_imports: set[str] = set()
        self.forbidden_references: set[str] = set()

    def visit_Import(self, node: ast.Import) -> None:
        self.forbidden_imports.update(
            alias.name for alias in node.names if _is_forbidden_module(alias.name)
        )

    def visit_ImportFrom(self, node: ast.ImportFrom) -> None:
        module = node.module or ""
        if _is_forbidden_module(module):
            self.forbidden_imports.add(module)
        self.forbidden_imports.update(
            f"{module}.{alias.name}"
            for alias in node.names
            if _is_forbidden_module(f"{module}.{alias.name}")
        )

    def visit_Name(self, node: ast.Name) -> None:
        if node.id in {
            "oracle_spec",
            "artifact",
            "oracle_passed",
            "semantic_label",
            "mutation_score",
        }:
            self.forbidden_references.add(node.id)

    def visit_Attribute(self, node: ast.Attribute) -> None:
        if node.attr in {
            "oracle_spec",
            "artifact",
            "oracle_passed",
            "semantic_label",
            "mutation_score",
        }:
            self.forbidden_references.add(node.attr)
        self.generic_visit(node)

    def visit_Subscript(self, node: ast.Subscript) -> None:
        if (
            isinstance(node.slice, ast.Constant)
            and node.slice.value
            in {
                "oracle_spec",
                "artifact",
                "oracle_passed",
                "semantic_label",
                "mutation_score",
            }
        ):
            self.forbidden_references.add(node.slice.value)
        self.generic_visit(node)

    def visit_Call(self, node: ast.Call) -> None:
        is_mapping_get = isinstance(node.func, ast.Attribute) and node.func.attr == "get"
        is_getattr = isinstance(node.func, ast.Name) and node.func.id == "getattr"
        field_argument = 0 if is_mapping_get else 1
        if (
            (is_mapping_get or is_getattr)
            and len(node.args) > field_argument
            and isinstance(node.args[field_argument], ast.Constant)
            and node.args[field_argument].value
            in {
                "oracle_spec",
                "artifact",
                "oracle_passed",
                "semantic_label",
                "mutation_score",
            }
        ):
            self.forbidden_references.add(node.args[field_argument].value)
        self.generic_visit(node)


def test_feature_plane_cannot_import_label_plane():
    import feature_plane

    implementation_dir = Path(feature_plane.__file__).parent
    references = _FeaturePlaneForbiddenReferences()
    for source_path in implementation_dir.glob("*.py"):
        references.visit(ast.parse(source_path.read_text(encoding="utf-8")))

    assert not references.forbidden_imports
    assert not references.forbidden_references
