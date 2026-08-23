"""Deterministic, leakage-resistant splits for the confirmatory H2 analysis.

The unit of assignment is a connected component of ``source_intent_id`` and
``project_id``.  This is slightly stricter than assigning intents alone: if a
project contains more than one source intent, all of those intents travel
together so that neither source-intent nor project information can cross a
split boundary.  Variants and replications are records inside that component
and are therefore kept together automatically.
"""

from __future__ import annotations

import hashlib
import json
from collections import defaultdict
from typing import Any, Mapping, Sequence

SPLITS = ("train", "calibration", "test")


def _required_group(record: Mapping[str, Any], key: str, *, index: int) -> str:
    value = record.get(key)
    if value is None or not str(value).strip():
        raise ValueError(f"record {index} is missing required grouping field {key}")
    return str(value)


def _source_intent(record: Mapping[str, Any], *, index: int) -> str:
    """Accept runtime ``intent_id`` while emitting canonical source IDs."""

    value = record.get("source_intent_id", record.get("intent_id"))
    if value is None or not str(value).strip():
        raise ValueError(f"record {index} is missing required grouping field source_intent_id")
    return str(value)


def _component_groups(records: Sequence[Mapping[str, Any]]) -> list[dict[str, list[str]]]:
    """Build bipartite connected components for intent/project groups."""

    parent: dict[tuple[str, str], tuple[str, str]] = {}

    def find(node: tuple[str, str]) -> tuple[str, str]:
        parent.setdefault(node, node)
        while parent[node] != node:
            parent[node] = parent[parent[node]]
            node = parent[node]
        return node

    def union(left: tuple[str, str], right: tuple[str, str]) -> None:
        left_root, right_root = find(left), find(right)
        if left_root != right_root:
            parent[right_root] = left_root

    pairs: list[tuple[str, str]] = []
    for index, record in enumerate(records):
        source = _source_intent(record, index=index)
        project = _required_group(record, "project_id", index=index)
        intent_node = ("intent", source)
        project_node = ("project", project)
        union(intent_node, project_node)
        pairs.append((source, project))

    grouped: dict[tuple[str, str], dict[str, set[str]]] = defaultdict(
        lambda: {"source_intent_ids": set(), "project_ids": set()}
    )
    for source, project in pairs:
        component = grouped[find(("intent", source))]
        component["source_intent_ids"].add(source)
        component["project_ids"].add(project)
    return [
        {
            "source_intent_ids": sorted(values["source_intent_ids"]),
            "project_ids": sorted(values["project_ids"]),
        }
        for values in grouped.values()
    ]


def _stable_component_order(components: list[dict[str, list[str]]], seed: int) -> list[dict[str, list[str]]]:
    def key(component: Mapping[str, list[str]]) -> str:
        payload = {"seed": seed, "source_intent_ids": component["source_intent_ids"], "project_ids": component["project_ids"]}
        return hashlib.sha256(json.dumps(payload, sort_keys=True).encode("utf-8")).hexdigest()

    return sorted(components, key=key)


