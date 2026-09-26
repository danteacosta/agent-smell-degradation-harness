from __future__ import annotations

from eval.confirmatory_report import clustered_pr_auc_delta, finalize_h2_claim


def _three_cluster_inputs() -> tuple[list[dict[str, str]], list[float], list[float], list[int]]:
    rows = [
        {"project_id": "positive"},
        {"project_id": "negative-a"},
        {"project_id": "negative-b"},
    ]
    return rows, [0.9, 0.3, 0.2], [0.8, 0.4, 0.1], [1, 0, 0]


def test_cluster_bootstrap_excludes_single_class_draws_from_ci() -> None:
    rows, provenance, baseline, labels = _three_cluster_inputs()
    effect = clustered_pr_auc_delta(
        rows,
        provenance,
        baseline,
        labels,
        draws=100,
        seed=0,
    )

    bootstrap = effect["bootstrap"]
    assert bootstrap["degenerate_draws"] > 0
    assert bootstrap["effective_draws"] + bootstrap["degenerate_draws"] == 100
    assert bootstrap["effective_draws"] < bootstrap["draws"]
    assert bootstrap["degenerate_rate"] == bootstrap["degenerate_draws"] / 100
    assert effect["ci95"]["low"] is not None


def test_all_degenerate_draws_make_effect_descriptive_only() -> None:
    rows, provenance, baseline, labels = _three_cluster_inputs()
    effect = clustered_pr_auc_delta(
        rows,
        provenance,
        baseline,
        labels,
        draws=1,
        seed=2,
    )

    assert effect["bootstrap"]["effective_draws"] == 0
    assert effect["bootstrap"]["degenerate_draws"] == 1
    assert effect["bootstrap"]["valid_for_inference"] is False
    assert effect["ci95"] == {"low": None, "high": None}
    assert finalize_h2_claim(effect, margin=0.05)["claim"] == "descriptive_only"


def test_observed_degeneracy_above_frozen_limit_blocks_support() -> None:
    rows, provenance, baseline, labels = _three_cluster_inputs()
    effect = clustered_pr_auc_delta(
        rows,
        provenance,
        baseline,
        labels,
        draws=100,
        seed=0,
        max_degenerate_rate=0.05,
    )
    assert effect["bootstrap"]["degenerate_rate"] > 0.05
    assert effect["bootstrap"]["valid_for_inference"] is False

    # Exercise the fail-closed rule independently of the observed point
    # estimate and interval produced by this compact fixture.
    effect["delta_pr_auc"] = 0.20
    effect["ci95"] = {"low": 0.10, "high": 0.30}

    assert finalize_h2_claim(effect, margin=0.05)["claim"] == "not_supported"
