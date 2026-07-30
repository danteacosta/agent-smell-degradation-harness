from __future__ import annotations

from eval.runner import run_eval_with_agent
from eval.task_adapters import (
    AcceptanceCriteriaAdapter,
    CodeGenerationAdapter,
    TraceabilityAdapter,
)


class _OracleAgent:
    def generate(self, pair, variant, task_family):
        return pair["oracle_spec"][task_family]


def _pair() -> dict:
    return {
        "intent_id": "RF-ADAPTER",
        "clean_requirement": "Reject elapsed time of five minutes or less.",
        "smelly_requirement": "Reject old requests.",
        "smell": {"type": "vague_threshold"},
        "oracle_spec": {
            "codegen": {"delay_threshold_minutes": 5, "comparator": ">"},
            "test_gen": {
                "must_reject_minutes": [0, 5],
                "must_accept_minutes": [6],
                "criterion": "delay_minutes > 5",
            },
        },
    }


def test_runner_executes_only_the_configured_task_adapters(tmp_path):
    _metrics, episodes = run_eval_with_agent(
        _OracleAgent(),
        pairs=[_pair()],
        task_adapters=(AcceptanceCriteriaAdapter(),),
        output_path=tmp_path / "metrics.json",
        traces_dir=tmp_path / "traces",
    )

    assert {episode["task_family"] for episode in episodes} == {"test_gen"}
    assert all(episode["mutation_score"] == 1.0 for episode in episodes)


def test_traceability_adapter_validates_the_completed_episode_trace(tmp_path):
    _metrics, episodes = run_eval_with_agent(
        _OracleAgent(),
        pairs=[_pair()],
        task_adapters=(CodeGenerationAdapter(),),
        validators=(TraceabilityAdapter(),),
        output_path=tmp_path / "metrics.json",
        traces_dir=tmp_path / "traces",
    )

    assert len(episodes) == 2
    assert all(episode["traceability_valid"] is True for episode in episodes)
