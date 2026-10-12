import copy
import hashlib
import json

import pytest

from eval.evidence_diagnostic_qualification import assess_evidence_diagnostic


LABEL_FIELDS = ("record_id", "pair_id", "project_id", "constraint_id", "family", "expected_decision")


def freeze_labels(value):
    value["frozen_labels"] = [{key: row[key] for key in LABEL_FIELDS} for row in value["records"]]
    frozen = {"project_split": value["project_split"], "labels": value["frozen_labels"]}
    encoded = json.dumps(frozen, sort_keys=True, separators=(",", ":"), ensure_ascii=True).encode("utf-8")
    value["label_review"]["frozen_labels_sha256"] = hashlib.sha256(encoded).hexdigest()
    return value


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
    return freeze_labels({
        "schema_version": "evidence-diagnostic-qualification/v1",
        "project_split": {"calibration-project": "calibration", "evaluation-project": "evaluation"},
        "threshold_selected_on": "calibration", "diagnostic_threshold": 0.8,
        "label_review": {
            "reviewer_ids": ["reviewer-a", "reviewer-b"],
            "predictions_hidden_during_review": True,
            "completed_before_scoring": True,
            "rubric_sha256": hashlib.sha256(b"authored qualification rubric v1").hexdigest(),
            "frozen_labels_sha256": "",
        },
        "records": records,
    })


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
    freeze_labels(value)
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
    freeze_labels(value)
    with pytest.raises(ValueError, match="pair_id"):
        assess_evidence_diagnostic(value)


def test_deleting_a_failed_scheduled_record_cannot_improve_accuracy():
    value = packet()
    failed = copy.deepcopy(value["records"][0])
    failed.update(record_id="scheduled-failure", pair_id="failed-pair", diagnostic_decision="support")
    value["records"].append(failed)
    freeze_labels(value)
    report = assess_evidence_diagnostic(value)
    assert report["systems"]["diagnostic"]["scheduled_denominator"] == 4
    assert report["systems"]["diagnostic"]["strict_accuracy"] == 0.75
    value["records"].pop()
    with pytest.raises(ValueError, match="frozen"):
        assess_evidence_diagnostic(value)


@pytest.mark.parametrize("change", ["insert_result", "change_identity", "change_label", "delete_inventory", "change_inventory", "missing_inventory"])
def test_scoring_requires_exact_frozen_identity_and_label_coverage(change):
    value = packet()
    if change == "insert_result":
        extra = copy.deepcopy(value["records"][0])
        extra["record_id"] = "unplanned"
        value["records"].append(extra)
    elif change == "change_identity":
        value["records"][0]["constraint_id"] = "substituted"
    elif change == "change_label":
        value["records"][0].update(family="valid_alternative", expected_decision="support")
    elif change == "delete_inventory":
        value["frozen_labels"].pop()
    elif change == "change_inventory":
        value["frozen_labels"][0]["constraint_id"] = "substituted"
    else:
        value.pop("frozen_labels")
    with pytest.raises(ValueError, match="frozen"):
        assess_evidence_diagnostic(value)


def test_result_order_and_predictions_do_not_change_the_frozen_labels():
    value = packet()
    frozen_hash = value["label_review"]["frozen_labels_sha256"]
    value["records"].reverse()
    value["records"][0]["diagnostic_decision"] = "support"
    report = assess_evidence_diagnostic(value)
    assert report["systems"]["diagnostic"]["scheduled_denominator"] == 3
    assert report["systems"]["diagnostic"]["strict_accuracy"] == pytest.approx(2 / 3)
    assert report["label_review"]["frozen_labels_sha256"] == frozen_hash


@pytest.mark.parametrize("decision", [None, "failed", ""])
def test_missing_or_failed_decisions_cannot_produce_a_partial_score(decision):
    value = packet()
    value["records"][0]["diagnostic_decision"] = decision
    with pytest.raises(ValueError):
        assess_evidence_diagnostic(value)


@pytest.mark.parametrize("mutation", ["duplicate_id", "extra_field", "non_object", "missing_field", "empty", "wrong_digest"])
def test_malformed_or_unbound_frozen_inventory_is_rejected(mutation):
    value = packet()
    if mutation == "duplicate_id":
        value["frozen_labels"].append(copy.deepcopy(value["frozen_labels"][0]))
    elif mutation == "extra_field":
        value["frozen_labels"][0]["diagnostic_decision"] = "reject"
    elif mutation == "non_object":
        value["frozen_labels"][0] = []
    elif mutation == "missing_field":
        value["frozen_labels"][0].pop("pair_id")
    elif mutation == "empty":
        value["frozen_labels"] = []
    else:
        value["label_review"]["frozen_labels_sha256"] = hashlib.sha256(b"different labels").hexdigest()
    with pytest.raises(ValueError, match="frozen"):
        assess_evidence_diagnostic(value)


def test_calibration_rows_are_bound_but_do_not_enter_evaluation_metrics():
    value = packet()
    extra = copy.deepcopy(value["records"][0])
    extra.update(record_id="calibration-only", pair_id="calibration-pair", project_id="calibration-project",
                 diagnostic_decision="support")
    value["records"].append(extra)
    freeze_labels(value)
    report = assess_evidence_diagnostic(value)
    assert report["systems"]["diagnostic"]["scheduled_denominator"] == 3
    assert report["systems"]["diagnostic"]["strict_accuracy"] == 1
    value["records"].pop()
    with pytest.raises(ValueError, match="frozen"):
        assess_evidence_diagnostic(value)


def test_reclassifying_a_failed_evaluation_project_cannot_improve_accuracy():
    value = packet()
    failed = copy.deepcopy(value["records"][0])
    failed.update(record_id="second-project-failure", pair_id="second-project-pair",
                  project_id="second-evaluation-project", diagnostic_decision="support")
    value["project_split"]["second-evaluation-project"] = "evaluation"
    value["records"].append(failed)
    freeze_labels(value)
    report = assess_evidence_diagnostic(value)
    assert report["systems"]["diagnostic"]["strict_accuracy"] == 0.75
    value["project_split"]["second-evaluation-project"] = "development"
    with pytest.raises(ValueError, match="frozen"):
        assess_evidence_diagnostic(value)
