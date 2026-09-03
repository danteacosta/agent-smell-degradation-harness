"""Fingerprints for the exact exploratory generation and judging protocol.

The hashes are computed from runtime-owned constants and the frozen rubric.
They are checked during preflight, before a provider adapter is constructed or
any network request is allowed.
"""

from __future__ import annotations

import hashlib
import json
from collections.abc import Mapping
from pathlib import Path
from typing import Any

from agents.staged_runtime import GENERATION_OUTPUT_SCHEMA, GENERATION_PROMPT_TEMPLATES
from label_plane.exploratory_judge import JUDGE_PROMPT_TEMPLATE, JUDGE_RESPONSE_SCHEMA


SCHEMA_VERSION = "exploratory-protocol-hashes/v1"
DEFAULT_RUBRIC_PATH = Path("tasks/acceptance_criteria_llm_judge_rubric.json")
HASH_FIELDS = (
    "generation_prompt_template_sha256",
    "judge_prompt_template_sha256",
    "generation_output_schema_sha256",
    "judge_response_schema_sha256",
    "rubric_sha256",
)


class ProtocolHashError(ValueError):
    """Raised when a frozen protocol fingerprint does not match the runtime."""


def _normalize_newlines(value: Any) -> Any:
    if isinstance(value, str):
        return value.replace("\r\n", "\n").replace("\r", "\n")
    if isinstance(value, Mapping):
        return {
            _normalize_newlines(key): _normalize_newlines(nested)
            for key, nested in value.items()
        }
    if isinstance(value, (list, tuple)):
        return [_normalize_newlines(nested) for nested in value]
    return value


def canonical_json_bytes(value: Any) -> bytes:
    """Serialize protocol inputs deterministically as canonical UTF-8 bytes."""

    normalized = _normalize_newlines(value)
    try:
        text = json.dumps(
            normalized,
            ensure_ascii=False,
            sort_keys=True,
            separators=(",", ":"),
            allow_nan=False,
        )
    except (TypeError, ValueError) as error:
        raise ProtocolHashError("protocol input is not canonicalizable") from error
    return text.encode("utf-8")


def sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def sha256_text(value: str) -> str:
    if not isinstance(value, str):
        raise ProtocolHashError("text protocol input must be a string")
    return sha256_bytes(_normalize_newlines(value).encode("utf-8"))


def sha256_json(value: Any) -> str:
    return sha256_bytes(canonical_json_bytes(value))


def _rubric_path(repository_root: str | Path | None) -> Path:
    root = Path(repository_root) if repository_root is not None else Path.cwd()
    return root / DEFAULT_RUBRIC_PATH


def _load_rubric(repository_root: str | Path | None) -> Any:
    path = _rubric_path(repository_root)
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as error:
        raise ProtocolHashError(f"cannot read frozen judge rubric: {path}") from error


def build_protocol_hashes(repository_root: str | Path | None = None) -> dict[str, str]:
    """Recompute every frozen protocol hash from its source of truth."""

    return {
        "generation_prompt_template_sha256": sha256_json(
            GENERATION_PROMPT_TEMPLATES
        ),
        "judge_prompt_template_sha256": sha256_text(JUDGE_PROMPT_TEMPLATE),
        "generation_output_schema_sha256": sha256_json(GENERATION_OUTPUT_SCHEMA),
        "judge_response_schema_sha256": sha256_json(JUDGE_RESPONSE_SCHEMA),
        "rubric_sha256": sha256_json(_load_rubric(repository_root)),
    }


def verify_protocol_hashes(
    expected: Mapping[str, Any],
    *,
    repository_root: str | Path | None = None,
) -> dict[str, str]:
    """Fail closed when any frozen protocol input differs from the runtime."""

    if not isinstance(expected, Mapping) or set(expected) != set(HASH_FIELDS):
        raise ProtocolHashError("frozen protocol hashes have an invalid field set")
    actual = build_protocol_hashes(repository_root)
    mismatches = [
        field for field in HASH_FIELDS
        if not isinstance(expected[field], str) or expected[field] != actual[field]
    ]
    if mismatches:
        raise ProtocolHashError(
            "frozen protocol hash mismatch: " + ", ".join(sorted(mismatches))
        )
    return actual


__all__ = [
    "DEFAULT_RUBRIC_PATH",
    "GENERATION_OUTPUT_SCHEMA",
    "GENERATION_PROMPT_TEMPLATES",
    "HASH_FIELDS",
    "JUDGE_PROMPT_TEMPLATE",
    "JUDGE_RESPONSE_SCHEMA",
    "ProtocolHashError",
    "build_protocol_hashes",
    "canonical_json_bytes",
    "sha256_bytes",
    "sha256_json",
    "sha256_text",
    "verify_protocol_hashes",
]
