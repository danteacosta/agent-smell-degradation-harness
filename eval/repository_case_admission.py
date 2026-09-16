"""Fail-closed admission for repository-level behavioral experiment cases.

This module validates evidence bindings only.  Passing the gate does not prove
that a requirement interpretation is valid and does not make a case
confirmatory; the named human reviews remain separate scientific controls.
"""
from __future__ import annotations

import argparse
from datetime import datetime
import hashlib
import json
from pathlib import PurePosixPath, Path
import re
from urllib.parse import urlparse


SCHEMA_VERSION = "repository-e2e-case/v1"
CASE_KEYS = {
    "schema_version", "case_id", "project_id", "repository_url",
    "source_revision_url", "source_revision_id", "requirement_locator",
    "requirement_sha256", "base_commit", "gold_commit",
    "implementation_paths", "upstream_test_paths", "observable_interface",
    "interaction_contract", "target_constraint_id",
    "clean_requirement_sha256", "rewrite_control_requirement_sha256",
    "smelly_requirement_sha256", "changed_span_sha256", "scaffold_sha256",
    "shared_oracle_sha256", "oracle_frozen_at",
    "variant_assignment_frozen_at", "test_generation_source",
    "same_oracle_for_all_variants", "same_scaffold_for_all_variants",
    "rewrite_control_preserves_intent", "gold_passed", "mutation_killed",
    "gold_run_receipt_sha256", "mutant_run_receipt_sha256", "reviews", "status",
}
INTERACTION_KEYS = {"initial_state", "action", "observable_outcome"}
REVIEW_KEYS = {
    "mapping_review", "manipulation_review", "oracle_review", "rights_review",
}
REVIEW_RECORD_KEYS = {"status", "reviewer_id", "evidence_sha256"}
REVIEW_STATES = {"pending", "approved", "rejected"}
CASE_STATES = {"screening", "eligible", "rejected"}
INTERFACES = {"browser", "http_api", "cli", "desktop_ui"}
SHA40 = re.compile(r"[0-9a-f]{40}")
SHA256 = re.compile(r"[0-9a-f]{64}")
FORBIDDEN_ORACLE_KEYS = {
    "clean_oracle", "smelly_oracle", "oracle_by_variant",
    "variant_oracle", "per_variant_oracle",
}


def _require_exact_keys(value: dict, expected: set[str], label: str) -> None:
    observed = set(value)
    if observed != expected:
        missing = sorted(expected - observed)
        extra = sorted(observed - expected)
        raise ValueError(f"{label} keys mismatch; missing={missing}, extra={extra}")


