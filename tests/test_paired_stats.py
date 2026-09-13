from protocol.paired_stats import (
    bootstrap_ci,
    export_paired_stats,
    pair_degradation_outcomes,
    paired_proportion_diff,
)

import pytest


def test_paired_proportion_diff():
    assert paired_proportion_diff(1.0, 0.5) == 0.5
    assert paired_proportion_diff(0.8, 0.8) == 0.0
    assert paired_proportion_diff(0.0, 1.0) == -1.0


def test_bootstrap_ci_reproducible():
    values = [1.0, 0.0, 1.0, 0.0, 1.0]
    low, high = bootstrap_ci(values, n_boot=200, seed=0)
    low2, high2 = bootstrap_ci(values, n_boot=200, seed=0)
    assert (low, high) == (low2, high2)
    assert low <= sum(values) / len(values) <= high


def test_bootstrap_ci_empty():
    assert bootstrap_ci([]) == (0.0, 0.0)


def test_export_paired_stats_without_outcomes():
    report = export_paired_stats(1.0, 0.6)
    assert report["proportion_diff"] == 0.4
    assert "proportion_diff_ci" not in report


def test_export_paired_stats_with_outcomes():
    report = export_paired_stats(1.0, 0.5, pair_outcomes=[1.0, 0.0, 1.0, 0.0])
    assert report["proportion_diff"] == 0.5
    assert "proportion_diff_ci" in report
    ci = report["proportion_diff_ci"]
    assert ci["low"] <= 0.5 <= ci["high"]


def test_pair_degradation_outcomes():
    episodes = [
        {"intent_id": "a", "task_family": "codegen", "variant": "clean", "oracle_passed": True},
        {"intent_id": "a", "task_family": "codegen", "variant": "smelly", "oracle_passed": False},
        {"intent_id": "b", "task_family": "codegen", "variant": "clean", "oracle_passed": True},
        {"intent_id": "b", "task_family": "codegen", "variant": "smelly", "oracle_passed": True},
    ]
    assert pair_degradation_outcomes(episodes) == [1.0, 0.0]


def _identified_pair(replication=0, run="run", clean=True, smelly=False):
    return [{"intent_id": "a", "task_family": "codegen", "run_id": run,
             "replication_id": replication, "variant": v, "oracle_passed": result}
            for v, result in (("clean", clean), ("smelly", smelly))]


def test_pairing_preserves_runs_and_repetitions():
    rows = _identified_pair() + _identified_pair(1, smelly=True) + _identified_pair(run="other")
    assert pair_degradation_outcomes(rows) == [1.0, 0.0, 1.0]


@pytest.mark.parametrize("fault", ["duplicate", "missing", "mixed_identity", "non_boolean", "unknown_variant", "configuration", "provider", "runtime_error"])
def test_legacy_pairing_rejects_ambiguous_or_incomplete_records(fault):
    rows = _identified_pair()
    if fault == "duplicate":
        rows.append(rows[0].copy())
    elif fault == "missing":
        rows.pop()
    elif fault == "mixed_identity":
        del rows[0]["replication_id"]
    elif fault == "non_boolean":
        rows[0]["oracle_passed"] = "false"
    elif fault == "unknown_variant":
        rows[0]["variant"] = "other"
    elif fault == "configuration":
        rows[0]["configuration_id"], rows[1]["configuration_id"] = "A", "B"
    elif fault == "provider":
        rows[0]["provider_meta"] = {"provider": "A", "model": "model"}
        rows[1]["provider_meta"] = {"provider": "B", "model": "model"}
    else:
        rows[1]["behavior_status"] = "runtime_error"
    with pytest.raises(ValueError):
        pair_degradation_outcomes(rows)
