from __future__ import annotations

from pathlib import Path

import yaml

from gates.run import check_gate, check_gate_blind, load_baseline, load_thresholds

THRESHOLDS = {
    "floors": {
        "oracle_pass_rate_clean": 1.0,
        "semantic_provenance_coverage": 1.0,
    },
    "ceilings": {
        "paired_degradation_rate": 0.0,
    },
    "require_degradation_detector": True,
}

GOOD_METRICS = {
    "paired_degradation_rate": 0.0,
    "oracle_pass_rate_clean": 1.0,
    "semantic_provenance_coverage": 1.0,
    "degradation_detected": False,
}


def test_good_metrics_pass():
    passed, failures = check_gate(GOOD_METRICS, THRESHOLDS)
    assert passed is True
    assert failures == []


def test_high_paired_degradation_rate_fails():
    metrics = {
        **GOOD_METRICS,
        "paired_degradation_rate": 0.25,
        "degradation_detected": True,
    }
    passed, failures = check_gate(metrics, THRESHOLDS)
    assert passed is False
    assert any("paired_degradation_rate" in msg for msg in failures)


def test_low_semantic_provenance_coverage_fails():
    metrics = {**GOOD_METRICS, "semantic_provenance_coverage": 0.5}
    passed, failures = check_gate(metrics, THRESHOLDS)
    assert passed is False
    assert any("semantic_provenance_coverage" in msg for msg in failures)


def test_blind_gate_ignores_provenance_and_degradation():
    metrics = {
        **GOOD_METRICS,
        "paired_degradation_rate": 0.5,
        "semantic_provenance_coverage": 0.0,
        "degradation_detected": True,
    }
    passed, failures = check_gate_blind(metrics, THRESHOLDS)
    assert passed is True
    assert failures == []


def test_blind_gate_fails_on_low_oracle_pass_rate():
    metrics = {**GOOD_METRICS, "oracle_pass_rate_clean": 0.5}
    passed, failures = check_gate_blind(metrics, THRESHOLDS)
    assert passed is False
    assert any("oracle_pass_rate_clean" in msg for msg in failures)


def test_missing_degradation_detected_fails_when_required():
    metrics = {k: v for k, v in GOOD_METRICS.items() if k != "degradation_detected"}
    passed, failures = check_gate(metrics, THRESHOLDS)
    assert passed is False
    assert any("degradation_detected" in msg for msg in failures)


def test_inconsistent_degradation_detected_fails():
    metrics = {
        **GOOD_METRICS,
        "paired_degradation_rate": 0.25,
        "degradation_detected": False,
    }
    passed, failures = check_gate(metrics, THRESHOLDS)
    assert passed is False
    assert any("degradation_detected" in msg for msg in failures)


def test_load_thresholds_from_yaml():
    repo_root = Path(__file__).resolve().parents[1]
    thresholds = load_thresholds(repo_root / "eval" / "thresholds.yaml")
    assert thresholds["floors"]["oracle_pass_rate_clean"] == 1.0
    assert thresholds["ceilings"]["paired_degradation_rate"] == 0.0
    assert thresholds["require_degradation_detector"] is True


def test_load_baseline_from_json():
    repo_root = Path(__file__).resolve().parents[1]
    baseline = load_baseline(repo_root / "eval" / "baselines" / "ci.json")
    assert "note" in baseline
