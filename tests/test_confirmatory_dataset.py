from __future__ import annotations

import copy
import hashlib
import json
from pathlib import Path

import pytest

from label_plane.datasets import (
    CONFIRMATORY_MANIFEST_PATH,
    build_confirmatory_manifest,
    load_confirmatory_manifest,
    validate_confirmatory_manifest,
)


def _source_record(tmp_path: Path, index: int, *, project: str = "project-a") -> dict[str, object]:
    source = tmp_path / f"source-{index}.json"
    source.write_text(json.dumps({"intent": index}, sort_keys=True) + "\n", encoding="utf-8")
    requirements = [
        "Archive inactive customer sessions after the retention interval.",
        "Rotate service credentials before their scheduled expiry.",
        "Reconcile warehouse counts at the close of each business day.",
        "Quarantine malformed uploads before persistence.",
        "Issue renewal notices ahead of subscription expiration.",
        "Validate shipping addresses before checkout completion.",
        "Record the reason whenever support escalates a case.",
        "Purge expired access tokens during the nightly maintenance job.",
        "Schedule maintenance windows outside customer operating hours.",
        "Index customer receipts using their immutable order identifier.",
        "Export a signed audit summary at the end of each reporting period.",
        "Route failed payment retries to the account recovery queue.",
    ]
    return {
        "source_intent_id": f"intent-{index:02d}",
        "source": str(source),
        "source_sha256": hashlib.sha256(source.read_bytes()).hexdigest(),
        "provenance_url": f"https://example.invalid/project-{project}/intent-{index:02d}",
        "project_id": project,
        "defect_family": "threshold_ambiguity",
        "clean_requirement": requirements[index],
        "smelly_requirement": requirements[index].replace(" the ", " ", 1) + " after some time.",
        "natural_variant": False,
        "contamination_notes": "No model output or evaluation answer was used.",
    }


def _complete_manifest(tmp_path: Path) -> dict[str, object]:
    records = [_source_record(tmp_path, index, project=f"project-{index % 3}") for index in range(12)]
    return {
        "schema_version": "confirmatory-v1",
        "expected": {"intents": 12, "variants": ["clean", "smelly"], "replications": 5},
        "near_clone_threshold": 0.92,
        "approved_paraphrases": [],
        "records": records,
    }


def test_checked_in_manifest_fails_closed_until_12_provenanced_intents_exist():
    manifest = load_confirmatory_manifest()

    with pytest.raises(ValueError, match="12 distinct source intents"):
        validate_confirmatory_manifest(manifest)

    assert CONFIRMATORY_MANIFEST_PATH.exists()
    assert CONFIRMATORY_MANIFEST_PATH.with_name("schema.json").exists()


def test_confirmatory_manifest_expands_to_exact_12_by_2_by_5_and_is_deterministic(tmp_path: Path):
    manifest = _complete_manifest(tmp_path)

    first = validate_confirmatory_manifest(manifest)
    second = validate_confirmatory_manifest(copy.deepcopy(manifest))

    assert first["counts"] == {
        "intent_count": 12,
        "project_count": 3,
        "episode_count": 120,
        "replication_count": 5,
        "variant_count": 2,
    }
    assert first["manifest_sha256"] == second["manifest_sha256"]
    assert len(first["records"]) == 120
    assert first["project_holdouts"] == {
        "project-0": sorted(f"intent-{index:02d}" for index in range(0, 12, 3)),
        "project-1": sorted(f"intent-{index:02d}" for index in range(1, 12, 3)),
        "project-2": sorted(f"intent-{index:02d}" for index in range(2, 12, 3)),
    }

    built = build_confirmatory_manifest(manifest)
    assert built["manifest_sha256"] == first["manifest_sha256"]


def test_confirmatory_manifest_rejects_source_hash_tampering(tmp_path: Path):
    manifest = _complete_manifest(tmp_path)
    manifest["records"][0]["source_sha256"] = "0" * 64  # type: ignore[index]

    with pytest.raises(ValueError, match="source hash mismatch"):
        validate_confirmatory_manifest(manifest)


def test_confirmatory_manifest_rejects_missing_provenance_and_project(tmp_path: Path):
    manifest = _complete_manifest(tmp_path)
    manifest["records"][0]["provenance_url"] = ""  # type: ignore[index]
    manifest["records"][1]["project_id"] = ""  # type: ignore[index]

    with pytest.raises(ValueError, match="provenance_url"):
        validate_confirmatory_manifest(manifest)


def test_confirmatory_manifest_rejects_near_clone_sources(tmp_path: Path):
    manifest = _complete_manifest(tmp_path)
    manifest["records"][1]["clean_requirement"] = manifest["records"][0]["clean_requirement"]  # type: ignore[index]

    with pytest.raises(ValueError, match="duplicate source intent text"):
        validate_confirmatory_manifest(manifest)
