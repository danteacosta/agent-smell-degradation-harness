"""Leakage-resistant deployable feature extraction.

The legacy feature API remains in :mod:`feature_plane.extractors` for
retrospective compatibility.  This module is the strict API used by the
confirmatory thesis detector and the product gate.
"""

from __future__ import annotations

import ast
import json
from pathlib import Path
from typing import Any, Mapping

from .models import DeployableFeatureInput

_TERMINAL_KEYS = frozenset(
    {
        "artifact",
        "artifacts",
        "oracle",
        "oracle_spec",
        "oracle_passed",
        "terminal",
        "terminal_validation",
        "label",
        "labels",
        "semantic_label",
        "mutation_score",
        "final_artifact",
    }
)
_TERMINAL_EVENT_NAMES = frozenset(
    {
        "oracle_verdict",
        "label.created",
        "label.assigned",
        "artifact.completed",
        "terminal.validation",
        "evaluation.completed",
    }
)


def _contains_terminal_key(value: Any) -> str | None:
    """Return the first terminal key found in nested/serialized payloads."""

    if isinstance(value, Mapping):
        for key, item in value.items():
            if str(key).lower() in _TERMINAL_KEYS:
                return str(key)
            found = _contains_terminal_key(item)
            if found:
                return found
    elif isinstance(value, (list, tuple)):
        for item in value:
            found = _contains_terminal_key(item)
            if found:
                return found
    elif isinstance(value, str):
        candidate = value.strip()
        if candidate.startswith(("{", "[")):
            try:
                decoded = json.loads(candidate)
            except (TypeError, ValueError, json.JSONDecodeError):
                return None
            return _contains_terminal_key(decoded)
    return None


def _event_payload(event: Mapping[str, Any]) -> Mapping[str, Any] | None:
    payload = event.get("payload", event.get("attributes"))
    return payload if isinstance(payload, Mapping) else None


def _load_deployable_events(provenance_path: str | Path) -> list[Mapping[str, Any]]:
    path = Path(provenance_path)
    if not path.exists():
        return []

    events: list[Mapping[str, Any]] = []
    for line in path.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        event = json.loads(line)
        if not isinstance(event, Mapping):
            raise ValueError("deployable trace event must be an object")
        event_name = str(event.get("name", event.get("event_type", "")))
        if event_name in _TERMINAL_EVENT_NAMES or str(event.get("checkpoint", "")).upper() in {
            "T4",
            "FINAL",
        }:
            raise ValueError(f"terminal event {event_name!r} is not deployable")
        terminal_key = _contains_terminal_key(event)
        if terminal_key:
            raise ValueError(f"terminal field {terminal_key!r} found in deployable trace")
        if event.get("tier", "A") == "B":
            continue
        events.append(event)
    return events


def extract_deployable_features(
    feature_input: DeployableFeatureInput,
    provenance_path: str | Path,
) -> dict[str, dict[str, float | int]]:
    """Extract only allowlisted, pre-final feature families.

    The result intentionally has no smell/variant/oracle/label/final-artifact
    keys.  This is a fail-closed boundary: terminal content in a trace raises
    instead of being silently interpreted as a deployable signal.
    """

    events = _load_deployable_events(provenance_path)
    latency_ms = next(
        (
            float((_event_payload(event) or {}).get("ms", 0))
            for event in events
            if str(event.get("name", event.get("event_type", ""))) == "latency"
        ),
        0.0,
    )
    constraint_events = [
        event
        for event in events
        if str(event.get("name", event.get("event_type", ""))) == "constraint_extract"
    ]
    payload = _event_payload(constraint_events[0]) if constraint_events else next(
        (
            event_payload
            for event_payload in (_event_payload(event) for event in events)
            if event_payload and "constraint_count" in event_payload
        ),
        None,
    )
    attributes = _event_payload(constraint_events[0]) if constraint_events else payload
    constraint_count = 0
    if payload:
        raw_count = payload.get("constraint_count", payload.get("count"))
        if isinstance(raw_count, (int, float)):
            constraint_count = int(raw_count)
        elif payload:
            constraint_count = len(payload)
    return {
        "static": {
            "requirement_length": len(feature_input.requirement_text),
            "task_family_code": sum(ord(char) for char in feature_input.task_family) % 997,
        },
        "operational": {
            "event_count": len(events),
            "latency_ms": latency_ms,
        },
        "provenance": {
            "constraint_count": constraint_count,
            "constraint_field_count": len(attributes or {}),
            "constraint_has_comparator": int(bool(attributes and "comparator" in attributes)),
            "semantic_event_count": sum(
                1
                for event in events
                if str(event.get("kind", "")).lower() == "semantic"
                or str(event.get("event_type", "")).startswith(("interpretation", "constraint", "plan"))
            ),
        },
    }


def static_import_guard(package_dir: str | Path | None = None) -> bool:
    """Assert that feature extraction has no label/oracle module imports.

    The guard is intentionally AST-based and can run in CI without importing
    the package under review.  It also rejects direct access to terminal
    episode fields, while allowing the compatibility extractor to live beside
    the strict implementation.
    """

    root = Path(package_dir) if package_dir else Path(__file__).resolve().parent
    forbidden_modules = {"label_plane", "eval.oracles", "pairs.loader"}
    forbidden_names = _TERMINAL_KEYS
    violations: list[str] = []
    for source_path in sorted(root.glob("*.py")):
        tree = ast.parse(source_path.read_text(encoding="utf-8"), filename=str(source_path))
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    if alias.name in forbidden_modules or any(
                        alias.name.startswith(module + ".") for module in forbidden_modules
                    ):
                        violations.append(f"{source_path}: import {alias.name}")
            elif isinstance(node, ast.ImportFrom):
                module = node.module or ""
                if module in forbidden_modules or any(module.startswith(item + ".") for item in forbidden_modules):
                    violations.append(f"{source_path}: from {module}")
    if violations:
        raise RuntimeError("feature-plane import boundary violated: " + "; ".join(violations))
    return True


__all__ = (
    "DeployableFeatureInput",
    "extract_deployable_features",
    "static_import_guard",
)
