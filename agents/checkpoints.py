"""Versioned, externally materialized pre-final checkpoint summaries.

``runtime_native`` denotes events emitted by the instrumented runtime during
the episode.  It never denotes model chain-of-thought or privileged hidden
state.
"""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from datetime import datetime
from typing import Any

from protocol.atomic_obligations import (
    validate_atomic_obligation_observations,
    validate_atomic_obligations,
)
from protocol.conditional_semantics import validate_conditional_semantics

CHECKPOINT_SCHEMA_VERSION = "pre-final/v1"
REQUIRED_SECTIONS = ("interpretation", "plan", "execution")
SECTION_FIELDS = {
    "interpretation": (
        "constraints",
        "quantities",
        "unresolved_references",
        "assumptions",
        "contradictions",
        "conditional_semantics",
        "atomic_obligations",
    ),
    "plan": ("validation_checks", "planned_tools", "coverage_targets"),
    "execution": (
        "revisions",
        "validation_attempts",
        "errors",
        "retrieval_events",
        "constraint_lineage",
        "context_management",
        "atomic_obligation_observations",
    ),
}
CHECKPOINT_ORDER = (
    "interpretation.completed",
    "plan.completed",
    "execution.started",
    "tool.completed",
)


@dataclass(frozen=True)
class CheckpointObservation:
    checkpoint: str
    payload: Mapping[str, Any]
    started_at: str
    ended_at: str
    provenance: str = "runtime_native"


@dataclass(frozen=True)
class AgentExecution:
    checkpoints: tuple[CheckpointObservation, ...]
    artifact: Mapping[str, Any]
    provider_meta: Mapping[str, Any]


def validate_checkpoint_payload(
    payload: Mapping[str, Any],
    *,
    require_conditional_semantics: bool = False,
    require_constraint_lineage: bool = False,
    require_atomic_obligations: bool = False,
) -> dict[str, dict[str, Any]]:
    """Validate and normalize a provider checkpoint payload.

    Only the versioned allowlist is admitted to the feature plane. Unknown
    fields are rejected so provider responses cannot smuggle experiment or
    terminal metadata into confirmatory traces. The atomic-obligation fields
    are additive and can be normalized for legacy development traces.
    """

    if set(payload) != set(REQUIRED_SECTIONS):
        raise ValueError("provider checkpoints must contain interpretation, plan, and execution")
    optional_fields = {
        "interpretation": {"conditional_semantics", "atomic_obligations"},
        "execution": {
            "constraint_lineage",
            "context_management",
            "atomic_obligation_observations",
        },
    }
    normalized: dict[str, dict[str, Any]] = {}
    for section in REQUIRED_SECTIONS:
        value = payload[section]
        if not isinstance(value, Mapping):
            raise ValueError(f"checkpoint section {section} must be an object")
        allowed = set(SECTION_FIELDS[section])
        required = allowed - optional_fields.get(section, set())
        present = set(value)
        if present - allowed or not required.issubset(present):
            raise ValueError(f"checkpoint section {section} has an invalid field set")
        if (
            require_conditional_semantics
            and section == "interpretation"
            and "conditional_semantics" not in present
        ):
            raise ValueError("interpretation.conditional_semantics is required")
        if (
            require_constraint_lineage
            and section == "execution"
            and "constraint_lineage" not in present
        ):
            raise ValueError("execution.constraint_lineage is required")
        if (
            require_atomic_obligations
            and section == "interpretation"
            and "atomic_obligations" not in present
        ):
            raise ValueError("interpretation.atomic_obligations is required")
        if (
            require_atomic_obligations
            and section == "execution"
            and "atomic_obligation_observations" not in present
        ):
            raise ValueError("execution.atomic_obligation_observations is required")
        row = dict(value)
        for field in optional_fields.get(section, set()):
            row.setdefault(field, [])
        for field in SECTION_FIELDS[section]:
            if field in {"revisions", "validation_attempts", "retrieval_events"}:
                if not isinstance(row[field], int) or row[field] < 0:
                    raise ValueError(
                        f"checkpoint field {section}.{field} must be a non-negative integer"
                    )
            elif section == "interpretation" and field == "conditional_semantics":
                try:
                    row[field] = validate_conditional_semantics(row[field])
                except ValueError as error:
                    raise ValueError(str(error)) from error
            elif section == "interpretation" and field == "atomic_obligations":
                try:
                    row[field] = validate_atomic_obligations(
                        row[field], row["constraints"]
                    )
                except ValueError as error:
                    raise ValueError(str(error)) from error
            elif section == "execution" and field == "constraint_lineage":
                row[field] = _validate_constraint_lineage(row[field])
            elif section == "execution" and field == "context_management":
                row[field] = _validate_context_management(row[field])
            elif section == "execution" and field == "atomic_obligation_observations":
                try:
                    row[field] = validate_atomic_obligation_observations(
                        row[field],
                        constraint_lineage=row.get("constraint_lineage"),
                    )
                except ValueError as error:
                    raise ValueError(str(error)) from error
            elif not isinstance(row[field], list):
                raise ValueError(f"checkpoint field {section}.{field} must be a list")
        normalized[section] = row
    return normalized


