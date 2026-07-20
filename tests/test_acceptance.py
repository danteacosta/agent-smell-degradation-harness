"""ATDD acceptance criteria AT1–AT5 for the Tier 0–1 smell-degradation harness."""

from __future__ import annotations

from pathlib import Path

from eval.runner import run_eval
from eval.simulate_regressions import simulate_all
from gates.run import check_gate, load_thresholds

ROOT = Path(__file__).resolve().parents[1]
THRESHOLDS = load_thresholds(ROOT / "eval" / "thresholds.yaml")


def test_at1_happy_path_gate_passes_offline(tmp_path):
    """AT1: offline happy path — run_eval then check_gate passes without API keys."""
    metrics, _ = run_eval(
        output_path=tmp_path / "last_run.json",
        traces_dir=tmp_path / "traces",
    )
    assert metrics["paired_degradation_rate"] == 0.0
    ok, reasons = check_gate(metrics, THRESHOLDS)
    assert ok is True, reasons


def test_at2_smell_blind_fails_gate(tmp_path):
    """AT2: FM1 smell-blind injection fails the full gate."""
    metrics, _ = run_eval(
        failure_mode="smell-blind",
        output_path=tmp_path / "last_run.json",
        traces_dir=tmp_path / "traces",
    )
    ok, _ = check_gate(metrics, THRESHOLDS)
    assert ok is False


def test_at3_oracle_mismatch_fails_gate(tmp_path):
    """AT3: FM2 oracle-mismatch fails the full gate."""
    metrics, _ = run_eval(
        failure_mode="oracle-mismatch",
        output_path=tmp_path / "last_run.json",
        traces_dir=tmp_path / "traces",
    )
    ok, _ = check_gate(metrics, THRESHOLDS)
    assert ok is False


def test_at4_provenance_collapse_fails_gate(tmp_path):
    """AT4: FM3 provenance-collapse (skip semantic provenance) fails the full gate."""
    metrics, _ = run_eval(
        skip_semantic_provenance=True,
        output_path=tmp_path / "last_run.json",
        traces_dir=tmp_path / "traces",
    )
    ok, _ = check_gate(metrics, THRESHOLDS)
    assert ok is False


def test_at5_simulate_before_after_and_optional_ci(tmp_path):
    """AT5: simulate_all 0→1 catch rates, test_gen coverage, optional CI secrets check."""
    report = simulate_all(
        report_path=tmp_path / "sim_report.json",
        thresholds=THRESHOLDS,
        work_dir=tmp_path / "simulate",
    )

    for mode in ("smell-blind", "oracle-mismatch", "provenance-collapse"):
        assert report[mode]["before_catch_rate"] == 0.0
        assert report[mode]["after_catch_rate"] == 1.0

    assert "test_gen" in report["task_families_exercised"]

    workflow = ROOT / ".github" / "workflows" / "eval.yml"
    if workflow.is_file():
        text = workflow.read_text(encoding="utf-8")
        assert "secrets." not in text
        assert "OPENAI" not in text
        assert "ANTHROPIC" not in text
