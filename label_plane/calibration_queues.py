"""Freeze a probability audit before creating an outcome-enriched review queue.

The probability sample is selected from blinded tasks using project-like strata
only. Diagnostic inputs are validated before sampling, but their boolean values
cannot change sample membership. Both outputs remain annotator-blinded; reasons live in the
private selection manifest.
"""

from __future__ import annotations

from hashlib import sha256
import json
import random
from typing import Any, Iterable, Mapping

from label_plane.annotation_protocol import (
    validate_blinded_outcome_payload,
    validate_blinded_payload,
)


_SIGNAL_FIELDS = (
    "machine_disagreement",
    "machine_abstention",
    "invalid_evidence",
    "metamorphic_violation",
    "incomplete_trace",
)
_SIGNAL_KEYS = frozenset({"item_id", "stratum_id", *_SIGNAL_FIELDS})


def _canonical_hash(value: Any) -> str:
    return sha256(
        json.dumps(
            value,
            ensure_ascii=False,
            sort_keys=True,
            separators=(",", ":"),
        ).encode("utf-8")
    ).hexdigest()


def _validated_tasks(tasks: Iterable[Mapping[str, Any]]) -> tuple[list[dict[str, Any]], str]:
    rows = [dict(task) for task in tasks]
    if not rows:
        raise ValueError("calibration queue preparation requires blinded tasks")
    kinds: set[str] = set()
    for task in rows:
        if "generated_acceptance_criteria" in task:
            validate_blinded_outcome_payload(task)
            kinds.add("primary_outcome")
        else:
            validate_blinded_payload(task)
            expected = {
                "item_id",
                "presented_text",
                "rubric_version",
                "duplicate_subset",
            }
            if set(task) != expected:
                raise ValueError("blinded requirement task has an invalid field set")
            if not str(task["item_id"]).strip() or not str(task["presented_text"]).strip():
                raise ValueError("blinded requirement task requires visible item and text")
            kinds.add("requirement")
    if len(kinds) != 1:
        raise ValueError("calibration queues cannot mix task kinds")
    ids = [str(task["item_id"]) for task in rows]
    if len(ids) != len(set(ids)):
        raise ValueError("blinded tasks require unique item IDs")
    rows.sort(key=lambda task: str(task["item_id"]))
    return rows, kinds.pop()


def _validated_signals(
    signals: Iterable[Mapping[str, Any]], item_ids: set[str]
) -> dict[str, dict[str, Any]]:
    by_id: dict[str, dict[str, Any]] = {}
    for raw in signals:
        row = dict(raw)
        extra = set(row) - _SIGNAL_KEYS
        if extra:
            raise ValueError(f"review signals contain unsupported fields: {sorted(extra)}")
        item_id = str(row.get("item_id") or "").strip()
        stratum_id = str(row.get("stratum_id") or "").strip()
        if not item_id or not stratum_id:
            raise ValueError("review signals require item_id and stratum_id")
        if item_id not in item_ids:
            raise ValueError(f"review signal references an unknown item: {item_id}")
        if item_id in by_id:
            raise ValueError(f"duplicate review signal for item: {item_id}")
        for field in _SIGNAL_FIELDS:
            if not isinstance(row.get(field, False), bool):
                raise ValueError(f"review signal {field} must be boolean")
            row[field] = row.get(field, False)
        by_id[item_id] = row
    missing = sorted(item_ids - set(by_id))
    if missing:
        raise ValueError(f"review signals missing blinded task IDs: {missing}")
    return by_id


def _allocation(strata: Mapping[str, list[str]], count: int) -> dict[str, int]:
    if count < len(strata):
        raise ValueError("calibration count must include at least one item per stratum")
    if count > sum(len(values) for values in strata.values()):
        raise ValueError("calibration count exceeds the task population")
    total = sum(len(values) for values in strata.values())
    allocation = {stratum: 1 for stratum in strata}
    while sum(allocation.values()) < count:
        candidates = [
            stratum
            for stratum, values in strata.items()
            if allocation[stratum] < len(values)
        ]
        chosen = max(
            candidates,
            key=lambda stratum: (
                count * len(strata[stratum]) / total - allocation[stratum],
                len(strata[stratum]),
                stratum,
            ),
        )
        allocation[chosen] += 1
    return allocation


