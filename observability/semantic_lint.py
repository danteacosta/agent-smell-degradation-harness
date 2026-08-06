"""Deterministic semantic-quality checks for experiment artifacts."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

_LABEL_KEYS = {"oracle", "oracle_verdict", "label", "ground_truth", "outcome", "adjudication"}
_SECRET_PARTS = ("api_key", "secret", "token", "password")


@dataclass(frozen=True)
class Finding:
    code: str
    severity: str
    message: str
    source: str


def lint_event(event: dict[str, Any]) -> list[Finding]:
    findings: list[Finding] = []
    refs = event.get("source_refs") or event.get("attributes", {}).get("source_refs")
    if not refs:
        findings.append(Finding("missing_source_refs", "error", "event has no source references", "event"))
    plane = event.get("plane") or event.get("attributes", {}).get("plane")
    if plane == "pre_final" and (_contains_key(event, _LABEL_KEYS) or _contains_alias(event)):
        findings.append(Finding("cross_plane_label", "error", "pre_final event contains label-plane data", "event"))
    if _contains_secret_key(event):
        findings.append(Finding("secret_like_field", "error", "event contains a secret-like field", "event"))
    return findings


def validate_events(events: list[dict[str, Any]], *, strict: bool = False) -> list[Finding]:
    findings = [finding for event in events for finding in lint_event(event)]
    if strict and findings:
        raise ValueError(", ".join(sorted({finding.code for finding in findings})))
    return findings


def _contains_key(value: Any, keys: set[str]) -> bool:
    if isinstance(value, dict):
        return any(key in keys or _contains_key(item, keys) for key, item in value.items())
    if isinstance(value, list):
        return any(_contains_key(item, keys) for item in value)
    return False


def _contains_secret_key(value: Any) -> bool:
    if isinstance(value, dict):
        return any(any(part in str(key).lower() for part in _SECRET_PARTS) or _contains_secret_key(item) for key, item in value.items())
    if isinstance(value, list):
        return any(_contains_secret_key(item) for item in value)
    return False


def _contains_alias(value: Any) -> bool:
    if isinstance(value, dict):
        return any("groundtruth" in str(key).lower().replace("-", "_") or "outcome" in str(key).lower() for key in value) or any(
            _contains_alias(item) for item in value.values()
        )
    if isinstance(value, list):
        return any(_contains_alias(item) for item in value)
    return False
