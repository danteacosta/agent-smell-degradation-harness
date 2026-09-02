"""Validate private corpus intake and emit a redacted admission manifest.

Raw requirements remain outside the repository.  The emitted manifest contains
only provenance, review decisions, and SHA-256 digests, so it can be versioned
without redistributing source text or accidentally exposing an annotation
target.
"""

from __future__ import annotations

import hashlib
import json
import re
from datetime import datetime
from pathlib import Path
from typing import Any, Iterable, Mapping
from urllib.parse import urlparse

SCHEMA_VERSION = "prepilot-corpus/v3"
PRIMARY_DEFECT_FAMILY = "incompleteness_missing_condition"
REQUIRED_MANIPULATION_CHECKS = (
    "defect_present",
    "no_secondary_defect",
    "intent_preserved",
    "clean_variant_realistic",
    "constraint_independently_auditable",
)
REQUIRED_RIGHTS_ASSERTIONS = (
    "redistribution_allowed",
    "derivative_use_allowed",
    "external_provider_processing_allowed",
    "attribution_recorded",
)
_HASH_FIELDS = (
    "canonical_text_sha256",
    "clean_requirement_sha256",
    "defective_requirement_sha256",
)
_REDACTED_RECORD_FIELDS = {
    "source_intent_id",
    "project_id",
    "source_url",
    "license",
    "license_evidence_url",
    "reuse_permission_status",
    "rights_review",
    "retrieved_at",
    *_HASH_FIELDS,
    "defect_family",
    "removed_constraint_id",
    "near_clone_group",
    "near_clone_reviewed",
    "manipulation_check",
    "record_sha256",
}
_RAW_TEXT_FIELDS = {
    "canonical_text",
    "source_text",
    "clean_requirement",
    "defective_requirement",
}
_CANDIDATE_FIELDS = {
    "schema_version",
    "status",
    "record_count",
    "unique_intent_count",
    "project_count",
    "minimum_projects",
    "expected_intents",
    "raw_text_exported",
    "records",
}
_FROZEN_FIELDS = _CANDIDATE_FIELDS | {
    "frozen_at",
    "freeze_reviewer_id",
    "manifest_sha256",
}
_RIGHTS_REVIEW_FIELDS = set(REQUIRED_RIGHTS_ASSERTIONS) | {
    "reviewer_id",
    "reviewed_at",
}
_MANIPULATION_REVIEW_FIELDS = set(REQUIRED_MANIPULATION_CHECKS) | {"reviewer_id"}
_SHA256_RE = re.compile(r"[0-9a-f]{64}")


class CorpusIntakeError(ValueError):
    """Raised when a candidate corpus cannot be admitted safely."""


