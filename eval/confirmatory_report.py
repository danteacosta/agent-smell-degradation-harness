"""Deterministic primary H2 effect and claim report."""

from __future__ import annotations

import random
from collections import defaultdict
from collections.abc import Mapping, Sequence
from typing import Any

from protocol.metrics import average_precision


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
    cluster_key: str = "project_id",
    draws: int = 2000,
    seed: int = 0,
    max_degenerate_rate: float | None = None,
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
            "conditional_percentile_interval": {"low": None, "high": None},
            "bootstrap": {
                "clusters": len(cluster_ids),
                "draws": 0,
                "effective_draws": 0,
                "degenerate_draws": 0,
                "degenerate_rate": None,
                "max_degenerate_rate": max_degenerate_rate,
                "within_frozen_degeneracy_limit": None,
                "degenerate_support_possible": None,
                "valid_for_inference": False,
                "seed": seed,
                "cluster_key": cluster_key,
            },
            "leave_one_cluster_out": {
                "draws": 0,
                "min": None,
                "max": None,
                "max_abs_shift_from_observed": None,
            },
            "claim": "descriptive_only",
        }
    observed_prov = average_precision(provenance_scores, labels)
    observed_base = average_precision(baseline_scores, labels)
    observed_delta = observed_prov - observed_base
    degenerate_support_possible = any(
        len({labels[index] for index in groups[cluster_id]}) < 2
        for cluster_id in cluster_ids
    )
    rng = random.Random(seed)
    bootstrap: list[float] = []
    degenerate = 0
    requested_draws = max(1, int(draws))
    for _ in range(requested_draws):
        sampled_ids = [rng.choice(cluster_ids) for _ in cluster_ids]
        indices = [index for group in sampled_ids for index in groups[group]]
        sampled_labels = [labels[index] for index in indices]
        if len(set(sampled_labels)) < 2:
            degenerate += 1
            continue
        bootstrap.append(
            average_precision([provenance_scores[index] for index in indices], sampled_labels)
            - average_precision([baseline_scores[index] for index in indices], sampled_labels)
        )
    bootstrap.sort()
    low = (
        bootstrap[max(0, int(0.025 * (len(bootstrap) - 1)))]
        if bootstrap
        else None
    )
    high = (
        bootstrap[min(len(bootstrap) - 1, int(0.975 * (len(bootstrap) - 1)))]
        if bootstrap
        else None
    )
    degenerate_rate = degenerate / requested_draws
    within_frozen_degeneracy_limit = (
        max_degenerate_rate is None or degenerate_rate <= max_degenerate_rate
    )
    # The percentile endpoints above are conditional on an estimable resample.
    # Until coverage for that conditional procedure is established, the
    # possibility of a one-class resample makes the result descriptive. This
    # support check is deterministic and cannot change with seed or draw count.
    valid_for_inference = bool(bootstrap) and not degenerate_support_possible
    conditional_percentile_interval = {"low": low, "high": high}
    inferential_interval = (
        conditional_percentile_interval
        if valid_for_inference
        else {"low": None, "high": None}
    )
    leave_one_cluster_out = []
    if len(cluster_ids) > 3:
        for omitted in cluster_ids:
            indices = [
                index
                for cluster_id in cluster_ids
                if cluster_id != omitted
                for index in groups[cluster_id]
            ]
            omitted_labels = [labels[index] for index in indices]
            if len(set(omitted_labels)) < 2:
                continue
            leave_one_cluster_out.append(
                average_precision(
                    [provenance_scores[index] for index in indices], omitted_labels
                )
                - average_precision(
                    [baseline_scores[index] for index in indices], omitted_labels
                )
            )
    return {
        "provenance_pr_auc": observed_prov,
        "baseline_pr_auc": observed_base,
        "delta_pr_auc": observed_delta,
        "ci95": inferential_interval,
        "conditional_percentile_interval": conditional_percentile_interval,
        "bootstrap": {
            "clusters": len(cluster_ids),
            "draws": requested_draws,
            "effective_draws": len(bootstrap),
            "degenerate_draws": degenerate,
            "degenerate_rate": degenerate_rate,
            "max_degenerate_rate": max_degenerate_rate,
            "within_frozen_degeneracy_limit": within_frozen_degeneracy_limit,
            "degenerate_support_possible": degenerate_support_possible,
            "valid_for_inference": valid_for_inference,
            "seed": seed,
            "cluster_key": cluster_key,
        },
        "leave_one_cluster_out": {
            "draws": len(leave_one_cluster_out),
            "min": min(leave_one_cluster_out) if leave_one_cluster_out else None,
            "max": max(leave_one_cluster_out) if leave_one_cluster_out else None,
            "max_abs_shift_from_observed": (
                max(abs(value - observed_delta) for value in leave_one_cluster_out)
                if leave_one_cluster_out
                else None
            ),
        },
        "claim": "not_supported" if valid_for_inference else "descriptive_only",
    }


def finalize_h2_claim(effect: dict[str, Any], *, margin: float = 0.05) -> dict[str, Any]:
    effect = dict(effect)
    effect["margin"] = margin
    low = effect.get("ci95", {}).get("low")
    bootstrap_valid = effect.get("bootstrap", {}).get("valid_for_inference", True)
    if not bootstrap_valid:
        effect["claim"] = "descriptive_only"
    elif (
        effect.get("delta_pr_auc", 0.0) >= margin
        and low is not None
        and low > 0
    ):
        effect["claim"] = "supported"
    else:
        effect["claim"] = "not_supported"
    return effect


__all__ = ("ablation_pr_auc", "average_precision", "clustered_pr_auc_delta", "finalize_h2_claim", "shuffled_negative_control")
