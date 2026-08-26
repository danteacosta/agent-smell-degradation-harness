"""Small, dependency-free uncertainty helpers for discovery metrics."""

from __future__ import annotations

from statistics import NormalDist
from typing import Any


def wilson_interval(
    successes: int,
    trials: int,
    *,
    confidence: float = 0.95,
) -> dict[str, Any]:
    """Return a JSON-ready two-sided Wilson interval for a binomial rate."""

    if isinstance(successes, bool) or isinstance(trials, bool):
        raise ValueError("successes and trials must be integers")
    if successes < 0 or trials < 0 or successes > trials:
        raise ValueError("successes must be between zero and trials")
    if not 0.0 < confidence < 1.0:
        raise ValueError("confidence must be between zero and one")

    base: dict[str, Any] = {
        "estimate": successes / trials if trials else None,
        "successes": successes,
        "trials": trials,
        "confidence": confidence,
        "method": "wilson",
        "status": "ok" if trials else "inconclusive",
        "lower": None,
        "upper": None,
    }
    if not trials:
        return base

    z = NormalDist().inv_cdf(0.5 + confidence / 2.0)
    p = successes / trials
    z_squared = z * z
    denominator = 1.0 + z_squared / trials
    center = (p + z_squared / (2.0 * trials)) / denominator
    margin = (
        z
        * ((p * (1.0 - p) / trials) + z_squared / (4.0 * trials * trials)) ** 0.5
        / denominator
    )
    base["lower"] = max(0.0, center - margin)
    base["upper"] = min(1.0, center + margin)
    return base
