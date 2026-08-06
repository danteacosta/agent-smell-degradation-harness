from __future__ import annotations

import pytest

from label_plane.human_annotation import load_primary_label_manifest


def test_primary_label_manifest_requires_adjudicated_20_percent_subset():
    manifest = {
        "schema_version": "human-labels/v1",
        "duplicate_subset_fraction": 0.20,
        "labels": [
            {"episode_id": "E-1", "label": "degraded", "adjudicated": True, "missing": False},
            {"episode_id": "E-2", "label": "clean", "adjudicated": True, "missing": False},
        ],
    }
    assert load_primary_label_manifest(manifest, ["E-1", "E-2"]) == {"E-1": 1, "E-2": 0}


def test_primary_label_manifest_fails_closed_on_missing_or_unadjudicated_label():
    manifest = {
        "schema_version": "human-labels/v1",
        "duplicate_subset_fraction": 0.20,
        "labels": [{"episode_id": "E-1", "label": 1, "adjudicated": False}],
    }
    with pytest.raises(ValueError, match="adjudication"):
        load_primary_label_manifest(manifest, ["E-1"])
