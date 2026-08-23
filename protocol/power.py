"""Pre-result H1 power and H2 precision simulations."""

from __future__ import annotations

import random
from typing import Any, Sequence


def _sign_flip_pvalue(values: list[float], *, rng: random.Random, max_exact_clusters: int = 16, monte_carlo_draws: int = 20_000) -> tuple[float, str]:
    observed = abs(sum(values) / len(values))
    if len(values) <= max_exact_clusters:
        exceed, total = 0, 1 << len(values)
        for mask in range(total):
            signed = sum(value if mask & (1 << index) else -value for index, value in enumerate(values))
            if abs(signed / len(values)) >= observed - 1e-12:
                exceed += 1
        return exceed / total, "exact"
    exceed = 0
    for _ in range(monte_carlo_draws):
        signed = sum(value if rng.random() < 0.5 else -value for value in values)
        if abs(signed / len(values)) >= observed - 1e-12:
            exceed += 1
    return (exceed + 1) / (monte_carlo_draws + 1), "monte_carlo"


def estimate_sign_flip_power(*, n_clusters: int = 12, standardized_effect: float = 0.5, alpha: float = 0.05, simulations: int = 2000, seed: int = 0, monte_carlo_draws: int = 20_000) -> dict[str, Any]:
    if n_clusters < 3 or simulations < 1 or not 0 < alpha < 1:
        raise ValueError("invalid power-analysis dimensions")
    if standardized_effect < 0:
        raise ValueError("standardized_effect must be non-negative")
    rng, rejected, method = random.Random(seed), 0, "exact"
    for _ in range(simulations):
        values = [rng.gauss(standardized_effect, 1.0) for _ in range(n_clusters)]
        pvalue, method = _sign_flip_pvalue(values, rng=rng, monte_carlo_draws=monte_carlo_draws)
        rejected += int(pvalue < alpha)
    return {"method": f"cluster_sign_flip_{method}-v2", "n_clusters": n_clusters, "standardized_effect": standardized_effect, "alpha": alpha, "simulations": simulations, "seed": seed, "monte_carlo_draws": monte_carlo_draws if method == "monte_carlo" else 0, "estimated_power": rejected / simulations}


def _average_precision(scores: Sequence[float], labels: Sequence[int]) -> float:
    positives = sum(labels)
    if positives == 0:
        raise ValueError("PR-AUC is undefined without positive labels")
    ranked = sorted(zip(scores, labels), key=lambda item: item[0], reverse=True)
    hits, total = 0, 0.0
    for rank, (_, label) in enumerate(ranked, start=1):
        if label:
            hits += 1
            total += hits / rank
    return total / positives


def _quantile(values: list[float], probability: float) -> float:
    ordered = sorted(values)
    index = min(len(ordered) - 1, max(0, round(probability * (len(ordered) - 1))))
    return ordered[index]


def _split_project_quotas(
    projects: int, fractions: tuple[float, float, float]
) -> dict[str, int]:
    names = ("train", "calibration", "test")
    quotas = {name: 1 for name in names}
    remaining = projects - len(names)
    while remaining:
        selected = max(
            names,
            key=lambda name: (
                projects * fractions[names.index(name)] - quotas[name],
                -names.index(name),
            ),
        )
        quotas[selected] += 1
        remaining -= 1
    return quotas


