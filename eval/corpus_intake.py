"""Validate private corpus intake and emit a redacted admission manifest.

Raw requirements remain outside the repository.  The emitted manifest contains
only provenance, review decisions, and SHA-256 digests, so it can be versioned
without redistributing source text or accidentally exposing an annotation
target.
"""

from __future__ import annotations

import hashlib
import json
from datetime import datetime
from pathlib import Path
from typing import Any, Iterable, Mapping
from urllib.parse import urlparse

SCHEMA_VERSION = "prepilot-corpus/v4"
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
    reviewer = str(raw.get("reviewer_id", "")).strip()
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
    reviewer_id = str(raw.get("reviewer_id", "")).strip()
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
    source_revision_url = _required_url(record, "source_revision_url")
    source_revision_id = _required_id(record, "source_revision_id")
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
        "source_revision_url": source_revision_url,
        "source_revision_id": source_revision_id,
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
    if expected_intents <= 0 or minimum_projects <= 0:
        raise CorpusIntakeError("corpus count gates must be positive")
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


__all__ = [
    "CorpusIntakeError",
    "SCHEMA_VERSION",
    "REQUIRED_RIGHTS_ASSERTIONS",
    "build_redacted_manifest",
    "load_private_records",
]
