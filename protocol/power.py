"""Pre-result power calculations for the cluster-level H1 sign-flip test."""

from __future__ import annotations

import random
from typing import Any


def _sign_flip_pvalue(values: list[float]) -> float:
    observed = abs(sum(values) / len(values))
    exceed = 0
    total = 1 << len(values)
    for mask in range(total):
        signed = sum(value if mask & (1 << index) else -value for index, value in enumerate(values))
        if abs(signed / len(values)) >= observed - 1e-12:
            exceed += 1
    return exceed / total


def estimate_sign_flip_power(
    *,
    n_clusters: int = 12,
    standardized_effect: float = 0.5,
    alpha: float = 0.05,
    simulations: int = 2000,
    seed: int = 0,
) -> dict[str, Any]:
    """Estimate power before outcomes using a fixed cluster-level simulation.

    ``standardized_effect`` is the planned mean paired delta divided by the
    cluster-level standard deviation. Replications are deliberately absent:
    they do not increase the independent cluster count.
    """

    if n_clusters < 3 or simulations < 1 or not 0 < alpha < 1:
        raise ValueError("invalid power-analysis dimensions")
    if standardized_effect < 0:
        raise ValueError("standardized_effect must be non-negative")
    rng = random.Random(seed)
    rejected = 0
    for _ in range(simulations):
        values = [rng.gauss(standardized_effect, 1.0) for _ in range(n_clusters)]
        if _sign_flip_pvalue(values) < alpha:
            rejected += 1
    return {
        "method": "cluster_sign_flip_monte_carlo-v1",
        "n_clusters": n_clusters,
        "standardized_effect": standardized_effect,
        "alpha": alpha,
        "simulations": simulations,
        "seed": seed,
        "estimated_power": rejected / simulations,
    }


def sensitivity_table(
    effects: tuple[float, ...] = (0.25, 0.5, 0.75, 1.0),
    *,
    n_clusters: int = 12,
    alpha: float = 0.05,
    simulations: int = 2000,
    seed: int = 0,
) -> list[dict[str, Any]]:
    return [
        estimate_sign_flip_power(
            n_clusters=n_clusters,
            standardized_effect=effect,
            alpha=alpha,
            simulations=simulations,
            seed=seed + index,
        )
        for index, effect in enumerate(effects)
    ]


__all__ = ("estimate_sign_flip_power", "sensitivity_table")
