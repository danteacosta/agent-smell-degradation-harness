"""Build the blinded, deterministic call inventory for the exploratory pre-pilot."""

from __future__ import annotations

import base64
import hashlib
import hmac
import json
import secrets
from dataclasses import dataclass
from pathlib import Path
from random import Random
from typing import Any, Iterable, Mapping


@dataclass(frozen=True)
class ReferenceConstraint:
    constraint_id: str
    text: str

    def to_public_dict(self) -> dict[str, str]:
        return {"constraint_id": self.constraint_id, "text": self.text}


@dataclass(frozen=True)
class PublicEpisode:
    episode_id: str


@dataclass(frozen=True)
class PublicArtifact:
    artifact_id: str


@dataclass(frozen=True)
class PublicBaseTask:
    base_task_id: str
    artifact_id: str


@dataclass(frozen=True)
class PublicOccurrence:
    occurrence_id: str
    base_task_id: str
    duplicate: bool


@dataclass(frozen=True)
class _PrivateJoin:
    episode_id: str
    artifact_id: str
    base_task_id: str
    source_intent_id: str
    variant_index: int
    replication_index: int
    provider_slot_id: str


@dataclass(frozen=True)
class _PrivateReferenceConstraint:
    constraint_id: str
    text: str
    source_intent_id: str


@dataclass(frozen=True)
class ExploratoryCallPlan:
    episodes: tuple[PublicEpisode, ...]
    artifacts: tuple[PublicArtifact, ...]
    base_tasks: tuple[PublicBaseTask, ...]
    occurrences: tuple[PublicOccurrence, ...]
    duplicate_occurrences: tuple[PublicOccurrence, ...]
    reference_constraints: tuple[ReferenceConstraint, ...]
    max_attempts_per_api_call: int = 2
    _private_join: tuple[_PrivateJoin, ...] = ()
    _run_nonce: bytes = b""

    @property
    def duplicate_base_task_count(self) -> int:
        return len(self.duplicate_occurrences)

    @property
    def judging_occurrence_count_per_judge(self) -> int:
        return len(self.occurrences)

    @property
    def logical_judging_calls(self) -> int:
        return len(self.occurrences) * 2

    @property
    def logical_operations(self) -> int:
        return len(self.artifacts) + self.logical_judging_calls

    @property
    def provider_api_calls(self) -> int:
        return len(self.artifacts) * 3 + self.logical_judging_calls

    def to_public_dict(self) -> dict[str, Any]:
        """Return the blinded plan; private joins and nonce are intentionally omitted."""
        return {
            "schema_version": "exploratory-call-plan/v1",
            "episodes": [{"episode_id": item.episode_id} for item in self.episodes],
            "artifacts": [{"artifact_id": item.artifact_id} for item in self.artifacts],
            "base_tasks": [
                {"base_task_id": item.base_task_id, "artifact_id": item.artifact_id}
                for item in self.base_tasks
            ],
            "occurrences": [
                {
                    "occurrence_id": item.occurrence_id,
                    "base_task_id": item.base_task_id,
                    "duplicate": item.duplicate,
                }
                for item in self.occurrences
            ],
            "reference_constraints": [item.to_public_dict() for item in self.reference_constraints],
            "max_attempts_per_api_call": self.max_attempts_per_api_call,
        }


def _canonical_field(value: str) -> bytes:
    encoded = value.encode("utf-8")
    return len(encoded).to_bytes(4, "big") + encoded


def _opaque_id(nonce: bytes, namespace: str, ordinal: int) -> str:
    message = _canonical_field(namespace) + _canonical_field(str(ordinal))
    digest = hmac.new(nonce, message, hashlib.sha256).digest()[:16]
    return base64.b32encode(digest).decode("ascii").rstrip("=").lower()


def _occurrence_id(nonce: bytes, base_task_id: str, index: int) -> str:
    message = _canonical_field("occurrence") + _canonical_field(base_task_id) + _canonical_field(str(index))
    digest = hmac.new(nonce, message, hashlib.sha256).digest()[:16]
    return base64.b32encode(digest).decode("ascii").rstrip("=").lower()


