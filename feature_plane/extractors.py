from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Mapping

from .models import FeatureEpisodeInput


def _events(provenance_path: str | Path) -> list[Mapping[str, Any]]:
    path = Path(provenance_path)
    if not path.exists():
        return []
    return [
        event
        for line in path.read_text(encoding="utf-8").splitlines()
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
    provenance_path: str | Path,
) -> dict[str, dict[str, float | int]]:
    events = _events(provenance_path)
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
    constraint_events = [
        event
        for event in events
        if event.get("kind") == "semantic"
        and event.get("name") == "constraint_extract"
    ]
    features = {
        "static_smell": _static_smell(feature_input),
        "operational": {"event_count": len(events), "latency_ms": latency_ms},
        "provenance_semantic": {
            "constraint_event_present": int(constraint_payload is not None),
            "constraint_field_count": len(constraint_payload or {}),
            "constraint_has_comparator": int(
                isinstance(constraint_payload, Mapping)
                and "comparator" in constraint_payload
            ),
            "semantic_event_count": len(constraint_events),
        },
    }
    interpretation = next(
        (
            event.get("payload")
            for event in events
            if event.get("kind") == "semantic"
            and event.get("name") == "interpretation.completed"
            and isinstance(event.get("payload"), Mapping)
        ),
        None,
    )
    plan = next(
        (
            event.get("payload")
            for event in events
            if event.get("kind") == "semantic"
            and event.get("name") == "plan.completed"
            and isinstance(event.get("payload"), Mapping)
        ),
        None,
    )
    execution = next(
        (
            event.get("payload")
            for event in events
            if event.get("name") == "tool.completed"
            and isinstance(event.get("payload"), Mapping)
        ),
        None,
    )
    rich_checkpoint_payload = interpretation is not None and any(
        key in interpretation
        for key in (
            "constraints",
            "quantities",
            "unresolved_references",
            "assumptions",
            "contradictions",
        )
    )
    if rich_checkpoint_payload:
        constraints = interpretation.get("constraints", [])
        quantities = interpretation.get("quantities", [])
        unresolved = interpretation.get("unresolved_references", [])
        assumptions = interpretation.get("assumptions", [])
        contradictions = interpretation.get("contradictions", [])
        plan = plan or {}
        execution = execution or {}
        semantic = features["provenance_semantic"]
        semantic.update(
            {
                "constraint_event_present": 1,
                "constraint_field_count": len(interpretation),
                "constraint_count": len(constraints) if isinstance(constraints, list) else 0,
                "quantity_count": len(quantities) if isinstance(quantities, list) else 0,
                "unresolved_reference_count": len(unresolved) if isinstance(unresolved, list) else 0,
                "assumption_count": len(assumptions) if isinstance(assumptions, list) else 0,
                "contradiction_count": len(contradictions) if isinstance(contradictions, list) else 0,
                "validation_check_count": (
                    len(plan.get("validation_checks", []))
                    if isinstance(plan.get("validation_checks", []), list)
                    else 0
                ),
                "planned_tool_count": (
                    len(plan.get("planned_tools", []))
                    if isinstance(plan.get("planned_tools", []), list)
                    else 0
                ),
                "coverage_target_count": (
                    len(plan.get("coverage_targets", []))
                    if isinstance(plan.get("coverage_targets", []), list)
                    else 0
                ),
                "revision_count": int(execution.get("revisions", 0)),
                "validation_attempt_count": int(execution.get("validation_attempts", 0)),
                "error_count": (
                    len(execution.get("errors", []))
                    if isinstance(execution.get("errors", []), list)
                    else 0
                ),
                "retrieval_event_count": int(execution.get("retrieval_events", 0)),
                "semantic_event_count": sum(
                    1
                    for event in events
                    if event.get("kind") == "semantic"
                    and event.get("name")
                    in {"interpretation.completed", "plan.completed"}
                ),
            }
        )
    return features
