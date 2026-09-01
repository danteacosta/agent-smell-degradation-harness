"""Secondary clean/smelly by context-condition interaction analysis.

This module is intentionally outside the primary H1/H2 estimands. It consumes
terminal ordinal outcomes only after collection and reports the difference of
the paired clean-minus-smelly contrast between the stress and no-compaction
cells. The feature plane never imports this module.
"""

from __future__ import annotations

import argparse
import json
from collections import defaultdict
from collections.abc import Mapping, Sequence
from pathlib import Path
from typing import Any

from protocol.paired_stats import clustered_bootstrap_ci, paired_permutation_pvalue

CONTEXT_CONDITIONS = ("no_compaction", "compaction_stress_test")
VARIANTS = ("clean", "smelly")
_SEVERITY_SCALE = {"low": 1.0, "medium": 2.0, "high": 3.0}
_CELLS = tuple(
    (variant, condition)
    for condition in CONTEXT_CONDITIONS
    for variant in VARIANTS
)


def _context_condition(episode: Mapping[str, Any]) -> str:
    direct = episode.get("context_condition")
    if isinstance(direct, str) and direct.strip():
        return direct.strip()
    provider_meta = episode.get("provider_meta")
    if isinstance(provider_meta, Mapping):
        context = provider_meta.get("context_management")
        if isinstance(context, Mapping):
            value = context.get("condition")
            if isinstance(value, str) and value.strip():
                return value.strip()
    return ""


def _ordinal_severity(value: Any) -> float:
    if isinstance(value, bool):
        raise ValueError("interaction severity must not be boolean")
    if isinstance(value, (int, float)):
        return float(value)
    normalized = str(value).strip().lower()
    if normalized in _SEVERITY_SCALE:
        return _SEVERITY_SCALE[normalized]
    raise ValueError(
        "interaction severity must be numeric or one of low, medium, high"
    )


def _case_key(episode: Mapping[str, Any]) -> tuple[str, str, int]:
    intent_id = str(episode.get("intent_id", "")).strip()
    task_family = str(episode.get("task_family", "")).strip()
    raw_replication = episode.get("replication_id", 0)
    if isinstance(raw_replication, bool) or not isinstance(raw_replication, int):
        raise ValueError("interaction replication_id must be an integer")
    if not intent_id or not task_family or raw_replication < 0:
        raise ValueError("interaction cases require intent_id, task_family, and replication_id")
    return intent_id, task_family, raw_replication


def _group_cells(
    episodes: Sequence[Mapping[str, Any]],
) -> dict[tuple[str, str, int], dict[tuple[str, str], float]]:
    grouped: dict[tuple[str, str, int], dict[tuple[str, str], float]] = {}
    for episode in episodes:
        if not isinstance(episode, Mapping):
            raise ValueError("interaction episodes must be objects")
        variant = str(episode.get("variant", "")).strip()
        condition = _context_condition(episode)
        if variant not in VARIANTS:
            raise ValueError(f"interaction has unsupported variant: {variant}")
        if condition not in CONTEXT_CONDITIONS:
            raise ValueError(
                "interaction has unsupported or missing context condition: "
                f"{condition or '<missing>'}"
            )
        key = _case_key(episode)
        cell = (variant, condition)
        values = grouped.setdefault(key, {})
        if cell in values:
            raise ValueError(f"duplicate interaction cell: {key}/{cell}")
        values[cell] = _ordinal_severity(episode.get("degradation_severity"))
    return grouped