def _validate_constraint_lineage(value: Any) -> list[dict[str, Any]]:
    """Validate a bounded pre-final lineage without accepting T4 evidence."""

    if not isinstance(value, list):
        raise ValueError("checkpoint field execution.constraint_lineage must be a list")
    forbidden = {"artifact", "criterion", "label", "oracle", "outcome", "final"}
    normalized: list[dict[str, Any]] = []
    seen: set[str] = set()
    for entry in value:
        if not isinstance(entry, Mapping) or set(entry) != {
            "constraint_id", "constraint_sha256", "planned_check_ids", "observation_id", "status", "available_at"
        }:
            raise ValueError("constraint lineage entries have an invalid field set")
        if any(key in forbidden for key in entry):
            raise ValueError("constraint lineage cannot contain terminal evidence")
        constraint_id = str(entry["constraint_id"]).strip()
        digest = str(entry["constraint_sha256"]).strip()
        checks = entry["planned_check_ids"]
        observation_id = str(entry["observation_id"]).strip()
        status = str(entry["status"])
        available_at = str(entry["available_at"])
        if not constraint_id or constraint_id in seen or len(digest) != 64:
            raise ValueError("constraint lineage requires unique IDs and SHA-256 hashes")
        if not isinstance(checks, list) or any(not isinstance(item, str) or not item.strip() for item in checks):
            raise ValueError("constraint lineage planned_check_ids must be a list of IDs")
        if not observation_id or status not in {"covered", "uncovered"} or available_at != "T3":
            raise ValueError("constraint lineage has invalid pre-final status metadata")
        seen.add(constraint_id)
        normalized.append({
            "constraint_id": constraint_id,
            "constraint_sha256": digest,
            "planned_check_ids": list(checks),
            "observation_id": observation_id,
            "status": status,
            "available_at": available_at,
        })
    return normalized


_CONTEXT_EVENT_FIELDS = {
    "schema_version",
    "event_id",
    "stage",
    "operation",
    "trigger",
    "started_at",
    "ended_at",
    "context_size_before",
    "context_size_after",
    "context_size_unit",
    "checkpoint_id",
    "checkpoint_sha256",
}
_CONTEXT_OPERATIONS = {"none", "compact", "decompose", "retrieve", "evict", "truncate"}


def _validate_context_management(value: Any) -> list[dict[str, Any]]:
    """Validate prompt-free context-management events at the T3 boundary."""

    if not isinstance(value, list):
        raise ValueError("checkpoint field execution.context_management must be a list")
    normalized: list[dict[str, Any]] = []
    seen: set[str] = set()
    for entry in value:
        if not isinstance(entry, Mapping) or set(entry) != _CONTEXT_EVENT_FIELDS:
            raise ValueError("context-management entries have an invalid field set")
        if entry["schema_version"] != "context-management/v1":
            raise ValueError("context-management event has an unsupported schema version")
        event_id = str(entry["event_id"]).strip()
        stage = str(entry["stage"]).strip()
        operation = str(entry["operation"]).strip()
        trigger = str(entry["trigger"]).strip()
        checkpoint_id = str(entry["checkpoint_id"]).strip()
        digest = str(entry["checkpoint_sha256"]).strip()
        if not event_id or event_id in seen or not stage or not trigger or not checkpoint_id:
            raise ValueError("context-management events require unique IDs and non-empty metadata")
        if operation not in _CONTEXT_OPERATIONS:
            raise ValueError("context-management event has an unsupported operation")
        if len(digest) != 64 or any(char not in "0123456789abcdef" for char in digest):
            raise ValueError("context-management event requires a SHA-256 checkpoint hash")
        try:
            started_at = datetime.fromisoformat(str(entry["started_at"]))
            ended_at = datetime.fromisoformat(str(entry["ended_at"]))
        except ValueError as error:
            raise ValueError("context-management timestamps must be ISO-8601") from error
        if (
            started_at.tzinfo is None
            or ended_at.tzinfo is None
            or ended_at < started_at
        ):
            raise ValueError("context-management timestamps must be timezone-aware and monotonic")
        before = entry["context_size_before"]
        after = entry["context_size_after"]
        if (
            isinstance(before, bool)
            or not isinstance(before, int)
            or before < 0
            or isinstance(after, bool)
            or not isinstance(after, int)
            or after < 0
            or after > before
        ):
            raise ValueError("context-management sizes must be non-negative and non-expanding")
        if entry["context_size_unit"] != "utf8_bytes":
            raise ValueError("context-management currently requires context_size_unit=utf8_bytes")
        seen.add(event_id)
        normalized.append({
            "schema_version": "context-management/v1",
            "event_id": event_id,
            "stage": stage,
            "operation": operation,
            "trigger": trigger,
            "started_at": str(entry["started_at"]),
            "ended_at": str(entry["ended_at"]),
            "context_size_before": before,
            "context_size_after": after,
            "context_size_unit": "utf8_bytes",
            "checkpoint_id": checkpoint_id,
            "checkpoint_sha256": digest,
        })
    return normalized