def load_reference_constraints(path: str | Path) -> tuple[_PrivateReferenceConstraint, ...]:
    """Load the private, independently authored reference-constraint file."""
    payload = json.loads(Path(path).read_text(encoding="utf-8"))
    if payload.get("schema_version") != "prepilot-reference-constraints/v1":
        raise ValueError("reference constraints require schema prepilot-reference-constraints/v1")
    records = payload.get("records")
    if not isinstance(records, list):
        raise ValueError("reference constraints require records")
    result = []
    seen_intents: set[str] = set()
    seen_ids: set[str] = set()
    for record in records:
        try:
            intent = str(record["source_intent_id"]).strip()
            constraint_id = str(record["constraint_id"]).strip()
            text = str(record["text"]).strip()
        except (KeyError, TypeError):
            raise ValueError("reference constraints require source intent, opaque ID, and text") from None
        if not intent or not constraint_id or not text or intent in seen_intents or constraint_id in seen_ids:
            raise ValueError("reference constraints require unique source intents and constraint IDs")
        seen_intents.add(intent)
        seen_ids.add(constraint_id)
        result.append(_PrivateReferenceConstraint(constraint_id, text, intent))
    return tuple(result)


def build_exploratory_call_plan(
    normalized_records: Iterable[Mapping[str, Any]],
    provider_slots: Iterable[Mapping[str, Any]],
    reference_constraints: Iterable[ReferenceConstraint | _PrivateReferenceConstraint] | str | Path,
    *,
    run_nonce: bytes | None = None,
    duplicate_seed: int = 0,
    duplicate_fraction: float = 0.2,
) -> ExploratoryCallPlan:
    records = sorted(normalized_records, key=lambda item: str(item["source_intent_id"]))
    slots = tuple(provider_slots)
    constraints = (
        load_reference_constraints(reference_constraints)
        if isinstance(reference_constraints, (str, Path))
        else tuple(reference_constraints)
    )
    intents = tuple(str(item["source_intent_id"]) for item in records)
    if len(records) != 12 or len(set(intents)) != 12:
        raise ValueError("call plan requires exactly 12 unique normalized source intents")
    slot_ids = tuple(str(item["slot_id"]) for item in slots)
    if len(slots) != 2 or len(set(slot_ids)) != 2:
        raise ValueError("call plan requires exactly two unique provider slots")
    constraint_intents = {getattr(item, "source_intent_id", None) for item in constraints}
    if constraint_intents != set(intents) or len(constraints) != 12:
        raise ValueError("reference constraints require exactly one record per source intent")
    if run_nonce is None:
        run_nonce = secrets.token_bytes(32)
    if len(run_nonce) != 32:
        raise ValueError("run_nonce must be a 256-bit private value")
    if not 0 <= duplicate_fraction <= 1:
        raise ValueError("duplicate fraction must be between zero and one")

    episodes: list[PublicEpisode] = []
    artifacts: list[PublicArtifact] = []
    tasks: list[PublicBaseTask] = []
    joins: list[_PrivateJoin] = []
    episode_ordinal = artifact_ordinal = task_ordinal = 0
    for intent in intents:
        for variant_index in range(2):
            for replication_index in range(5):
                episode_id = _opaque_id(run_nonce, "episode", episode_ordinal)
                episodes.append(PublicEpisode(episode_id))
                episode_ordinal += 1
                for slot_id in slot_ids:
                    artifact_id = _opaque_id(run_nonce, "artifact", artifact_ordinal)
                    base_task_id = _opaque_id(run_nonce, "base-task", task_ordinal)
                    artifacts.append(PublicArtifact(artifact_id))
                    tasks.append(PublicBaseTask(base_task_id, artifact_id))
                    joins.append(_PrivateJoin(episode_id, artifact_id, base_task_id, intent, variant_index, replication_index, slot_id))
                    artifact_ordinal += 1
                    task_ordinal += 1

    duplicate_count = round(len(tasks) * duplicate_fraction)
    selected = set(Random(duplicate_seed).sample(range(len(tasks)), duplicate_count))
    occurrences = []
    for index, task in enumerate(tasks):
        occurrences.append(PublicOccurrence(_occurrence_id(run_nonce, task.base_task_id, 0), task.base_task_id, False))
        if index in selected:
            occurrences.append(PublicOccurrence(_occurrence_id(run_nonce, task.base_task_id, 1), task.base_task_id, True))
    duplicates = tuple(item for item in occurrences if item.duplicate)
    public_constraints = tuple(ReferenceConstraint(item.constraint_id, item.text) for item in constraints)
    return ExploratoryCallPlan(tuple(episodes), tuple(artifacts), tuple(tasks), tuple(occurrences), duplicates, public_constraints, _private_join=tuple(joins), _run_nonce=run_nonce)
