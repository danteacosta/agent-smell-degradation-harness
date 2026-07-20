from __future__ import annotations

import random
from typing import Any


def paired_proportion_diff(clean_pass_rate: float, smelly_pass_rate: float) -> float:
    """Difference in pass rates: clean minus smelly."""
    return clean_pass_rate - smelly_pass_rate


def bootstrap_ci(
    values: list[float],
    n_boot: int = 200,
    seed: int = 0,
) -> tuple[float, float]:
    """Simple percentile bootstrap CI for the mean of values."""
    if not values:
        return (0.0, 0.0)

    rng = random.Random(seed)
    n = len(values)
    boot_means = sorted(
        sum(rng.choice(values) for _ in range(n)) / n for _ in range(n_boot)
    )
    low_idx = max(0, int(0.025 * (n_boot - 1)))
    high_idx = min(n_boot - 1, int(0.975 * (n_boot - 1)))
    return (boot_means[low_idx], boot_means[high_idx])


def export_paired_stats(
    clean_pass_rate: float,
    smelly_pass_rate: float,
    pair_outcomes: list[float] | None = None,
) -> dict[str, Any]:
    """Build paired-stats dict for analysis reports."""
    diff = paired_proportion_diff(clean_pass_rate, smelly_pass_rate)
    report: dict[str, Any] = {
        "clean_pass_rate": clean_pass_rate,
        "smelly_pass_rate": smelly_pass_rate,
        "proportion_diff": diff,
    }
    if pair_outcomes is not None:
        low, high = bootstrap_ci(pair_outcomes)
        report["proportion_diff_ci"] = {"low": low, "high": high}
    return report


def pair_degradation_outcomes(episodes: list[dict[str, Any]]) -> list[float]:
    """Per intent×family pair: 1.0 if clean passes and smelly fails, else 0.0."""
    pair_results: dict[tuple[str, str], dict[str, bool]] = {}
    for ep in episodes:
        key = (ep["intent_id"], ep["task_family"])
        pair_results.setdefault(key, {})[ep["variant"]] = ep["oracle_passed"]

    outcomes: list[float] = []
    for results in pair_results.values():
        degraded = bool(results.get("clean")) and not results.get("smelly")
        outcomes.append(1.0 if degraded else 0.0)
    return outcomes
