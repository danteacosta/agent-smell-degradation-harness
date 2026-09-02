from __future__ import annotations

import copy
import hashlib
import json
import subprocess
import sys
from pathlib import Path

import pytest

from eval.corpus_intake import (
    CorpusIntakeError,
    build_redacted_manifest,
    validate_private_records_against_frozen_manifest,
    freeze_validated_manifest,
)


REPO_ROOT = Path(__file__).parents[1]
FROZEN_AT = "2026-09-02T14:00:00+00:00"


def _record(index: int, *, project: int | None = None) -> dict:
    project_id = project if project is not None else index % 6
    return {
        "source_intent_id": f"source-{index:02d}",
        "project_id": f"project-{project_id}",
        "source_url": f"https://private.example/requirements/{index}",
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
        "canonical_text": f"PRIVATE SOURCE SECRET {index}.",
        "clean_requirement": f"The service shall process private request {index} within 5 minutes.",
        "defective_requirement": f"The service shall process private request {index} quickly.",
        "defect_family": "incompleteness_missing_condition",
        "removed_constraint_id": f"constraint-{index}",
        "near_clone_group": f"project-{project_id}-group-{index}",
        "near_clone_reviewed": True,
        "manipulation_check": {
            "defect_present": True,
            "no_secondary_defect": True,
            "intent_preserved": True,
            "clean_variant_realistic": True,
            "constraint_independently_auditable": True,
            "reviewer_id": "manipulation-reviewer-a",
        },
    }


def _candidate() -> tuple[list[dict], dict]:
    records = [_record(index) for index in range(12)]
    return records, build_redacted_manifest(records)


