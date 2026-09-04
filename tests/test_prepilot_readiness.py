from __future__ import annotations

import copy
import json
from pathlib import Path

import pytest

from eval.prepilot_readiness import evaluate_launch_plan, load_launch_plan


ROOT = Path(__file__).parents[1]
CANDIDATE = ROOT / "data" / "prepilot" / "launch-plan.candidate.json"


def _ready_plan() -> dict:
    plan = load_launch_plan(CANDIDATE)
    plan["status"] = "pilot_ready"
    plan["corpus"].update(
        {
            "manifest_frozen": True,
            "unique_intents": 12,
            "all_sources_licensed": True,
            "all_project_ids_present": True,
            "near_clone_screening_complete": True,
            "manipulation_checks_complete": True,
            "development_seed_replaced": True,
        }
    )
    for index, config in enumerate(plan["provider_configurations"]):
        config.update(
            {
                "provider": f"provider-{index}",
                "model": f"model-{index}",
                "model_version": "2026-08",
                "qualification_passed": True,
                "qualification_report_path": f"runs/qualification-{index}.json",
                "t1_t3_before_t4": True,
                "configuration_hash": f"hash-{index}",
            }
        )
    plan["annotation"].update(
        {
            "rubric_frozen": True,
            "trained_annotators": 2,
            "duplicate_subset_selected_outcome_blind": True,
            "blinding_verified": True,
            "adjudication_owner": "independent-reviewer",
        }
    )
    plan["budget"].update(
        {
            "estimated_provider_cost_usd": 80,
            "approved_cap_usd": 125,
            "estimated_annotation_hours": 24,
        }
    )
    plan["go_no_go"] = {key: True for key in plan["go_no_go"]}
    return plan


def test_checked_in_candidate_is_honestly_blocked() -> None:
    report = evaluate_launch_plan(load_launch_plan(CANDIDATE))

    assert report["decision"] == "no_go"
    assert report["confirmatory_authorized"] is False
    assert "development seed has not been replaced" not in report["blockers"]
    assert "corpus manifest is not frozen" not in report["blockers"]
    assert "corpus does not contain 12 unique intents" not in report["blockers"]
    assert any("provider configuration" in item for item in report["blockers"])
    assert "annotation rubric is not frozen" in report["blockers"]
    assert any("advisor_authorized_pre_pilot" in item for item in report["blockers"])


def test_complete_pre_pilot_plan_can_pass_without_authorizing_confirmatory() -> None:
    report = evaluate_launch_plan(_ready_plan())

    assert report["decision"] == "go"
    assert report["blockers"] == []
    assert report["projected_provider_cost_usd"] == 100
    assert report["confirmatory_authorized"] is False


def test_duplicate_provider_configuration_fails_closed() -> None:
    plan = _ready_plan()
    plan["provider_configurations"][1] = copy.deepcopy(plan["provider_configurations"][0])

    report = evaluate_launch_plan(plan)

    assert report["decision"] == "no_go"
    assert "provider/model configurations must be distinct" in report["blockers"]


def test_budget_over_cap_fails_closed() -> None:
    plan = _ready_plan()
    plan["budget"]["approved_cap_usd"] = 99

    report = evaluate_launch_plan(plan)

    assert report["decision"] == "no_go"
    assert "provider cost plus contingency exceeds the approved cap" in report["blockers"]


def test_confirmatory_claim_level_is_rejected() -> None:
    plan = _ready_plan()
    plan["claim_level"] = "confirmatory"

    with pytest.raises(ValueError, match="non_confirmatory_pre_pilot"):
        evaluate_launch_plan(plan)


def test_secret_like_fields_are_rejected(tmp_path: Path) -> None:
    plan = _ready_plan()
    plan["provider_configurations"][0]["api_key"] = "do-not-store"
    path = tmp_path / "plan.json"
    path.write_text(json.dumps(plan), encoding="utf-8")

    with pytest.raises(ValueError, match="secret-like field"):
        load_launch_plan(path)