def _text(value: object, label: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{label} must contain text")
    if any(ord(character) < 32 for character in value):
        raise ValueError(f"{label} must not contain control characters")
    return value.strip()


def _hash(value: object, pattern: re.Pattern[str], label: str) -> str:
    text = _text(value, label)
    if pattern.fullmatch(text) is None:
        raise ValueError(f"{label} must be a lowercase hexadecimal digest")
    return text


def _timestamp(value: object, label: str) -> datetime:
    text = _text(value, label)
    try:
        parsed = datetime.fromisoformat(text.replace("Z", "+00:00"))
    except ValueError as error:
        raise ValueError(f"{label} must be an RFC 3339 timestamp") from error
    if parsed.tzinfo is None or parsed.utcoffset() is None:
        raise ValueError(f"{label} must include a timezone")
    return parsed


def _paths(value: object, label: str) -> list[str]:
    if not isinstance(value, list) or not value:
        raise ValueError(f"{label} must be a non-empty list")
    paths: list[str] = []
    for index, item in enumerate(value):
        text = _text(item, f"{label}[{index}]")
        path = PurePosixPath(text)
        if path.is_absolute() or text != path.as_posix() or any(
                part in {"", ".", ".."} for part in path.parts):
            raise ValueError(f"{label}[{index}] must be a normalized relative path")
        paths.append(text)
    if len(paths) != len(set(paths)):
        raise ValueError(f"{label} must not contain duplicates")
    return paths


def _reject_variant_oracles(value: object) -> None:
    if isinstance(value, dict):
        for key, nested in value.items():
            normalized = str(key).strip().lower().replace("-", "_")
            if normalized in FORBIDDEN_ORACLE_KEYS:
                raise ValueError("variant-specific oracles are forbidden")
            _reject_variant_oracles(nested)
    elif isinstance(value, list):
        for nested in value:
            _reject_variant_oracles(nested)


def assess_repository_case(case: dict) -> dict:
    """Validate one case and report every unresolved admission blocker."""
    if not isinstance(case, dict):
        raise ValueError("repository case must be an object")
    _reject_variant_oracles(case)
    _require_exact_keys(case, CASE_KEYS, "repository case")
    if case["schema_version"] != SCHEMA_VERSION:
        raise ValueError("unsupported repository case schema")

    case_id = _text(case["case_id"], "case_id")
    _text(case["project_id"], "project_id")
    repository_url = _text(case["repository_url"], "repository_url")
    source_url = _text(case["source_revision_url"], "source_revision_url")
    for label, url in (("repository_url", repository_url),
                       ("source_revision_url", source_url)):
        parsed = urlparse(url)
        if parsed.scheme != "https" or parsed.netloc != "github.com":
            raise ValueError(f"{label} must be an HTTPS GitHub URL")

    source_revision = _hash(case["source_revision_id"], SHA40,
                            "source_revision_id")
    repository_path = urlparse(repository_url).path.rstrip("/")
    expected_source_prefix = f"{repository_path}/blob/{source_revision}/"
    source_path = urlparse(source_url).path
    if (len(PurePosixPath(repository_path).parts) != 3
            or not source_path.startswith(expected_source_prefix)):
        raise ValueError("source_revision_url must bind repository and source_revision_id")
    _text(case["requirement_locator"], "requirement_locator")
    _hash(case["requirement_sha256"], SHA256, "requirement_sha256")
    base_commit = _hash(case["base_commit"], SHA40, "base_commit")
    gold_commit = _hash(case["gold_commit"], SHA40, "gold_commit")
    if base_commit == gold_commit:
        raise ValueError("base_commit and gold_commit must differ")
    _paths(case["implementation_paths"], "implementation_paths")
    _paths(case["upstream_test_paths"], "upstream_test_paths")

    if case["observable_interface"] not in INTERFACES:
        raise ValueError("unsupported observable_interface")
    interaction = case["interaction_contract"]
    if not isinstance(interaction, dict):
        raise ValueError("interaction_contract must be an object")
    _require_exact_keys(interaction, INTERACTION_KEYS, "interaction_contract")
    for key in sorted(INTERACTION_KEYS):
        _text(interaction[key], f"interaction_contract.{key}")
    _text(case["target_constraint_id"], "target_constraint_id")

    requirement_hashes = {
        label: _hash(case[label], SHA256, label)
        for label in (
            "clean_requirement_sha256",
            "rewrite_control_requirement_sha256",
            "smelly_requirement_sha256",
        )
    }
    if len(set(requirement_hashes.values())) != len(requirement_hashes):
        raise ValueError("clean, rewrite-control and smelly requirements must differ")
    _hash(case["changed_span_sha256"], SHA256, "changed_span_sha256")
    _hash(case["scaffold_sha256"], SHA256, "scaffold_sha256")
    _hash(case["shared_oracle_sha256"], SHA256, "shared_oracle_sha256")
    oracle_frozen = _timestamp(case["oracle_frozen_at"], "oracle_frozen_at")
    assignment_frozen = _timestamp(
        case["variant_assignment_frozen_at"], "variant_assignment_frozen_at")
    if assignment_frozen < oracle_frozen:
        raise ValueError("variant assignment must not precede oracle freeze")

    for key in (
            "same_oracle_for_all_variants", "same_scaffold_for_all_variants",
            "rewrite_control_preserves_intent", "gold_passed", "mutation_killed"):
        if type(case[key]) is not bool:
            raise ValueError(f"{key} must be a boolean")
    for result_field, receipt_field in (
            ("gold_passed", "gold_run_receipt_sha256"),
            ("mutation_killed", "mutant_run_receipt_sha256")):
        receipt = case[receipt_field]
        if case[result_field]:
            _hash(receipt, SHA256, receipt_field)
        elif receipt is not None:
            raise ValueError(f"{receipt_field} must be null when {result_field} is false")
    reviews = case["reviews"]
    if not isinstance(reviews, dict):
        raise ValueError("reviews must be an object")
    _require_exact_keys(reviews, REVIEW_KEYS, "reviews")
    for name, record in reviews.items():
        if not isinstance(record, dict):
            raise ValueError(f"reviews.{name} must be an object")
        _require_exact_keys(record, REVIEW_RECORD_KEYS, f"reviews.{name}")
        state = record["status"]
        if state not in REVIEW_STATES:
            raise ValueError(f"reviews.{name} has an unsupported state")
        if state == "pending":
            if record["reviewer_id"] is not None or record["evidence_sha256"] is not None:
                raise ValueError(f"pending reviews.{name} must not claim evidence")
        else:
            _text(record["reviewer_id"], f"reviews.{name}.reviewer_id")
            _hash(record["evidence_sha256"], SHA256,
                  f"reviews.{name}.evidence_sha256")
    if case["status"] not in CASE_STATES:
        raise ValueError("unsupported repository case status")

    blockers: list[str] = []
    if case["test_generation_source"] != "canonical_complete_requirement_only":
        blockers.append("tests_not_generated_from_canonical_complete_requirement")
    if not case["same_oracle_for_all_variants"]:
        blockers.append("oracle_not_shared_across_variants")
    if not case["same_scaffold_for_all_variants"]:
        blockers.append("scaffold_not_shared_across_variants")
    if not case["rewrite_control_preserves_intent"]:
        blockers.append("rewrite_control_not_intent_preserving")
    if not case["gold_passed"]:
        blockers.append("gold_implementation_not_verified")
    if not case["mutation_killed"]:
        blockers.append("oracle_did_not_kill_targeted_mutant")
    for review in sorted(REVIEW_KEYS):
        if reviews[review]["status"] != "approved":
            blockers.append(f"{review}:{reviews[review]['status']}")
    if case["status"] != "eligible":
        blockers.append(f"case_status:{case['status']}")

    canonical = json.dumps(case, ensure_ascii=False, sort_keys=True,
                           separators=(",", ":")).encode()
    return {
        "schema_version": "repository-e2e-admission/v1",
        "case_id": case_id,
        "eligible": not blockers,
        "blockers": blockers,
        "manifest_sha256": hashlib.sha256(canonical).hexdigest(),
        "scientific_claim": "admission_control_only",
    }


def admit_repository_case(case: dict) -> dict:
    """Return an assessment only for an eligible case; otherwise fail closed."""
    result = assess_repository_case(case)
    if not result["eligible"]:
        raise ValueError("repository case is not eligible: " + ", ".join(result["blockers"]))
    return result


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--manifest", type=Path, required=True)
    args = parser.parse_args()
    try:
        case = json.loads(args.manifest.read_text(encoding="utf-8"))
        result = assess_repository_case(case)
    except (OSError, json.JSONDecodeError, ValueError) as error:
        parser.error(str(error))
    print(json.dumps(result, sort_keys=True))
    return 0 if result["eligible"] else 2


if __name__ == "__main__":
    raise SystemExit(main())
