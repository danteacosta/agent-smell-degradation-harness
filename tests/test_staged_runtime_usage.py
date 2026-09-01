from __future__ import annotations

import json

from agents.providers import ProviderRequest
from agents.runtime import RuntimeCheckpointAgent


class _MeasuredProvider:
    name = "measured-fixture"

    def __init__(self) -> None:
        self.responses = iter(
            [
                {
                    "constraints": [],
                    "quantities": [],
                    "unresolved_references": [],
                    "assumptions": [],
                    "contradictions": [],
                    "conditional_semantics": [],
                    "atomic_obligations": [],
                },
                {
                    "validation_checks": [],
                    "planned_tools": [],
                    "coverage_targets": [],
                },
                {"criterion": "bounded"},
            ]
        )
        self.last_call_metadata = {}

    def complete(self, request: ProviderRequest) -> str:
        self.last_call_metadata = {
            "usage": {"input_tokens": 10, "output_tokens": 2},
            "cost_usd": 0.01,
            "response_model": "resolved-fixture",
            "response_id": "response-fixture",
        }
        return json.dumps(next(self.responses))


def test_staged_runtime_aggregates_observed_usage_and_cost() -> None:
    pair = {
        "clean_requirement": "Return one criterion.",
        "smelly_requirement": "Return one criterion.",
        "generation_contract": {
            "acceptance_criteria": {"output_keys": ["criterion"]},
        },
    }
    result = RuntimeCheckpointAgent.from_provider(
        _MeasuredProvider(),
        model="configured-fixture",
        model_version="snapshot-fixture",
    ).execute_with_checkpoints(
        pair,
        variant="clean",
        task_family="acceptance_criteria",
    )

    assert result.provider_meta["usage"] == {
        "input_tokens": 30,
        "output_tokens": 6,
    }
    assert result.provider_meta["cost_usd"] == 0.03
    assert result.provider_meta["cost_reported"] is True
    assert result.provider_meta["cost_status"] == "measured"
    assert all(stage.get("usage") for stage in result.provider_meta["stages"] if stage["stage"] in {"T1", "T2", "artifact"})
    assert "response_id" in result.provider_meta["stages"][0]