def _canonical_json(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def _sha256_text(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def _sha256_json(value: Any) -> str:
    return _sha256_text(_canonical_json(value))


def _required_text(record: Mapping[str, Any], key: str) -> str:
    value = record.get(key)
    if not isinstance(value, str) or not value.strip():
        raise CorpusIntakeError(f"record field {key} must be non-empty text")
    return value


def _required_id(record: Mapping[str, Any], key: str) -> str:
    value = _required_text(record, key).strip()
    if value.lower() in {"tbd", "unknown", "null", "none"}:
        raise CorpusIntakeError(f"record field {key} cannot be a placeholder")
    return value


def _required_url(record: Mapping[str, Any], key: str) -> str:
    value = _required_text(record, key).strip()
    parsed = urlparse(value)
    if parsed.scheme not in {"http", "https"} or not parsed.netloc:
        raise CorpusIntakeError(f"record field {key} must be an http(s) URL")
    return value


def _required_timestamp(record: Mapping[str, Any], key: str) -> str:
    value = _required_text(record, key).strip()
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError as error:
        raise CorpusIntakeError(f"record field {key} must be ISO-8601") from error
    if parsed.tzinfo is None:
        raise CorpusIntakeError(f"record field {key} must include a timezone")
    return value


def _check_hash(record: Mapping[str, Any], field: str, expected: str) -> str:
    provided = record.get(field)
    if provided is not None and str(provided).lower() != expected:
        raise CorpusIntakeError(f"{field} does not match the private source text")
    return expected


def _review_checks(record: Mapping[str, Any]) -> tuple[dict[str, bool], str]:
    raw = record.get("manipulation_check")
    if raw is None and isinstance(record.get("review"), Mapping):
        raw = record["review"].get("manipulation_checks")
    if not isinstance(raw, Mapping):
        raise CorpusIntakeError("manipulation_check is required")
    checks: dict[str, bool] = {}
    for field in REQUIRED_MANIPULATION_CHECKS:
        if raw.get(field) is not True:
            raise CorpusIntakeError(f"manipulation check is not confirmed: {field}")
        checks[field] = True
    reviewer_value = raw.get("reviewer_id")
    if not isinstance(reviewer_value, str):
        raise CorpusIntakeError("manipulation_check.reviewer_id must be text")
    reviewer = reviewer_value.strip()
    if not reviewer or reviewer.lower() in {"tbd", "unknown"}:
        raise CorpusIntakeError("manipulation_check.reviewer_id is required")
    return checks, reviewer


def _rights_review(record: Mapping[str, Any]) -> dict[str, Any]:
    raw = record.get("rights_review")
    if not isinstance(raw, Mapping):
        raise CorpusIntakeError("rights_review is required")
    assertions: dict[str, bool] = {}
    for field in REQUIRED_RIGHTS_ASSERTIONS:
        if raw.get(field) is not True:
            raise CorpusIntakeError(f"rights review is not confirmed: {field}")
        assertions[field] = True
    reviewer_value = raw.get("reviewer_id")
    if not isinstance(reviewer_value, str):
        raise CorpusIntakeError("rights_review.reviewer_id must be text")
    reviewer_id = reviewer_value.strip()
    if not reviewer_id or reviewer_id.lower() in {"tbd", "unknown"}:
        raise CorpusIntakeError("rights_review.reviewer_id is required")
    reviewed_at = _required_timestamp(raw, "reviewed_at")
    return {
        **assertions,
        "reviewer_id": reviewer_id,
        "reviewed_at": reviewed_at,
    }


def _license_record(record: Mapping[str, Any]) -> tuple[str, str, str]:
    license_name = _required_id(record, "license")
    evidence_key = "license_url" if record.get("license_url") else "permission_record_url"
    evidence_url = _required_url(record, evidence_key)
    permission = str(record.get("reuse_permission_status", "")).strip().lower()
    if permission not in {"license_confirmed", "written_permission"}:
        raise CorpusIntakeError(
            "reuse_permission_status must be license_confirmed or written_permission"
        )
    return license_name, evidence_url, permission


def _validate_record(record: Mapping[str, Any]) -> dict[str, Any]:
    if not isinstance(record, Mapping):
        raise CorpusIntakeError("each corpus record must be an object")
    source_intent_id = _required_id(record, "source_intent_id")
    project_id = _required_id(record, "project_id")
    source_url = _required_url(record, "source_url")
    retrieved_at = _required_timestamp(record, "retrieved_at")
    license_name, license_evidence_url, permission = _license_record(record)
    rights_review = _rights_review(record)
    clean = _required_text(record, "clean_requirement")
    defective = _required_text(record, "defective_requirement")
    canonical = _required_text(
        record,
        "canonical_text" if record.get("canonical_text") is not None else "source_text",
    )
    if clean == defective:
        raise CorpusIntakeError(
            f"{source_intent_id} clean and defective variants must differ"
        )
    defect_family = _required_id(record, "defect_family")
    if defect_family != PRIMARY_DEFECT_FAMILY:
        raise CorpusIntakeError(
            f"{source_intent_id} defect_family must be {PRIMARY_DEFECT_FAMILY}"
        )
    removed_constraint_id = _required_id(record, "removed_constraint_id")
    near_clone_group = _required_id(record, "near_clone_group")
    near_clone_reviewed = record.get("near_clone_reviewed")
    if near_clone_reviewed is not True:
        raise CorpusIntakeError(
            f"{source_intent_id} near_clone_reviewed must be true before admission"
        )
    manipulation_checks, reviewer_id = _review_checks(record)
    canonical_hash = _check_hash(record, "canonical_text_sha256", _sha256_text(canonical))
    clean_hash = _check_hash(
        record, "clean_requirement_sha256", _sha256_text(clean)
    )
    defective_hash = _check_hash(
        record, "defective_requirement_sha256", _sha256_text(defective)
    )
    redacted = {
        "source_intent_id": source_intent_id,
        "project_id": project_id,
        "source_url": source_url,
        "license": license_name,
        "license_evidence_url": license_evidence_url,
        "reuse_permission_status": permission,
        "rights_review": rights_review,
        "retrieved_at": retrieved_at,
        "canonical_text_sha256": canonical_hash,
        "clean_requirement_sha256": clean_hash,
        "defective_requirement_sha256": defective_hash,
        "defect_family": defect_family,
        "removed_constraint_id": removed_constraint_id,
        "near_clone_group": near_clone_group,
        "near_clone_reviewed": True,
        "manipulation_check": {
            **manipulation_checks,
            "reviewer_id": reviewer_id,
        },
    }
    redacted["record_sha256"] = _sha256_json(redacted)
    return redacted


def load_private_records(path: str | Path) -> list[dict[str, Any]]:
    source = Path(path)
    try:
        text = source.read_text(encoding="utf-8")
    except OSError as error:
        raise CorpusIntakeError(f"cannot read private corpus input: {source}") from error
    if source.suffix.lower() == ".jsonl":
        records: list[Any] = [
            json.loads(line)
            for line in text.splitlines()
            if line.strip()
        ]
    else:
        try:
            payload = json.loads(text)
        except json.JSONDecodeError as error:
            raise CorpusIntakeError(f"corpus input is not valid JSON: {source}") from error
        if isinstance(payload, list):
            records = payload
        elif isinstance(payload, Mapping) and isinstance(payload.get("records"), list):
            records = payload["records"]
        else:
            raise CorpusIntakeError("corpus input must be a JSON array or JSONL")
    if not records:
        raise CorpusIntakeError("corpus input has no records")
    if not all(isinstance(record, Mapping) for record in records):
        raise CorpusIntakeError("each corpus record must be an object")
    return [dict(record) for record in records]


def build_redacted_manifest(
    records: Iterable[Mapping[str, Any]],
    *,
    expected_intents: int = 12,
    minimum_projects: int = 6,
) -> dict[str, Any]:
    if type(expected_intents) is not int or expected_intents != 12:
        raise CorpusIntakeError("expected_intents must be exactly 12")
    if type(minimum_projects) is not int or minimum_projects < 6:
        raise CorpusIntakeError("minimum_projects must be an integer >= 6")
    redacted = [_validate_record(record) for record in records]
    intent_ids = [str(record["source_intent_id"]) for record in redacted]
    if len(set(intent_ids)) != len(intent_ids):
        raise CorpusIntakeError("source_intent_id values must be unique")
    hash_values: list[str] = []
    for record in redacted:
        hash_values.extend(str(record[field]) for field in _HASH_FIELDS)
    if len(set(hash_values)) != len(hash_values):
        raise CorpusIntakeError(
            "canonical, clean, and defective source hashes must be globally unique"
        )
    project_ids = {str(record["project_id"]) for record in redacted}
    if len(redacted) != expected_intents:
        raise CorpusIntakeError(
            f"expected exactly {expected_intents} unique intents, got {len(redacted)}"
        )
    if len(project_ids) < minimum_projects:
        raise CorpusIntakeError(
            f"expected at least {minimum_projects} projects, got {len(project_ids)}"
        )
    return {
        "schema_version": SCHEMA_VERSION,
        "status": "validated_candidate",
        "record_count": len(redacted),
        "unique_intent_count": len(intent_ids),
        "project_count": len(project_ids),
        "minimum_projects": minimum_projects,
        "expected_intents": expected_intents,
        "raw_text_exported": False,
        "records": sorted(redacted, key=lambda row: str(row["source_intent_id"])),
    }


def _validate_redacted_record(record: Mapping[str, Any]) -> dict[str, Any]:
    if not isinstance(record, Mapping):
        raise CorpusIntakeError("frozen manifest records must be objects")
    unexpected = set(record) - _REDACTED_RECORD_FIELDS
    if unexpected:
        if unexpected & _RAW_TEXT_FIELDS:
            raise CorpusIntakeError("frozen manifest records must remain redacted")
        raise CorpusIntakeError("frozen manifest record has unexpected fields")
    missing = _REDACTED_RECORD_FIELDS - set(record)
    if missing:
        raise CorpusIntakeError("frozen manifest record is not a complete redacted record")
    _reject_raw_text_injection(record)
    _required_id(record, "source_intent_id")
    _required_id(record, "project_id")
    _required_url(record, "source_url")
    _required_id(record, "license")
    _required_url(record, "license_evidence_url")
    if record["reuse_permission_status"] not in {
        "license_confirmed",
        "written_permission",
    }:
        raise CorpusIntakeError(
            "frozen record reuse_permission_status is not confirmed"
        )
    _required_id(record, "defect_family")
    if record["defect_family"] != PRIMARY_DEFECT_FAMILY:
        raise CorpusIntakeError("frozen record has an unsupported defect family")
    _required_id(record, "removed_constraint_id")
    _required_id(record, "near_clone_group")
    if record["near_clone_reviewed"] is not True:
        raise CorpusIntakeError("frozen record near_clone_reviewed must be true")
    _required_timestamp(record, "retrieved_at")
    rights_review = record.get("rights_review")
    if not isinstance(rights_review, Mapping) or set(rights_review) != _RIGHTS_REVIEW_FIELDS:
        raise CorpusIntakeError("frozen record rights_review is incomplete or has unexpected fields")
    if not isinstance(rights_review.get("reviewer_id"), str):
        raise CorpusIntakeError("frozen record rights_review.reviewer_id must be text")
    _rights_review(record)
    manipulation_check = record.get("manipulation_check")
    if not isinstance(manipulation_check, Mapping) or set(manipulation_check) != _MANIPULATION_REVIEW_FIELDS:
        raise CorpusIntakeError("frozen record manipulation_check is incomplete or has unexpected fields")
    if not isinstance(manipulation_check.get("reviewer_id"), str):
        raise CorpusIntakeError("frozen record manipulation_check.reviewer_id must be text")
    _review_checks(record)
    for field in (*_HASH_FIELDS, "record_sha256"):
        value = record.get(field)
        if not isinstance(value, str) or _SHA256_RE.fullmatch(value) is None:
            raise CorpusIntakeError(f"frozen record {field} must be a lowercase SHA-256 hex digest")
    redacted = dict(record)
    expected = _sha256_json({key: value for key, value in redacted.items() if key != "record_sha256"})
    if redacted["record_sha256"] != expected:
        raise CorpusIntakeError("record_sha256 does not match the redacted record")
    return redacted


def _reject_raw_text_injection(value: Any) -> None:
    """Reject raw-text-shaped keys at every nesting level without echoing values."""
    if isinstance(value, Mapping):
        for key, nested in value.items():
            normalized_key = str(key).lower().replace("-", "_")
            if normalized_key in _RAW_TEXT_FIELDS or (
                "raw" in normalized_key and "text" in normalized_key
            ):
                raise CorpusIntakeError("raw-text-like fields are not allowed in frozen manifests")
            _reject_raw_text_injection(nested)
    elif isinstance(value, (list, tuple)):
        for nested in value:
            _reject_raw_text_injection(nested)


def _validate_freeze_metadata(frozen_at: str, freeze_reviewer_id: str) -> None:
    if not isinstance(frozen_at, str) or not frozen_at.strip() or frozen_at.strip().lower() in {
        "tbd",
        "unknown",
    }:
        raise CorpusIntakeError("frozen_at must be a non-placeholder ISO-8601 timestamp")
    _required_timestamp({"frozen_at": frozen_at}, "frozen_at")
    if not isinstance(freeze_reviewer_id, str) or not freeze_reviewer_id.strip() or freeze_reviewer_id.strip().lower() in {
        "tbd",
        "unknown",
        "none",
        "null",
    }:
        raise CorpusIntakeError("freeze_reviewer_id must be a non-placeholder reviewer id")


def freeze_validated_manifest(
    candidate: Mapping[str, Any], *, frozen_at: str, freeze_reviewer_id: str
) -> dict[str, Any]:
    """Freeze an already-built, redacted candidate without retaining source text."""
    if not isinstance(candidate, Mapping):
        raise CorpusIntakeError("candidate manifest must be an object")
    unexpected = set(candidate) - _CANDIDATE_FIELDS
    if unexpected:
        if unexpected & _RAW_TEXT_FIELDS:
            raise CorpusIntakeError("candidate manifest must remain redacted")
        raise CorpusIntakeError("candidate manifest has unexpected fields")
    _validate_freeze_metadata(frozen_at, freeze_reviewer_id)
    if candidate.get("schema_version") != SCHEMA_VERSION:
        raise CorpusIntakeError("candidate manifest has an unsupported schema_version")
    if candidate.get("status") != "validated_candidate":
        raise CorpusIntakeError("candidate manifest must have validated_candidate status")
    if candidate.get("raw_text_exported") is not False:
        raise CorpusIntakeError("candidate manifest raw_text_exported must be false")
    if type(candidate.get("expected_intents")) is not int or candidate.get("expected_intents") != 12:
        raise CorpusIntakeError("candidate manifest expected_intents must be exactly 12")
    if (
        type(candidate.get("minimum_projects")) is not int
        or candidate.get("minimum_projects") < 6
    ):
        raise CorpusIntakeError(
            "candidate manifest minimum_projects must be an integer >= 6"
        )
    records = [_validate_redacted_record(record) for record in candidate.get("records", [])]
    if len(records) != 12 or len(records) != candidate.get("record_count") or len(records) != candidate.get("unique_intent_count"):
        raise CorpusIntakeError("candidate manifest record counts are inconsistent")
    intent_ids = [str(record["source_intent_id"]) for record in records]
    if len(set(intent_ids)) != len(intent_ids):
        raise CorpusIntakeError("source_intent_id values must be unique")
    project_ids = {str(record["project_id"]) for record in records}
    if len(project_ids) < 6 or len(project_ids) != candidate.get("project_count"):
        raise CorpusIntakeError("candidate manifest project count is inconsistent")
    hash_values = [str(record[field]) for record in records for field in _HASH_FIELDS]
    if len(set(hash_values)) != len(hash_values):
        raise CorpusIntakeError("source hashes must be globally unique")
    frozen = {
        "schema_version": SCHEMA_VERSION,
        "status": "frozen",
        "record_count": len(records),
        "unique_intent_count": len(intent_ids),
        "project_count": len(project_ids),
        "minimum_projects": candidate.get("minimum_projects"),
        "expected_intents": candidate.get("expected_intents"),
        "raw_text_exported": False,
        "frozen_at": frozen_at,
        "freeze_reviewer_id": freeze_reviewer_id.strip(),
        "records": sorted(records, key=lambda row: str(row["source_intent_id"])),
    }
    if frozen["minimum_projects"] is None or frozen["expected_intents"] is None:
        raise CorpusIntakeError("candidate manifest count gates are required")
    frozen["manifest_sha256"] = _sha256_json(frozen)
    return frozen


def validate_private_records_against_frozen_manifest(
    records: Iterable[Mapping[str, Any]], frozen_manifest: Mapping[str, Any]
) -> list[dict[str, Any]]:
    """Verify private records and return their redacted, frozen-bound metadata join."""
    if not isinstance(frozen_manifest, Mapping) or frozen_manifest.get("status") != "frozen":
        raise CorpusIntakeError("frozen manifest must have frozen status")
    unexpected = set(frozen_manifest) - _FROZEN_FIELDS
    if unexpected:
        if unexpected & _RAW_TEXT_FIELDS:
            raise CorpusIntakeError("frozen manifest must remain redacted")
        raise CorpusIntakeError("frozen manifest has unexpected fields")
    if frozen_manifest.get("schema_version") != SCHEMA_VERSION:
        raise CorpusIntakeError("frozen manifest has an unsupported schema_version")
    if frozen_manifest.get("raw_text_exported") is not False:
        raise CorpusIntakeError("frozen manifest raw_text_exported must be false")
    _validate_freeze_metadata(
        frozen_manifest.get("frozen_at", ""),
        frozen_manifest.get("freeze_reviewer_id", ""),
    )
    expected_hash = frozen_manifest.get("manifest_sha256")
    unsigned = {key: value for key, value in frozen_manifest.items() if key != "manifest_sha256"}
    if not isinstance(expected_hash, str) or expected_hash != _sha256_json(unsigned):
        raise CorpusIntakeError("manifest_sha256 does not match the frozen manifest")
    if type(frozen_manifest.get("expected_intents")) is not int or frozen_manifest.get("expected_intents") != 12:
        raise CorpusIntakeError("frozen manifest expected_intents must be 12")
    if (
        type(frozen_manifest.get("minimum_projects")) is not int
        or frozen_manifest.get("minimum_projects") < 6
    ):
        raise CorpusIntakeError(
            "frozen manifest minimum_projects must be an integer >= 6"
        )
    frozen_rows = [_validate_redacted_record(row) for row in frozen_manifest.get("records", [])]
    frozen_intent_ids = [str(row["source_intent_id"]) for row in frozen_rows]
    frozen_project_ids = {str(row["project_id"]) for row in frozen_rows}
    if len(frozen_rows) != 12:
        raise CorpusIntakeError("frozen manifest must contain exactly 12 records")
    if len(set(frozen_intent_ids)) != len(frozen_intent_ids):
        raise CorpusIntakeError("frozen manifest source-intent IDs must be unique")
    if len(frozen_project_ids) < 6:
        raise CorpusIntakeError("frozen manifest must contain at least 6 projects")
    if frozen_manifest.get("record_count") != len(frozen_rows):
        raise CorpusIntakeError("frozen manifest record_count is inconsistent")
    if frozen_manifest.get("unique_intent_count") != len(frozen_intent_ids):
        raise CorpusIntakeError("frozen manifest unique_intent_count is inconsistent")
    if frozen_manifest.get("project_count") != len(frozen_project_ids):
        raise CorpusIntakeError("frozen manifest project_count is inconsistent")
    normalized = build_redacted_manifest(
        records,
        expected_intents=int(frozen_manifest["expected_intents"]),
        minimum_projects=int(frozen_manifest["minimum_projects"]),
    )
    frozen_records = {str(row["source_intent_id"]): row for row in frozen_rows}
    normalized_records = {
        str(row["source_intent_id"]): row for row in normalized["records"]
    }
    if set(normalized_records) != set(frozen_records):
        raise CorpusIntakeError("private records source-intent IDs do not match frozen manifest")
    join: list[dict[str, Any]] = []
    for intent_id in sorted(frozen_records):
        expected = frozen_records[intent_id]
        actual = normalized_records[intent_id]
        for field in ("project_id", *_HASH_FIELDS, "rights_review", "record_sha256"):
            if actual.get(field) != expected.get(field):
                raise CorpusIntakeError(f"private record {field} does not match frozen manifest")
        join.append(dict(actual))
    return join


__all__ = [
    "CorpusIntakeError",
    "SCHEMA_VERSION",
    "REQUIRED_RIGHTS_ASSERTIONS",
    "build_redacted_manifest",
    "freeze_validated_manifest",
    "load_private_records",
    "validate_private_records_against_frozen_manifest",
]
