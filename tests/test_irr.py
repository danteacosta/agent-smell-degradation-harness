from __future__ import annotations

from pathlib import Path

import pytest

from protocol.irr import cohens_kappa, compare_annotations, load_annotations, percent_agreement


ROOT = Path(__file__).resolve().parents[1]
ANNOTATION_DIR = ROOT / "data" / "annotation"


def test_load_annotations_reads_csv():
    rows = load_annotations(ANNOTATION_DIR / "example_ann_a.csv")
    assert len(rows) == 6
    assert rows[0]["episode_id"] == "RF-09_codegen_clean"


def test_percent_agreement_perfect():
    assert percent_agreement(["a", "b"], ["a", "b"]) == 1.0


def test_cohens_kappa_perfect():
    assert cohens_kappa(["a", "a", "b"], ["a", "a", "b"]) == 1.0


def test_compare_example_annotations():
    result = compare_annotations(
        ANNOTATION_DIR / "example_ann_a.csv",
        ANNOTATION_DIR / "example_ann_b.csv",
    )
    assert result["n_items"] == 6
    assert 0.0 <= result["mode_kappa"] <= 1.0
    assert result["mode_agreement"] == 5 / 6
    assert result["severity_agreement"] == 5 / 6


def test_load_annotations_missing_column(tmp_path):
    bad = tmp_path / "bad.csv"
    bad.write_text("episode_id,mode\nx,ok\n", encoding="utf-8")
    with pytest.raises(ValueError, match="severity"):
        load_annotations(bad)


# Krippendorff (2011), section C. The last unit is a singleton.
PUBLISHED_MISSING = [
    [1, 2, 3, 3, 2, 1, 4, 1, 2, None, None, None],
    [1, 2, 3, 3, 2, 2, 4, 1, 2, 5, None, 3],
    [None, 3, 3, 3, 2, 3, 4, 2, 2, 5, 1, None],
    [1, 2, 3, 3, 2, 4, 4, 1, 2, 5, 1, None],
]


def test_alpha_matches_published_missing_data_coincidences():
    from protocol.irr import krippendorff_alpha

    assert krippendorff_alpha(PUBLISHED_MISSING) == pytest.approx(1 - 312 / 1216)
    # Published margins: 9,13,10,5,3. Midpoints: 4.5,15.5,27,34.5,38.5.
    # Upper triangle O: 4/3,1/3,1/3,0,4/3,1/3,0,1/3,0,0.
    # Sum O*d²=1891/2; sum n_c*n_k*d²=199740; alpha=108577/133160.
    assert krippendorff_alpha(PUBLISHED_MISSING, level_of_measurement="ordinal") == pytest.approx(108577 / 133160)


def test_alpha_ignores_singletons_and_unused_ordinal_ranks():
    from protocol.irr import krippendorff_alpha

    paired = [[0, 1, 2], [0, 2, 2]]
    singletons = [paired[0] + [99], paired[1] + [None]]
    for level in ("nominal", "ordinal"):
        assert krippendorff_alpha(singletons, level_of_measurement=level) == pytest.approx(
            krippendorff_alpha(paired, level_of_measurement=level)
        )
    assert krippendorff_alpha(paired, level_of_measurement="ordinal", ordinal_order=[0, "unused", 1, 2]) == pytest.approx(
        krippendorff_alpha(paired, level_of_measurement="ordinal", ordinal_order=[0, 1, 2])
    )


@pytest.mark.parametrize("data", [[], [[], []], [[None], [None]], [[1, None], [None, 2]], [[1, 1], [1, 1]]])
def test_alpha_is_undefined_without_pairable_variation(data):
    from protocol.irr import krippendorff_alpha

    with pytest.raises(ValueError, match="undefined"):
        krippendorff_alpha(data)


@pytest.mark.parametrize("alpha", [float("nan"), float("inf"), -float("inf"), 1.1, -1.1])
def test_decision_rejects_invalid_estimates(alpha):
    from protocol.irr import irr_decision

    with pytest.raises(ValueError, match="alpha"):
        irr_decision(alpha)


