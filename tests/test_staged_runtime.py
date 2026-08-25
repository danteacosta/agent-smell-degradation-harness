from __future__ import annotations

import json
from datetime import datetime, timedelta, timezone

import pytest

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
            "conditional_semantics": [{
                "antecedent": "a request exceeds five minutes",
                "consequent": "the request is rejected",
                "necessity_status": "sufficient_only",
                "temporal_relation": "next_state",
                "negative_case": {"status": "specified", "description": "the request is at or below five minutes"},
            }],
        }),
        json.dumps({
            "validation_checks": ["check boundary"],
            "planned_tools": ["contract validator"],
            "coverage_targets": ["reject after 5 minutes"],
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
    t3 = result.checkpoints[-1].payload
    assert t3["errors"] == []
    assert result.provider_meta["stages"][2]["validator"] == "semantic-plan-contract-validator/v2"
    assert result.provider_meta["stages"][2]["uncovered_constraint_count"] == 0
    assert result.provider_meta["stages"][2]["conditional_clause_count"] == 1
    assert result.checkpoints[0].payload["conditional_semantics"][0]["necessity_status"] == "sufficient_only"
    assert result.provider_meta["runtime"] == "staged-provider/v1"
    assert all("sha256" in key for key in ("request_sha256", "response_sha256"))


def test_staged_prompts_do_not_disclose_variant_or_oracle() -> None:
    captured: list[str] = []
    captured_requests: list[tuple[dict, str]] = []

    class CapturingProvider:
        name = "capture"

        def __init__(self) -> None:
            self.responses = iter([
                {"constraints": [], "quantities": [], "unresolved_references": [], "assumptions": [], "contradictions": [], "conditional_semantics": []},
                {"validation_checks": [], "planned_tools": [], "coverage_targets": []},
                {"criterion": "bounded"},
            ])

        def complete(self, request):
            captured.append(request.prompt)
            captured_requests.append((request.pair, request.variant))
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
    assert captured_requests[0][0] == {
        "requirement": "Incomplete requirement.",
        "task_family": "acceptance_criteria",
        "output_keys": ["criterion"],
    }
    assert all(variant == "opaque" for _pair, variant in captured_requests)


def test_staged_provider_requires_conditional_semantics_before_artifact() -> None:
    provider = ReplayProvider([
        json.dumps({
            "constraints": [],
            "quantities": [],
            "unresolved_references": [],
            "assumptions": [],
            "contradictions": [],
        }),
        json.dumps({"criterion": "must not be requested"}),
    ])
    pair = {
        "clean_requirement": "Return one criterion.",
        "smelly_requirement": "Return something.",
        "generation_contract": {"acceptance_criteria": {"output_keys": ["criterion"]}},
    }
    with pytest.raises(ValueError, match="conditional_semantics"):
        RuntimeCheckpointAgent.from_provider(
            provider, model="m", model_version="v"
        ).execute_with_checkpoints(pair, variant="clean", task_family="acceptance_criteria")
    assert provider.calls_made == 1


def test_t3_materializes_cross_stage_coverage_failures_before_artifact() -> None:
    responses = [
        json.dumps({
            "constraints": ["reject requests after five minutes"],
            "quantities": ["five minutes"],
            "unresolved_references": ["which clock is authoritative"],
            "assumptions": [],
            "contradictions": [],
            "conditional_semantics": [],
        }),
        json.dumps({
            "validation_checks": ["check the response schema"],
            "planned_tools": ["contract validator"],
            "coverage_targets": [],
        }),
        json.dumps({"criterion": "reject late requests"}),
    ]
    pair = {
        "clean_requirement": "Reject requests after five minutes.",
        "smelly_requirement": "Reject late requests.",
        "generation_contract": {"acceptance_criteria": {"output_keys": ["criterion"]}},
    }
    result = RuntimeCheckpointAgent.from_provider(
        ReplayProvider(responses), model="replay-model", model_version="fixture-v1"
    ).execute_with_checkpoints(
        pair, variant="clean", task_family="acceptance_criteria"
    )

    t3 = result.checkpoints[-1].payload
    assert len(t3["errors"]) == 2
    t3_metadata = result.provider_meta["stages"][2]
    assert t3_metadata["uncovered_constraint_count"] == 1
    assert t3_metadata["unacknowledged_uncertainty_count"] == 1


def test_malformed_plan_stops_before_t3_and_terminal_artifact() -> None:
    provider = ReplayProvider([
        json.dumps({
            "constraints": [],
            "quantities": [],
            "unresolved_references": [],
            "assumptions": [],
            "contradictions": [],
            "conditional_semantics": [],
        }),
        "not-json",
        json.dumps({"criterion": "must never be requested"}),
    ])
    pair = {
        "clean_requirement": "Return one criterion.",
        "smelly_requirement": "Return something.",
        "generation_contract": {"acceptance_criteria": {"output_keys": ["criterion"]}},
    }

    try:
        RuntimeCheckpointAgent.from_provider(
            provider, model="replay-model", model_version="fixture-v1"
        ).execute_with_checkpoints(
            pair, variant="clean", task_family="acceptance_criteria"
        )
    except json.JSONDecodeError:
        pass
    else:
        raise AssertionError("malformed plan must fail closed")
    assert provider.calls_made == 2


def test_provider_failure_stops_before_terminal_artifact() -> None:
    class FailingProvider:
        name = "failing"

        def __init__(self) -> None:
            self.calls = 0

        def complete(self, request):
            self.calls += 1
            if self.calls == 2:
                raise TimeoutError("provider timeout")
            return json.dumps({
                "constraints": [],
                "quantities": [],
                "unresolved_references": [],
                "assumptions": [],
                "contradictions": [],
                "conditional_semantics": [],
            })

    provider = FailingProvider()
    pair = {
        "clean_requirement": "Return one criterion.",
        "smelly_requirement": "Return something.",
        "generation_contract": {"acceptance_criteria": {"output_keys": ["criterion"]}},
    }
    try:
        RuntimeCheckpointAgent.from_provider(
            provider, model="m", model_version="v"
        ).execute_with_checkpoints(
            pair, variant="clean", task_family="acceptance_criteria"
        )
    except TimeoutError:
        pass
    else:
        raise AssertionError("provider timeout must fail closed")
    assert provider.calls == 2
