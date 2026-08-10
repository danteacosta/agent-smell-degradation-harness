from __future__ import annotations

import json

import pytest

from wedge.check import _tier_a_risk, run_fixture
from wedge.decisions import Decision


@pytest.mark.parametrize(
    ("fixture", "expected"),
    [
        ("demo-clean", Decision.APPROVE),
        ("demo-smelly", Decision.CLARIFY),
        ("demo-degraded", Decision.WARN),
    ],
)
def test_wedge_fixture_decisions(fixture: str, expected: Decision):
    result = run_fixture(fixture)
    assert result["decision"] == expected.value


def test_wedge_result_schema():
    result = run_fixture("demo-clean")
    assert set(result) >= {
        "decision",
        "reasons",
        "static_smell",
        "tier_a_risk",
        "tier_b_degraded",
    }
    json.dumps(result)


def test_wedge_tier_a_risk_uses_trace_derived_semantic_risk():
    assert _tier_a_risk(
        {
            "static_smell": {"smell_present": 0},
            "provenance_semantic": {
                "constraint_event_present": 1,
                "constraint_field_count": 2,
                "constraint_has_comparator": 1,
                "semantic_event_count": 1,
            },
        }
    ) == 0.0


def test_wedge_alert_contains_actionable_constraint_evidence():
    result = run_fixture("demo-degraded")
    assert result["evidence"]
    finding = result["evidence"][0]
    assert set(finding) >= {
        "constraint",
        "checkpoint",
        "confidence",
        "recommended_action",
    }
    assert finding["checkpoint"] == "pre-final"
    assert 0.0 <= finding["confidence"] <= 1.0
    assert finding["recommended_action"]
