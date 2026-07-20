from __future__ import annotations

from typing import Any


def compute_paired_degradation_rate(
    pair_results: dict[tuple[str, str], dict[str, bool]],
) -> float:
    """Fraction of intent×family pairs where smelly fails AND clean passes."""
    if not pair_results:
        return 0.0
    degraded = sum(
        1
        for results in pair_results.values()
        if results.get("clean") and not results.get("smelly")
    )
    return degraded / len(pair_results)


def compute_oracle_pass_rate(episodes: list[dict[str, Any]], variant: str) -> float:
    subset = [ep for ep in episodes if ep["variant"] == variant]
    if not subset:
        return 0.0
    passed = sum(1 for ep in subset if ep["oracle_passed"])
    return passed / len(subset)


def compute_semantic_provenance_coverage(episodes: list[dict[str, Any]]) -> float:
    if not episodes:
        return 0.0
    covered = sum(1 for ep in episodes if ep["has_semantic_provenance"])
    return covered / len(episodes)


def compute_taxonomy_modes(episodes: list[dict[str, Any]]) -> dict[str, int]:
    counts: dict[str, int] = {}
    for ep in episodes:
        mode = ep["degradation_mode"]
        counts[mode] = counts.get(mode, 0) + 1
    return counts


def aggregate_metrics(episodes: list[dict[str, Any]]) -> dict[str, Any]:
    pair_results: dict[tuple[str, str], dict[str, bool]] = {}
    for ep in episodes:
        key = (ep["intent_id"], ep["task_family"])
        pair_results.setdefault(key, {})[ep["variant"]] = ep["oracle_passed"]

    paired_rate = compute_paired_degradation_rate(pair_results)
    task_families = sorted({ep["task_family"] for ep in episodes})

    return {
        "paired_degradation_rate": paired_rate,
        "oracle_pass_rate_clean": compute_oracle_pass_rate(episodes, "clean"),
        "oracle_pass_rate_smelly": compute_oracle_pass_rate(episodes, "smelly"),
        "semantic_provenance_coverage": compute_semantic_provenance_coverage(episodes),
        "degradation_detected": paired_rate > 0,
        "episode_count": len(episodes),
        "task_families_exercised": task_families,
        "taxonomy_modes": compute_taxonomy_modes(episodes),
    }
