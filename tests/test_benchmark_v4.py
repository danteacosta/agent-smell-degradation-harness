from __future__ import annotations

import copy

import pytest


def test_v4_benchmark_metadata_is_complete_and_validates_each_pair():
    from label_plane.datasets import load_v4_validation_metadata, validate_v4_metadata

    metadata = load_v4_validation_metadata()

    assert len(metadata["records"]) >= 6
    validate_v4_metadata(metadata)
    for record in metadata["records"]:
        assert record["source"]
        assert record["license"]
        assert record["source_sha256"]
        assert record["preserved_intent"] is True
        assert record["single_defect"] is True
        assert record["manipulation"]
        assert isinstance(record["natural_variant"], bool)
        assert record["contamination_notes"]


def test_v4_dataset_assets_publish_schema_license_and_card():
    from label_plane.datasets import V4_DATASET_ROOT

    assert (V4_DATASET_ROOT / "schema.json").exists()
    assert (V4_DATASET_ROOT / "licenses.json").exists()
    assert (V4_DATASET_ROOT / "dataset_card.md").exists()


def test_v4_metadata_rejects_a_source_hash_that_does_not_match_the_record():
    from label_plane.datasets import load_v4_validation_metadata, validate_v4_metadata

    metadata = copy.deepcopy(load_v4_validation_metadata())
    metadata["records"][0]["source_sha256"] = "not-a-hash"

    with pytest.raises(ValueError, match="hash"):
        validate_v4_metadata(metadata)
