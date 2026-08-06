"""Versioned, provider-produced pre-final checkpoint summaries."""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any

CHECKPOINT_SCHEMA_VERSION = "pre-final/v1"
REQUIRED_SECTIONS = ("interpretation", "plan", "execution")
SECTION_FIELDS = {
    "interpretation": (
        "constraints",
        "quantities",
        "unresolved_references",
        "assumptions",
        "contradictions",
    ),
    "plan": ("validation_checks", "planned_tools", "coverage_targets"),
    "execution": ("revisions", "validation_attempts", "errors", "retrieval_events"),
}


def validate_checkpoint_payload(payload: Mapping[str, Any]) -> dict[str, dict[str, Any]]:
    """Validate and normalize a provider checkpoint payload.

    Only the versioned allowlist is admitted to the feature plane. Unknown
    fields are rejected so provider responses cannot smuggle experiment or
    terminal metadata into confirmatory traces.
    """

    if set(payload) != set(REQUIRED_SECTIONS):
        raise ValueError("provider checkpoints must contain interpretation, plan, and execution")
    normalized: dict[str, dict[str, Any]] = {}
    for section in REQUIRED_SECTIONS:
        value = payload[section]
        if not isinstance(value, Mapping):
            raise ValueError(f"checkpoint section {section} must be an object")
        allowed = set(SECTION_FIELDS[section])
        if set(value) != allowed:
            raise ValueError(f"checkpoint section {section} has an invalid field set")
        row = dict(value)
        for field in SECTION_FIELDS[section]:
            if field in {"revisions", "validation_attempts", "retrieval_events"}:
                if not isinstance(row[field], int) or row[field] < 0:
                    raise ValueError(f"checkpoint field {section}.{field} must be a non-negative integer")
            elif not isinstance(row[field], list):
                raise ValueError(f"checkpoint field {section}.{field} must be a list")
        normalized[section] = row
    return normalized


__all__ = ("CHECKPOINT_SCHEMA_VERSION", "REQUIRED_SECTIONS", "validate_checkpoint_payload")
