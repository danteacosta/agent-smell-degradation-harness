from __future__ import annotations

import json
from typing import Any, Mapping

from .models import FeatureEpisodeInput


def _events(provenance_jsonl: str) -> list[Mapping[str, Any]]:
    return [
        event
        for line in provenance_jsonl.splitlines()
        if line.strip()
        for event in (json.loads(line),)
        if isinstance(event, Mapping)
        and event.get("tier", "A") != "B"
        and event.get("name") != "oracle_verdict"
    ]


def _static_smell(feature_input: FeatureEpisodeInput) -> dict[str, int]:
    smell = feature_input.smell
    smell_type = "" if not smell else str(smell.get("type", ""))
    return {
        "smell_present": int(smell is not None),
        "requirement_length": len(feature_input.requirement_text),
        "smell_type_code": sum(ord(char) for char in smell_type) % 997,
    }


def extract_pre_final_features(
    feature_input: FeatureEpisodeInput,
) -> dict[str, dict[str, float | int]]:
    events = _events(feature_input.provenance_jsonl)
    latency_ms = next(
        (
            float(event.get("payload", {}).get("ms", 0))
            for event in events
            if event.get("kind") == "operational" and event.get("name") == "latency"
        ),
        0.0,
    )
    constraint_payload = next(
        (
            event.get("payload")
            for event in events
            if event.get("kind") == "semantic"
            and event.get("name") == "constraint_extract"
            and isinstance(event.get("payload"), Mapping)
        ),
        None,
    )
    return {
        "static_smell": _static_smell(feature_input),
        "operational": {"event_count": len(events), "latency_ms": latency_ms},
        "provenance_semantic": {
            "constraint_event_present": int(constraint_payload is not None),
            "constraint_field_count": len(constraint_payload or {}),
            "constraint_has_comparator": int(
                isinstance(constraint_payload, Mapping)
                and "comparator" in constraint_payload
            ),
            "semantic_event_count": sum(
                event.get("kind") == "semantic" for event in events
            ),
        },
    }
