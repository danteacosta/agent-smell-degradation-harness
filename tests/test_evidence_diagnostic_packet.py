import copy

import pytest

from eval.evidence_diagnostic_packet import freeze_label_inventory
from eval.evidence_diagnostic_qualification import assess_evidence_diagnostic


def labels():
    families = {
        "wrong_binding": "reject",
        "valid_alternative": "support",
        "insufficient_evidence": "abstain",
    }
    return [
        {
            "record_id": f"evaluation-{index}",
            "pair_id": f"pair-{index}",
            "project_id": "evaluation-project",
            "constraint_id": f"constraint-{index}",
            "family": family,
            "expected_decision": expected,
        }
        for index, (family, expected) in enumerate(families.items())
    ]


def test_frozen_inventory_round_trips_through_the_qualification_evaluator():
    split = {"calibration-project": "calibration", "evaluation-project": "evaluation"}
    result = freeze_label_inventory(split, labels())
    records = [
        {**label, "diagnostic_decision": label["expected_decision"], "baseline_decision": "support"}
        for label in result["frozen_labels"]
    ]
    packet = {
        "schema_version": "evidence-diagnostic-qualification/v1",
        "project_split": split,
        "threshold_selected_on": "calibration",
        "diagnostic_threshold": 0.8,
        "label_review": {
            "reviewer_ids": ["reviewer-a", "reviewer-b"],
            "predictions_hidden_during_review": True,
            "completed_before_scoring": True,
            "rubric_sha256": "a" * 64,
            "frozen_labels_sha256": result["frozen_labels_sha256"],
        },
        "frozen_labels": result["frozen_labels"],
        "records": records,
    }
    report = assess_evidence_diagnostic(packet)
    assert report["systems"]["diagnostic"]["strict_accuracy"] == 1
    assert report["systems"]["diagnostic"]["scheduled_denominator"] == 3


def test_freezing_does_not_mutate_authoring_labels():
    original = labels()
    snapshot = copy.deepcopy(original)
    result = freeze_label_inventory({"evaluation-project": "evaluation"}, original)
    result["frozen_labels"][0]["constraint_id"] = "changed-after-freeze"
    assert original == snapshot


@pytest.mark.parametrize("mutation", [
    "prediction", "duplicate", "unknown_project", "wrong_expected", "missing_field",
])
def test_invalid_or_leaky_authoring_labels_fail_closed(mutation):
    value = labels()
    if mutation == "prediction":
        value[0]["diagnostic_decision"] = "reject"
    elif mutation == "duplicate":
        value[1]["record_id"] = value[0]["record_id"]
    elif mutation == "unknown_project":
        value[0]["project_id"] = "unplanned-project"
    elif mutation == "wrong_expected":
        value[0]["expected_decision"] = "support"
    else:
        value[0].pop("pair_id")
    with pytest.raises(ValueError):
        freeze_label_inventory({"evaluation-project": "evaluation"}, value)


def test_receipt_binds_project_assignment_and_inventory_order():
    value = labels()
    split = {"evaluation-project": "evaluation"}
    first = freeze_label_inventory(split, value)["frozen_labels_sha256"]
    reordered = freeze_label_inventory(split, list(reversed(value)))["frozen_labels_sha256"]
    assert first != reordered
    with pytest.raises(ValueError, match="every qualification family"):
        freeze_label_inventory({"evaluation-project": "development"}, value)


@pytest.mark.parametrize("field", ["project_id", "constraint_id"])
def test_inconsistent_pairs_are_rejected_before_predictions_exist(field):
    value = labels()
    extra = copy.deepcopy(value[0])
    extra["record_id"] = "other-record"
    extra[field] = "other-identity"
    value.append(extra)
    split = {"evaluation-project": "evaluation", "other-identity": "development"}
    with pytest.raises(ValueError, match="pair_id"):
        freeze_label_inventory(split, value)


def test_missing_control_family_is_rejected_before_freezing():
    with pytest.raises(ValueError, match="every qualification family"):
        freeze_label_inventory({"evaluation-project": "evaluation"}, labels()[:-1])
