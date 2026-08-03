from __future__ import annotations

import pytest

from eval.h2_detection import evaluate_confirmatory


def _episodes() -> list[dict[str, object]]:
    rows: list[dict[str, object]] = []
    for index in range(9):
        for variant in ("clean", "smelly"):
            rows.append(
                {
                    "intent_id": f"I-{index}",
                    "source_intent_id": f"I-{index}",
                    "project_id": f"P-{index % 3}",
                    "variant": variant,
                    "replication_id": 0,
                    "oracle_passed": variant == "clean" or index % 2 == 0,
                    "h2_scores": {
                        "static_smell": float(index % 2),
                        "operational": float(index) / 10,
                        "provenance_semantic": float(index) / 10 + (0.4 if variant == "smelly" else 0),
                    },
                }
            )
    return rows


def test_confirmatory_h2_selects_on_train_calibrates_on_calibration_and_evaluates_holdout():
    report = evaluate_confirmatory(_episodes(), seed=3)
    assert report["protocol"] == "H2-confirmatory-v1"
    assert report["model_selection"]["fit_split"] == "train"
    assert report["calibration"]["fit_split"] == "calibration"
    assert report["held_out"]["split"] == "test"
    assert report["held_out"]["n"] > 0
    assert 0 <= report["held_out"]["pr_auc"] <= 1
    assert 0 <= report["held_out"]["false_alert_rate"] <= 1
    assert 0 <= report["held_out"]["warning_coverage"] <= 1
    assert report["split"]["provenance"]["seed"] == 3


def test_confirmatory_h2_fails_closed_without_project_ids():
    episodes = _episodes()
    for row in episodes:
        row.pop("project_id")
    with pytest.raises(ValueError, match="project_id"):
        evaluate_confirmatory(episodes)