def validate_agent_execution(
    execution: AgentExecution,
    *,
    not_before: str | None = None,
    require_conditional_semantics: bool = False,
    require_constraint_lineage: bool = False,
    require_atomic_obligations: bool = False,
) -> AgentExecution:
    if tuple(observation.checkpoint for observation in execution.checkpoints) != CHECKPOINT_ORDER:
        raise ValueError("runtime checkpoints must follow interpretation, plan, execution start, and tool completion")
    previous_end: datetime | None = None
    if not_before is not None:
        previous_end = datetime.fromisoformat(not_before)
        if previous_end.tzinfo is None:
            raise ValueError("not_before timestamp must include a timezone")
    section_by_checkpoint = {
        "interpretation.completed": "interpretation",
        "plan.completed": "plan",
        "tool.completed": "execution",
    }
    normalized: list[CheckpointObservation] = []
    for observation in execution.checkpoints:
        if observation.provenance != "runtime_native":
            raise ValueError(f"checkpoint {observation.checkpoint} is not runtime-native")
        try:
            started_at = datetime.fromisoformat(observation.started_at)
            ended_at = datetime.fromisoformat(observation.ended_at)
        except ValueError as error:
            raise ValueError("checkpoint timestamps must be ISO-8601") from error
        if started_at.tzinfo is None or ended_at.tzinfo is None:
            raise ValueError("checkpoint timestamps must include a timezone")
        if ended_at < started_at or (previous_end is not None and started_at < previous_end):
            raise ValueError("runtime checkpoint timestamps must be monotonic")
        previous_end = ended_at
        section = section_by_checkpoint.get(observation.checkpoint)
        if section is None:
            if observation.payload:
                raise ValueError("execution.started payload must be empty")
            payload: Mapping[str, Any] = {}
        else:
            payload = validate_checkpoint_payload(
                {
                    key: observation.payload if key == section else _empty_section(key)
                    for key in REQUIRED_SECTIONS
                },
                require_conditional_semantics=require_conditional_semantics,
                require_constraint_lineage=require_constraint_lineage,
                require_atomic_obligations=require_atomic_obligations,
            )[section]
        normalized.append(
            CheckpointObservation(
                observation.checkpoint,
                payload,
                observation.started_at,
                observation.ended_at,
                observation.provenance,
            )
        )
    if not isinstance(execution.artifact, Mapping):
        raise ValueError("runtime execution artifact must be an object")
    if not isinstance(execution.provider_meta, Mapping):
        raise ValueError("runtime execution metadata must be an object")
    return AgentExecution(tuple(normalized), dict(execution.artifact), dict(execution.provider_meta))


def _empty_section(section: str) -> dict[str, Any]:
    return {
        field: 0 if field in {"revisions", "validation_attempts", "retrieval_events"} else []
        for field in SECTION_FIELDS[section]
    }


__all__ = (
    "AgentExecution",
    "CHECKPOINT_ORDER",
    "CHECKPOINT_SCHEMA_VERSION",
    "CheckpointObservation",
    "REQUIRED_SECTIONS",
    "validate_agent_execution",
    "validate_checkpoint_payload",
)
