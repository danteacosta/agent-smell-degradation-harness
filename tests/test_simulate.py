from __future__ import annotations

import json
from pathlib import Path

import pytest

from eval.simulate_regressions import (
    MODES,
    check_gate_pre_harness,
    simulate_all,
    simulate_mode,
)
from gates.run import check_gate, check_gate_blind, load_thresholds


REPO_ROOT = Path(__file__).resolve().parents[1]
THRESHOLDS_PATH = REPO_ROOT / "eval" / "thresholds.yaml"


@pytest.fixture
def thresholds():
    return load_thresholds(THRESHOLDS_PATH)


@pytest.mark.parametrize("mode", sorted(MODES))
def test_mode_before_zero_after_one(mode, tmp_path, thresholds):
    traces_dir = tmp_path / mode / "traces"
    result = simulate_mode(mode, traces_dir=traces_dir, thresholds=thresholds)

    assert result["before_catch_rate"] == 0.0
    assert result["after_catch_rate"] == 1.0
    assert "metrics" in result


def test_smell_blind_degradation_full_gate_fails_blind_passes(tmp_path, thresholds):
    traces_dir = tmp_path / "smell-blind" / "traces"
    result = simulate_mode("smell-blind", traces_dir=traces_dir, thresholds=thresholds)
    metrics = result["metrics"]

    assert metrics["paired_degradation_rate"] > 0
    assert check_gate_blind(metrics, thresholds)[0] is True
    assert check_gate(metrics, thresholds)[0] is False


def test_oracle_mismatch_clean_oracle_drops(tmp_path, thresholds):
    traces_dir = tmp_path / "oracle-mismatch" / "traces"
    result = simulate_mode(
        "oracle-mismatch", traces_dir=traces_dir, thresholds=thresholds
    )
    metrics = result["metrics"]

    assert metrics["oracle_pass_rate_clean"] < thresholds["floors"]["oracle_pass_rate_clean"]
    assert check_gate(metrics, thresholds)[0] is False


def test_provenance_collapse_zero_coverage(tmp_path, thresholds):
    traces_dir = tmp_path / "provenance-collapse" / "traces"
    result = simulate_mode(
        "provenance-collapse", traces_dir=traces_dir, thresholds=thresholds
    )
    metrics = result["metrics"]

    assert metrics["semantic_provenance_coverage"] == 0.0
    assert check_gate_blind(metrics, thresholds)[0] is True
    assert check_gate(metrics, thresholds)[0] is False


def test_check_gate_pre_harness_always_passes_with_episodes(thresholds):
    metrics = {
        "episode_count": 1,
        "paired_degradation_rate": 1.0,
        "semantic_provenance_coverage": 0.0,
        "oracle_pass_rate_clean": 0.0,
    }
    passed, failures = check_gate_pre_harness(metrics, thresholds)
    assert passed is True
    assert failures == []


def test_simulate_all_report_shape(tmp_path, thresholds):
    report_path = tmp_path / "sim_report.json"
    report = simulate_all(
        report_path=report_path,
        thresholds=thresholds,
        work_dir=tmp_path / "simulate",
    )

    for mode in MODES:
        assert mode in report
        assert report[mode]["before_catch_rate"] == 0.0
        assert report[mode]["after_catch_rate"] == 1.0
        assert "metrics" in report[mode]

    assert "test_gen" in report["task_families_exercised"]
    assert "codegen" in report["task_families_exercised"]
    assert report_path.exists()
    written = json.loads(report_path.read_text())
    assert written["smell-blind"]["after_catch_rate"] == 1.0


def test_simulate_does_not_overwrite_last_run(tmp_path, thresholds):
    last_run_path = tmp_path / "last_run.json"
    sentinel = {"sentinel": "keep-me", "episode_count": 99}
    last_run_path.write_text(json.dumps(sentinel), encoding="utf-8")

    simulate_all(
        report_path=tmp_path / "sim_report.json",
        thresholds=thresholds,
        work_dir=tmp_path / "simulate",
        last_run_path=last_run_path,
    )

    assert json.loads(last_run_path.read_text()) == sentinel
