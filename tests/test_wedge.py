from __future__ import annotations

import json

import pytest

from wedge.check import run_fixture
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