def _sample_calibration(
    strata: Mapping[str, list[str]], *, count: int, seed: int
) -> tuple[set[str], list[dict[str, Any]]]:
    allocation = _allocation(strata, count)
    selected: set[str] = set()
    records: list[dict[str, Any]] = []
    for stratum in sorted(strata):
        ids = sorted(strata[stratum])
        derived_seed = int.from_bytes(
            sha256(f"{seed}:{stratum}".encode("utf-8")).digest()[:8], "big"
        )
        chosen = sorted(random.Random(derived_seed).sample(ids, allocation[stratum]))
        selected.update(chosen)
        probability = allocation[stratum] / len(ids)
        records.extend(
            {
                "item_id": item_id,
                "stratum_id": stratum,
                "inclusion_probability": probability,
            }
            for item_id in chosen
        )
    return selected, records


def _sample_triage(
    signals: Mapping[str, Mapping[str, Any]],
    calibration_ids: set[str],
    *,
    count: int,
) -> list[dict[str, Any]]:
    if count < 0:
        raise ValueError("triage count must be non-negative")
    groups: dict[str, list[dict[str, Any]]] = {}
    for item_id, signal in signals.items():
        if item_id in calibration_ids:
            continue
        reasons = [field for field in _SIGNAL_FIELDS if signal[field]]
        if not reasons:
            continue
        groups.setdefault(str(signal["stratum_id"]), []).append(
            {
                "item_id": item_id,
                "stratum_id": str(signal["stratum_id"]),
                "priority_score": len(reasons),
                "reasons": reasons,
            }
        )
    for rows in groups.values():
        rows.sort(key=lambda row: (-row["priority_score"], row["item_id"]))

    selected: list[dict[str, Any]] = []
    while len(selected) < count and any(groups.values()):
        round_strata = sorted(
            (stratum for stratum, rows in groups.items() if rows),
            key=lambda stratum: (-groups[stratum][0]["priority_score"], stratum),
        )
        for stratum in round_strata:
            if len(selected) == count:
                break
            selected.append(groups[stratum].pop(0))
    return selected


def freeze_calibration_queues(
    tasks: Iterable[Mapping[str, Any]],
    signals: Iterable[Mapping[str, Any]],
    *,
    calibration_count: int,
    triage_count: int,
    seed: int,
    source_selection_sha256: str,
) -> tuple[list[dict[str, Any]], list[dict[str, Any]], dict[str, Any]]:
    """Return disjoint blinded probability-audit and diagnostic-review queues."""

    if len(source_selection_sha256) != 64 or any(
        character not in "0123456789abcdef" for character in source_selection_sha256
    ):
        raise ValueError("source selection SHA-256 must be lowercase hexadecimal")
    rows, task_kind = _validated_tasks(tasks)
    by_id = {str(task["item_id"]): task for task in rows}
    signal_map = _validated_signals(signals, set(by_id))
    strata: dict[str, list[str]] = {}
    for item_id, signal in signal_map.items():
        strata.setdefault(str(signal["stratum_id"]), []).append(item_id)

    calibration_ids, calibration_records = _sample_calibration(
        strata, count=calibration_count, seed=seed
    )
    triage_records = _sample_triage(
        signal_map, calibration_ids, count=triage_count
    )
    triage_ids = {record["item_id"] for record in triage_records}
    calibration_tasks = [by_id[item_id] for item_id in sorted(calibration_ids)]
    triage_tasks = [by_id[item_id] for item_id in sorted(triage_ids)]
    manifest: dict[str, Any] = {
        "schema_version": "human-calibration-queues/v2",
        "source_selection_sha256": source_selection_sha256,
        "source_selection_verification": "caller_supplied_reference_not_verified",
        "hash_encoding": "sha256_utf8_sorted_keys_compact_json_ensure_ascii_false",
        "population_sha256": _canonical_hash(rows),
        "signals_sha256": _canonical_hash([signal_map[key] for key in sorted(signal_map)]),
        "calibration_tasks_sha256": _canonical_hash(calibration_tasks),
        "triage_tasks_sha256": _canonical_hash(triage_tasks),
        "task_kind": task_kind,
        "selection_order": "project_stratified_probability_sample_before_diagnostic_triage",
        "seed": seed,
        "population_count": len(rows),
        "stratum_count": len(strata),
        "calibration_count": len(calibration_tasks),
        "calibration_sample": sorted(
            calibration_records, key=lambda record: record["item_id"]
        ),
        "triage_count": len(triage_tasks),
        "triage_requested_count": triage_count,
        "triage_queue": triage_records,
        "interpretation": {
            "calibration": "probability sample; supports only prespecified sampling-based analyses",
            "triage": "outcome-enriched debugging queue; cannot estimate prevalence or accuracy",
            "confirmatory": "neither queue replaces blinded double annotation and adjudication",
        },
    }
    manifest["selection_sha256"] = _canonical_hash(manifest)
    return calibration_tasks, triage_tasks, manifest
