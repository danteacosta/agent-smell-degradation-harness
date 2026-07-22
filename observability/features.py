from __future__ import annotations

import json
from functools import lru_cache
from pathlib import Path
from typing import Any

from pairs.loader import load_all_pairs

TIER_B_NAMES = frozenset({"oracle_verdict"})
TIER_B_KEYS = frozenset({"oracle_passed", "oracle_verdict", "mutation_score"})


def _load_provenance_events(provenance_path: str | Path) -> list[dict[str, Any]]:
    path = Path(provenance_path)
    if not path.exists():
        return []
    events: list[dict[str, Any]] = []
    for line in path.read_text(encoding="utf-8").splitlines():
        if line.strip():
            events.append(json.loads(line))
    return events


def _tier_a_events(events: list[dict[str, Any]]) -> list[dict[str, Any]]:
    filtered: list[dict[str, Any]] = []
    for event in events:
        tier = event.get("tier", "A")
        name = event.get("name", "")
        if tier == "B" or name in TIER_B_NAMES:
            continue
        filtered.append(event)
    return filtered


@lru_cache(maxsize=1)
def _oracle_spec_lookup() -> dict[tuple[str, str], dict[str, Any]]:
    lookup: dict[tuple[str, str], dict[str, Any]] = {}
    for pair in load_all_pairs():
        intent_id = pair["intent_id"]
        for task_family, spec in pair["oracle_spec"].items():
            lookup[(intent_id, task_family)] = spec
    return lookup


def _oracle_spec(intent_id: str, task_family: str) -> dict[str, Any]:
    return _oracle_spec_lookup().get((intent_id, task_family), {})


def _smell_type_code(smell: dict[str, Any] | None) -> int:
    if not smell:
        return 0
    smell_type = smell.get("type", "")
    return sum(ord(ch) for ch in smell_type) % 997


def _extract_static_smell(episode: dict[str, Any]) -> dict[str, float | int]:
    smell = episode.get("smell")
    requirement_text = episode.get("requirement_text", "")
    return {
        "smell_present": 1 if smell is not None else 0,
        "requirement_length": len(requirement_text),
        "smell_type_code": _smell_type_code(smell),
    }


def _extract_operational(events: list[dict[str, Any]]) -> dict[str, float | int]:
    latency_ms = 0.0
    for event in events:
        if event.get("kind") == "operational" and event.get("name") == "latency":
            latency_ms = float(event.get("payload", {}).get("ms", 0))
            break
    return {
        "event_count": len(events),
        "latency_ms": latency_ms,
    }


def _constraint_extract_payload(
    events: list[dict[str, Any]],
) -> dict[str, Any] | None:
    for event in events:
        if event.get("kind") == "semantic" and event.get("name") == "constraint_extract":
            payload = event.get("payload")
            if isinstance(payload, dict):
                return payload
    return None


def _extract_provenance_semantic(
    episode: dict[str, Any],
    events: list[dict[str, Any]],
) -> dict[str, float | int]:
    payload = _constraint_extract_payload(events)
    artifact = episode.get("artifact") or {}
    expected = _oracle_spec(episode["intent_id"], episode["task_family"])

    constraint_match = 0
    payload_matches_artifact = 0
    is_weak_comparator = 0
    if payload is not None:
        constraint_match = 1 if payload == expected else 0
        payload_matches_artifact = 1 if payload == artifact else 0
        if payload.get("comparator") == ">=" and expected.get("comparator") == ">":
            is_weak_comparator = 1
        if payload.get("refund_window_minutes") != expected.get("refund_window_minutes"):
            if expected.get("refund_window_minutes") is not None:
                constraint_match = 0

    semantic_event_count = sum(1 for event in events if event.get("kind") == "semantic")
    return {
        "constraint_match": constraint_match,
        "payload_matches_artifact": payload_matches_artifact,
        "is_weak_comparator": is_weak_comparator,
        "semantic_event_count": semantic_event_count,
    }


def extract_tier_a_features(
    episode: dict[str, Any],
    provenance_path: str | Path,
) -> dict[str, dict[str, float | int]]:
    events = _tier_a_events(_load_provenance_events(provenance_path))
    features = {
        "static_smell": _extract_static_smell(episode),
        "operational": _extract_operational(events),
        "provenance_semantic": _extract_provenance_semantic(episode, events),
    }
    for family in features.values():
        for key in family:
            assert key not in TIER_B_KEYS
    return features
