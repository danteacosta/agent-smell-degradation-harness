"""SDK-free adapters for common observability export shapes.

These adapters intentionally normalize only pre-final checkpoint evidence. A
consumer can feed the normalized envelope into its own ARP bundle builder; no
vendor SDK or API key is required by the replay gate.
"""

from __future__ import annotations

import copy
import datetime as dt
import json
from collections.abc import Mapping
from typing import Any

from protocol.conditional_semantics import validate_conditional_semantics

from .schema import (
    ARP_PACKAGE_VERSION,
    ARP_WIRE_VERSION,
    CHECKPOINT_SCHEMA_VERSION,
    ContractError,
    REPLAY_VERSION,
    sha256_bytes,
    validate_bundle_mapping,
)

SUPPORTED_SOURCES = {"phoenix", "langfuse", "braintrust"}
_EVENT_KEYS = {"interpretation.completed", "plan.completed", "tool.completed"}
_TERMINAL_KEYS = {
    "artifact", "artifacts", "oracle", "oracle_passed", "terminal", "terminal_validation",
    "label", "labels", "semantic_label", "final_artifact", "variant", "variant_id", "smell",
    "defect_family", "defect_type", "mutation", "expected", "expected_decision",
}


def _contains_terminal(value: Any) -> bool:
    if isinstance(value, Mapping):
        return any(str(k).lower() in _TERMINAL_KEYS or _contains_terminal(v) for k, v in value.items())
    if isinstance(value, list):
        return any(_contains_terminal(item) for item in value)
    return False


