import copy

import pytest

from eval.evidence_diagnostic_qualification import assess_evidence_diagnostic


def packet():
    families = {
        "wrong_binding": "reject",
        "valid_alternative": "support",
        "insufficient_evidence": "abstain",
    }
    records = []
    for index, (family, expected) in enumerate(families.items()):
        records.append({
            "record_id": f"eval-{index}", "project_id": "evaluation-project",
            "constraint_id": f"constraint-{index}", "family": family,
            "expected_decision": expected, "diagnostic_decision": expected,
            "baseline_decision": "support",
        })
    return {
        "schema_version": "evidence-diagnostic-qualification/v1",
        "project_split": {"calibration-project": "calibration", "evaluation-project": "evaluation"},
        "threshold_selected_on": "calibration", "diagnostic_threshold": 0.8,
        "records": records,
    }


def test_reports_each_failure_mode_without_hiding_the_scheduled_denominator():
    report = assess_evidence_diagnostic(packet())
    assert report["confirmatory_eligible"] is False
    assert report["systems"]["diagnostic"]["scheduled_denominator"] == 3
    assert report["systems"]["diagnostic"]["strict_accuracy"] == 1
    assert report["systems"]["baseline"]["strict_accuracy"] == pytest.approx(1 / 3)
    assert report["diagnostic_minus_baseline"]["valid_alternative"] == 0
    assert report["diagnostic_minus_baseline"]["wrong_binding"] == 1


@pytest.mark.parametrize("mutation", [
    "duplicate", "missing_family", "unfrozen_threshold", "bad_threshold",
    "unknown_project", "wrong_expected", "bad_decision", "non_object",
])
def test_malformed_or_leaky_packets_fail_closed(mutation):
    value = packet()
    if mutation == "duplicate":
        value["records"][1]["record_id"] = value["records"][0]["record_id"]
    elif mutation == "missing_family":
        value["records"].pop()
    elif mutation == "unfrozen_threshold":
        value["threshold_selected_on"] = "evaluation"
    elif mutation == "bad_threshold":
        value["diagnostic_threshold"] = float("nan")
    elif mutation == "unknown_project":
        value["records"][0]["project_id"] = "not-in-split"
    elif mutation == "wrong_expected":
        value["records"][0]["expected_decision"] = "support"
    elif mutation == "bad_decision":
        value["records"][0]["diagnostic_decision"] = "maybe"
    elif mutation == "non_object":
        value["records"][0] = []
    with pytest.raises(ValueError):
        assess_evidence_diagnostic(value)


def test_development_records_never_enter_evaluation_metrics():
    value = packet()
    extra = copy.deepcopy(value["records"][0])
    extra.update(record_id="dev-only", project_id="development-project", diagnostic_decision="support")
    value["project_split"]["development-project"] = "development"
    value["records"].append(extra)
    report = assess_evidence_diagnostic(value)
    assert report["systems"]["diagnostic"]["scheduled_denominator"] == 3
