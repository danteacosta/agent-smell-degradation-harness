from __future__ import annotations

from replay.integrations import normalize_trace_export
from replay.policy import DEFAULT_POLICY, load_failure_cases
from replay.utility import RunOutcome, summarize_outcomes


def test_observability_exports_normalize_without_terminal_data() -> None:
    for source, payload in (
        ("phoenix", {"spans": [{"name": "interpretation.completed", "attributes": {"constraints": ["x"]}}]}),
        ("langfuse", {"observations": [{"name": "plan.completed", "metadata": {"planned_tools": ["pytest"]}}]}),
        ("braintrust", {"spans": [{"name": "tool.completed", "attributes": {"errors": [], "revisions": 0}}]}),
    ):
        normalized = normalize_trace_export(source, payload)
        assert normalized["source"] == source
        assert normalized["events"]
        assert "oracle_passed" not in normalized["events"][0]["attributes"]


def test_unknown_source_and_terminal_attributes_fail_closed() -> None:
    try:
        normalize_trace_export("unknown", {"events": []})
    except ValueError as exc:
        assert "source" in str(exc)
    else:
        raise AssertionError("unknown source was accepted")
    try:
        normalize_trace_export("phoenix", {"spans": [{"name": "interpretation.completed", "attributes": {"label": "bad"}}]})
    except ValueError as exc:
        assert "terminal" in str(exc)
    else:
        raise AssertionError("terminal attributes were accepted")


def test_policy_and_failure_case_registry_are_versioned() -> None:
    assert DEFAULT_POLICY.version == "constraint-gate/v1"
    cases = load_failure_cases()
    assert cases
    assert all(case["case_id"] for case in cases)
    assert all(case["confirmatory"] is False for case in cases)


def test_utility_metrics_cover_roi_inputs() -> None:
    summary = summarize_outcomes(
        [
            RunOutcome("block", True, 40.0, False, 0.02, 120.0),
            RunOutcome("warn", False, 80.0, False, 0.03, None),
            RunOutcome("approve", True, 0.0, True, 0.01, None),
        ]
    )
    assert summary["captured_regressions"] == 1
    assert abs(summary["false_alerts_per_100_runs"] - 100 / 3) < 1e-9
    assert summary["escaped_incidents"] == 1
    assert summary["cost_per_run_usd"] == 0.02
    assert summary["lead_time_ms"] == 120.0


def test_utility_outcomes_reject_impossible_values() -> None:
    import math
    import pytest

    invalid = [
        {"decision": "bogus"},
        {"decision": "approve", "regression": 1},
        {"decision": "approve", "review_seconds": -1},
        {"decision": "approve", "cost_usd": math.nan},
        {"decision": "approve", "failure_time_ms": 4.0},
    ]
    for overrides in invalid:
        values = {"decision": "approve", "regression": False, "review_seconds": 0.0, "escaped_incident": False, "cost_usd": 0.0, "failure_time_ms": None}
        values.update(overrides)
        with pytest.raises(ValueError):
            RunOutcome(**values)