def _canonical_event_bytes(events: list[Mapping[str, Any]]) -> bytes:
    return b"".join(
        json.dumps(dict(event), ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8") + b"\n"
        for event in events
    )


def _parse_timestamp(value: Any, field: str) -> dt.datetime:
    if not isinstance(value, str) or not value:
        raise ContractError(f"{field} must be a non-empty ISO-8601 timestamp")
    try:
        return dt.datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError as exc:
        raise ContractError(f"{field} must be ISO-8601") from exc


def _typed_attributes(name: str, attributes: Mapping[str, Any]) -> dict[str, Any]:
    if not isinstance(attributes, Mapping):
        raise ContractError(f"{name}.attributes must be an object")
    result = copy.deepcopy(dict(attributes))
    if name == "interpretation.completed":
        required = {"constraints", "quantities", "unresolved_references", "assumptions", "contradictions"}
        extended = required | {"conditional_semantics"}
        if set(result) == required:
            result["conditional_semantics"] = []
        elif set(result) != extended:
            raise ContractError("T1 attributes do not match pre-final/v1")
        for field in ("constraints", "unresolved_references", "assumptions", "contradictions"):
            values = result[field]
            if not isinstance(values, list) or not all(isinstance(item, str) for item in values):
                raise ContractError(f"T1.{field} must be an array of strings")
        for quantity in result["quantities"]:
            if not isinstance(quantity, Mapping) or set(quantity) != {"value", "unit"}:
                raise ContractError("T1.quantities items must contain value and unit")
            if isinstance(quantity["value"], bool) or not isinstance(quantity["value"], (int, float)) or not isinstance(quantity["unit"], str):
                raise ContractError("T1.quantity value/unit types are invalid")
        try:
            result["conditional_semantics"] = validate_conditional_semantics(result["conditional_semantics"])
        except ValueError as error:
            raise ContractError(str(error)) from error
    elif name == "plan.completed":
        required = {"validation_checks", "planned_tools", "coverage_targets"}
        if set(result) != required or any(not isinstance(result[field], list) or not all(isinstance(item, str) for item in result[field]) for field in required):
            raise ContractError("T2 attributes do not match pre-final/v1")
    elif name == "tool.completed":
        required = {"revisions", "validation_attempts", "errors", "retrieval_events"}
        if set(result) != required:
            raise ContractError("T3 attributes do not match pre-final/v1")
        for field in ("revisions", "validation_attempts", "retrieval_events"):
            if isinstance(result[field], bool) or not isinstance(result[field], int) or result[field] < 0:
                raise ContractError(f"T3.{field} must be a non-negative integer")
        if not isinstance(result["errors"], list) or not all(isinstance(item, str) for item in result["errors"]):
            raise ContractError("T3.errors must be an array of strings")
    else:
        raise ContractError(f"unsupported checkpoint {name}")
    if _contains_terminal(result):
        raise ContractError("terminal or mutation data is not deployable")
    return result


def normalize_trace_export(source: str, payload: Mapping[str, Any]) -> dict[str, Any]:
    """Normalize Phoenix spans, Langfuse observations, or Braintrust spans.

    This is deliberately a boundary adapter, not a claim of vendor schema
    completeness. Unknown fields are retained only under non-deployable
    metadata; terminal keys fail closed before any feature extraction.
    """

    source = source.lower().strip()
    if source not in SUPPORTED_SOURCES:
        raise ValueError(f"unsupported trace source: {source}")
    if source == "langfuse":
        raw_events = payload.get("observations", [])
    else:
        raw_events = payload.get("spans", payload.get("events", []))
    if not isinstance(raw_events, list) or not raw_events:
        raise ValueError(f"{source} export must contain spans/observations")
    events: list[dict[str, Any]] = []
    for raw in raw_events:
        if not isinstance(raw, Mapping):
            raise ValueError("trace events must be objects")
        if _contains_terminal(raw):
            raise ValueError("terminal or mutation data is not deployable")
        name = str(raw.get("name", raw.get("event_type", "")))
        if name not in _EVENT_KEYS:
            continue
        attributes = raw.get("attributes", raw.get("metadata", {}))
        if not isinstance(attributes, Mapping):
            raise ValueError("trace attributes must be objects")
        if _contains_terminal(attributes):
            raise ValueError("terminal attributes are not deployable")
        normalized = {
            "name": name,
            "attributes": dict(attributes),
            "source": source,
            "event_id": raw.get("event_id"),
            "started_at": raw.get("started_at"),
            "ended_at": raw.get("ended_at"),
            "parent_event_id": raw.get("parent_event_id"),
            "content_reference": raw.get("content_reference"),
        }
        events.append(normalized)
    if not events:
        raise ValueError(f"{source} export has no supported pre-final checkpoints")
    return {"source": source, "events": events, "metadata": {"adapter": f"{source}/generic-v1"}}


def build_replay_bundle(
    source: str,
    payload: Mapping[str, Any],
    *,
    requirement: Mapping[str, Any],
    case_id: str,
    context: Mapping[str, Any],
) -> dict[str, Any]:
    """Build a strict, explicitly non-confirmatory product replay bundle."""

    if not isinstance(requirement, Mapping) or set(requirement) != {"text", "task_family"}:
        raise ContractError("product bundle requires only text and task_family requirement fields")
    if not isinstance(case_id, str) or not case_id.strip():
        raise ContractError("case_id must be a non-empty string")
    required_context = {"experiment_id", "run_id", "episode_id", "replication_id"}
    if not isinstance(context, Mapping) or not required_context.issubset(context):
        raise ContractError("product bundle requires explicit ARP identity context")
    if not isinstance(context["replication_id"], int) or isinstance(context["replication_id"], bool) or context["replication_id"] < 0:
        raise ContractError("replication_id must be a non-negative integer")
    normalized = normalize_trace_export(source, payload)
    raw_events = normalized["events"]
    if [event["name"] for event in raw_events] != ["interpretation.completed", "plan.completed", "tool.completed"]:
        raise ContractError("product bundle requires exactly one ordered T1/T2/T3 checkpoint")
    events: list[dict[str, Any]] = []
    previous_id: str | None = None
    previous_end: dt.datetime | None = None
    for sequence, raw in enumerate(raw_events, start=1):
        event_id = raw.get("event_id")
        if not isinstance(event_id, str) or not event_id.strip():
            raise ContractError("source event_id is required; builder will not fabricate it")
        started = _parse_timestamp(raw.get("started_at"), f"{event_id}.started_at")
        ended = _parse_timestamp(raw.get("ended_at"), f"{event_id}.ended_at")
        if ended < started or (previous_end is not None and started < previous_end):
            raise ContractError("product event timestamps must be chronological")
        parent = raw.get("parent_event_id")
        if sequence == 1 and parent is not None:
            raise ContractError("T1 parent_event_id must be null")
        if sequence > 1 and parent != previous_id:
            raise ContractError("parent_event_id must reference the preceding source event")
        event = {
            "event_id": event_id,
            "schema_version": ARP_WIRE_VERSION,
            "experiment_id": str(context["experiment_id"]),
            "run_id": str(context["run_id"]),
            "episode_id": str(context["episode_id"]),
            "replication_id": context["replication_id"],
            "sequence_number": sequence,
            "checkpoint": raw["name"],
            "event_type": raw["name"],
            "started_at": raw["started_at"],
            "ended_at": raw["ended_at"],
            "attributes": _typed_attributes(raw["name"], raw["attributes"]),
            "content_reference": raw.get("content_reference"),
            "parent_event_id": parent,
        }
        events.append(event)
        previous_id, previous_end = event_id, ended
    raw_bytes = _canonical_event_bytes(events)
    manifest = {
        "replay_version": REPLAY_VERSION,
        "checkpoint_schema_version": CHECKPOINT_SCHEMA_VERSION,
        "arp_wire_version": ARP_WIRE_VERSION,
        "arp_package_version": ARP_PACKAGE_VERSION,
        "case_id": case_id,
        "status": "non_confirmatory_adapter_demo",
        "source": source.lower().strip(),
        "trace_sha256": sha256_bytes(raw_bytes),
    }
    bundle = {
        "manifest": manifest,
        "requirement": dict(requirement),
        "events": events,
        "_trace_raw": raw_bytes,
        "diagnostic_sidecar": {"source": source.lower().strip(), "adapter": normalized["metadata"]["adapter"]},
    }
    validate_bundle_mapping(bundle)
    return bundle