def test_bootstrap_reports_degenerate_draws_without_replacing_them():
    from protocol.irr import bootstrap_krippendorff_alpha

    # Only draws with both distinct, unanimously coded units are estimable.
    result = bootstrap_krippendorff_alpha([[0, 1], [0, 1]], n_bootstrap=100, seed=7)
    assert result["n_bootstrap"] == 100
    assert 0 < result["n_undefined"] < 100
    assert result["n_valid"] + result["n_undefined"] == 100
    assert result["lower"] == result["upper"] == 1.0


def test_bootstrap_can_report_no_estimable_draws():
    from protocol.irr import bootstrap_krippendorff_alpha

    result = bootstrap_krippendorff_alpha([[0, 1], [0, 1]], n_bootstrap=1, seed=0)
    assert result["n_valid"] == 0
    assert result["n_undefined"] == 1
    assert result["lower"] is None and result["upper"] is None


def test_ordinal_order_rejects_duplicate_labels():
    from protocol.irr import krippendorff_alpha

    with pytest.raises(ValueError, match="unique"):
        krippendorff_alpha([[0, 1], [0, 1]], level_of_measurement="ordinal", ordinal_order=[0, 1, 0])


def test_item_mapping_preserves_non_string_annotator_keys():
    from protocol.irr import krippendorff_alpha

    assert krippendorff_alpha({"a": {1: 0, 2: 0}, "b": {1: 1, 2: 1}}) == 1.0


def test_unequal_rater_counts_weight_units_by_pairable_values():
    from protocol.irr import krippendorff_alpha

    # Units [a,a,b] and [b,b]: weighted upper coincidence disagreement=1,
    # five pairable values, n_a*n_b=6; alpha=1-4/6.
    assert krippendorff_alpha([["a", "b"], ["a", "b"], ["b", None]]) == pytest.approx(1 / 3)


def test_alpha_is_invariant_to_rater_and_unit_permutation():
    from protocol.irr import krippendorff_alpha

    permuted = [list(reversed(row)) for row in reversed(PUBLISHED_MISSING)]
    for level in ("nominal", "ordinal"):
        assert krippendorff_alpha(permuted, level_of_measurement=level) == pytest.approx(
            krippendorff_alpha(PUBLISHED_MISSING, level_of_measurement=level)
        )


def test_alpha_preserves_negative_agreement_and_decision_thresholds():
    from protocol.irr import irr_decision, krippendorff_alpha

    assert krippendorff_alpha([[0, 0], [1, 1]]) == -0.5
    assert irr_decision(-1).claim_narrowing_required
    assert irr_decision(0.60).status == "adjudicate_before_confirmatory_claim"
    assert irr_decision(0.70).status == "acceptable"


def test_bootstrap_does_not_hide_invalid_ordinal_configuration():
    from protocol.irr import bootstrap_krippendorff_alpha

    with pytest.raises(ValueError, match="include"):
        bootstrap_krippendorff_alpha([[0, 1], [0, 1]], level_of_measurement="ordinal", ordinal_order=[0])


@pytest.mark.parametrize("body", [
    "x,ok,low\nx,bad,high\n", "x,ok,low\nx,ok,low\n",
    "x,ok\n", "x,,low\n", "x,ok,   \n", " ,ok,low\n",
])
def test_annotation_csv_rejects_ambiguous_or_missing_judgments(tmp_path, body):
    path = tmp_path / "annotations.csv"
    path.write_text("episode_id,mode,severity\n" + body, encoding="utf-8")
    with pytest.raises(ValueError, match="duplicate|blank|missing"):
        compare_annotations(path, path)


@pytest.mark.parametrize("second_label", ["a", "b"])
def test_human_annotations_do_not_silently_overwrite_duplicate_judgments(second_label):
    from types import SimpleNamespace
    from protocol.irr import krippendorff_alpha

    rows = [
        SimpleNamespace(item_id="x", annotator_id="r", label="a"),
        SimpleNamespace(item_id="x", annotator_id="r", label=second_label),
        SimpleNamespace(item_id="x", annotator_id="s", label="b"),
        SimpleNamespace(item_id="y", annotator_id="r", label="a"),
        SimpleNamespace(item_id="y", annotator_id="s", label="a"),
    ]
    with pytest.raises(ValueError, match="duplicate"):
        krippendorff_alpha(rows)
