"""Frozen confirmatory sample-size and project-holdout gate."""

from __future__ import annotations

from collections import Counter
from collections.abc import Mapping, Sequence
from typing import Any

MIN_INTENTS = 24
MIN_PROJECTS = 6
MIN_INTENTS_PER_PROJECT = 4
MIN_INTENTS_PER_SPLIT = 8


def validate_confirmatory_design(
    episodes: Sequence[Mapping[str, Any]],
    partitions: Mapping[str, Sequence[Mapping[str, Any]]],
) -> dict[str, Any]:
    intent_ids = {str(row.get("source_intent_id", row.get("intent_id", ""))) for row in episodes}
    project_ids = {str(row.get("project_id", "")) for row in episodes}
    per_project = Counter(
        (str(row.get("project_id", "")), str(row.get("source_intent_id", row.get("intent_id", ""))))
        for row in episodes
    )
    project_intents: dict[str, set[str]] = {}
    for project, intent in per_project:
        project_intents.setdefault(project, set()).add(intent)
    split_intents = {
        split: len({str(row.get("source_intent_id", row.get("intent_id", ""))) for row in rows})
        for split, rows in partitions.items()
    }
    counts = {
        "intent_count": len(intent_ids),
        "project_count": len(project_ids),
        "min_intents_per_project": min((len(value) for value in project_intents.values()), default=0),
        "split_intents": split_intents,
    }
    failures = []
    if counts["intent_count"] < MIN_INTENTS:
        failures.append(f"requires at least {MIN_INTENTS} independent intents")
    if counts["project_count"] < MIN_PROJECTS:
        failures.append(f"requires at least {MIN_PROJECTS} projects")
    if counts["min_intents_per_project"] < MIN_INTENTS_PER_PROJECT:
        failures.append(f"requires at least {MIN_INTENTS_PER_PROJECT} intents per project")
    if any(value < MIN_INTENTS_PER_SPLIT for value in split_intents.values()):
        failures.append(f"requires at least {MIN_INTENTS_PER_SPLIT} intents per split")
    if failures:
        raise ValueError("confirmatory design gate failed: " + "; ".join(failures))
    return {"status": "confirmatory", "counts": counts}


__all__ = (
    "MIN_INTENTS",
    "MIN_PROJECTS",
    "MIN_INTENTS_PER_PROJECT",
    "MIN_INTENTS_PER_SPLIT",
    "validate_confirmatory_design",
)
