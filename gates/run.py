from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import yaml


def load_thresholds(path: Path) -> dict[str, Any]:
    with path.open(encoding="utf-8") as fh:
        return yaml.safe_load(fh)


def load_baseline(path: Path) -> dict[str, Any]:
    with path.open(encoding="utf-8") as fh:
        return json.load(fh)


def check_gate(
    metrics: dict[str, Any],
    thresholds: dict[str, Any],
    baseline: dict[str, Any] | None = None,
) -> tuple[bool, list[str]]:
    """Return (passed, failure_messages). Baseline reserved for future slip checks."""
    _ = baseline
    failures: list[str] = []
    floors = thresholds.get("floors", {})
    ceilings = thresholds.get("ceilings", {})

    oracle_floor = floors.get("oracle_pass_rate_clean")
    if oracle_floor is not None:
        value = metrics.get("oracle_pass_rate_clean")
        if value is None or value < oracle_floor:
            failures.append(
                f"oracle_pass_rate_clean {value} below floor {oracle_floor}"
            )

    provenance_floor = floors.get("semantic_provenance_coverage")
    if provenance_floor is not None:
        value = metrics.get("semantic_provenance_coverage")
        if value is None or value < provenance_floor:
            failures.append(
                f"semantic_provenance_coverage {value} below floor {provenance_floor}"
            )

    degradation_ceiling = ceilings.get("paired_degradation_rate")
    if degradation_ceiling is not None:
        value = metrics.get("paired_degradation_rate")
        if value is None or value > degradation_ceiling:
            failures.append(
                f"paired_degradation_rate {value} above ceiling {degradation_ceiling}"
            )

    if thresholds.get("require_degradation_detector"):
        if "degradation_detected" not in metrics:
            failures.append("degradation_detected missing from metrics")
        elif not isinstance(metrics["degradation_detected"], bool):
            failures.append("degradation_detected must be a bool")
        else:
            paired_rate = metrics.get("paired_degradation_rate", 0.0)
            expected = paired_rate > 0
            if metrics["degradation_detected"] != expected:
                failures.append(
                    "degradation_detected "
                    f"{metrics['degradation_detected']} inconsistent with "
                    f"paired_degradation_rate {paired_rate}"
                )

    return len(failures) == 0, failures


def check_gate_blind(
    metrics: dict[str, Any],
    thresholds: dict[str, Any],
) -> tuple[bool, list[str]]:
    """Operational-only gate: oracle pass rate floor only."""
    failures: list[str] = []
    floors = thresholds.get("floors", {})
    oracle_floor = floors.get("oracle_pass_rate_clean")

    if oracle_floor is not None:
        value = metrics.get("oracle_pass_rate_clean")
        if value is None or value < oracle_floor:
            failures.append(
                f"oracle_pass_rate_clean {value} below floor {oracle_floor}"
            )

    return len(failures) == 0, failures