def simulate_h2_precision(
    *,
    intents: int,
    projects: int,
    prevalence: float = 0.5,
    baseline_effect: float = 0.45,
    provenance_increment: float = 0.20,
    practical_margin: float = 0.05,
    train_fraction: float = 0.5,
    calibration_fraction: float = 0.2,
    test_fraction: float = 0.3,
    simulations: int = 500,
    bootstrap_draws: int = 1000,
    seed: int = 0,
) -> dict[str, Any]:
    """Simulate the frozen-test H2 estimand with project-level resampling.

    Only projects assigned to the untouched test partition contribute to the
    ΔPR-AUC interval.  This mirrors confirmatory evaluation instead of using
    all projects and thereby overstating precision.
    """
    if intents < projects or projects < 3 or simulations < 1 or bootstrap_draws < 20:
        raise ValueError("invalid H2 precision simulation dimensions")
    if not 0 < prevalence < 1:
        raise ValueError("prevalence must be between zero and one")
    fractions = (train_fraction, calibration_fraction, test_fraction)
    if any(value <= 0 for value in fractions) or abs(sum(fractions) - 1.0) > 1e-9:
        raise ValueError("split fractions must be positive and sum to one")
    quotas = _split_project_quotas(projects, fractions)
    rng, widths, supported, degenerate = random.Random(seed), [], 0, 0
    for _ in range(simulations):
        project_order = list(range(projects))
        rng.shuffle(project_order)
        test_projects = set(project_order[-quotas["test"] :])
        project_shifts = [rng.gauss(0.0, 0.25) for _ in range(projects)]
        rows: list[tuple[int, int, float, float]] = []
        for intent in range(intents):
            project, label = intent % projects, int(rng.random() < prevalence)
            base = rng.gauss(project_shifts[project] + baseline_effect * label, 1.0)
            enriched = base + rng.gauss(provenance_increment * label, 0.45)
            if project in test_projects:
                rows.append((project, label, base, enriched))
        observed_labels = [row[1] for row in rows]
        if len(set(observed_labels)) < 2:
            degenerate += bootstrap_draws
            continue
        observed_delta = _average_precision(
            [row[3] for row in rows], observed_labels
        ) - _average_precision([row[2] for row in rows], observed_labels)
        deltas: list[float] = []
        for _draw in range(bootstrap_draws):
            project_ids = sorted(test_projects)
            selected = [rng.choice(project_ids) for _ in project_ids]
            sampled = [row for project in selected for row in rows if row[0] == project]
            labels = [row[1] for row in sampled]
            if not labels or len(set(labels)) < 2:
                degenerate += 1
                continue
            deltas.append(_average_precision([row[3] for row in sampled], labels) - _average_precision([row[2] for row in sampled], labels))
        if len(deltas) < max(20, bootstrap_draws // 2):
            continue
        lower, upper = _quantile(deltas, 0.025), _quantile(deltas, 0.975)
        widths.append(upper - lower)
        supported += int(observed_delta >= practical_margin and lower > 0)
    expected_test_intents = round(intents * quotas["test"] / projects)
    return {
        "method": "frozen_test_project_cluster_bootstrap_pr_auc_delta-v2",
        "evaluation_scope": "test_partition_only",
        "cluster_key": "project_id",
        "design": {
            "intents": intents,
            "projects": projects,
            "split_fractions": dict(zip(("train", "calibration", "test"), fractions)),
            "split_project_quotas": quotas,
            "expected_test_intents": expected_test_intents,
        },
        "assumptions": {
            "prevalence": prevalence,
            "baseline_effect": baseline_effect,
            "provenance_increment": provenance_increment,
            "practical_margin": practical_margin,
        },
        "simulations": simulations,
        "bootstrap_draws": bootstrap_draws,
        "seed": seed,
        "completed_simulations": len(widths),
        "estimated_margin_power": supported / len(widths) if widths else 0.0,
        "median_ci_width": _quantile(widths, 0.5) if widths else 1.0,
        "p90_ci_width": _quantile(widths, 0.9) if widths else 1.0,
        "degenerate_rate": degenerate / (simulations * bootstrap_draws),
    }


def sensitivity_table(effects: tuple[float, ...] = (0.25, 0.5, 0.75, 1.0), *, n_clusters: int = 12, alpha: float = 0.05, simulations: int = 2000, seed: int = 0) -> list[dict[str, Any]]:
    return [estimate_sign_flip_power(n_clusters=n_clusters, standardized_effect=effect, alpha=alpha, simulations=simulations, seed=seed + index) for index, effect in enumerate(effects)]


__all__ = ("estimate_sign_flip_power", "sensitivity_table", "simulate_h2_precision")
