import hashlib
import json
from pathlib import Path

import pytest

from scripts import six_project_e2e_freeze as freeze


ROOT = Path(__file__).resolve().parents[1]


def test_four_new_projects_have_exact_single_span_omissions_and_source_custody() -> None:
    cases = freeze.case_definitions()
    assert set(cases) == {"paperless-ngx", "kanboard", "nextcloud", "openproject"}
    for project, case in cases.items():
        variants = case["variants"]
        omitted = case["omission"]["text"]
        assert variants["A"].count(omitted) == 1, project
        assert variants["A"].replace(omitted, "", 1) == variants["C"], project
        assert len({variants[arm] for arm in freeze.ARMS}) == 3
        source = ROOT / case["source"]["path"]
        license_path = ROOT / case["rights"]["path"]
        assert hashlib.sha256(source.read_bytes()).hexdigest() == case["source"]["sha256"]
        assert hashlib.sha256(license_path.read_bytes()).hexdigest() == case["rights"]["sha256"]
        assert case["source"]["exact_excerpt"] in source.read_text(encoding="utf-8")


def test_shared_interfaces_are_arm_invariant_and_do_not_disclose_verdicts() -> None:
    cases = freeze.case_definitions()
    for project, case in cases.items():
        interface = case["common_interface"]
        requests = freeze.requests_for(case)
        assert len({requests[arm] for arm in freeze.ARMS}) == 3
        assert all(requests[arm].endswith(interface) for arm in freeze.ARMS)
        for forbidden in ("smell", "omitted span", "expected verdict", "hidden test"):
            assert forbidden not in interface.casefold(), (project, forbidden)
    assert "drag" not in cases["paperless-ngx"]["common_interface"].casefold()
    assert "trash" not in cases["nextcloud"]["common_interface"].casefold()
    assert "done" not in cases["kanboard"]["common_interface"].casefold()
    assert "automatically" not in cases["openproject"]["common_interface"].casefold()


def test_schedule_is_balanced_deterministic_and_covers_72_slots() -> None:
    first = freeze.build_schedule()
    assert first == freeze.build_schedule()
    assert len(first) == 72
    assert len({row["slot_id"] for row in first}) == 72
    assert {
        (row["project_id"], row["model"], row["replication"], row["arm"])
        for row in first
    } == {
        (project, model, repetition, arm)
        for project in freeze.PROJECTS
        for model in freeze.MODELS
        for repetition in freeze.REPETITIONS
        for arm in freeze.ARMS
    }
    assert all(freeze.OPAQUE_SLOT.fullmatch(row["slot_id"]) for row in first)


def test_freeze_manifest_is_pre_outcome_and_fail_closed() -> None:
    manifest = freeze.build_manifest()
    assert manifest["planned_slots"] == 72
    assert manifest["provider_calls"] == 0
    assert manifest["outcomes_observed"] is False
    assert manifest["automatic_dispatch_allowed"] is False
    assert manifest["projects_after_completion"] == 6
    assert manifest["oracle_qualification"]["qualified"] is True
    assert manifest["oracle_qualification"]["controls"] == 20
    assert manifest["claims"]["confirmatory"] is False
    assert manifest["claims"]["h1_confirmed"] is False
    assert freeze.validate_manifest(manifest) == manifest

    altered = json.loads(json.dumps(manifest))
    altered["schedule"][0]["arm"] = "C" if altered["schedule"][0]["arm"] != "C" else "A"
    with pytest.raises(ValueError, match="schedule drift"):
        freeze.validate_manifest(altered)


def test_materialization_is_immutable_and_hash_binds_each_request(tmp_path: Path) -> None:
    output = tmp_path / "freeze"
    manifest = freeze.materialize(output)
    assert len(list((output / "requests").glob("*.json"))) == 72
    for row in manifest["schedule"]:
        request_path = output / "requests" / f"{row['slot_id']}.json"
        assert hashlib.sha256(request_path.read_bytes()).hexdigest() == manifest[
            "request_sha256"
        ][row["slot_id"]]
    assert freeze.validate_materialized(output)["planned_slots"] == 72
    with pytest.raises(FileExistsError):
        freeze.materialize(output)
