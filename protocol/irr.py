from __future__ import annotations

import csv
from pathlib import Path
from typing import Any


def load_annotations(path: Path | str) -> list[dict[str, str]]:
    rows: list[dict[str, str]] = []
    with Path(path).open(encoding="utf-8", newline="") as handle:
        reader = csv.DictReader(handle)
        required = {"episode_id", "mode", "severity"}
        if reader.fieldnames is None or not required.issubset(set(reader.fieldnames)):
            missing = required - set(reader.fieldnames or [])
            raise ValueError(f"annotation file missing columns: {sorted(missing)}")
        for row in reader:
            rows.append({key: row[key] for key in required})
    return rows


def percent_agreement(y1: list[Any], y2: list[Any]) -> float:
    if len(y1) != len(y2):
        raise ValueError("label lists must have equal length")
    if not y1:
        return 0.0
    matches = sum(a == b for a, b in zip(y1, y2, strict=True))
    return matches / len(y1)


def cohens_kappa(y1: list[Any], y2: list[Any]) -> float:
    if len(y1) != len(y2):
        raise ValueError("label lists must have equal length")
    n = len(y1)
    if n == 0:
        return 0.0

    categories = sorted(set(y1) | set(y2))
    observed = sum(a == b for a, b in zip(y1, y2, strict=True)) / n
    expected = 0.0
    for category in categories:
        p1 = y1.count(category) / n
        p2 = y2.count(category) / n
        expected += p1 * p2

    if expected == 1.0:
        return 1.0 if observed == 1.0 else 0.0
    return (observed - expected) / (1.0 - expected)


def compare_annotations(
    path_a: Path | str,
    path_b: Path | str,
) -> dict[str, Any]:
    ann_a = load_annotations(path_a)
    ann_b = load_annotations(path_b)

    by_id_a = {row["episode_id"]: row for row in ann_a}
    by_id_b = {row["episode_id"]: row for row in ann_b}
    common_ids = sorted(set(by_id_a) & set(by_id_b))

    modes_a = [by_id_a[eid]["mode"] for eid in common_ids]
    modes_b = [by_id_b[eid]["mode"] for eid in common_ids]
    severities_a = [by_id_a[eid]["severity"] for eid in common_ids]
    severities_b = [by_id_b[eid]["severity"] for eid in common_ids]

    return {
        "n_items": len(common_ids),
        "mode_kappa": cohens_kappa(modes_a, modes_b),
        "mode_agreement": percent_agreement(modes_a, modes_b),
        "severity_kappa": cohens_kappa(severities_a, severities_b),
        "severity_agreement": percent_agreement(severities_a, severities_b),
    }
