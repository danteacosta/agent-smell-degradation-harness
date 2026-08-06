"""Deterministic primary H2 effect and claim report."""

from __future__ import annotations

import random
from collections import defaultdict
from collections.abc import Mapping, Sequence
from typing import Any


def average_precision(scores: Sequence[float], labels: Sequence[int]) -> float:
    positives = sum(labels)
    if positives == 0:
        return 0.0
    ranked = sorted(zip(scores, labels), key=lambda item: float(item[0]), reverse=True)
    hits = 0
    area = 0.0
    for rank, (_, label) in enumerate(ranked, start=1):
        if label:
            hits += 1
            area += hits / rank
    return area / positives


def shuffled_negative_control(scores: Sequence[float], labels: Sequence[int], *, seed: int = 0) -> dict[str, Any]:
    """Report a deterministic label-independent control for leakage checks."""
    shuffled = list(scores)
    random.Random(seed).shuffle(shuffled)
    return {"control": "shuffled_scores", "seed": seed, "pr_auc": average_precision(shuffled, labels), "n": len(labels)}


def ablation_pr_auc(scores_by_family: Mapping[str, Sequence[float]], labels: Sequence[int]) -> dict[str, float]:
    """Report each deployable family alone; no post-hoc family selection."""
    return {family: average_precision(scores, labels) for family, scores in sorted(scores_by_family.items())}


def clustered_pr_auc_delta(
    rows: Sequence[Mapping[str, Any]],
    provenance_scores: Sequence[float],
    baseline_scores: Sequence[float],
    labels: Sequence[int],
    *,
    cluster_key: str = "source_intent_id",
    draws: int = 2000,
    seed: int = 0,
) -> dict[str, Any]:
    if not (len(rows) == len(provenance_scores) == len(baseline_scores) == len(labels)):
        raise ValueError("H2 effect rows, scores, and labels must have equal length")
    groups: dict[str, list[int]] = defaultdict(list)
    for index, row in enumerate(rows):
        group = str(row.get(cluster_key, "")).strip()
        if not group:
            raise ValueError(f"H2 effect rows require {cluster_key}")
        groups[group].append(index)
    cluster_ids = sorted(groups)
    if len(cluster_ids) < 3:
        return {
            "provenance_pr_auc": average_precision(provenance_scores, labels),
            "baseline_pr_auc": average_precision(baseline_scores, labels),
            "delta_pr_auc": average_precision(provenance_scores, labels)
            - average_precision(baseline_scores, labels),
            "ci95": {"low": None, "high": None},
            "bootstrap": {"clusters": len(cluster_ids), "draws": 0, "degenerate_draws": 0},
            "claim": "descriptive_only",
        }
    observed_prov = average_precision(provenance_scores, labels)
    observed_base = average_precision(baseline_scores, labels)
    observed_delta = observed_prov - observed_base
    rng = random.Random(seed)
    bootstrap: list[float] = []
    degenerate = 0
    for _ in range(max(1, int(draws))):
        sampled_ids = [rng.choice(cluster_ids) for _ in cluster_ids]
        indices = [index for group in sampled_ids for index in groups[group]]
        sampled_labels = [labels[index] for index in indices]
        if len(set(sampled_labels)) < 2:
            degenerate += 1
        bootstrap.append(
            average_precision([provenance_scores[index] for index in indices], sampled_labels)
            - average_precision([baseline_scores[index] for index in indices], sampled_labels)
        )
    bootstrap.sort()
    low = bootstrap[max(0, int(0.025 * (len(bootstrap) - 1)))]
    high = bootstrap[min(len(bootstrap) - 1, int(0.975 * (len(bootstrap) - 1)))]
    return {
        "provenance_pr_auc": observed_prov,
        "baseline_pr_auc": observed_base,
        "delta_pr_auc": observed_delta,
        "ci95": {"low": low, "high": high},
        "bootstrap": {
            "clusters": len(cluster_ids),
            "draws": len(bootstrap),
            "degenerate_draws": degenerate,
            "seed": seed,
            "cluster_key": cluster_key,
        },
        "claim": "not_supported",
    }


def finalize_h2_claim(effect: dict[str, Any], *, margin: float = 0.05) -> dict[str, Any]:
    effect = dict(effect)
    effect["margin"] = margin
    low = effect.get("ci95", {}).get("low")
    effect["claim"] = (
        "supported"
        if effect.get("delta_pr_auc", 0.0) >= margin and low is not None and low > 0
        else effect.get("claim", "not_supported")
    )
    return effect


__all__ = ("ablation_pr_auc", "average_precision", "clustered_pr_auc_delta", "finalize_h2_claim", "shuffled_negative_control")
