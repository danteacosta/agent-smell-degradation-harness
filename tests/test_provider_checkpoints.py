from __future__ import annotations

import json
from pathlib import Path
from datetime import datetime, timedelta, timezone

import pytest

from eval.runner import run_eval_with_agent
from eval.task_adapters import AcceptanceCriteriaAdapter
from agents.stub import StubAgent
from agents.checkpoints import AgentExecution, CheckpointObservation


def _pair() -> dict:
    return {
        "intent_id": "checkpoint-1",
        "clean_requirement": "Reject requests after 5 minutes.",
        "smelly_requirement": "Reject old requests.",
        "smell": {"type": "vague_threshold"},
        "oracle_spec": {
            "test_gen": {
                "must_reject_minutes": [6],
                "criterion": "delay_minutes > 5",
            }
        },
    }


class _CheckpointAgent:
    provider = "runtime-fixture"
    model = "checkpoint-fixture"
    run_mode = "runtime"
    checkpoint_provenance = "runtime_native"

    def execute_with_checkpoints(self, pair, *, variant, task_family):
        start = datetime.now(timezone.utc) + timedelta(milliseconds=1)
        moments = [(start + timedelta(milliseconds=index)).isoformat() for index in range(4)]
        return AgentExecution(
            checkpoints=(
                CheckpointObservation("interpretation.completed", {
                "constraints": ["delay_minutes > 5"],
                "quantities": [{"value": 5, "unit": "minutes"}],
                "unresolved_references": [],
                "assumptions": [],
                "contradictions": [],
                }, moments[0], moments[0]),
                CheckpointObservation("plan.completed", {
                "validation_checks": ["boundary at 5 minutes"],
                "planned_tools": ["acceptance_criteria_validator"],
                "coverage_targets": ["delay threshold"],
                }, moments[1], moments[1]),
                CheckpointObservation("execution.started", {}, moments[2], moments[2]),
                CheckpointObservation("tool.completed", {
                "revisions": 0,
                "validation_attempts": 1,
                "errors": [],
                "retrieval_events": 0,
                }, moments[3], moments[3]),
            ),
            artifact=pair["oracle_spec"][task_family],
            provider_meta={"provider": self.provider, "model": self.model, "latency_ms": 4.0},
        )


def test_confirmatory_run_records_provider_checkpoints_without_experiment_metadata(tmp_path):
    _metrics, episodes = run_eval_with_agent(
        _CheckpointAgent(),
        pairs=[_pair()],
        task_adapters=(AcceptanceCriteriaAdapter(),),
        confirmatory=True,
        split="test",
        source_revision="test-revision",
        output_path=tmp_path / "metrics.json",
        traces_dir=tmp_path / "traces",
    )

    events = [
        json.loads(line)
        for line in (tmp_path / "traces").glob("*.jsonl")
        for line in line.read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]
    interpretation = next(event for event in events if event["checkpoint"] == "interpretation.completed")
    plan = next(event for event in events if event["checkpoint"] == "plan.completed")
    assert interpretation["attributes"]["constraints"] == ["delay_minutes > 5"]
    assert plan["attributes"]["validation_checks"] == ["boundary at 5 minutes"]
    assert "variant" not in interpretation["attributes"]
    assert "smell" not in interpretation["attributes"]
    assert episodes[0]["provider_meta"]["provider"] == "runtime-fixture"
    assert episodes[0]["arp_manifest_path"].endswith(".manifest.json")
    manifest = json.loads(Path(episodes[0]["arp_manifest_path"]).read_text(encoding="utf-8"))
    assert manifest["profile"] == "agent-smell-degradation/v1"
    assert manifest["extensions"]["agent-smell-degradation/v1"]["checkpoint_provenance"] == "runtime_native"
    assert all(event["schema_version"] == "3.0.0" for event in events)
    assert [event["checkpoint"] for event in events] == [
        "input.received",
        "interpretation.completed",
        "plan.completed",
        "execution.started",
        "tool.completed",
        "artifact.completed",
        "evaluation.completed",
    ] * 2


def test_confirmatory_run_rejects_agents_without_provider_checkpoints(tmp_path):
    class ArtifactOnly:
        def generate(self, pair, variant, task_family):
            return pair["oracle_spec"][task_family]

    with pytest.raises(ValueError, match="provider checkpoints"):
        run_eval_with_agent(
            ArtifactOnly(),
            pairs=[_pair()],
            task_adapters=(AcceptanceCriteriaAdapter(),),
            confirmatory=True,
            split="test",
            source_revision="test-revision",
            output_path=tmp_path / "metrics.json",
            traces_dir=tmp_path / "traces",
        )


def test_confirmatory_run_rejects_stub_mode_even_when_it_can_emit_checkpoint_shape(tmp_path):
    with pytest.raises(ValueError, match="real provider"):
        run_eval_with_agent(
            StubAgent(),
            pairs=[_pair()],
            task_adapters=(AcceptanceCriteriaAdapter(),),
            confirmatory=True,
            split="test",
            source_revision="test-revision",
            output_path=tmp_path / "metrics.json",
            traces_dir=tmp_path / "traces",
        )


def test_confirmatory_run_rejects_prompted_checkpoint_snapshots(tmp_path):
    class PromptedSnapshotAgent(_CheckpointAgent):
        checkpoint_provenance = "prompted_snapshot"

    with pytest.raises(ValueError, match="runtime-native checkpoints"):
        run_eval_with_agent(
            PromptedSnapshotAgent(),
            pairs=[_pair()],
            task_adapters=(AcceptanceCriteriaAdapter(),),
            confirmatory=True,
            split="test",
            source_revision="test-revision",
            output_path=tmp_path / "metrics.json",
            traces_dir=tmp_path / "traces",
        )


def test_confirmatory_preflight_requires_frozen_split_before_writing(tmp_path):
    traces = tmp_path / "traces"

    with pytest.raises(ValueError, match="frozen train/calibration/test split"):
        run_eval_with_agent(
            _CheckpointAgent(),
            pairs=[_pair()],
            task_adapters=(AcceptanceCriteriaAdapter(),),
            confirmatory=True,
            output_path=tmp_path / "metrics.json",
            traces_dir=traces,
        )

    assert not traces.exists()


def test_confirmatory_preflight_rejects_replay_even_with_native_shaped_events(tmp_path):
    class ReplayAgent(_CheckpointAgent):
        run_mode = "replay"

    with pytest.raises(ValueError, match="not stub, mock, or replay"):
        run_eval_with_agent(
            ReplayAgent(),
            pairs=[_pair()],
            task_adapters=(AcceptanceCriteriaAdapter(),),
            confirmatory=True,
            split="test",
            source_revision="test-revision",
            output_path=tmp_path / "metrics.json",
            traces_dir=tmp_path / "traces",
        )