def build_grouped_split_manifest(
    records: Sequence[Mapping[str, Any]],
    *,
    seed: int = 0,
    train_fraction: float = 0.6,
    calibration_fraction: float = 0.2,
    test_fraction: float = 0.2,
    min_groups_per_split: int = 1,
) -> dict[str, Any]:
    """Return a reproducible train/calibration/test assignment manifest.

    The function deliberately fails closed when project identity is absent or
    fewer than three disjoint connected components are available.  A
    confirmatory holdout cannot be justified by silently falling back to an
    intent-only split.
    """

    if not records:
        raise ValueError("confirmatory split requires at least one record")
    fractions = (train_fraction, calibration_fraction, test_fraction)
    if any(value <= 0 for value in fractions) or abs(sum(fractions) - 1.0) > 1e-9:
        raise ValueError("split fractions must be positive and sum to 1")
    components = _component_groups(records)
    if min_groups_per_split < 1:
        raise ValueError("min_groups_per_split must be positive")
    if len(components) < len(SPLITS) * min_groups_per_split:
        required_groups = len(SPLITS) * min_groups_per_split
        required_label = "three" if required_groups == 3 else str(required_groups)
        raise ValueError(
            f"confirmatory split requires at least {required_label} "
            "disjoint source/project groups for the requested holdout"
        )
    ordered = _stable_component_order(components, seed)
    total_records = len(records)
    targets = {
        "train": total_records * train_fraction,
        "calibration": total_records * calibration_fraction,
        "test": total_records * test_fraction,
    }
    assignments: dict[tuple[str, str], str] = {}
    counts = {split: 0 for split in SPLITS}
    # Convert fractions to deterministic component quotas, subject to an
    # explicit minimum.  This avoids the old six-group round-robin behavior
    # that silently turned a nominal 60/20/20 split into 33/33/33.
    quotas = {split: min_groups_per_split for split in SPLITS}
    remaining = len(components) - sum(quotas.values())
    while remaining:
        split = max(
            SPLITS,
            key=lambda candidate: (
                len(components) * fractions[SPLITS.index(candidate)] - quotas[candidate],
                -SPLITS.index(candidate),
            ),
        )
        quotas[split] += 1
        remaining -= 1
    assigned_groups = {split: 0 for split in SPLITS}
    component_sizes = {
        tuple(component["source_intent_ids"]): sum(
            1
            for record_index, record in enumerate(records)
            if _source_intent(record, index=record_index) in component["source_intent_ids"]
        )
        for component in ordered
    }
    ordered = sorted(
        ordered,
        key=lambda component: (-component_sizes[tuple(component["source_intent_ids"])], ordered.index(component)),
    )
    for component in ordered:
        eligible = [split for split in SPLITS if assigned_groups[split] < quotas[split]]
        split = max(
            eligible,
            key=lambda candidate: (
                targets[candidate] - counts[candidate],
                quotas[candidate] - assigned_groups[candidate],
                -SPLITS.index(candidate),
            ),
        )
        for source in component["source_intent_ids"]:
            for project in component["project_ids"]:
                assignments[(source, project)] = split
        counts[split] += sum(
            1
            for record_index, record in enumerate(records)
            if _source_intent(record, index=record_index) in component["source_intent_ids"]
        )
        assigned_groups[split] += 1

    assignment_rows = [
        {
            "source_intent_id": source,
            "project_id": project,
            "split": assignments[(source, project)],
        }
        for source, project in sorted(assignments)
    ]
    assignment_hash = hashlib.sha256(
        json.dumps(assignment_rows, sort_keys=True, separators=(",", ":")).encode("utf-8")
    ).hexdigest()
    return {
        "schema_version": "h2-split-1",
        "group_by": ["source_intent_id", "project_id"],
        "seed": seed,
        "fractions": {
            "train": train_fraction,
            "calibration": calibration_fraction,
            "test": test_fraction,
        },
        "assignments": assignment_rows,
        "provenance": {
            "seed": seed,
            "algorithm": "stable-bipartite-component-quota-greedy-v2",
            "record_count": total_records,
            "group_count": len(components),
            "group_quotas": quotas,
            "record_counts": counts,
            "assignment_hash": assignment_hash,
        },
    }


def apply_split_manifest(
    records: Sequence[Mapping[str, Any]], manifest: Mapping[str, Any]
) -> dict[str, list[Mapping[str, Any]]]:
    """Apply and validate a split manifest to records without reassigning them."""

    assignments = {
        (str(row["source_intent_id"]), str(row["project_id"])): str(row["split"])
        for row in manifest.get("assignments", [])
    }
    if set(assignments.values()) != set(SPLITS):
        raise ValueError("split manifest must contain train, calibration, and test assignments")
    partitions: dict[str, list[Mapping[str, Any]]] = {split: [] for split in SPLITS}
    for index, record in enumerate(records):
        source = _source_intent(record, index=index)
        project = _required_group(record, "project_id", index=index)
        split = assignments.get((source, project))
        if split is None:
            raise ValueError(f"record {index} has no assignment in split manifest")
        if split not in partitions:
            raise ValueError(f"invalid split {split!r}")
        partitions[split].append(record)
    if any(not rows for rows in partitions.values()):
        raise ValueError("split manifest produced an empty partition")
    return partitions


# Short aliases make the protocol convenient for callers while preserving one
# canonical implementation and manifest shape.
build_confirmatory_split_manifest = build_grouped_split_manifest
apply_confirmatory_split_manifest = apply_split_manifest


__all__ = (
    "SPLITS",
    "apply_confirmatory_split_manifest",
    "apply_split_manifest",
    "build_confirmatory_split_manifest",
    "build_grouped_split_manifest",
)
