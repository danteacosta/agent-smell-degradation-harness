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
        "variant",
        "variant_id",
        "smell",
        "defect_family",
        "defect_type",
        "mutation",
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
_CHECKPOINT_ORDER = {
    "input.received": 0,
    "interpretation.completed": 1,
    "plan.completed": 2,
    "execution.started": 3,
    "tool.completed": 4,
    "retrieval.completed": 4,
}


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
    # Canonical ARP attributes are the feature-plane boundary.  The legacy
    # payload may contain experiment metadata and is intentionally ignored.
    payload = event.get("attributes", event.get("payload"))
    return payload if isinstance(payload, Mapping) else None


def _load_deployable_events(provenance_path: str | Path) -> list[Mapping[str, Any]]:
    path = Path(provenance_path)
    if not path.exists():
        return []

    events: list[Mapping[str, Any]] = []
    last_order = -1
    for line in path.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        event = json.loads(line)
        if not isinstance(event, Mapping):
            raise ValueError("deployable trace event must be an object")
        # ARP v2's canonical checkpoint is authoritative; ``name`` is a
        # legacy compatibility label and may intentionally retain a terminal
        # historical name such as ``artifact.completed``.
        event_name = str(event.get("event_type", event.get("name", "")))
        event_name = {"constraint_extract": "interpretation.completed", "latency": "execution.started"}.get(event_name, event_name)
        # Tier-B oracle/evaluation events are deliberately outside the feature
        # plane.  They must be ignored rather than interpreted as features.
        if event.get("tier", "A") == "B":
            continue
        if event_name in _TERMINAL_EVENT_NAMES or str(event.get("checkpoint", "")).upper() in {
            "T4",
            "FINAL",
        }:
            raise ValueError(f"terminal event {event_name!r} is not deployable")
        # ARP v2 keeps deployable attributes separate from the legacy
        # compatibility payload, which may contain variant metadata for
        # retrospective reports. Inspect only the canonical attributes.
        terminal_source: Any = event.get("attributes") if "attributes" in event else event
        terminal_key = _contains_terminal_key(terminal_source)
        if terminal_key:
            raise ValueError(f"terminal field {terminal_key!r} found in deployable trace")
        if event_name not in _CHECKPOINT_ORDER:
            raise ValueError(f"non-deployable checkpoint {event_name!r}")
        order = _CHECKPOINT_ORDER[event_name]
        if order < last_order:
            raise ValueError("deployable checkpoints are out of order")
        last_order = order
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
    def checkpoint(name: str) -> Mapping[str, Any]:
        for event in events:
            event_name = str(event.get("checkpoint", event.get("event_type", event.get("name", ""))))
            if event_name == name:
                return _event_payload(event) or {}
        return {}

    interpretation = checkpoint("interpretation.completed")
    plan = checkpoint("plan.completed")
    execution = checkpoint("tool.completed")
    legacy = checkpoint("constraint_extract")
    if not interpretation and legacy:
        interpretation = legacy
    constraints = interpretation.get("constraints", [])
    quantities = interpretation.get("quantities", [])
    unresolved = interpretation.get("unresolved_references", [])
    assumptions = interpretation.get("assumptions", [])
    contradictions = interpretation.get("contradictions", [])
    validation_checks = plan.get("validation_checks", [])
    planned_tools = plan.get("planned_tools", [])
    coverage_targets = plan.get("coverage_targets", [])
    raw_count = interpretation.get("constraint_count", interpretation.get("count"))
    constraint_count = int(raw_count) if isinstance(raw_count, (int, float)) else len(constraints)
    comparator_text = " ".join(str(value) for value in constraints)
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
            "constraint_event_present": int(bool(interpretation or legacy)),
            "constraint_count": constraint_count,
            "constraint_field_count": len(interpretation),
            "constraint_has_comparator": int(any(token in comparator_text for token in ("<", ">", "="))),
            "quantity_count": len(quantities) if isinstance(quantities, list) else 0,
            "unresolved_reference_count": len(unresolved) if isinstance(unresolved, list) else 0,
            "assumption_count": len(assumptions) if isinstance(assumptions, list) else 0,
            "contradiction_count": len(contradictions) if isinstance(contradictions, list) else 0,
            "validation_check_count": len(validation_checks) if isinstance(validation_checks, list) else 0,
            "planned_tool_count": len(planned_tools) if isinstance(planned_tools, list) else 0,
            "coverage_target_count": len(coverage_targets) if isinstance(coverage_targets, list) else 0,
            "revision_count": int(execution.get("revisions", 0)),
            "validation_attempt_count": int(execution.get("validation_attempts", 0)),
            "error_count": len(execution.get("errors", [])) if isinstance(execution.get("errors", []), list) else 0,
            "retrieval_event_count": int(execution.get("retrieval_events", 0)),
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
    source_paths = [root / "deployable.py"] if (root / "deployable.py").exists() else sorted(root.glob("*.py"))
    for source_path in source_paths:
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
            elif isinstance(node, ast.Subscript):
                if isinstance(node.slice, ast.Constant) and str(node.slice.value).lower() in forbidden_names:
                    violations.append(f"{source_path}: terminal field {node.slice.value}")
            elif isinstance(node, ast.Attribute) and node.attr.lower() in forbidden_names:
                violations.append(f"{source_path}: terminal attribute {node.attr}")
    if violations:
        raise RuntimeError("feature-plane import boundary violated: " + "; ".join(violations))
    return True


__all__ = (
    "DeployableFeatureInput",
    "extract_deployable_features",
    "static_import_guard",
)
