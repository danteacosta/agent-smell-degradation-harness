from protocol.paired_stats import (
    bootstrap_ci,
    export_paired_stats,
    pair_degradation_outcomes,
    paired_proportion_diff,
)


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
