import hashlib
import json
from pathlib import Path

import pytest

from scripts import six_project_e2e_freeze as original
from scripts import three_project_scaffold_freeze as successor


ROOT = Path(__file__).resolve().parents[1]


def test_successor_preserves_original_cases_and_declares_post_outcome_redesign() -> None:
    manifest = successor.build_manifest()
    original_cases = original.case_definitions()

    assert manifest["stage"] == "post_outcome_successor_pre_generation"
    assert manifest["replaces_original_collection"] is False
    assert manifest["outcomes_observed_in_predecessor"] is True
    assert manifest["new_provider_calls"] == 0
    assert set(manifest["cases"]) == {"paperless-ngx", "nextcloud", "openproject"}
    for project, case in manifest["cases"].items():
        assert case["variants"] == original_cases[project]["variants"]
        assert case["omission"] == original_cases[project]["omission"]
        assert case["source"] == original_cases[project]["source"]
        assert case["rights"] == original_cases[project]["rights"]


def test_scaffolds_are_arm_invariant_hash_bound_and_own_the_dom() -> None:
    manifest = successor.build_manifest()
    for project, case in manifest["cases"].items():
        scaffold = ROOT / case["scaffold"]["path"]
        raw = scaffold.read_bytes()
        text = raw.decode("utf-8")
        assert hashlib.sha256(raw).hexdigest() == case["scaffold"]["sha256"]
        assert text.count(successor.PLACEHOLDER) == 1
        assert "data-document-id" in text if project == "paperless-ngx" else True
        assert "data-file-id" in text if project == "nextcloud" else True
        assert 'aria-label="Remaining Work"' in text if project == "openproject" else True
        prompts = successor.requests_for(case)
        assert all(prompts[arm].endswith(text) for arm in successor.ARMS)


def test_schedule_is_balanced_deterministic_and_covers_54_slots() -> None:
    first = successor.build_schedule()
    assert first == successor.build_schedule()
    assert len(first) == 54
    assert len({row["slot_id"] for row in first}) == 54
    assert {
        (row["project_id"], row["model"], row["replication"], row["arm"])
        for row in first
    } == {
        (project, model, repetition, arm)
        for project in successor.PROJECTS
        for model in successor.MODELS
        for repetition in successor.REPETITIONS
        for arm in successor.ARMS
    }


def test_manifest_fails_closed_on_schedule_or_scaffold_drift() -> None:
    manifest = successor.build_manifest()
    assert manifest["planned_slots"] == 54
    assert manifest["automatic_dispatch_allowed"] is False
    assert manifest["oracle_qualification"]["qualified"] is True
    assert manifest["oracle_qualification"]["controls"] == 18
    assert manifest["claims"] == {
        "pilot": True,
        "confirmatory": False,
        "h1_confirmed": False,
        "h2_evaluated": False,
    }
    assert successor.validate_manifest(manifest) == manifest

    altered = json.loads(json.dumps(manifest))
    altered["schedule"][0]["arm"] = "C" if altered["schedule"][0]["arm"] != "C" else "A"
    with pytest.raises(ValueError, match="schedule drift"):
        successor.validate_manifest(altered)


def test_materialization_hash_binds_all_requests(tmp_path: Path) -> None:
    output = tmp_path / "freeze"
    manifest = successor.materialize(output)
    assert len(list((output / "requests").glob("*.json"))) == 54
    for row in manifest["schedule"]:
        request = output / "requests" / f"{row['slot_id']}.json"
        assert hashlib.sha256(request.read_bytes()).hexdigest() == manifest["request_sha256"][row["slot_id"]]
    assert successor.validate_materialized(output)["planned_slots"] == 54
    with pytest.raises(FileExistsError):
        successor.materialize(output)
