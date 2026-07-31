from __future__ import annotations

import random
from collections.abc import Mapping, Sequence
from typing import Any


def paired_proportion_diff(clean_pass_rate: float, smelly_pass_rate: float) -> float:
    """Difference in pass rates: clean minus smelly."""
    return clean_pass_rate - smelly_pass_rate


def ordinal_paired_delta(
    clean_severity: Sequence[float],
    defective_severity: Sequence[float],
) -> float:
    """Mean paired ordinal severity delta (clean minus defective).

    Replications are repeated measures of the same intent; callers should
    provide pairs in the same intent/replication order and cluster the result
    for uncertainty estimation with :func:`clustered_bootstrap_ci`.
    """

    if len(clean_severity) != len(defective_severity):
        raise ValueError("paired ordinal samples must have equal lengths")
    if not clean_severity:
        return 0.0
    return sum(float(clean) - float(defective) for clean, defective in zip(clean_severity, defective_severity)) / len(clean_severity)


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


def _cluster_means(values: Mapping[str, Sequence[float]]) -> list[float]:
    means: list[float] = []
    for cluster_id in sorted(values):
        cluster = [float(value) for value in values[cluster_id]]
        if cluster:
            means.append(sum(cluster) / len(cluster))
    return means


def clustered_bootstrap_ci(
    values: Mapping[str, Sequence[float]],
    n_boot: int = 2000,
    seed: int = 0,
) -> tuple[float, float]:
    """Bootstrap a mean while resampling intent clusters, not episodes.

    Each intent contributes one cluster mean per draw, so five replications of
    one intent cannot masquerade as five independent observations.
    """

    clusters = _cluster_means(values)
    if not clusters:
        return (0.0, 0.0)
    draws = max(1, int(n_boot))
    rng = random.Random(seed)
    boot_means = sorted(
        sum(rng.choice(clusters) for _ in clusters) / len(clusters)
        for _ in range(draws)
    )
    low_idx = max(0, int(0.025 * (draws - 1)))
    high_idx = min(draws - 1, int(0.975 * (draws - 1)))
    return (boot_means[low_idx], boot_means[high_idx])


def paired_permutation_pvalue(
    deltas: Sequence[float] | Mapping[str, Sequence[float]],
    *,
    n_perm: int = 5000,
    seed: int = 0,
) -> float:
    """Two-sided paired randomization p-value by deterministic sign flips.

    A mapping preserves the intent clusters in the input and is flattened in
    stable key order.  The finite-sample +1 correction prevents an impossible
    zero p-value while retaining exact ``1.0`` for an all-zero effect.
    """

    if isinstance(deltas, Mapping):
        # Reduce repeated measurements to one intent-level contrast before
        # randomization.  Otherwise an intent with five replications would
        # receive five times the weight of an intent with one replication.
        ordered = [
            sum(float(value) for value in deltas[key]) / len(deltas[key])
            for key in sorted(deltas)
            if deltas[key]
        ]
    else:
        ordered = [float(value) for value in deltas]
    if not ordered:
        return 1.0
    observed = abs(sum(ordered) / len(ordered))
    if observed == 0.0:
        return 1.0
    rng = random.Random(seed)
    draws = max(1, int(n_perm))
    extreme = 0
    for _ in range(draws):
        randomized = sum(value if rng.getrandbits(1) else -value for value in ordered) / len(ordered)
        if abs(randomized) >= observed:
            extreme += 1
    return (extreme + 1) / (draws + 1)


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
