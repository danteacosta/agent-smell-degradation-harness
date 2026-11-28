from __future__ import annotations

import pytest

from eval.confirmatory_report import clustered_pr_auc_delta, finalize_h2_claim


def _three_cluster_inputs() -> tuple[list[dict[str, str]], list[float], list[float], list[int]]:
    rows = [
        {"project_id": "positive"},
        {"project_id": "negative-a"},
        {"project_id": "negative-b"},
    ]
    return rows, [0.9, 0.3, 0.2], [0.8, 0.4, 0.1], [1, 0, 0]


def test_cluster_bootstrap_with_single_class_draws_is_descriptive_only() -> None:
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
    assert bootstrap["valid_for_inference"] is False
    assert effect["ci95"] == {"low": None, "high": None}
    assert effect["conditional_percentile_interval"]["low"] is not None
    assert finalize_h2_claim(effect, margin=0.05)["claim"] == "descriptive_only"


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


def test_possible_degenerate_resample_is_invalid_even_when_draw_does_not_observe_it() -> None:
    rows, provenance, baseline, labels = _three_cluster_inputs()
    effect = clustered_pr_auc_delta(
        rows,
        provenance,
        baseline,
        labels,
        draws=1,
        seed=1,
    )

    assert effect["bootstrap"]["degenerate_draws"] == 0
    assert effect["bootstrap"]["degenerate_support_possible"] is True
    assert effect["bootstrap"]["valid_for_inference"] is False
    assert effect["ci95"] == {"low": None, "high": None}


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

    assert finalize_h2_claim(effect, margin=0.05)["claim"] == "descriptive_only"


def test_degeneracy_within_design_limit_remains_descriptive_only() -> None:
    rows, provenance, baseline, labels = _three_cluster_inputs()
    effect = clustered_pr_auc_delta(
        rows,
        provenance,
        baseline,
        labels,
        draws=100,
        seed=0,
        max_degenerate_rate=1.0,
    )

    assert effect["bootstrap"]["degenerate_draws"] > 0
    assert effect["bootstrap"]["within_frozen_degeneracy_limit"] is True
    assert effect["bootstrap"]["valid_for_inference"] is False
    assert effect["ci95"] == {"low": None, "high": None}
    assert finalize_h2_claim(effect, margin=0.05)["claim"] == "descriptive_only"


def test_invalid_bootstrap_overrides_stale_supported_claim() -> None:
    rows, provenance, baseline, labels = _three_cluster_inputs()
    effect = clustered_pr_auc_delta(rows, provenance, baseline, labels, draws=1, seed=2)
    effect["claim"] = "supported"
    effect["delta_pr_auc"] = 0.20
    effect["ci95"] = {"low": 0.10, "high": 0.30}

    assert finalize_h2_claim(effect, margin=0.05)["claim"] == "descriptive_only"


def test_small_cluster_fallback_preserves_report_schema() -> None:
    effect = clustered_pr_auc_delta(
        [{"project_id": "a"}, {"project_id": "b"}],
        [0.9, 0.2],
        [0.8, 0.1],
        [1, 0],
        seed=11,
        max_degenerate_rate=0.05,
    )

    assert effect["conditional_percentile_interval"] == {"low": None, "high": None}
    assert effect["bootstrap"]["within_frozen_degeneracy_limit"] is None
    assert effect["bootstrap"]["seed"] == 11
    assert effect["bootstrap"]["cluster_key"] == "project_id"
    assert effect["leave_one_cluster_out"] == {
        "draws": 0,
        "min": None,
        "max": None,
        "max_abs_shift_from_observed": None,
    }


@pytest.mark.parametrize('bootstrap', [None, {}, {'valid_for_inference': None},
                                      {'valid_for_inference': 1},
                                      {'valid_for_inference': 'true'},
                                      {'valid_for_inference': False}])
def test_missing_or_nonboolean_bootstrap_validity_cannot_support_h2(bootstrap):
    effect={'delta_pr_auc':.20, 'ci95':{'low':.10,'high':.30},
            'bootstrap':bootstrap, 'claim':'supported'}
    assert finalize_h2_claim(effect)['claim'] == 'descriptive_only'
    assert effect['claim'] == 'supported'  # Do not rewrite the input evidence.


def test_absent_bootstrap_cannot_default_to_supported_h2():
    effect={'delta_pr_auc':.20, 'ci95':{'low':.10,'high':.30}}
    assert finalize_h2_claim(effect)['claim'] == 'descriptive_only'


def test_explicit_valid_grouped_report_preserves_h2_margin_rule():
    rows=[{'project_id':project} for project in ('a','b','c') for _ in (0,1)]
    labels=[0,1]*3
    effect=clustered_pr_auc_delta(rows,[.1,.9]*3,[.5]*6,labels,draws=100)
    assert effect['bootstrap']['valid_for_inference'] is True
    assert finalize_h2_claim(effect)['claim'] == 'supported'
    assert finalize_h2_claim(effect,margin=.6)['claim'] == 'not_supported'


def test_length_matched_control_removes_pure_length_signal():
    from eval.length_control import length_matched_control

    # Longer episodes are more often positive, so length alone ranks well,
    # but within matched-length pairs the length-driven score is uninformative.
    lengths = [5, 5, 6, 6, 10, 10, 11, 11, 20, 20, 21, 21]
    labels = [0, 1, 0, 1, 0, 1, 0, 1, 0, 1, 0, 1]
    scores = [float(n) for n in lengths]
    result = length_matched_control(scores, labels, lengths, tolerance=0, min_pairs=6)
    assert result["n_pairs"] == 6
    assert result["status"] == "ok"
    assert result["matched_auroc"] == 0.5
    assert result["claim"] == "descriptive_only"


def test_length_matched_control_reports_insufficient_pairs_and_rejects_bad_input():
    import pytest

    from eval.length_control import length_matched_control

    result = length_matched_control([1.0, 2.0], [0, 1], [3, 40], tolerance=3)
    assert result["n_pairs"] == 0 and result["matched_auroc"] is None
    assert result["status"] == "insufficient_pairs"
    with pytest.raises(ValueError):
        length_matched_control([1.0], [0, 1], [1])
    with pytest.raises(ValueError):
        length_matched_control([1.0], [2], [1])
