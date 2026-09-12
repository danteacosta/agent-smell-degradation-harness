from __future__ import annotations

import copy
import hashlib
import json

import pytest

from label_plane.oracle_review import CANDIDATE, PAIRS, digest, main, run_reference_audit


def candidate():
    return json.loads(CANDIDATE.read_text())


def test_partial_oracle_exposes_dependence_on_unsupported_expectations():
    proposal = candidate()
    before = copy.deepcopy(proposal)
    report = run_reference_audit(proposal)
    assert proposal == before
    assert report["case_count"] == 4 and report["reference_count"] == 8
    assert report["live_authorized"] is False
    assert report["confirmatory_eligible"] is False
    assert report["review_status"] == "pending_independent_review"
    assert report["candidate_sha256"] == digest(proposal)
    rows = {r["intent_id"]: r for r in report["cases"]}
    assert all(r["legacy_reference_contrast"] is True for r in rows.values())
    assert {k for k, r in rows.items() if r["candidate_reference_contrast"]} == {
        "ARTA-NFR-002", "ARTA-PEERING-001"
    }
    for row in rows.values():
        left, right = row["references"].values()
        assert left["candidate_oracle_sha256"] == right["candidate_oracle_sha256"] == row["candidate_oracle_sha256"]
        assert left["unscored_test_ids"] == right["unscored_test_ids"]
        assert left["checked_points"] == right["checked_points"] == 1
    assert rows["ARTA-GAMMA-002"]["references"]["smelly_plausible"]["candidate_status"] == "compatible_on_checked_points"
    assert rows["ARTA-ERTMS-002"]["references"]["smelly_plausible"]["unscored_test_ids"] == [
        "required_ack_received", "ack_not_required"
    ]


@pytest.mark.parametrize("mutation", ["missing", "unknown", "all_unspecified", "duplicate", "approved", "wrong_hash", "wrong_oracle", "path", "no_rationale"])
def test_invalid_inventory_is_rejected_before_any_execution(monkeypatch, mutation):
    import eval.codegen_sandbox as sandbox

    proposal = candidate()
    record = proposal["cases"][-1]  # Validate later records before running earlier ones.
    if mutation == "missing":
        record["decisions"].pop("malicious_request")
    elif mutation == "unknown":
        record["decisions"]["benign_request"] = "pass"
    elif mutation == "all_unspecified":
        record["decisions"] = dict.fromkeys(record["decisions"], "unspecified")
    elif mutation == "duplicate":
        proposal["cases"].append(copy.deepcopy(record))
    elif mutation == "approved":
        proposal["review_status"] = "approved"
    elif mutation == "wrong_hash":
        record["pair_sha256"] = "0" * 64
    elif mutation == "wrong_oracle":
        record["oracle_sha256"] = "0" * 64
    elif mutation == "path":
        record["intent_id"] = "../../malicious"
    else:
        record["rationale"] = " "

    def forbidden(*args, **kwargs):
        pytest.fail("invalid candidate dispatched reference execution")

    monkeypatch.setattr(sandbox, "evaluate_trusted_fixture", forbidden)
    with pytest.raises(ValueError):
        run_reference_audit(proposal)


def test_rehashing_changed_source_cannot_authorize_execution(tmp_path, monkeypatch):
    import eval.codegen_sandbox as sandbox

    proposal = candidate()
    proposal["cases"] = proposal["cases"][:1]
    record = proposal["cases"][0]
    path = PAIRS / "arta-gamma-002.json"
    case = json.loads(path.read_text())
    case["oracle_spec"]["behavior_codegen"]["_execution"]["reference_implementations"]["clean"] = "def evaluate(concurrent_users):\n    return False"
    payload = json.dumps(case).encode()
    (tmp_path / path.name).write_bytes(payload)
    record["pair_sha256"] = hashlib.sha256(payload).hexdigest()
    record["oracle_sha256"] = digest(case["oracle_spec"])
    monkeypatch.setattr(sandbox, "evaluate_trusted_fixture", lambda *a: pytest.fail("executed modified source"))
    with pytest.raises(ValueError, match="trusted historical inventory"):
        run_reference_audit(proposal, tmp_path)


@pytest.mark.parametrize("status", ["runtime_error", "timeout", "invalid", "unsafe_not_run"])
def test_execution_failure_cannot_be_reported_as_no_effect(monkeypatch, status):
    import eval.codegen_sandbox as sandbox

    monkeypatch.setattr(sandbox, "evaluate_trusted_fixture", lambda *a: {
        "status": status, "cases": [], "failed": 0, "errors": 1,
    })
    report = run_reference_audit(candidate())
    for row in report["cases"]:
        assert row["candidate_reference_contrast"] is None
        assert row["legacy_reference_contrast"] is None
        assert all(r["candidate_status"] == "execution_incomplete" for r in row["references"].values())


def test_report_is_reproducible_and_does_not_overwrite_existing_evidence(tmp_path):
    output = tmp_path / "report.json"
    main(["--output", str(output)])
    before = output.read_bytes()
    assert json.loads(before) == run_reference_audit(candidate())
    with pytest.raises(FileExistsError):
        main(["--output", str(output)])
    assert output.read_bytes() == before


def test_cli_has_no_provider_or_source_override():
    with pytest.raises(SystemExit) as exc:
        main(["--mode", "live"])
    assert exc.value.code == 2
