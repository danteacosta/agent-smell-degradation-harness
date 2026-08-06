from __future__ import annotations

import json

import pytest

from eval.runner import run_eval_with_agent
from eval.task_adapters import AcceptanceCriteriaAdapter


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
    provider = "replay"
    model = "checkpoint-fixture"
    run_mode = "replay"

    def observe_checkpoints(self, pair, *, variant, task_family):
        return {
            "interpretation": {
                "constraints": ["delay_minutes > 5"],
                "quantities": [{"value": 5, "unit": "minutes"}],
                "unresolved_references": [],
                "assumptions": [],
                "contradictions": [],
            },
            "plan": {
                "validation_checks": ["boundary at 5 minutes"],
                "planned_tools": ["acceptance_criteria_validator"],
                "coverage_targets": ["delay threshold"],
            },
            "execution": {
                "revisions": 0,
                "validation_attempts": 1,
                "errors": [],
                "retrieval_events": 0,
            },
        }

    def generate(self, pair, variant, task_family):
        return pair["oracle_spec"][task_family]


def test_confirmatory_run_records_provider_checkpoints_without_experiment_metadata(tmp_path):
    _metrics, episodes = run_eval_with_agent(
        _CheckpointAgent(),
        pairs=[_pair()],
        task_adapters=(AcceptanceCriteriaAdapter(),),
        confirmatory=True,
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
    assert episodes[0]["provider_meta"]["provider"] == "replay"


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
            output_path=tmp_path / "metrics.json",
            traces_dir=tmp_path / "traces",
        )
