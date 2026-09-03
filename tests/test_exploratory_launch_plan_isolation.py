from __future__ import annotations

import copy

from eval.prepilot_readiness import evaluate_launch_plan, load_launch_plan


def test_exploratory_fields_cannot_change_official_readiness() -> None:
    baseline = load_launch_plan("data/prepilot/launch-plan.candidate.json")
    before = evaluate_launch_plan(baseline)

    changed = copy.deepcopy(baseline)
    exploratory = changed["exploratory_llm_judged_prepilot"]
    exploratory.update(
        {
            "status": "completed",
            "corpus_manifest_sha256": "a" * 64,
            "configuration_sha256": "b" * 64,
            "judge_rubric_sha256": "c" * 64,
            "observed_logical_operations": 816,
            "observed_provider_api_calls": 1296,
            "observed_artifact_count": 240,
            "observed_judge_occurrence_count": 288,
            "observed_cost_usd": 0.91,
            "report_reference": "/private/tmp/exploratory-report.json",
        }
    )
    changed["exploratory_llm_judged_prepilot"]["provider_configurations"][0][
        "qualification_report_reference"
    ] = "/private/tmp/openai-smoke.json"
    changed["exploratory_llm_judged_prepilot"]["provider_configurations"][1][
        "qualification_report_reference"
    ] = "/private/tmp/deepseek-smoke.json"

    after = evaluate_launch_plan(changed)

    assert after["decision"] == before["decision"] == "no_go"
    assert after["blockers"] == before["blockers"]
    assert after["claim_level"] == before["claim_level"]
    assert after["confirmatory_authorized"] is False