def analyze_context_interaction(
    episodes: Sequence[Mapping[str, Any]],
    *,
    require_complete: bool = True,
) -> dict[str, Any]:
    """Compute the secondary 2x2 difference-in-differences estimate."""

    grouped = _group_cells(episodes)
    complete: list[tuple[tuple[str, str, int], dict[tuple[str, str], float]]] = []
    incomplete: list[dict[str, Any]] = []
    for key, cells in sorted(grouped.items()):
        missing = [cell for cell in _CELLS if cell not in cells]
        if missing:
            incomplete.append(
                {
                    "case": {
                        "intent_id": key[0],
                        "task_family": key[1],
                        "replication_id": key[2],
                    },
                    "missing_cells": [
                        f"{variant}/{condition}" for variant, condition in missing
                    ],
                }
            )
        else:
            complete.append((key, cells))
    if require_complete and incomplete:
        raise ValueError(
            "context interaction requires four cells per case; "
            f"{len(incomplete)} case(s) are incomplete"
        )

    cell_values: dict[str, list[float]] = defaultdict(list)
    per_cluster_values: dict[str, list[float]] = defaultdict(list)
    for key, cells in complete:
        for variant, condition in _CELLS:
            cell_values[f"{variant}/{condition}"].append(cells[(variant, condition)])
        no_compaction_delta = (
            cells[("clean", "no_compaction")]
            - cells[("smelly", "no_compaction")]
        )
        compaction_delta = (
            cells[("clean", "compaction_stress_test")]
            - cells[("smelly", "compaction_stress_test")]
        )
        interaction = compaction_delta - no_compaction_delta
        cluster_id = f"{key[0]}::{key[1]}"
        per_cluster_values[cluster_id].append(interaction)

    cluster_means = {
        cluster_id: sum(values) / len(values)
        for cluster_id, values in sorted(per_cluster_values.items())
        if values
    }
    interaction_mean = (
        sum(cluster_means.values()) / len(cluster_means)
        if cluster_means
        else 0.0
    )
    ci_low, ci_high = clustered_bootstrap_ci(per_cluster_values)
    cell_means = {
        cell: {
            "mean": round(sum(values) / len(values), 6) if values else 0.0,
            "count": len(values),
        }
        for cell, values in sorted(cell_values.items())
    }
    return {
        "schema_version": "context-interaction/v1",
        "confirmatory": False,
        "primary_estimand_changed": False,
        "requirement_factor": list(VARIANTS),
        "context_factor": list(CONTEXT_CONDITIONS),
        "estimand": (
            "(clean - smelly) under compaction_stress_test minus "
            "(clean - smelly) under no_compaction"
        ),
        "input_episode_count": len(episodes),
        "complete_case_count": len(complete),
        "incomplete_case_count": len(incomplete),
        "incomplete_cases": incomplete,
        "cell_means": cell_means,
        "cluster_unit": "intent_id/task_family",
        "complete_cluster_count": len(cluster_means),
        "interaction_mean": round(interaction_mean, 6),
        "interaction_ci95": {
            "low": round(ci_low, 6),
            "high": round(ci_high, 6),
        },
        "interaction_paired_permutation_pvalue": paired_permutation_pvalue(
            per_cluster_values
        ),
        "cluster_interactions": [
            {
                "cluster_id": cluster_id,
                "interaction": round(value, 6),
                "replication_count": len(per_cluster_values[cluster_id]),
            }
            for cluster_id, value in sorted(cluster_means.items())
        ],
    }


def write_context_interaction(
    episodes_path: Path | str,
    output_path: Path | str | None = None,
    *,
    require_complete: bool = True,
) -> dict[str, Any]:
    path = Path(episodes_path)
    episodes = [
        json.loads(line)
        for line in path.read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]
    report = analyze_context_interaction(episodes, require_complete=require_complete)
    if output_path is not None:
        destination = Path(output_path)
        destination.parent.mkdir(parents=True, exist_ok=True)
        destination.write_text(
            json.dumps(report, indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )
    return report


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--episodes", type=Path, required=True)
    parser.add_argument("--output", type=Path)
    parser.add_argument(
        "--allow-incomplete",
        action="store_true",
        help="Report complete cases while listing incomplete cases",
    )
    args = parser.parse_args(argv)
    report = write_context_interaction(
        args.episodes,
        args.output,
        require_complete=not args.allow_incomplete,
    )
    print(json.dumps(report, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
