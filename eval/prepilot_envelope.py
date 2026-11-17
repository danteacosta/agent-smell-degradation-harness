"""Offline budget-envelope calculator for the non-confirmatory pre-pilot.

Computes the ``budget`` fields that ``eval.prepilot_readiness`` requires
(``estimated_annotation_hours``, ``estimated_provider_cost_usd``) from
*explicit, human-supplied* assumptions. There are no defaults: a missing or
non-positive assumption is an error, so the tool cannot manufacture an
estimate. It reads the launch plan only for the design (episode count) and the
duplicate-coding fraction, never writes to it, makes no provider calls, and
approves nothing. The approved cap and every go/no-go gate stay human.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

SCHEMA_VERSION = "prepilot-envelope/v1"
REQUIRED = (
    "annotation_minutes_per_episode",
    "adjudication_fraction",
    "adjudication_minutes_per_episode",
    "provider_cost_usd_per_episode",
    "episodes_per_provider_configuration",
)


def _positive(assumptions: dict[str, Any], key: str, *, allow_zero: bool = False) -> float:
    if key not in assumptions:
        raise ValueError(f"missing assumption: {key}")
    value = assumptions[key]
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise ValueError(f"assumption {key} must be a number")
    if value < 0 or (value == 0 and not allow_zero):
        raise ValueError(f"assumption {key} must be positive")
    return float(value)


def compute_envelope(plan: dict[str, Any], assumptions: dict[str, Any]) -> dict[str, Any]:
    """Return the budget block implied by the plan design and the assumptions."""
    episodes = plan["design"]["episode_count"]
    dup = plan["annotation"]["duplicate_subset_fraction"]
    configs = len(plan["provider_configurations"])
    contingency = plan["budget"]["contingency_fraction"]
    if not isinstance(episodes, int) or episodes <= 0:
        raise ValueError("design.episode_count must be a positive integer")

    minutes = _positive(assumptions, "annotation_minutes_per_episode")
    adj_fraction = _positive(assumptions, "adjudication_fraction", allow_zero=True)
    adj_minutes = _positive(assumptions, "adjudication_minutes_per_episode")
    cost_each = _positive(assumptions, "provider_cost_usd_per_episode")
    per_config = _positive(assumptions, "episodes_per_provider_configuration")
    if adj_fraction > 1:
        raise ValueError("adjudication_fraction must be at most 1")

    # Every episode is coded once; the duplicate subset is coded by a second annotator.
    coded_units = episodes * (1.0 + dup)
    adjudicated = episodes * dup * adj_fraction
    hours = (coded_units * minutes + adjudicated * adj_minutes) / 60.0
    cost = configs * per_config * cost_each
    return {
        "schema_version": SCHEMA_VERSION,
        "status": "planning_arithmetic_only",
        "episodes": episodes,
        "coded_units": round(coded_units, 2),
        "adjudicated_units": round(adjudicated, 2),
        "provider_configurations": configs,
        "assumptions": {key: assumptions[key] for key in REQUIRED},
        "budget": {
            "estimated_annotation_hours": round(hours, 2),
            "estimated_provider_cost_usd": round(cost, 2),
            "projected_cost_with_contingency_usd": round(cost * (1.0 + contingency), 2),
            "contingency_fraction": contingency,
        },
        "note": "Arithmetic on stated assumptions; not a measurement. The approved cap and gates remain human decisions.",
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--plan", type=Path, required=True)
    parser.add_argument("--assumptions", type=Path, required=True)
    args = parser.parse_args(argv)
    try:
        plan = json.loads(args.plan.read_text(encoding="utf-8"))
        assumptions = json.loads(args.assumptions.read_text(encoding="utf-8"))
        report = compute_envelope(plan, assumptions)
    except (OSError, ValueError, KeyError, TypeError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2
    print(json.dumps(report, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
