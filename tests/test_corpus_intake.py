from __future__ import annotations

import json

import pytest

from eval.corpus_intake import (
    CorpusIntakeError,
    build_redacted_manifest,
    load_private_records,
)


def _record(index: int) -> dict:
    return {
        "source_intent_id": f"source-{index:02d}",
        "project_id": f"project-{index % 6}",
        "source_url": f"https://example.org/requirements/{index}",
        "license": "CC-BY-4.0",
        "license_url": "https://creativecommons.org/licenses/by/4.0/",
        "reuse_permission_status": "license_confirmed",
        "rights_review": {
            "redistribution_allowed": True,
            "derivative_use_allowed": True,
            "external_provider_processing_allowed": True,
            "attribution_recorded": True,
            "reviewer_id": "rights-reviewer-a",
            "reviewed_at": "2026-09-02T10:00:00+00:00",
        },
        "retrieved_at": "2026-09-01T12:00:00+00:00",
        "canonical_text": f"Canonical source statement {index}.",
        "clean_requirement": f"The service shall process request {index} within 5 minutes.",
        "defective_requirement": f"The service shall process request {index} quickly.",
        "defect_family": "incompleteness_missing_condition",
        "removed_constraint_id": f"constraint-{index}",
        "near_clone_group": f"project-{index % 6}-group-{index}",
        "near_clone_reviewed": True,
        "manipulation_check": {
            "defect_present": True,
            "no_secondary_defect": True,
            "intent_preserved": True,
            "clean_variant_realistic": True,
            "constraint_independently_auditable": True,
            "reviewer_id": "reviewer-a",
        },
    }


def test_intake_emits_hash_only_manifest_for_twelve_intents() -> None:
    records = [_record(index) for index in range(12)]

    manifest = build_redacted_manifest(records)
    serialized = json.dumps(manifest, ensure_ascii=False)

    assert manifest["status"] == "validated_candidate"
    assert manifest["record_count"] == 12
    assert manifest["project_count"] == 6
    assert manifest["raw_text_exported"] is False
    assert "The service shall process request" not in serialized
    assert all("clean_requirement" not in row for row in manifest["records"])
    assert all(len(row["clean_requirement_sha256"]) == 64 for row in manifest["records"])


def test_intake_rejects_missing_rights_review_and_duplicate_intents() -> None:
    records = [_record(index) for index in range(12)]
    records[0]["reuse_permission_status"] = "pending"
    with pytest.raises(CorpusIntakeError, match="reuse_permission_status"):
        build_redacted_manifest(records)

    records = [_record(index) for index in range(12)]
    records[1]["source_intent_id"] = records[0]["source_intent_id"]
    with pytest.raises(CorpusIntakeError, match="unique"):
        build_redacted_manifest(records)


def test_intake_rejects_unconfirmed_external_provider_processing_rights() -> None:
    records = [_record(index) for index in range(12)]
    records[0]["rights_review"]["external_provider_processing_allowed"] = False

    with pytest.raises(
        CorpusIntakeError,
        match="external_provider_processing_allowed",
    ):
        build_redacted_manifest(records)


def test_intake_requires_timestamped_rights_review() -> None:
    records = [_record(index) for index in range(12)]
    records[0]["rights_review"].pop("reviewed_at")

    with pytest.raises(CorpusIntakeError, match="reviewed_at"):
        build_redacted_manifest(records)


def test_private_jsonl_loader_keeps_raw_records_for_one_redaction_pass(tmp_path) -> None:
    source = tmp_path / "intake.jsonl"
    source.write_text(
        "\n".join(json.dumps(_record(index)) for index in range(12)) + "\n",
        encoding="utf-8",
    )

    records = load_private_records(source)
    manifest = build_redacted_manifest(records)

    assert len(records) == 12
    assert "clean_requirement" in records[0]
    assert "clean_requirement" not in manifest["records"][0]
