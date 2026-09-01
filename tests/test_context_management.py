from __future__ import annotations

import json

from agents.providers import ReplayProvider
from agents.runtime import RuntimeCheckpointAgent
from protocol.context_management import (
    DeterministicCompactionManager,
    NoCompactionManager,
)


def _responses() -> list[str]:
    return [
        json.dumps(
            {
                "constraints": ["reject after five minutes"],
                "quantities": ["five minutes"],
                "unresolved_references": [],
                "assumptions": [],
                "contradictions": [],
                "conditional_semantics": [
                    {
                        "antecedent": "a request exceeds five minutes",
                        "consequent": "the request is rejected",
                        "necessity_status": "sufficient_only",
                        "temporal_relation": "next_state",
                        "negative_case": {
                            "status": "specified",
                            "description": "the request is at or below five minutes",
                        },
                    }
                ],
            }
        ),
        json.dumps(
            {
                "validation_checks": ["check boundary"],
                "planned_tools": ["contract validator"],
                "coverage_targets": ["reject after five minutes"],
            }
        ),
        json.dumps({"criterion": "reject after five minutes"}),
    ]


class CapturingReplayProvider(ReplayProvider):
    def __init__(self, responses: list[str]) -> None:
        super().__init__(responses)
        self.prompts: list[str] = []

    def complete(self, request) -> str:
        self.prompts.append(request.prompt)
        return super().complete(request)


def _pair() -> dict:
    long_requirement = (
        "The service shall reject a request after five minutes and record the "
        "rejection reason. "
        + "The independently relevant constraint must remain observable. " * 30
    )
    return {
        "clean_requirement": long_requirement,
        "smelly_requirement": "Reject late requests.",
        "generation_contract": {
            "acceptance_criteria": {"output_keys": ["criterion"]}
        },
    }


def _run(condition: str, manager) -> tuple[CapturingReplayProvider, object]:
    provider = CapturingReplayProvider(_responses())
    agent = RuntimeCheckpointAgent.from_provider(
        provider,
        model="replay-model",
        model_version="fixture-v1",
        context_manager=manager,
    )
    result = agent.execute_with_checkpoints(
        _pair(),
        variant="clean",
        task_family="acceptance_criteria",
    )
    assert result.provider_meta["context_management"]["condition"] == condition
    return provider, result


def test_context_matrix_records_clean_and_smelly_cells_without_terminal_leakage() -> None:
    cells = {}
    for variant in ("clean", "smelly"):
        for condition, manager in (
            ("no_compaction", NoCompactionManager()),
            (
                "compaction_stress_test",
                DeterministicCompactionManager(max_context_bytes=128),
            ),
        ):
            provider = CapturingReplayProvider(_responses())
            agent = RuntimeCheckpointAgent.from_provider(
                provider,
                model="replay-model",
                model_version="fixture-v1",
                context_manager=manager,
            )
            result = agent.execute_with_checkpoints(
                _pair(),
                variant=variant,
                task_family="acceptance_criteria",
            )
            cells[(variant, condition)] = (provider, result)

    assert set(cells) == {
        ("clean", "no_compaction"),
        ("clean", "compaction_stress_test"),
        ("smelly", "no_compaction"),
        ("smelly", "compaction_stress_test"),
    }

    expected_fields = {
        "schema_version",
        "event_id",
        "stage",
        "operation",
        "trigger",
        "started_at",
        "ended_at",
        "context_size_before",
        "context_size_after",
        "context_size_unit",
        "checkpoint_id",
        "checkpoint_sha256",
    }
    for (variant, condition), (provider, result) in cells.items():
        pre_final = result.provider_meta["pre_final_context_management"]
        assert pre_final["condition"] == condition
        assert pre_final["event_count"] == 2
        assert pre_final["compaction_count"] == (0 if condition == "no_compaction" else 2)

        events = result.checkpoints[-1].payload["context_management"]
        assert len(events) == 2
        assert all(set(event) == expected_fields for event in events)
        assert all(event["context_size_after"] <= event["context_size_before"] for event in events)
        assert all(len(event["checkpoint_sha256"]) == 64 for event in events)
        assert all(
            forbidden not in event
            for event in events
            for forbidden in ("prompt", "requirement", "artifact", "oracle", "label", "variant")
        )

        if condition == "no_compaction":
            assert all(event["operation"] == "none" for event in events)
            assert all("context compacted" not in prompt for prompt in provider.prompts)
        else:
            assert all(event["operation"] == "compact" for event in events)
            assert all("context compacted" in prompt for prompt in provider.prompts)
        assert variant in ("clean", "smelly")


def test_no_compaction_is_identity_and_stress_condition_is_explicit() -> None:
    identity_provider, identity_result = _run("no_compaction", NoCompactionManager())
    stress_provider, stress_result = _run(
        "compaction_stress_test",
        DeterministicCompactionManager(max_context_bytes=128),
    )

    assert identity_result.provider_meta["context_management"]["compaction_count"] == 0
    assert stress_result.provider_meta["context_management"]["compaction_count"] == 3
    assert identity_provider.prompts != stress_provider.prompts
    assert all(event["operation"] == "none" for event in identity_result.checkpoints[-1].payload["context_management"])
    assert all(event["operation"] == "compact" for event in stress_result.checkpoints[-1].payload["context_management"])
