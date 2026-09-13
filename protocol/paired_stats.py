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


_PAIR_DIMENSIONS = (
    "experiment_id", "run_id", "replication_id", "project_id", "workload_id",
    "configuration_id", "policy",
)


def group_binary_pairs(episodes: Sequence[Mapping[str, Any]]) -> dict[tuple, dict[str, bool]]:
    """Strict descriptive pairing for legacy binary reports, not H1/H2 inference.

    Old records may omit identity dimensions uniformly. Duplicate identities or
    missing arms cannot be recovered by guessing and are rejected. The planned
    behavioral analyzer is the appropriate path for incomplete observations.
    """
    groups: dict[tuple, dict[str, bool]] = {}
    identity_shape = None
    for episode in episodes:
        shape = tuple(field in episode for field in _PAIR_DIMENSIONS) + ("provider_meta" in episode,)
        if identity_shape is not None and shape != identity_shape:
            raise ValueError("mixed legacy/identified episode records")
        identity_shape = shape
        for field in ("intent_id", "task_family"):
            if not isinstance(episode.get(field), str) or not episode[field]:
                raise ValueError("intent_id and task_family must be nonempty strings")
        dimensions = []
        for field in _PAIR_DIMENSIONS:
            value = episode.get(field)
            if field in episode and (type(value) not in (str, int) or (not value and field != "project_id" and value != 0)):
                raise ValueError("invalid episode identity dimension")
            # Type tags prevent integer/string replication IDs from collapsing.
            dimensions.append((type(value).__name__, value))
        provider = episode.get("provider_meta", {})
        if not isinstance(provider, Mapping):
            raise ValueError("provider_meta must be an object")
        provider_key = tuple(provider.get(f) for f in ("provider", "model"))
        if any(v is not None and not isinstance(v, str) for v in provider_key):
            raise ValueError("invalid provider/model identity")
        variant, passed = episode.get("variant"), episode.get("oracle_passed")
        if variant not in {"clean", "smelly"} or type(passed) is not bool:
            raise ValueError("legacy pairing requires clean/smelly and Boolean outcomes")
        if episode.get("behavior_status", "passed") not in {"passed", "failed"}:
            raise ValueError("incomplete behavior requires the planned diagnostic analyzer")
        key = (episode["intent_id"], episode["task_family"], *dimensions, *provider_key)
        pair = groups.setdefault(key, {})
        if variant in pair:
            raise ValueError("duplicate episode identity; provide distinct replication IDs")
        pair[variant] = passed
    if any(set(pair) != {"clean", "smelly"} for pair in groups.values()):
        raise ValueError("missing paired variant; use the planned diagnostic analyzer")
    return groups


def pair_degradation_outcomes(episodes: list[dict[str, Any]]) -> list[float]:
    """Per complete identified pair: 1 when clean passes and smelly fails."""
    pair_results = group_binary_pairs(episodes)

    outcomes: list[float] = []
    for results in pair_results.values():
        degraded = results["clean"] and not results["smelly"]
        outcomes.append(1.0 if degraded else 0.0)
    return outcomes
