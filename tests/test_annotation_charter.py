from __future__ import annotations

from copy import deepcopy
import json
from pathlib import Path

import pytest

from label_plane.annotation_charter import evaluate_annotation_charter, file_sha256


ROOT = Path(__file__).resolve().parents[1]
RUBRIC = ROOT / "tasks" / "annotation_rubric.json"
CANDIDATE = ROOT / "data" / "annotation" / "annotation-study-charter.candidate.json"


def _candidate() -> dict:
    return json.loads(CANDIDATE.read_text(encoding="utf-8"))


def _ready() -> dict:
    payload = _candidate()
    payload["status"] = "ready"
    payload["roles"] = {
        "primary_annotator_ids": ["reviewer-a", "reviewer-b"],
        "adjudicator_id": "reviewer-c",
        "role_independence_confirmed": True,
    }
    payload["artifacts"]["rubric_sha256"] = file_sha256(RUBRIC)
    payload["artifacts"]["queue_manifest_sha256"] = "a" * 64
    payload["process"]["rehearsal_completed_by"] = ["reviewer-a", "reviewer-b"]
    payload["process"]["feedback_channel_ref"] = "private://annotation-feedback"
    payload["governance"] = {
        "ethics_privacy_decision_ref": "private://governance/decision",
        "access_control_ref": "private://access/policy",
        "participation_terms_ref": "private://participation/terms",
        "retention_and_deletion_ref": "private://retention/policy",
        "approved_for_distribution": True,
    }
    return payload


def test_candidate_is_fail_closed_and_reports_staffing_and_governance_blockers():
    report = evaluate_annotation_charter(_candidate(), rubric_path=RUBRIC)

    assert report["ready"] is False
    assert "two distinct primary annotators are required" in report["blockers"]
    assert "a named adjudicator is required" in report["blockers"]
    assert "annotation packet distribution is not approved" in report["blockers"]


def test_complete_charter_can_be_declared_ready_without_creating_labels():
    report = evaluate_annotation_charter(_ready(), rubric_path=RUBRIC)

    assert report["ready"] is True
    assert report["blockers"] == []
    assert "creates no labels" in report["scientific_boundary"]


def test_ready_charter_rejects_hash_drift_and_role_overlap(tmp_path):
    payload = _ready()
    payload["roles"]["adjudicator_id"] = "reviewer-a"
    queue_manifest = tmp_path / "queue.json"
    queue_manifest.write_text("{}\n", encoding="utf-8")

    with pytest.raises(ValueError, match="adjudicator must be independent"):
        evaluate_annotation_charter(
            payload,
            rubric_path=RUBRIC,
            queue_manifest_path=queue_manifest,
        )


def test_machine_judgments_cannot_be_promoted_and_all_scenario_types_are_required():
    payload = _ready()
    payload["claim_boundary"]["model_judgments_secondary_only"] = False
    payload["annotation_scenarios"] = payload["annotation_scenarios"][:1]

    with pytest.raises(ValueError, match="model_judgments_secondary_only"):
        evaluate_annotation_charter(payload, rubric_path=RUBRIC)


def test_blocked_charter_reports_rubric_drift_without_raising():
    payload = deepcopy(_candidate())
    payload["artifacts"]["rubric_sha256"] = "0" * 64

    report = evaluate_annotation_charter(payload, rubric_path=RUBRIC)

    assert report["ready"] is False
    assert "rubric_sha256 does not match the supplied rubric" in report["blockers"]