def _rehash_record(record: dict) -> None:
    unsigned = {key: value for key, value in record.items() if key != "record_sha256"}
    serialized = json.dumps(unsigned, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    record["record_sha256"] = hashlib.sha256(serialized.encode("utf-8")).hexdigest()


def _rehash_manifest(manifest: dict) -> None:
    unsigned = {key: value for key, value in manifest.items() if key != "manifest_sha256"}
    serialized = json.dumps(unsigned, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    manifest["manifest_sha256"] = hashlib.sha256(serialized.encode("utf-8")).hexdigest()


def test_validated_candidate_freezes_to_canonical_hash_only_manifest() -> None:
    records, candidate = _candidate()
    before = copy.deepcopy(candidate)

    frozen = freeze_validated_manifest(
        candidate, frozen_at=FROZEN_AT, freeze_reviewer_id="freeze-reviewer-a"
    )
    serialized = json.dumps(frozen, ensure_ascii=False)

    assert frozen["schema_version"] == "prepilot-corpus/v3"
    assert frozen["status"] == "frozen"
    assert frozen["frozen_at"] == FROZEN_AT
    assert frozen["freeze_reviewer_id"] == "freeze-reviewer-a"
    assert frozen["record_count"] == 12
    assert frozen["project_count"] == 6
    assert frozen["raw_text_exported"] is False
    assert len(frozen["manifest_sha256"]) == 64
    assert candidate == before
    assert all(
        not {"canonical_text", "source_text", "clean_requirement", "defective_requirement"}
        & set(row)
        for row in frozen["records"]
    )
    assert "PRIVATE SOURCE SECRET" not in serialized
    assert "private request" not in serialized
    assert records[0]["canonical_text"].startswith("PRIVATE SOURCE")


def test_freeze_preserves_valid_corpus_with_more_than_six_projects() -> None:
    records = [_record(index, project=index % 7) for index in range(12)]
    candidate = build_redacted_manifest(records)

    frozen = freeze_validated_manifest(
        candidate, frozen_at=FROZEN_AT, freeze_reviewer_id="freeze-reviewer-a"
    )

    assert frozen["record_count"] == 12
    assert frozen["project_count"] == 7


def test_candidate_rejects_weakened_count_gate_overrides() -> None:
    records = [_record(index) for index in range(12)]

    with pytest.raises(CorpusIntakeError, match="expected_intents.*12"):
        build_redacted_manifest(records, expected_intents=11)
    with pytest.raises(CorpusIntakeError, match="minimum_projects.*6"):
        build_redacted_manifest(records, minimum_projects=5)


def test_seven_project_corpus_with_minimum_projects_override_freezes_and_joins() -> None:
    records = [_record(index, project=index % 7) for index in range(12)]
    candidate = build_redacted_manifest(records, minimum_projects=7)

    frozen = freeze_validated_manifest(
        candidate, frozen_at=FROZEN_AT, freeze_reviewer_id="freeze-reviewer-a"
    )

    assert frozen["project_count"] == 7
    assert frozen["minimum_projects"] == 7
    assert len(validate_private_records_against_frozen_manifest(records, frozen)) == 12


def test_freeze_rejects_declared_minimum_above_actual_project_count() -> None:
    _, candidate = _candidate()
    candidate["minimum_projects"] = 7

    with pytest.raises(CorpusIntakeError, match="projects|minimum"):
        freeze_validated_manifest(
            candidate, frozen_at=FROZEN_AT, freeze_reviewer_id="freeze-reviewer-a"
        )

    _, valid_candidate = _candidate()
    frozen = freeze_validated_manifest(
        valid_candidate, frozen_at=FROZEN_AT, freeze_reviewer_id="freeze-reviewer-a"
    )
    frozen["minimum_projects"] = 7
    _rehash_manifest(frozen)
    with pytest.raises(CorpusIntakeError, match="projects|minimum"):
        validate_private_records_against_frozen_manifest(
            [_record(index) for index in range(12)], frozen
        )


@pytest.mark.parametrize(
    "field", ["record_count", "unique_intent_count", "project_count", "expected_intents", "minimum_projects"]
)
def test_freeze_rejects_float_count_metadata(field: str) -> None:
    _, candidate = _candidate()
    invalid = copy.deepcopy(candidate)
    invalid[field] = float(invalid[field])

    with pytest.raises(CorpusIntakeError, match="count|integer|metadata"):
        freeze_validated_manifest(
            invalid, frozen_at=FROZEN_AT, freeze_reviewer_id="freeze-reviewer-a"
        )


def test_freeze_rejects_self_consistent_whitespace_variant() -> None:
    _, candidate = _candidate()
    invalid = copy.deepcopy(candidate)
    invalid["records"][0]["source_intent_id"] = " source-00 "
    _rehash_record(invalid["records"][0])

    with pytest.raises(CorpusIntakeError, match="record_sha256"):
        freeze_validated_manifest(
            invalid, frozen_at=FROZEN_AT, freeze_reviewer_id="freeze-reviewer-a"
        )


def test_private_join_rejects_noncanonical_row_with_recomputed_manifest_hash() -> None:
    records, candidate = _candidate()
    frozen = freeze_validated_manifest(
        candidate, frozen_at=FROZEN_AT, freeze_reviewer_id="freeze-reviewer-a"
    )
    frozen["records"][0]["source_intent_id"] = " source-00 "
    _rehash_manifest(frozen)

    with pytest.raises(CorpusIntakeError, match="canonical|normalized"):
        validate_private_records_against_frozen_manifest(records, frozen)


@pytest.mark.parametrize("review_name", ["rights_review", "manipulation_check"])
@pytest.mark.parametrize("reviewer_id", [None, 123])
def test_candidate_rejects_non_string_nested_reviewer_ids(
    review_name: str, reviewer_id: object
) -> None:
    records = [_record(index) for index in range(12)]
    records[0][review_name]["reviewer_id"] = reviewer_id

    with pytest.raises(CorpusIntakeError, match="reviewer_id"):
        build_redacted_manifest(records)


@pytest.mark.parametrize("review_name", ["rights_review", "manipulation_check"])
@pytest.mark.parametrize("reviewer_id", ["tbd", "unknown", "none", "null"])
def test_candidate_rejects_all_reviewer_placeholders(
    review_name: str, reviewer_id: str
) -> None:
    records = [_record(index) for index in range(12)]
    records[0][review_name]["reviewer_id"] = reviewer_id.upper()

    with pytest.raises(CorpusIntakeError, match="reviewer_id"):
        build_redacted_manifest(records)


@pytest.mark.parametrize(
    ("frozen_at", "reviewer"),
    [("TBD", "freeze-reviewer-a"), (FROZEN_AT, "TBD"), ("", "")],
)
def test_freeze_rejects_placeholder_metadata(frozen_at: str, reviewer: str) -> None:
    _, candidate = _candidate()

    with pytest.raises(CorpusIntakeError, match="frozen_at|freeze_reviewer_id"):
        freeze_validated_manifest(
            candidate, frozen_at=frozen_at, freeze_reviewer_id=reviewer
        )


def test_freeze_rejects_non_candidate_shapes_and_raw_fields() -> None:
    _, candidate = _candidate()

    for invalid in (
        {**candidate, "status": "frozen"},
        {**candidate, "raw_text_exported": True},
        {**candidate, "records": [*candidate["records"], {"source_text": "secret"}]},
    ):
        with pytest.raises(CorpusIntakeError):
            freeze_validated_manifest(
                invalid, frozen_at=FROZEN_AT, freeze_reviewer_id="freeze-reviewer-a"
            )

    raw_candidate = copy.deepcopy(candidate)
    raw_candidate["records"][0]["clean_requirement"] = "PRIVATE RAW SECRET"
    with pytest.raises(CorpusIntakeError, match="raw|redacted"):
        freeze_validated_manifest(
            raw_candidate, frozen_at=FROZEN_AT, freeze_reviewer_id="freeze-reviewer-a"
        )


def test_candidate_validator_rejects_count_project_rights_and_duplicate_hashes() -> None:
    with pytest.raises(CorpusIntakeError, match="exactly 12"):
        build_redacted_manifest([_record(index) for index in range(11)])

    with pytest.raises(CorpusIntakeError, match="at least 6"):
        build_redacted_manifest([_record(index, project=0) for index in range(12)])

    records = [_record(index) for index in range(12)]
    records[0]["rights_review"]["external_provider_processing_allowed"] = False
    with pytest.raises(CorpusIntakeError, match="external_provider_processing_allowed"):
        build_redacted_manifest(records)

    records = [_record(index) for index in range(12)]
    records[1]["canonical_text"] = records[0]["canonical_text"]
    with pytest.raises(CorpusIntakeError, match="hashes"):
        build_redacted_manifest(records)


def test_freeze_rejects_tampered_record_hash_and_duplicate_intent() -> None:
    _, candidate = _candidate()
    tampered = copy.deepcopy(candidate)
    tampered["records"][0]["record_sha256"] = "0" * 64
    with pytest.raises(CorpusIntakeError, match="record_sha256"):
        freeze_validated_manifest(
            tampered, frozen_at=FROZEN_AT, freeze_reviewer_id="freeze-reviewer-a"
        )

    duplicate = copy.deepcopy(candidate)
    duplicate["records"][1]["source_intent_id"] = duplicate["records"][0][
        "source_intent_id"
    ]
    with pytest.raises(CorpusIntakeError, match="unique"):
        freeze_validated_manifest(
            duplicate, frozen_at=FROZEN_AT, freeze_reviewer_id="freeze-reviewer-a"
        )


def test_freeze_rejects_nested_raw_text_injection_without_leaking_value() -> None:
    _, candidate = _candidate()
    injected = copy.deepcopy(candidate)
    secret = "NESTED PRIVATE SOURCE SECRET"
    injected["records"][0]["rights_review"]["audit"] = {"raw_text": secret}
    _rehash_record(injected["records"][0])

    with pytest.raises(CorpusIntakeError, match="raw|redacted") as error:
        freeze_validated_manifest(
            injected, frozen_at=FROZEN_AT, freeze_reviewer_id="freeze-reviewer-a"
        )
    assert secret not in str(error.value)


@pytest.mark.parametrize(
    "mutation",
    [
        lambda row: row["rights_review"].update(
            {"redistribution_allowed": False}
        ),
        lambda row: row["rights_review"].pop("reviewer_id"),
        lambda row: row["manipulation_check"].update({"defect_present": False}),
        lambda row: row["manipulation_check"].pop("reviewer_id"),
    ],
)
def test_freeze_rejects_false_or_incomplete_nested_reviews(mutation) -> None:
    _, candidate = _candidate()
    invalid = copy.deepcopy(candidate)
    mutation(invalid["records"][0])
    _rehash_record(invalid["records"][0])

    with pytest.raises(CorpusIntakeError):
        freeze_validated_manifest(
            invalid, frozen_at=FROZEN_AT, freeze_reviewer_id="freeze-reviewer-a"
        )


@pytest.mark.parametrize(
    "field", ["canonical_text_sha256", "clean_requirement_sha256", "defective_requirement_sha256"]
)
def test_freeze_rejects_malformed_source_hashes(field: str) -> None:
    _, candidate = _candidate()
    invalid = copy.deepcopy(candidate)
    invalid["records"][0][field] = "not-a-sha256"
    _rehash_record(invalid["records"][0])

    with pytest.raises(CorpusIntakeError, match="SHA-256|hash"):
        freeze_validated_manifest(
            invalid, frozen_at=FROZEN_AT, freeze_reviewer_id="freeze-reviewer-a"
        )


@pytest.mark.parametrize(
    "nested_field",
    [
        ("rights_review", "extra_nested_field"),
        ("manipulation_check", "extra_nested_field"),
    ],
)
def test_freeze_rejects_extra_nested_review_fields(nested_field: tuple[str, str]) -> None:
    _, candidate = _candidate()
    invalid = copy.deepcopy(candidate)
    review_name, field = nested_field
    invalid["records"][0][review_name][field] = "must not be exported"
    _rehash_record(invalid["records"][0])

    with pytest.raises(CorpusIntakeError, match="unexpected|allowlist|redacted") as error:
        freeze_validated_manifest(
            invalid, frozen_at=FROZEN_AT, freeze_reviewer_id="freeze-reviewer-a"
        )
    assert "must not be exported" not in str(error.value)


def test_private_join_rejects_self_consistent_frozen_manifest_with_eleven_records() -> None:
    records, candidate = _candidate()
    frozen = freeze_validated_manifest(
        candidate, frozen_at=FROZEN_AT, freeze_reviewer_id="freeze-reviewer-a"
    )
    frozen["records"] = frozen["records"][:-1]
    frozen["record_count"] = 11
    frozen["unique_intent_count"] = 11
    _rehash_manifest(frozen)

    with pytest.raises(CorpusIntakeError, match="count|12|records"):
        validate_private_records_against_frozen_manifest(records, frozen)


def test_private_join_rejects_self_consistent_inconsistent_frozen_metadata() -> None:
    records, candidate = _candidate()
    frozen = freeze_validated_manifest(
        candidate, frozen_at=FROZEN_AT, freeze_reviewer_id="freeze-reviewer-a"
    )
    frozen["record_count"] = 11
    _rehash_manifest(frozen)

    with pytest.raises(CorpusIntakeError, match="count|metadata|inconsistent"):
        validate_private_records_against_frozen_manifest(records, frozen)


@pytest.mark.parametrize("review_name", ["rights_review", "manipulation_check"])
def test_freeze_rejects_non_string_nested_reviewer_ids(review_name: str) -> None:
    _, candidate = _candidate()
    invalid = copy.deepcopy(candidate)
    invalid["records"][0][review_name]["reviewer_id"] = None
    _rehash_record(invalid["records"][0])

    with pytest.raises(CorpusIntakeError, match="reviewer_id"):
        freeze_validated_manifest(
            invalid, frozen_at=FROZEN_AT, freeze_reviewer_id="freeze-reviewer-a"
        )


def test_private_records_join_against_frozen_manifest_without_raw_text() -> None:
    records, candidate = _candidate()
    frozen = freeze_validated_manifest(
        candidate, frozen_at=FROZEN_AT, freeze_reviewer_id="freeze-reviewer-a"
    )

    joined = validate_private_records_against_frozen_manifest(records, frozen)
    serialized = json.dumps(joined, ensure_ascii=False)

    assert len(joined) == 12
    assert joined[0]["source_intent_id"] == "source-00"
    assert joined[0]["project_id"] == "project-0"
    assert "PRIVATE SOURCE SECRET" not in serialized
    assert "private request" not in serialized
    assert all("canonical_text" not in row for row in joined)
    assert all("clean_requirement" not in row for row in joined)

    tampered = copy.deepcopy(records)
    tampered[0]["clean_requirement"] = "PRIVATE TAMPERED SECRET"
    with pytest.raises(CorpusIntakeError, match="clean_requirement_sha256") as error:
        validate_private_records_against_frozen_manifest(tampered, frozen)
    assert "PRIVATE TAMPERED SECRET" not in str(error.value)


def test_freeze_cli_writes_only_fixed_redacted_repository_artifact(tmp_path: Path) -> None:
    records, candidate = _candidate()
    candidate_path = tmp_path / "private-candidate.json"
    candidate_path.write_text(json.dumps(candidate), encoding="utf-8")
    output_path = REPO_ROOT / "data/prepilot/corpus-manifest.json"
    existed = output_path.exists()
    previous_bytes = output_path.read_bytes() if existed else None
    try:
        result = subprocess.run(
            [
                sys.executable,
                "scripts/freeze_corpus_manifest.py",
                "--candidate",
                str(candidate_path),
                "--frozen-at",
                FROZEN_AT,
                "--freeze-reviewer-id",
                "freeze-reviewer-a",
            ],
            cwd=REPO_ROOT,
            capture_output=True,
            text=True,
            check=False,
        )

        assert result.returncode == 0, result.stderr
        assert output_path.exists()
        emitted = json.loads(output_path.read_text(encoding="utf-8"))
        assert emitted["status"] == "frozen"
        assert emitted["raw_text_exported"] is False
        assert "PRIVATE SOURCE SECRET" not in result.stdout + result.stderr
        assert "private request" not in output_path.read_text(encoding="utf-8")
    finally:
        if existed:
            output_path.write_bytes(previous_bytes)
        elif output_path.exists():
            output_path.unlink()


def test_validate_intake_script_runs_by_repository_path(tmp_path: Path) -> None:
    records = [_record(index) for index in range(12)]
    input_path = tmp_path / "private-records.json"
    output_path = tmp_path / "candidate.json"
    input_path.write_text(json.dumps(records), encoding="utf-8")

    result = subprocess.run(
        [
            sys.executable,
            "scripts/validate_corpus_intake.py",
            "--input",
            str(input_path),
            "--output",
            str(output_path),
        ],
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
        check=False,
    )

    assert result.returncode == 0, result.stderr
    assert json.loads(output_path.read_text(encoding="utf-8"))["status"] == (
        "validated_candidate"
    )
    assert "PRIVATE SOURCE SECRET" not in output_path.read_text(encoding="utf-8")
