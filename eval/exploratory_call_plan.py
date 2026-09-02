"""Build the blinded, deterministic call inventory for the exploratory pre-pilot."""

from __future__ import annotations

import base64
import hashlib
import hmac
import json
import secrets
from dataclasses import InitVar, dataclass
from pathlib import Path
from random import Random
from typing import Any, Iterable, Mapping

from label_plane.exploratory_judge import JUDGE_SCHEMA_VERSION, validate_judge_request


_FROZEN_DUPLICATE_SEED = 0
_FROZEN_DUPLICATE_FRACTION = 0.2
_REFERENCE_CONSTRAINT_FIELDS = frozenset({"source_intent_id", "constraint_id", "text"})
_REFERENCE_CONSTRAINT_SCHEMA_VERSION = "prepilot-reference-constraints/v1"
_PRIVATE_TARGET_TOKEN = "incompleteness_missing_condition"


@dataclass(frozen=True)
class ReferenceConstraint:
    constraint_id: str
    text: str

    def to_public_dict(self) -> dict[str, str]:
        _validate_public_constraint_values(self.constraint_id, self.text)
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
class _PrivateProviderConfiguration:
    slot_id: str
    provider: str
    model: str
    model_version: str


_PUBLIC_FIELD_SPECS = (
    ("episodes", PublicEpisode, ("episode_id",)),
    ("artifacts", PublicArtifact, ("artifact_id",)),
    ("base_tasks", PublicBaseTask, ("base_task_id", "artifact_id")),
    ("occurrences", PublicOccurrence, ("occurrence_id", "base_task_id", "duplicate")),
    ("duplicate_occurrences", PublicOccurrence, ("occurrence_id", "base_task_id", "duplicate")),
    ("reference_constraints", ReferenceConstraint, ("constraint_id", "text")),
)


@dataclass(frozen=True)
class ExploratoryCallPlan:
    episodes: tuple[PublicEpisode, ...]
    artifacts: tuple[PublicArtifact, ...]
    base_tasks: tuple[PublicBaseTask, ...]
    occurrences: tuple[PublicOccurrence, ...]
    duplicate_occurrences: tuple[PublicOccurrence, ...]
    reference_constraints: tuple[ReferenceConstraint, ...]
    max_attempts_per_api_call: int = 2
    _private_join: InitVar[tuple[_PrivateJoin, ...]] = ()
    _run_nonce: InitVar[bytes | None] = None
    _private_configurations: InitVar[tuple[_PrivateProviderConfiguration, ...]] = ()

    def __post_init__(
        self,
        _private_join: tuple[_PrivateJoin, ...],
        _run_nonce: bytes | None,
        _private_configurations: tuple[_PrivateProviderConfiguration, ...],
    ) -> None:
        for field_name, record_type, fields in _PUBLIC_FIELD_SPECS:
            object.__setattr__(
                self,
                field_name,
                _canonicalize_public_records(
                    getattr(self, field_name), record_type, fields, field_name
                ),
            )
        object.__setattr__(self, "_private_join", _freeze_private_records(_private_join, _PrivateJoin, "private join"))
        object.__setattr__(self, "_run_nonce", _validate_run_nonce(_run_nonce))
        object.__setattr__(
            self,
            "_private_configurations",
            _freeze_private_records(
                _private_configurations,
                _PrivateProviderConfiguration,
                "private provider configurations",
            ),
        )

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
            "duplicate_seed": _FROZEN_DUPLICATE_SEED,
            "duplicate_fraction": _FROZEN_DUPLICATE_FRACTION,
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


def _validate_run_nonce(nonce: Any) -> bytes:
    if type(nonce) is not bytes or len(nonce) != 32:
        raise ValueError("run_nonce must be bytes with exactly 32 bytes")
    return nonce


def _freeze_private_records(value: Any, expected_type: type[Any], name: str) -> tuple[Any, ...]:
    try:
        frozen = tuple(value)
    except TypeError:
        raise ValueError(f"{name} must be an iterable of immutable private records") from None
    if any(type(item) is not expected_type for item in frozen):
        raise ValueError(f"{name} must contain only immutable private records")
    if expected_type is _PrivateJoin and any(
        type(item.episode_id) is not str
        or type(item.artifact_id) is not str
        or type(item.base_task_id) is not str
        or type(item.source_intent_id) is not str
        or type(item.variant_index) is not int
        or type(item.replication_index) is not int
        or type(item.provider_slot_id) is not str
        for item in frozen
    ):
        raise ValueError(f"{name} must contain only immutable private records")
    if expected_type is _PrivateProviderConfiguration and any(
        type(value) is not str
        for item in frozen
        for value in (item.slot_id, item.provider, item.model, item.model_version)
    ):
        raise ValueError(f"{name} must contain only immutable private records")
    return frozen


