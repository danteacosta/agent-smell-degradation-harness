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
