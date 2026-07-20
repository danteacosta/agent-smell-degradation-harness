import json
from pathlib import Path

from eval.runner import run_eval


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
