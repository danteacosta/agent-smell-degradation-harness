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
            "pair_id": f"pair-{index}", "constraint_id": f"constraint-{index}", "family": family,
            "expected_decision": expected, "diagnostic_decision": expected,
            "baseline_decision": "support",
        })
    return {
        "schema_version": "evidence-diagnostic-qualification/v1",
        "project_split": {"calibration-project": "calibration", "evaluation-project": "evaluation"},
        "threshold_selected_on": "calibration", "diagnostic_threshold": 0.8,
        "label_review": {
            "reviewer_ids": ["reviewer-a", "reviewer-b"],
            "predictions_hidden_during_review": True,
            "completed_before_scoring": True,
            "rubric_sha256": "a" * 64,
            "frozen_labels_sha256": "b" * 64,
        },
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
    assert report["label_review"]["reviewer_count"] == 2


@pytest.mark.parametrize("mutation", [
    "duplicate", "missing_family", "unfrozen_threshold", "bad_threshold",
    "unknown_project", "wrong_expected", "bad_decision", "non_object",
    "missing_review", "single_reviewer", "predictions_visible", "bad_review_hash",
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
    elif mutation == "missing_review":
        value.pop("label_review")
    elif mutation == "single_reviewer":
        value["label_review"]["reviewer_ids"] = ["reviewer-a"]
    elif mutation == "predictions_visible":
        value["label_review"]["predictions_hidden_during_review"] = False
    elif mutation == "bad_review_hash":
        value["label_review"]["frozen_labels_sha256"] = "not-a-hash"
    with pytest.raises(ValueError):
        assess_evidence_diagnostic(value)


def test_development_records_never_enter_evaluation_metrics():
    value = packet()
    extra = copy.deepcopy(value["records"][0])
    extra.update(record_id="dev-only", pair_id="dev-pair", project_id="development-project",
                 diagnostic_decision="support")
    value["project_split"]["development-project"] = "development"
    value["records"].append(extra)
    report = assess_evidence_diagnostic(value)
    assert report["systems"]["diagnostic"]["scheduled_denominator"] == 3


@pytest.mark.parametrize("field", ["project_id", "constraint_id"])
def test_pair_identity_cannot_cross_projects_or_constraints(field):
    value = packet()
    extra = copy.deepcopy(value["records"][0])
    extra["record_id"] = "crossed-pair"
    if field == "project_id":
        value["project_split"]["second-evaluation-project"] = "evaluation"
        extra[field] = "second-evaluation-project"
    else:
        extra[field] = "different-constraint"
    value["records"].append(extra)
    with pytest.raises(ValueError, match="pair_id"):
        assess_evidence_diagnostic(value)
