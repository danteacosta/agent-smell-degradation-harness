import json
from pathlib import Path

from eval.runner import run_eval, run_eval_with_agent


def test_happy_path_default_stub(tmp_path):
    output_path = tmp_path / "metrics.json"
    traces_dir = tmp_path / "traces"

    metrics, _ = run_eval(
        failure_mode=None,
        output_path=output_path,
        traces_dir=traces_dir,
    )

    assert metrics["paired_degradation_rate"] == 0
    assert metrics["semantic_provenance_coverage"] == 1.0
    assert metrics["oracle_pass_rate_clean"] == 1.0
    assert metrics["degradation_detected"] is False

    assert output_path.exists()
    written = json.loads(output_path.read_text())
    assert written["paired_degradation_rate"] == 0
    assert written["semantic_provenance_coverage"] == 1.0

    trace_files = list(traces_dir.glob("*.jsonl"))
    assert len(trace_files) > 0


class _TerminalArtifactAgent:
    def generate(self, pair, variant, task_family):
        return {"terminal_only": f"{pair['intent_id']}:{task_family}:{variant}"}


def test_runner_records_ordered_lifecycle_with_pre_final_interpretation(tmp_path):
    pair = {
        "intent_id": "RF-LIFECYCLE",
        "clean_requirement": "Return eligible orders within 30 days.",
        "smelly_requirement": "Return old orders soon.",
        "smell": {"type": "vague_threshold"},
        "oracle_spec": {
            "codegen": {"terminal_only": "RF-LIFECYCLE:codegen:clean"},
            "test_gen": {"terminal_only": "RF-LIFECYCLE:test_gen:clean"},
        },
    }

    run_eval_with_agent(
        _TerminalArtifactAgent(),
        pairs=[pair],
        output_path=tmp_path / "metrics.json",
        traces_dir=tmp_path / "traces",
    )

    events = [
        json.loads(line)
        for line in (tmp_path / "traces" / "RF-LIFECYCLE_codegen_clean.jsonl")
        .read_text(encoding="utf-8")
        .splitlines()
    ]
    lifecycle_names = [
        event["name"]
        for event in events
        if event["name"]
        in {
            "input.received",
            "interpretation.completed",
            "plan.completed",
            "execution.started",
            "artifact.completed",
            "evaluation.completed",
        }
    ]

    assert lifecycle_names == [
        "input.received",
        "interpretation.completed",
        "plan.completed",
        "execution.started",
        "artifact.completed",
        "evaluation.completed",
    ]
    interpretation = next(
        event["payload"]
        for event in events
        if event["name"] == "interpretation.completed"
    )
    assert interpretation == {
        "requirement_text": "Return eligible orders within 30 days.",
        "task_family": "codegen",
        "variant": "clean",
        "policy": "direct",
    }
    assert "terminal_only" not in interpretation
    assert next(
        index for index, event in enumerate(events) if event["name"] == "interpretation.completed"
    ) < next(
        index for index, event in enumerate(events) if event["name"] == "artifact.completed"
    )
    artifact_completed = next(
        index for index, event in enumerate(events) if event["name"] == "artifact.completed"
    )
    oracle_verdict = next(
        index for index, event in enumerate(events) if event["name"] == "oracle_verdict"
    )
    evaluation_completed = next(
        index for index, event in enumerate(events) if event["name"] == "evaluation.completed"
    )
    assert artifact_completed < oracle_verdict < evaluation_completed
