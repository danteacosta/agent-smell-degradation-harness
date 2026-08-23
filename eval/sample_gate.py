"""Pilot and precision-governed confirmatory design gates."""

from __future__ import annotations

from collections import Counter
from collections.abc import Mapping, Sequence
from typing import Any

PILOT_MIN_INTENTS = 24
PILOT_MIN_PROJECTS = 6
MIN_CONFIRMATORY_INTENTS = 60
MIN_CONFIRMATORY_PROJECTS = 8
MIN_INTENTS_PER_PROJECT = 4
MIN_PROJECTS_PER_SPLIT = 2
MIN_TEST_INTENTS = 12
PRECISION_PLAN_SCHEMA = "h2-precision-plan/v1"


def _counts(episodes: Sequence[Mapping[str, Any]], partitions: Mapping[str, Sequence[Mapping[str, Any]]]) -> dict[str, Any]:
    intent_ids = {str(row.get("source_intent_id", row.get("intent_id", ""))) for row in episodes}
    project_ids = {str(row.get("project_id", "")) for row in episodes}
    per_project = Counter((str(row.get("project_id", "")), str(row.get("source_intent_id", row.get("intent_id", "")))) for row in episodes)
    project_intents: dict[str, set[str]] = {}
    for project, intent in per_project:
        project_intents.setdefault(project, set()).add(intent)
    return {
        "intent_count": len(intent_ids),
        "project_count": len(project_ids),
        "min_intents_per_project": min((len(value) for value in project_intents.values()), default=0),
        "split_intents": {split: len({str(row.get("source_intent_id", row.get("intent_id", ""))) for row in rows}) for split, rows in partitions.items()},
        "split_projects": {split: len({str(row.get("project_id", "")) for row in rows}) for split, rows in partitions.items()},
    }


def validate_pilot_design(episodes: Sequence[Mapping[str, Any]], partitions: Mapping[str, Sequence[Mapping[str, Any]]]) -> dict[str, Any]:
    counts = _counts(episodes, partitions)
    failures = []
    if counts["intent_count"] < PILOT_MIN_INTENTS:
        failures.append(f"requires at least {PILOT_MIN_INTENTS} independent intents")
    if counts["project_count"] < PILOT_MIN_PROJECTS:
        failures.append(f"requires at least {PILOT_MIN_PROJECTS} projects")
    if counts["min_intents_per_project"] < MIN_INTENTS_PER_PROJECT:
        failures.append(f"requires at least {MIN_INTENTS_PER_PROJECT} intents per project")
    if failures:
        raise ValueError("pilot design gate failed: " + "; ".join(failures))
    return {"status": "pilot", "counts": counts}


def validate_confirmatory_design(
    episodes: Sequence[Mapping[str, Any]],
    partitions: Mapping[str, Sequence[Mapping[str, Any]]],
    *,
    precision_plan: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    if precision_plan is None:
        raise ValueError("confirmatory design gate requires a frozen H2 precision plan")
    if precision_plan.get("schema_version") != PRECISION_PLAN_SCHEMA:
        raise ValueError("confirmatory precision plan has an unsupported schema")
    if precision_plan.get("status") != "frozen":
        raise ValueError("confirmatory precision plan must have status=frozen")
    simulation, thresholds, design = (precision_plan.get(key) for key in ("simulation", "thresholds", "design"))
    if not all(isinstance(value, Mapping) for value in (simulation, thresholds, design)):
        raise ValueError("confirmatory precision plan is incomplete")
    assert isinstance(simulation, Mapping) and isinstance(thresholds, Mapping) and isinstance(design, Mapping)
    if float(simulation["median_ci_width"]) > float(thresholds["max_median_ci_width"]):
        raise ValueError("confirmatory precision plan fails its CI-width threshold")
    if float(simulation["degenerate_rate"]) > float(thresholds["max_degenerate_rate"]):
        raise ValueError("confirmatory precision plan fails its degenerate-bootstrap threshold")
    if float(simulation["estimated_margin_power"]) < float(thresholds["target_margin_power"]):
        raise ValueError("confirmatory precision plan fails its target margin power")
    counts = _counts(episodes, partitions)
    required_intents = max(MIN_CONFIRMATORY_INTENTS, int(design["intents"]))
    required_projects = max(MIN_CONFIRMATORY_PROJECTS, int(design["projects"]))
    failures = []
    if counts["intent_count"] < required_intents:
        failures.append(f"requires at least {required_intents} independent intents")
    if counts["project_count"] < required_projects:
        failures.append(f"requires at least {required_projects} projects")
    if counts["min_intents_per_project"] < MIN_INTENTS_PER_PROJECT:
        failures.append(f"requires at least {MIN_INTENTS_PER_PROJECT} intents per project")
    if min(counts["split_projects"].values(), default=0) < MIN_PROJECTS_PER_SPLIT:
        failures.append(f"requires at least {MIN_PROJECTS_PER_SPLIT} projects per split")
    if counts["split_intents"].get("test", 0) < MIN_TEST_INTENTS:
        failures.append(f"requires at least {MIN_TEST_INTENTS} test intents")
    if failures:
        raise ValueError("confirmatory design gate failed: " + "; ".join(failures))
    return {"status": "confirmatory", "counts": counts, "precision_plan": {"schema_version": PRECISION_PLAN_SCHEMA, "design": dict(design), "simulation": dict(simulation), "thresholds": dict(thresholds)}}


__all__ = ("MIN_CONFIRMATORY_INTENTS", "MIN_CONFIRMATORY_PROJECTS", "MIN_INTENTS_PER_PROJECT", "MIN_PROJECTS_PER_SPLIT", "MIN_TEST_INTENTS", "PILOT_MIN_INTENTS", "PILOT_MIN_PROJECTS", "PRECISION_PLAN_SCHEMA", "validate_confirmatory_design", "validate_pilot_design")