def _canonicalize_public_records(
    value: Any, expected_type: type[Any], fields: tuple[str, ...], name: str
) -> tuple[Any, ...]:
    if isinstance(value, Mapping):
        raise ValueError(f"public {name} must be an iterable of public records, not a mapping")
    try:
        values = tuple(value)
    except TypeError:
        raise ValueError(f"public {name} must be an iterable of public records") from None

    canonical: list[Any] = []
    for item in values:
        if isinstance(item, Mapping):
            if set(item) != set(fields):
                raise ValueError(f"public {name} record fields are invalid")
            item = expected_type(**{field: item[field] for field in fields})
        if type(item) is not expected_type:
            raise ValueError(f"public {name} must contain only immutable public records")
        _validate_public_record(item, expected_type)
        canonical.append(item)
    return tuple(canonical)


def _validate_public_record(item: Any, expected_type: type[Any]) -> None:
    if expected_type is PublicEpisode and type(item.episode_id) is not str:
        raise ValueError("public episodes must contain only immutable public records")
    if expected_type is PublicArtifact and type(item.artifact_id) is not str:
        raise ValueError("public artifacts must contain only immutable public records")
    if expected_type is PublicBaseTask and any(
        type(value) is not str for value in (item.base_task_id, item.artifact_id)
    ):
        raise ValueError("public base_tasks must contain only immutable public records")
    if expected_type is PublicOccurrence and (
        type(item.occurrence_id) is not str
        or type(item.base_task_id) is not str
        or type(item.duplicate) is not bool
    ):
        raise ValueError("public occurrences must contain only immutable public records")
    if expected_type is ReferenceConstraint:
        if type(item.constraint_id) is not str or type(item.text) is not str:
            raise ValueError("public reference_constraints must contain only immutable public records")
        _validate_public_constraint_values(item.constraint_id, item.text)


def _validate_public_constraint_values(constraint_id: Any, text: Any) -> None:
    try:
        validate_judge_request(
            {
                "schema_version": JUDGE_SCHEMA_VERSION,
                "occurrence_id": "opaque-occurrence",
                "generated_acceptance_criteria": "visible criteria",
                "reference_constraints": [{"constraint_id": constraint_id, "text": text}],
            }
        )
    except ValueError:
        raise ValueError("reference constraints must satisfy the dedicated judge boundary") from None


def _parse_reference_constraint_record(record: Any) -> _PrivateReferenceConstraint:
    if not isinstance(record, Mapping) or set(record) != _REFERENCE_CONSTRAINT_FIELDS:
        raise ValueError(
            "reference constraints require exactly source_intent_id, constraint_id, and text fields"
        )
    source_intent_id = record["source_intent_id"]
    constraint_id = record["constraint_id"]
    text = record["text"]
    if not isinstance(source_intent_id, str) or not source_intent_id.strip():
        raise ValueError("reference constraints require a non-empty string source intent")
    if _PRIVATE_TARGET_TOKEN in source_intent_id.casefold():
        raise ValueError("reference constraints contain forbidden metadata")
    if not isinstance(constraint_id, str) or not isinstance(text, str):
        raise ValueError("reference constraints require string opaque IDs and text")
    _validate_public_constraint_values(constraint_id, text)
    return _PrivateReferenceConstraint(constraint_id, text, source_intent_id.strip())


def _validate_reference_constraint_uniqueness(
    constraints: Iterable[_PrivateReferenceConstraint],
) -> tuple[_PrivateReferenceConstraint, ...]:
    result = tuple(constraints)
    seen_intents: set[str] = set()
    seen_ids: set[str] = set()
    for item in result:
        if item.source_intent_id in seen_intents or item.constraint_id in seen_ids:
            raise ValueError("reference constraints require unique source intents and constraint IDs")
        seen_intents.add(item.source_intent_id)
        seen_ids.add(item.constraint_id)
    return result


