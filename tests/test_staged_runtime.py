from __future__ import annotations

import json
from datetime import datetime, timedelta, timezone

from agents.providers import ReplayProvider
from agents.runtime import RuntimeCheckpointAgent


def test_staged_provider_materializes_checkpoints_before_artifact() -> None:
    responses = [
        json.dumps({
            "constraints": ["after 5 minutes"],
            "quantities": ["5 minutes"],
            "unresolved_references": [],
            "assumptions": [],
            "contradictions": [],
        }),
        json.dumps({
            "validation_checks": ["check boundary"],
            "planned_tools": ["contract validator"],
            "coverage_targets": ["timeout"],
        }),
        json.dumps({"criterion": "reject after 5 minutes"}),
    ]
    provider = ReplayProvider(responses)
    values = iter(
        datetime(2026, 8, 23, tzinfo=timezone.utc) + timedelta(milliseconds=index)
        for index in range(20)
    )
    pair = {
        "clean_requirement": "Reject after 5 minutes.",
        "smelly_requirement": "Reject late requests.",
        "generation_contract": {"acceptance_criteria": {"output_keys": ["criterion"]}},
    }
    agent = RuntimeCheckpointAgent.from_provider(
        provider,
        model="replay-model",
        model_version="fixture-v1",
        clock=lambda: next(values),
    )

    result = agent.execute_with_checkpoints(
        pair, variant="clean", task_family="acceptance_criteria"
    )

    assert provider.calls_made == 3
    assert [item.checkpoint for item in result.checkpoints] == [
        "interpretation.completed", "plan.completed", "execution.started", "tool.completed"
    ]
    assert result.checkpoints[-1].ended_at < result.provider_meta["stages"][-1]["started_at"]
    assert result.artifact == {"criterion": "reject after 5 minutes"}
    assert result.provider_meta["runtime"] == "staged-provider/v1"
    assert all("sha256" in key for key in ("request_sha256", "response_sha256"))


def test_staged_prompts_do_not_disclose_variant_or_oracle() -> None:
    captured: list[str] = []

    class CapturingProvider:
        name = "capture"

        def __init__(self) -> None:
            self.responses = iter([
                {"constraints": [], "quantities": [], "unresolved_references": [], "assumptions": [], "contradictions": []},
                {"validation_checks": [], "planned_tools": [], "coverage_targets": []},
                {"criterion": "bounded"},
            ])

        def complete(self, request):
            captured.append(request.prompt)
            return json.dumps(next(self.responses))

    pair = {
        "clean_requirement": "Bounded requirement.",
        "smelly_requirement": "Incomplete requirement.",
        "oracle_spec": {"acceptance_criteria": {"secret": 42}},
        "smell": {"type": "missing-condition"},
        "generation_contract": {"acceptance_criteria": {"output_keys": ["criterion"]}},
    }
    result = RuntimeCheckpointAgent.from_provider(
        CapturingProvider(), model="m", model_version="v"
    ).execute_with_checkpoints(pair, variant="smelly", task_family="acceptance_criteria")

    joined = "\n".join(captured).lower()
    assert "missing-condition" not in joined
    assert "secret" not in joined
    assert "variant:" not in joined
    assert result.provider_meta["provider"] == "capture"
