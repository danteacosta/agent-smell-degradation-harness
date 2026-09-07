"""Offline reports retain failures and never expose private evidence."""
import copy
import json
import subprocess
import sys

import pytest

from label_plane.artifact_segments import build_snapshot


def api():
    from eval import evidence_addressing
    return evidence_addressing


def record(status="covered", expected="covered"):
    item = {"criteria": "PRIVATE record is stored.", "reference": "Store the PRIVATE record.",
            "scope": "complete", "obligations": [{"id": "private-condition", "text": "Store it."}]}
    cite = build_snapshot(item["criteria"])["segments"][0]["id"]
    raw = json.dumps({"checks": [{"id": "private-condition", "status": status,
                                 "evidence_ids": [cite] if status == "covered" else []}]})
    value = {"item": item, "raw_response": raw}
    if expected is not None:
        value["expected_checks"] = [expected]
    return value


def test_report_separates_missing_invalid_unlabeled_and_constructed_agreement():
    missing = record(); missing["raw_response"] = None
    bad = record(); bad["raw_response"] = "PRIVATE invalid JSON"
    rows = [record(), record("omitted"), record(expected=None), missing, bad]
    report = api().summarize(rows)
    assert report["attempted_records"] == 5
    assert report["valid_responses"] == 3
    assert report["invalid_records"] == 2
    assert report["first_error_counts"] == {"missing_response": 1, "response_json": 1}
    assert report["valid_response_status_counts"] == {"covered": 2, "omitted": 1, "uncertain": 0}
    assert report["construction_agreement"] == {
        "answer_records": 4, "valid_responses": 2, "matching": 1,
        "mismatching": 1, "unscored": 2, "records_without_answers": 1}
    assert report["semantic_validity"] == "not_measured"
    assert report["main_collection_released"] is False
    assert report["provider_calls_dispatched"] == 0
    assert report["planned_provider_calls"] is None
    assert rows[3]["raw_response"] is None


def test_report_does_not_publish_payload_hashes_paths_or_citation_ids():
    value = record()
    original = copy.deepcopy(value)
    report = json.dumps(api().summarize([value]), sort_keys=True)
    for private in ("PRIVATE", "private-condition", "seg-", "artifact_sha256", "raw_response"):
        assert private not in report
    assert value == original


def test_locator_failure_is_not_construction_success_even_with_matching_status():
    value = record()
    raw = json.loads(value["raw_response"])
    raw["checks"][0]["evidence_ids"] = ["reference-only"]
    value["raw_response"] = json.dumps(raw)
    report = api().summarize([value])
    assert report["first_error_counts"] == {"unknown_segment": 1}
    assert report["construction_agreement"]["matching"] == 0
    assert report["construction_agreement"]["unscored"] == 1


@pytest.mark.parametrize("bad", [None, [], {}, {"item": {}}, {"unexpected": "PRIVATE"}])
def test_malformed_record_is_counted_not_dropped_or_echoed(bad):
    report = api().summarize([bad])
    assert report["attempted_records"] == report["invalid_records"] == 1
    assert report["valid_responses"] == 0
    assert report["first_error_counts"] == {"invalid_record": 1}
    assert "PRIVATE" not in json.dumps(report)


@pytest.mark.parametrize("expected", [[], ["clean"], None, "covered", ["covered", "covered"], [[]]])
def test_invalid_construction_inventory_does_not_become_ground_truth(expected):
    value = record(); value["expected_checks"] = expected
    report = api().summarize([value])
    assert report["first_error_counts"] == {"invalid_answers": 1}
    assert report["construction_agreement"]["answer_records"] == 0


@pytest.mark.parametrize("rows", [None, {}, [], [None] * 1001],
                         ids=["null", "object", "empty", "oversized"])
def test_invalid_audit_envelope_is_rejected(rows):
    with pytest.raises(ValueError, match="invalid_audit"):
        api().summarize(rows)


def run_cli(*args):
    return subprocess.run([sys.executable, "-m", "eval.evidence_addressing", *args],
                          capture_output=True, text=True, timeout=10)


def test_toy_cli_is_offline_explicit_and_has_no_semantic_release():
    result = run_cli("--demo")
    assert result.returncode == 0, result.stderr
    report = json.loads(result.stdout)
    assert report["mode"] == "toy_demo"
    assert report["attempted_records"] == 4
    assert report["valid_responses"] == report["invalid_records"] == 2
    assert report["semantic_validity"] == "not_measured"
    assert report["main_collection_released"] is False
    assert result.stderr == ""


def test_cli_reports_audit_failures_without_payload_or_false_success(tmp_path):
    path = tmp_path / "PRIVATE.json"
    path.write_text(json.dumps([record(), {"PRIVATE": "secret"}]), encoding="utf-8")
    result = run_cli("--input", str(path))
    assert result.returncode == 2
    report = json.loads(result.stdout)
    assert report["attempted_records"] == 2 and report["valid_responses"] == 1
    assert "PRIVATE" not in result.stdout + result.stderr


@pytest.mark.parametrize("content", [b"{", b"\xff", b"x" * 1_048_577,
                                      b'[{"item":{},"item":{}}]', b'[[NaN]]'],
                         ids=["json", "utf8", "size", "duplicate-keys", "nan"])
def test_cli_rejects_bad_files_without_traceback_or_private_path(tmp_path, content):
    path = tmp_path / "PRIVATE.json"
    path.write_bytes(content)
    result = run_cli("--input", str(path))
    assert result.returncode == 2
    assert json.loads(result.stdout)["error"] == "invalid_audit_file"
    assert "PRIVATE" not in result.stdout + result.stderr
    assert "Traceback" not in result.stdout + result.stderr


def test_cli_missing_path_does_not_echo_private_filename(tmp_path):
    result = run_cli("--input", str(tmp_path / "PRIVATE-missing.json"))
    assert result.returncode == 2
    assert "PRIVATE" not in result.stdout + result.stderr


def test_demo_and_audit_execute_with_network_unavailable(monkeypatch, capsys):
    import socket

    def network_forbidden(*args, **kwargs):
        raise AssertionError("offline audit attempted network access")

    monkeypatch.setattr(socket, "socket", network_forbidden)
    monkeypatch.setattr(socket, "getaddrinfo", network_forbidden)
    assert api().summarize([record()])["provider_calls_dispatched"] == 0
    assert api().main(["--demo"]) == 0
    assert json.loads(capsys.readouterr().out)["main_collection_released"] is False


def test_valid_schema_with_wrong_construction_answer_is_not_semantic_approval(tmp_path):
    path = tmp_path / "responses.json"
    path.write_text(json.dumps([record("omitted")]), encoding="utf-8")
    result = run_cli("--input", str(path))
    assert result.returncode == 0  # Software integrity, not semantic correctness.
    report = json.loads(result.stdout)
    assert report["construction_agreement"]["mismatching"] == 1
    assert report["semantic_validity"] == "not_measured"
    assert report["main_collection_released"] is False
