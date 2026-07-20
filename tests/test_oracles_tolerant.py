from __future__ import annotations

from eval.oracles import score_artifact


def test_extra_artifact_keys_still_pass():
    spec = {"delay_threshold_minutes": 5, "comparator": ">"}
    artifact = {
        "delay_threshold_minutes": 5,
        "comparator": ">",
        "debug_note": "extra is fine",
    }
    result = score_artifact("RF-09", "codegen", artifact, spec)
    assert result.passed is True
    assert result.checks == {"delay_threshold_minutes": True, "comparator": True}


def test_checks_populated_on_failure():
    spec = {"delay_threshold_minutes": 5, "comparator": ">"}
    artifact = {"delay_threshold_minutes": 5, "comparator": ">="}
    result = score_artifact("RF-09", "codegen", artifact, spec)
    assert result.passed is False
    assert result.checks["comparator"] is False
    assert result.checks["delay_threshold_minutes"] is True
