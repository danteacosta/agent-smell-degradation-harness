from __future__ import annotations

from dataclasses import dataclass
import math
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

    def __post_init__(self) -> None:
        if self.decision not in {"approve", "warn", "block"}:
            raise ValueError("decision must be approve, warn, or block")
        if type(self.regression) is not bool or type(self.escaped_incident) is not bool:
            raise ValueError("regression and escaped_incident must be booleans")
        for name, value in (("review_seconds", self.review_seconds), ("cost_usd", self.cost_usd)):
            if isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(value) or value < 0:
                raise ValueError(f"{name} must be a finite non-negative number")
        if self.failure_time_ms is not None:
            if isinstance(self.failure_time_ms, bool) or not isinstance(self.failure_time_ms, (int, float)) or not math.isfinite(self.failure_time_ms) or self.failure_time_ms < 0:
                raise ValueError("failure_time_ms must be None or a finite non-negative number")
            if not self.regression or self.decision not in {"warn", "block"}:
                raise ValueError("failure_time_ms requires a captured regression")


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
