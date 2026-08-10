from __future__ import annotations

from dataclasses import dataclass
from statistics import mean
from typing import Any


@dataclass(frozen=True)
class RunOutcome:
    decision: str
    regression: bool
    review_seconds: float
    escaped_incident: bool
    cost_usd: float
    failure_time_ms: float | None


def summarize_outcomes(outcomes: list[RunOutcome]) -> dict[str, Any]:
    if not outcomes:
        raise ValueError("at least one outcome is required")
    captured = sum(item.regression and item.decision in {"warn", "block"} for item in outcomes)
    false_alerts = sum((not item.regression) and item.decision in {"warn", "block"} for item in outcomes)
    lead_times = [
        item.failure_time_ms
        for item in outcomes
        if item.regression and item.failure_time_ms is not None and item.decision in {"warn", "block"}
    ]
    escaped = sum(item.escaped_incident for item in outcomes)
    return {
        "runs": len(outcomes),
        "captured_regressions": captured,
        "false_alerts_per_100_runs": false_alerts / len(outcomes) * 100,
        "escaped_incidents": escaped,
        "escaped_incident_rate": escaped / len(outcomes),
        "review_seconds_mean": mean(item.review_seconds for item in outcomes),
        "cost_per_run_usd": mean(item.cost_usd for item in outcomes),
        "lead_time_ms": mean(lead_times) if lead_times else None,
        "status": "pilot_metric_not_customer_evidence",
    }
