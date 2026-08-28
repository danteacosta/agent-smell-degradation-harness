from __future__ import annotations

import pytest

from label_plane.human_annotation import load_primary_label_manifest


def test_primary_label_manifest_requires_adjudicated_double_coding_for_every_item():
    manifest = {
        "schema_version": "human-labels/v1",
        "duplicate_subset_fraction": 1.0,
        "labels": [
            {"episode_id": "E-1", "label": "degraded", "adjudicated": True, "missing": False, "independent_annotator_count": 2},
            {"episode_id": "E-2", "label": "clean", "adjudicated": True, "missing": False, "independent_annotator_count": 2},
        ],
    }
    assert load_primary_label_manifest(manifest, ["E-1", "E-2"]) == {"E-1": 1, "E-2": 0}


def test_primary_label_manifest_fails_closed_on_missing_or_unadjudicated_label():
    manifest = {
        "schema_version": "human-labels/v1",
        "duplicate_subset_fraction": 1.0,
        "labels": [{"episode_id": "E-1", "label": 1, "adjudicated": False, "independent_annotator_count": 2}],
    }
    with pytest.raises(ValueError, match="adjudication"):
        load_primary_label_manifest(manifest, ["E-1"])


def test_primary_label_manifest_rejects_single_annotator():
    manifest = {"schema_version": "human-labels/v1", "duplicate_subset_fraction": 1.0,
                "labels": [{"episode_id": "E-1", "label": 1, "adjudicated": True, "missing": False, "independent_annotator_count": 1}]}
    with pytest.raises(ValueError, match="two independent"):
        load_primary_label_manifest(manifest, ["E-1"])
