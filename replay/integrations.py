"""SDK-free adapters for common observability export shapes.

These adapters intentionally normalize only pre-final checkpoint evidence. A
consumer can feed the normalized envelope into its own ARP bundle builder; no
vendor SDK or API key is required by the replay gate.
"""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any

SUPPORTED_SOURCES = {"phoenix", "langfuse", "braintrust"}
_EVENT_KEYS = {"interpretation.completed", "plan.completed", "tool.completed"}
_TERMINAL_KEYS = {"oracle", "oracle_passed", "label", "labels", "artifact", "final_artifact", "variant", "mutation"}


def _contains_terminal(value: Any) -> bool:
    if isinstance(value, Mapping):
        return any(str(k).lower() in _TERMINAL_KEYS or _contains_terminal(v) for k, v in value.items())
    if isinstance(value, list):
        return any(_contains_terminal(item) for item in value)
    return False


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
        name = str(raw.get("name", raw.get("event_type", "")))
        if name not in _EVENT_KEYS:
            continue
        attributes = raw.get("attributes", raw.get("metadata", {}))
        if not isinstance(attributes, Mapping):
            raise ValueError("trace attributes must be objects")
        if _contains_terminal(attributes):
            raise ValueError("terminal attributes are not deployable")
        events.append({"name": name, "attributes": dict(attributes), "source": source})
    if not events:
        raise ValueError(f"{source} export has no supported pre-final checkpoints")
    return {"source": source, "events": events, "metadata": {"adapter": f"{source}/generic-v1"}}
