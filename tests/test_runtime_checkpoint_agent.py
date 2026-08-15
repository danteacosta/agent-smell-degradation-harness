from __future__ import annotations

from datetime import datetime, timedelta, timezone

from agents.checkpoints import AgentExecution, CheckpointObservation
from agents.runtime import RuntimeCheckpointAgent


def test_runtime_adapter_keeps_artifact_and_checkpoints_in_one_execution() -> None:
    calls: list[tuple[str, str]] = []
    start = datetime.now(timezone.utc)
    timestamps = [(start + timedelta(milliseconds=index)).isoformat() for index in range(4)]

    def execute(pair, variant, task_family):
        calls.append((variant, task_family))
        return AgentExecution(
            (
                CheckpointObservation("interpretation.completed", {
                    "constraints": ["x > 1"], "quantities": [], "unresolved_references": [],
                    "assumptions": [], "contradictions": [],
                }, timestamps[0], timestamps[0]),
                CheckpointObservation("plan.completed", {
                    "validation_checks": ["check x"], "planned_tools": [], "coverage_targets": [],
                }, timestamps[1], timestamps[1]),
                CheckpointObservation("execution.started", {}, timestamps[2], timestamps[2]),
                CheckpointObservation("tool.completed", {
                    "revisions": 0, "validation_attempts": 1, "errors": [], "retrieval_events": 0,
                }, timestamps[3], timestamps[3]),
            ),
            {"criterion": "x > 1"},
            {"latency_ms": 4.0},
        )

    agent = RuntimeCheckpointAgent(
        execute,
        provider="acp-runtime",
        model="model-neutral",
        model_version="2026-08",
    )

    result = agent.execute_with_checkpoints({}, variant="opaque-a", task_family="test_gen")

    assert calls == [("opaque-a", "test_gen")]
    assert result.artifact == {"criterion": "x > 1"}
    assert result.provider_meta["provider"] == "acp-runtime"
    assert agent.checkpoint_provenance == "runtime_native"