def load_reference_constraints(path: str | Path) -> tuple[_PrivateReferenceConstraint, ...]:
    """Load the private, independently authored reference-constraint file."""
    payload = json.loads(Path(path).read_text(encoding="utf-8"))
    if not isinstance(payload, Mapping) or set(payload) != {"schema_version", "records"}:
        raise ValueError("reference constraints require exactly schema_version and records fields")
    if payload["schema_version"] != _REFERENCE_CONSTRAINT_SCHEMA_VERSION:
        raise ValueError(
            "reference constraints require schema prepilot-reference-constraints/v1"
        )
    records = payload["records"]
    if not isinstance(records, list):
        raise ValueError("reference constraints require records")
    return _validate_reference_constraint_uniqueness(
        _parse_reference_constraint_record(record) for record in records
    )


def _normalize_direct_reference_constraints(
    values: Iterable[Mapping[str, Any] | _PrivateReferenceConstraint],
) -> tuple[_PrivateReferenceConstraint, ...]:
    parsed: list[_PrivateReferenceConstraint] = []
    for value in values:
        if isinstance(value, _PrivateReferenceConstraint):
            value = {
                "source_intent_id": value.source_intent_id,
                "constraint_id": value.constraint_id,
                "text": value.text,
            }
        parsed.append(_parse_reference_constraint_record(value))
    return _validate_reference_constraint_uniqueness(parsed)


def _provider_slot_configuration(slot: Any) -> _PrivateProviderConfiguration:
    if not isinstance(slot, Mapping):
        raise ValueError("provider slots require mapping configurations")
    required = ("slot_id", "provider", "model", "model_version")
    if any(not isinstance(slot.get(field), str) or not slot[field].strip() for field in required):
        raise ValueError("provider slots require non-empty string slot/provider/model/model_version")
    return _PrivateProviderConfiguration(
        slot_id=slot["slot_id"].strip(),
        provider=slot["provider"].strip(),
        model=slot["model"].strip(),
        model_version=slot["model_version"].strip(),
    )


def build_exploratory_call_plan(
    normalized_records: Iterable[Mapping[str, Any]],
    provider_slots: Iterable[Mapping[str, Any]],
    reference_constraints: Iterable[Mapping[str, Any] | _PrivateReferenceConstraint] | str | Path,
    *,
    run_nonce: bytes | None = None,
) -> ExploratoryCallPlan:
    records = sorted(normalized_records, key=lambda item: str(item["source_intent_id"]))
    slots = tuple(provider_slots)
    constraints = (
        load_reference_constraints(reference_constraints)
        if isinstance(reference_constraints, (str, Path))
        else _normalize_direct_reference_constraints(reference_constraints)
    )
    intents = tuple(str(item["source_intent_id"]) for item in records)
    if len(records) != 12 or len(set(intents)) != 12:
        raise ValueError("call plan requires exactly 12 unique normalized source intents")
    slot_configurations = tuple(_provider_slot_configuration(slot) for slot in slots)
    slot_ids = tuple(item.slot_id for item in slot_configurations)
    if len(slots) != 2 or len(set(slot_ids)) != 2:
        raise ValueError("call plan requires exactly two unique provider slots")
    provider_configurations = {
        (item.provider, item.model, item.model_version) for item in slot_configurations
    }
    if len(provider_configurations) != 2:
        raise ValueError("provider/model/model_version configurations must be distinct")
    if len({item.provider for item in slot_configurations}) != 2:
        raise ValueError("provider identity configurations must be distinct")
    constraint_intents = {item.source_intent_id for item in constraints}
    if constraint_intents != set(intents) or len(constraints) != 12:
        raise ValueError("reference constraints require exactly one record per source intent")
    if run_nonce is None:
        run_nonce = secrets.token_bytes(32)
    run_nonce = _validate_run_nonce(run_nonce)

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

    duplicate_count = round(len(tasks) * _FROZEN_DUPLICATE_FRACTION)
    selected = set(Random(_FROZEN_DUPLICATE_SEED).sample(range(len(tasks)), duplicate_count))
    occurrences = []
    for index, task in enumerate(tasks):
        occurrences.append(PublicOccurrence(_occurrence_id(run_nonce, task.base_task_id, 0), task.base_task_id, False))
        if index in selected:
            occurrences.append(PublicOccurrence(_occurrence_id(run_nonce, task.base_task_id, 1), task.base_task_id, True))
    duplicates = tuple(item for item in occurrences if item.duplicate)
    public_constraints = tuple(ReferenceConstraint(item.constraint_id, item.text) for item in constraints)
    return ExploratoryCallPlan(
        tuple(episodes),
        tuple(artifacts),
        tuple(tasks),
        tuple(occurrences),
        duplicates,
        public_constraints,
        _private_join=tuple(joins),
        _run_nonce=run_nonce,
        _private_configurations=slot_configurations,
    )
