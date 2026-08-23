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


def validate_agent_execution(
    execution: AgentExecution,
    *,
    not_before: str | None = None,
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
                }
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
