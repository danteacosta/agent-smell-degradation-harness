from pathlib import Path

from eval.mitigation_report import write_mitigation_report
from mitigation.tradeoff import (
    build_mitigation_report,
    is_mitigation_beneficial,
)


def test_is_mitigation_beneficial_when_both_zero_and_direct_positive():
    assert is_mitigation_beneficial(1.0, 0.0, 0.0) is True


def test_is_mitigation_beneficial_when_threshold_met():
    assert is_mitigation_beneficial(1.0, 0.4, 0.4) is True


def test_is_mitigation_beneficial_false_when_insufficient_reduction():
    assert is_mitigation_beneficial(0.6, 0.3, 0.3) is False


def test_build_mitigation_report_smell_blind_policies(tmp_path):
    report = build_mitigation_report(tmp_path / "work")

    assert report["direct"]["paired_degradation_rate"] > 0.0
    assert report["rewrite"]["paired_degradation_rate"] == 0.0
    assert report["clarify"]["paired_degradation_rate"] == 0.0
    assert report["happy_direct"]["paired_degradation_rate"] == 0.0
    assert report["mitigation_beneficial"] is True
    assert report["overhead"]["clarify_steps_mean"] == 1.0
    assert report["overhead"]["rewrite_char_delta_mean"] != 0.0
    assert report["gate"]["passed"] is True
    assert "rewrite" in report["gate"]["detail"]


def test_write_mitigation_report_json(tmp_path):
    output_path = tmp_path / "mitigation_report.json"
    report = write_mitigation_report(tmp_path / "work", output_path)

    assert output_path.exists()
    assert report["gate"]["passed"] is True
    assert "mitigation_beneficial" in report
