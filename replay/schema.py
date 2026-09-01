from __future__ import annotations

import datetime as dt
import hashlib
import json
import math
from collections.abc import Mapping
from typing import Any

from protocol.atomic_obligations import validate_atomic_obligations
from protocol.conditional_semantics import validate_conditional_semantics

REPLAY_VERSION = "constraint-replay/v1"
CHECKPOINT_SCHEMA_VERSION = "pre-final/v1"
ARP_WIRE_VERSION = "2.0.5"
ARP_PACKAGE_VERSION = "3.0.0"

EVENT_NAMES = (
    "interpretation.completed",
    "plan.completed",
    "tool.completed",
)
_TERMINAL_KEYS = {
    "artifact", "artifacts", "oracle", "oracle_passed", "terminal",
    "terminal_validation", "label", "labels", "semantic_label",
    "final_artifact", "variant", "variant_id", "smell", "defect_family",
    "defect_type", "mutation", "expected", "expected_decision",
}
_MANIFEST_KEYS = {
    "replay_version", "checkpoint_schema_version", "arp_wire_version", "arp_package_version",
    "requirement", "cases", "case_id", "trace", "trace_sha256", "status", "source",
}


class ContractError(ValueError):
    """Raised when deployable replay input violates the frozen contract."""


def _normalize(value: Any) -> Any:
    if isinstance(value, Mapping):
        return {str(key): _normalize(item) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return [_normalize(item) for item in value]
    if isinstance(value, float):
        if not math.isfinite(value):
            raise ContractError("canonical JSON cannot contain non-finite numbers")
        return 0 if value == 0 else value
    return value


def canonical_json_bytes(value: Any) -> bytes:
    """Return portable UTF-8 JSON bytes with no trailing newline."""

    try:
        return json.dumps(
            _normalize(value),
            ensure_ascii=False,
            sort_keys=True,
            separators=(",", ":"),
            allow_nan=False,
        ).encode("utf-8")
    except (TypeError, ValueError) as exc:
        raise ContractError(f"value is not canonical JSON: {exc}") from exc


def sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def _reject_terminal(value: Any, path: str = "attributes") -> None:
    if isinstance(value, Mapping):
        for key, item in value.items():
            if str(key).lower() in _TERMINAL_KEYS:
                raise ContractError(f"terminal field {path}.{key} is not deployable")
            _reject_terminal(item, f"{path}.{key}")
    elif isinstance(value, list):
        for index, item in enumerate(value):
            _reject_terminal(item, f"{path}[{index}]")


def _strings(value: Any, path: str) -> None:
    if not isinstance(value, list) or not all(isinstance(item, str) for item in value):
        raise ContractError(f"{path} must be an array of strings")


def _attributes_for(name: str, value: Any) -> dict[str, Any]:
    if not isinstance(value, Mapping):
        raise ContractError(f"{name}.attributes must be an object")
    normalized = dict(value)
    if name == "interpretation.completed":
        required = {"constraints", "quantities", "unresolved_references", "assumptions", "contradictions"}
        optional = {"conditional_semantics", "atomic_obligations"}
        extended = required | optional
        present = set(normalized)
        if present - extended or not required.issubset(present):
            raise ContractError("T1 attributes do not match pre-final/v1")
        normalized.setdefault("conditional_semantics", [])
        normalized.setdefault("atomic_obligations", [])
        for field in ("constraints", "unresolved_references", "assumptions", "contradictions"):
            _strings(normalized[field], f"T1.{field}")
        quantities = normalized["quantities"]
        if not isinstance(quantities, list):
            raise ContractError("T1.quantities must be an array")
        for item in quantities:
            if not isinstance(item, Mapping) or set(item) != {"value", "unit"}:
                raise ContractError("T1.quantities items must contain value and unit")
            if not isinstance(item["unit"], str) or not isinstance(item["value"], (int, float)) or isinstance(item["value"], bool):
                raise ContractError("T1.quantity value/unit types are invalid")
        try:
            normalized["conditional_semantics"] = validate_conditional_semantics(normalized["conditional_semantics"])
            normalized["atomic_obligations"] = validate_atomic_obligations(
                normalized["atomic_obligations"],
                normalized["constraints"],
            )
        except ValueError as error:
            raise ContractError(str(error)) from error
    elif name == "plan.completed":
        required = {"validation_checks", "planned_tools", "coverage_targets"}
        if set(value) != required:
            raise ContractError("T2 attributes do not match pre-final/v1")
        for field in required:
            _strings(value[field], f"T2.{field}")
    elif name == "tool.completed":
        required = {"revisions", "validation_attempts", "errors", "retrieval_events"}
        if set(value) != required:
            raise ContractError("T3 attributes do not match pre-final/v1")
        for field in ("revisions", "validation_attempts", "retrieval_events"):
            if not isinstance(value[field], int) or isinstance(value[field], bool) or value[field] < 0:
                raise ContractError(f"T3.{field} must be a non-negative integer")
        _strings(value["errors"], "T3.errors")
    else:
        raise ContractError(f"unsupported checkpoint {name}")
    _reject_terminal(normalized, f"{name}.attributes")
    return normalized


def _timestamp(value: Any, path: str) -> dt.datetime:
    if not isinstance(value, str) or not value:
        raise ContractError(f"{path} must be a non-empty timestamp")
    try:
        return dt.datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError as exc:
        raise ContractError(f"{path} must be ISO-8601") from exc


def validate_bundle_mapping(bundle: Mapping[str, Any]) -> dict[str, Any]:
    if not isinstance(bundle, Mapping):
        raise ContractError("bundle must be an object")
    for field in ("manifest", "requirement", "events"):
        if field not in bundle:
            raise ContractError(f"bundle missing {field}")
    manifest = bundle["manifest"]
    requirement = bundle["requirement"]
    events = bundle["events"]
    if not isinstance(manifest, Mapping):
        raise ContractError("manifest must be an object")
    if not set(manifest).issubset(_MANIFEST_KEYS):
        raise ContractError("manifest contains unknown deployable fields")
    _reject_terminal(manifest, "manifest")
    expected_versions = {
        "replay_version": REPLAY_VERSION,
        "checkpoint_schema_version": CHECKPOINT_SCHEMA_VERSION,
        "arp_wire_version": ARP_WIRE_VERSION,
        "arp_package_version": ARP_PACKAGE_VERSION,
    }
    for field, expected in expected_versions.items():
        if manifest.get(field) != expected:
            raise ContractError(f"manifest {field} must be {expected}")
    if not isinstance(manifest.get("case_id"), str) or not manifest["case_id"]:
        raise ContractError("manifest case_id must be non-empty")
    if not isinstance(requirement, Mapping) or set(requirement) != {"text", "task_family"}:
        raise ContractError("requirement contains unknown deployable fields")
    if not isinstance(requirement.get("text"), str) or not requirement["text"].strip():
        raise ContractError("requirement.text must be non-empty")
    if not isinstance(requirement.get("task_family"), str) or not requirement["task_family"].strip():
        raise ContractError("requirement.task_family must be non-empty")
    _reject_terminal(requirement, "requirement")
    if not isinstance(events, list) or len(events) != 3:
        raise ContractError("trace must contain exactly three checkpoint events")
    identity: tuple[Any, ...] | None = None
    normalized_events: list[dict[str, Any]] = []
    previous_end: dt.datetime | None = None
    previous_id: str | None = None
    for expected_sequence, (expected_name, event) in enumerate(zip(EVENT_NAMES, events), start=1):
        if not isinstance(event, Mapping):
            raise ContractError("trace events must be objects")
        required = {
            "event_id", "schema_version", "experiment_id", "run_id", "episode_id",
            "replication_id", "sequence_number", "checkpoint", "event_type",
            "started_at", "ended_at", "attributes", "content_reference", "parent_event_id",
        }
        if set(event) != required:
            raise ContractError(f"{expected_name} has an invalid ARP envelope")
        if event["schema_version"] != ARP_WIRE_VERSION or event["checkpoint"] != expected_name or event["event_type"] != expected_name:
            raise ContractError(f"event {expected_name} has an invalid ARP name/version")
        if not isinstance(event["event_id"], str) or not event["event_id"]:
            raise ContractError("event_id must be non-empty")
        if event["sequence_number"] != expected_sequence or event["replication_id"] != 0:
            raise ContractError("event sequence/replication is invalid")
        current_identity = (event["experiment_id"], event["run_id"], event["episode_id"])
        if identity is None:
            identity = current_identity
        elif identity != current_identity:
            raise ContractError("events must share experiment/run/episode identity")
        started = _timestamp(event["started_at"], f"{expected_name}.started_at")
        ended = _timestamp(event["ended_at"], f"{expected_name}.ended_at")
        if ended < started or (previous_end is not None and started < previous_end):
            raise ContractError("event timestamps must be chronological")
        if expected_sequence == 1 and event["parent_event_id"] is not None:
            raise ContractError("T1 parent_event_id must be null")
        if expected_sequence > 1 and event["parent_event_id"] != previous_id:
            raise ContractError("parent_event_id must reference the preceding event")
        normalized_event = dict(event)
        normalized_event["attributes"] = _attributes_for(expected_name, event["attributes"])
        normalized_events.append(normalized_event)
        previous_end = ended
        previous_id = event["event_id"]
    _validate_with_arp(events)
    return {"manifest": dict(manifest), "requirement": dict(requirement), "events": normalized_events}


def _validate_with_arp(events: list[Mapping[str, Any]]) -> None:
    """Run the installed ARP 3.0 compatibility validator when available.

    The local validator above owns the replay-specific payload and chronology
    invariants. ARP remains the compatibility authority for its wire envelope;
    a provider trace that ARP rejects is never allowed into the gate.
    """

    try:
        from agent_reliability_protocol import LifecycleEvent, validate_lifecycle_sequence
    except ImportError:
        return
    try:
        parsed = [LifecycleEvent.from_dict(event) for event in events]
        validate_lifecycle_sequence(parsed)
    except (TypeError, ValueError, KeyError) as exc:
        raise ContractError(f"ARP 3.0.0 rejected lifecycle trace: {exc}") from exc
