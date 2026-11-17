from __future__ import annotations

import json
from pathlib import Path

import pytest

from eval.prepilot_envelope import compute_envelope, main
from eval.prepilot_readiness import evaluate_launch_plan, load_launch_plan

ROOT = Path(__file__).parents[1]
CANDIDATE = ROOT / "data" / "prepilot" / "launch-plan.candidate.json"
ASSUMPTIONS = {
    "annotation_minutes_per_episode": 12,
    "adjudication_fraction": 0.25,
    "adjudication_minutes_per_episode": 10,
    "provider_cost_usd_per_episode": 0.5,
    "episodes_per_provider_configuration": 120,
}


def test_arithmetic_is_explicit():
    plan = load_launch_plan(CANDIDATE)
    out = compute_envelope(plan, ASSUMPTIONS)["budget"]
    # 120*1.2=144 coded units *12 min = 1728; adjudicated 120*0.2*0.25=6 *10 = 60; /60
    assert out["estimated_annotation_hours"] == pytest.approx((1728 + 60) / 60)
    assert out["estimated_provider_cost_usd"] == 120.0  # 2 configs * 120 * 0.5
    assert out["projected_cost_with_contingency_usd"] == 150.0


@pytest.mark.parametrize("key", sorted(ASSUMPTIONS))
def test_missing_assumption_is_rejected(key):
    plan = load_launch_plan(CANDIDATE)
    bad = {k: v for k, v in ASSUMPTIONS.items() if k != key}
    with pytest.raises(ValueError, match=key):
        compute_envelope(plan, bad)


def test_nonpositive_and_bool_rejected():
    plan = load_launch_plan(CANDIDATE)
    with pytest.raises(ValueError):
        compute_envelope(plan, {**ASSUMPTIONS, "provider_cost_usd_per_episode": 0})
    with pytest.raises(ValueError):
        compute_envelope(plan, {**ASSUMPTIONS, "annotation_minutes_per_episode": True})
    with pytest.raises(ValueError):
        compute_envelope(plan, {**ASSUMPTIONS, "adjudication_fraction": 1.5})


def test_envelope_clears_only_the_effort_blocker_and_keeps_no_go(tmp_path):
    plan = load_launch_plan(CANDIDATE)
    before = evaluate_launch_plan(plan)
    plan["budget"]["estimated_annotation_hours"] = compute_envelope(plan, ASSUMPTIONS)["budget"][
        "estimated_annotation_hours"
    ]
    after = evaluate_launch_plan(plan)
    assert "annotation effort has not been estimated" in before["blockers"]
    assert "annotation effort has not been estimated" not in after["blockers"]
    assert after["decision"] == "no_go"
    assert after["approved_cap_usd"] == 0.0


def test_cli_does_not_modify_plan_and_reports_errors(tmp_path, capsys):
    a = tmp_path / "a.json"
    a.write_text(json.dumps(ASSUMPTIONS))
    before = CANDIDATE.read_bytes()
    assert main(["--plan", str(CANDIDATE), "--assumptions", str(a)]) == 0
    assert CANDIDATE.read_bytes() == before
    a.write_text("{}")
    assert main(["--plan", str(CANDIDATE), "--assumptions", str(a)]) == 2
