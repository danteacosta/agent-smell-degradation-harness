"""Contract tests for the trusted RealWorld author-UI report adapter."""
from __future__ import annotations

import copy
import hashlib
import json
import subprocess
from types import SimpleNamespace

import pytest

from eval import realworld_author_ui_executor as oracle


URL = "http://fixture.invalid/article/bounded-ui-case"
INVALID = {
    "category": "malformed_report",
    "reason": "incomplete or inconsistent trusted report",
}
PAIRS = (
    ("article-alice", "author"),
    ("article-alice", "non-author"),
    ("article-bob", "author"),
    ("article-bob", "non-author"),
)
SCREENSHOTS = [f"{fixture}-{context}.png" for fixture, context in PAIRS]
ASSERTION_FOR_CONTEXT = {
    "author": "author_sees_delete_article",
    "non-author": "non_author_does_not_see_delete_article",
}
REASON_FOR_FIELD = {
    "title": "title_missing",
    "body": "body_missing",
    "article_author": "article_author_missing",
}


def _observation(fixture_id: str, context_id: str) -> dict:
    return {
        "fixture_id": fixture_id,
        "context_id": context_id,
        "final_url": URL,
        "title": {"matched": 1, "perceptible": 1},
        "body": {"matched": 1, "perceptible": 1},
        "article_author": {"matched": 1, "perceptible": 1},
        "delete_buttons": {
            "matched": 1 if context_id == "author" else 0,
            "perceptible": 1 if context_id == "author" else 0,
        },
        "runtime_errors": [],
        "screenshot": f"{fixture_id}-{context_id}.png",
    }


def _derived_claims(observations: list[dict]) -> tuple[list[str], list[str], list[dict]]:
    failed: set[str] = set()
    reasons: list[dict] = []
    for observation in observations:
        assertion_id = ASSERTION_FOR_CONTEXT[observation["context_id"]]
        violated = []
        if observation["final_url"] != URL:
            violated.append("route_mismatch")
        for field, reason in REASON_FOR_FIELD.items():
            if observation[field]["perceptible"] < 1:
                violated.append(reason)
        if violated:
            reasons.extend({
                "assertion_id": assertion_id,
                "fixture_id": observation["fixture_id"],
                "context_id": observation["context_id"],
                "reason": reason,
            } for reason in violated)
        elif (observation["context_id"] == "author"
              and observation["delete_buttons"]["perceptible"] == 0):
            failed.add(assertion_id)
        elif (observation["context_id"] == "non-author"
              and observation["delete_buttons"]["perceptible"] >= 1):
            failed.add(assertion_id)
    reasons.sort(key=lambda item: (
        item["assertion_id"], item["fixture_id"], item["context_id"], item["reason"]
    ))
    return sorted(failed), sorted({reason["assertion_id"] for reason in reasons}), reasons


def complete_report(*, mutate=None, synchronize: bool = True) -> dict:
    value = {
        "schema_version": "realworld-author-ui-browser/v1",
        "status": "complete",
        "app_sha256": hashlib.sha256(b"<html></html>").hexdigest(),
        "runner_version": "1",
        "browser_sandbox": False,
        "isolation": "fresh browser context per fixture/viewer pair",
        "browser_version": "Chromium 140.0",
        "viewport": {"width": 1000, "height": 720},
        "sample_grid": {"dimension": 5, "inset_ratio": 0.08},
        "observations": [_observation(*pair) for pair in PAIRS],
        "target_failed": [],
        "target_not_evaluable": [],
        "not_evaluable_reasons": [],
        "screenshots": SCREENSHOTS.copy(),
    }
    if mutate is not None:
        mutate(value)
    if synchronize:
        failed, not_evaluable, reasons = _derived_claims(value["observations"])
        value["target_failed"] = failed
        value["target_not_evaluable"] = not_evaluable
        value["not_evaluable_reasons"] = reasons
    return value


def encoded(value: dict) -> bytes:
    return json.dumps(value).encode()


def expected_complete(value: dict) -> dict:
    category = ("target_not_evaluable" if value["target_not_evaluable"] else
                "target_only_failure" if value["target_failed"] else "pass")
    return {
        "category": category,
        "target_failed": value["target_failed"],
        "target_not_evaluable": value["target_not_evaluable"],
        "not_evaluable_reasons": value["not_evaluable_reasons"],
    }


def test_complete_pass_report_is_accepted():
    value = complete_report()
    assert oracle.classify_report(encoded(value), 0) == expected_complete(value)


@pytest.mark.parametrize(
    ("indices", "expected_failed"),
    [
        ([0], ["author_sees_delete_article"]),
        ([1], ["non_author_does_not_see_delete_article"]),
        ([0, 1], list(oracle.ASSERTION_IDS)),
    ],
)
def test_target_failure_directions_are_recomputed(indices, expected_failed):
    def mutate(value):
        for index in indices:
            observation = value["observations"][index]
            if observation["context_id"] == "author":
                observation["delete_buttons"] = {"matched": 0, "perceptible": 0}
            else:
                observation["delete_buttons"] = {"matched": 1, "perceptible": 1}

    value = complete_report(mutate=mutate)
    assert value["target_failed"] == expected_failed
    assert oracle.classify_report(encoded(value), 10) == expected_complete(value)


def test_author_button_multiplicity_is_valid():
    value = complete_report(mutate=lambda report: report["observations"][0].update(
        delete_buttons={"matched": 2, "perceptible": 2}))
    assert oracle.classify_report(encoded(value), 0) == expected_complete(value)


@pytest.mark.parametrize("button_count", [
    {"matched": 0, "perceptible": 0},
    {"matched": 1, "perceptible": 0},
])
def test_removed_or_nonperceptible_non_author_control_passes(button_count):
    value = complete_report(mutate=lambda report: report["observations"][1].update(
        delete_buttons=button_count))
    assert oracle.classify_report(encoded(value), 0) == expected_complete(value)


@pytest.mark.parametrize(
    ("mutation", "reason"),
    [
        (lambda item: item.update(final_url="http://fixture.invalid/wrong"), "route_mismatch"),
        (lambda item: item["title"].update(perceptible=0), "title_missing"),
        (lambda item: item["body"].update(perceptible=0), "body_missing"),
        (lambda item: item["article_author"].update(perceptible=0), "article_author_missing"),
    ],
)
def test_each_prerequisite_reason_is_preserved(mutation, reason):
    value = complete_report(mutate=lambda report: mutation(report["observations"][0]))
    assert value["not_evaluable_reasons"] == [{
        "assertion_id": "author_sees_delete_article",
        "fixture_id": "article-alice",
        "context_id": "author",
        "reason": reason,
    }]
    assert oracle.classify_report(encoded(value), 11) == expected_complete(value)


def test_simultaneous_prerequisite_failures_emit_every_reason():
    def mutate(value):
        item = value["observations"][3]
        item["final_url"] = "http://fixture.invalid/wrong"
        item["title"]["perceptible"] = 0
        item["body"]["perceptible"] = 0
        item["article_author"]["perceptible"] = 0

    value = complete_report(mutate=mutate)
    assert [item["reason"] for item in value["not_evaluable_reasons"]] == [
        "article_author_missing", "body_missing", "route_mismatch", "title_missing"
    ]
    assert oracle.classify_report(encoded(value), 11) == expected_complete(value)


def test_mixed_not_evaluable_and_failure_retains_both_sets():
    def mutate(value):
        value["observations"][2]["body"]["perceptible"] = 0
        value["observations"][3]["delete_buttons"] = {"matched": 1, "perceptible": 1}

    value = complete_report(mutate=mutate)
    assert value["target_failed"] == ["non_author_does_not_see_delete_article"]
    assert value["target_not_evaluable"] == ["author_sees_delete_article"]
    assert oracle.classify_report(encoded(value), 11) == expected_complete(value)


def _extra_top(value):
    value["extra"] = 1


def _missing_top(value):
    del value["browser_version"]


def _extra_observation(value):
    value["observations"][0]["extra"] = 1


def _missing_observation(value):
    del value["observations"][0]["body"]


def _bool_count(value):
    value["observations"][0]["title"]["matched"] = True


def _negative_count(value):
    value["observations"][0]["delete_buttons"]["matched"] = -1


def _oversized_count(value):
    value["observations"][0]["delete_buttons"] = {"matched": 21, "perceptible": 1}


def _perceptible_exceeds_matched(value):
    value["observations"][0]["delete_buttons"] = {"matched": 1, "perceptible": 2}


def _duplicate_pair(value):
    value["observations"][1] = copy.deepcopy(value["observations"][0])


def _misordered_pair(value):
    value["observations"][0], value["observations"][1] = (
        value["observations"][1], value["observations"][0])


def _malformed_screenshot(value):
    value["observations"][0]["screenshot"] = "../article-alice-author.png"


def _wrong_screenshot_list(value):
    value["screenshots"] = list(reversed(value["screenshots"]))


def _oversized_runtime_errors(value):
    value["observations"][0]["runtime_errors"] = [
        {"kind": "console", "message": "error"}
    ] * 21


def _bad_runtime_error(value):
    value["observations"][0]["runtime_errors"] = [
        {"kind": "network", "message": "error"}
    ]


@pytest.mark.parametrize("mutation", [
    _extra_top,
    _missing_top,
    _extra_observation,
    _missing_observation,
    _bool_count,
    _negative_count,
    _oversized_count,
    _perceptible_exceeds_matched,
    _duplicate_pair,
    _misordered_pair,
    _malformed_screenshot,
    _wrong_screenshot_list,
    _oversized_runtime_errors,
    _bad_runtime_error,
    lambda value: value["observations"][0]["runtime_errors"].append(
        {"kind": "page", "message": "x" * 501}),
    lambda value: value.update(viewport={"width": 999, "height": 720}),
    lambda value: value.update(sample_grid={"dimension": 5, "inset_ratio": 0.0800001}),
    lambda value: value.update(browser_sandbox=True),
    lambda value: value.update(runner_version="2"),
    lambda value: value.update(isolation=""),
    lambda value: value.update(isolation="x" * 501),
    lambda value: value.update(browser_version=""),
    lambda value: value.update(browser_version="x" * 201),
    lambda value: value.update(app_sha256="A" * 64),
])
def test_closed_complete_schema_rejects_invalid_values(mutation):
    value = complete_report()
    mutation(value)
    assert oracle.classify_report(encoded(value), 0) == INVALID


def test_duplicate_json_keys_are_rejected_from_raw_bytes():
    raw = encoded(complete_report()).replace(
        b'"runner_version": "1",',
        b'"runner_version": "1", "runner_version": "1",',
    )
    assert oracle.classify_report(raw, 0) == INVALID


@pytest.mark.parametrize("raw", [
    None,
    b"",
    b"not json",
    b"[" * 1100 + b"0" + b"]" * 1100,
    b" " * 100001,
])
def test_missing_malformed_or_oversized_raw_report_is_rejected(raw):
    assert oracle.classify_report(raw, 0) == INVALID


def test_mutating_one_malformed_result_does_not_corrupt_later_results():
    first = oracle.classify_report(None, 0)
    first["category"] = "corrupted"
    first["extra"] = True

    second = oracle.classify_report(None, 0)

    assert second == INVALID
    assert second is not first


def test_unknown_schema_is_rejected():
    value = complete_report()
    value["schema_version"] = "realworld-author-ui-browser/v2"
    assert oracle.classify_report(encoded(value), 0) == INVALID


@pytest.mark.parametrize(("field", "member", "bad"), [
    ("viewport", "width", 1000.0),
    ("viewport", "height", 720.0),
    ("viewport", "width", True),
    ("viewport", "height", False),
    ("sample_grid", "dimension", 5.0),
    ("sample_grid", "dimension", True),
    ("sample_grid", "inset_ratio", False),
    ("sample_grid", "inset_ratio", "0.08"),
])
def test_viewport_and_sample_grid_reject_wrong_scalar_types(field, member, bad):
    value = complete_report()
    value[field][member] = bad
    assert oracle.classify_report(encoded(value), 0) == INVALID


def test_sample_grid_requires_float_inset_ratio():
    value = complete_report()
    assert type(value["sample_grid"]["inset_ratio"]) is float
    assert oracle.classify_report(encoded(value), 0) == expected_complete(value)


@pytest.mark.parametrize("field", ["target_failed", "target_not_evaluable"])
def test_declared_target_sets_must_be_sorted_unique_supported_and_consistent(field):
    for bad in (
        list(reversed(oracle.ASSERTION_IDS)),
        [oracle.ASSERTION_IDS[0], oracle.ASSERTION_IDS[0]],
        ["unsupported_assertion"],
        [oracle.ASSERTION_IDS[0]],
    ):
        value = complete_report()
        value[field] = bad
        assert oracle.classify_report(encoded(value), 0) == INVALID


def test_reason_objects_must_be_closed_sorted_unique_supported_and_consistent():
    def break_body(value):
        value["observations"][0]["body"]["perceptible"] = 0
        value["observations"][1]["title"]["perceptible"] = 0

    valid = complete_report(mutate=break_body)
    mutations = []
    reversed_reasons = copy.deepcopy(valid)
    reversed_reasons["not_evaluable_reasons"].reverse()
    mutations.append(reversed_reasons)
    duplicate = copy.deepcopy(valid)
    duplicate["not_evaluable_reasons"].append(copy.deepcopy(duplicate["not_evaluable_reasons"][-1]))
    mutations.append(duplicate)
    unsupported_id = copy.deepcopy(valid)
    unsupported_id["not_evaluable_reasons"][0]["assertion_id"] = "unsupported"
    mutations.append(unsupported_id)
    unsupported_reason = copy.deepcopy(valid)
    unsupported_reason["not_evaluable_reasons"][0]["reason"] = "unknown"
    mutations.append(unsupported_reason)
    extra = copy.deepcopy(valid)
    extra["not_evaluable_reasons"][0]["extra"] = True
    mutations.append(extra)
    inconsistent = copy.deepcopy(valid)
    inconsistent["not_evaluable_reasons"].pop()
    mutations.append(inconsistent)
    inconsistent_set = copy.deepcopy(valid)
    inconsistent_set["target_not_evaluable"] = ["author_sees_delete_article"]
    mutations.append(inconsistent_set)

    for value in mutations:
        assert oracle.classify_report(encoded(value), 11) == INVALID


def operational_report(status: str, browser_started: bool) -> dict:
    return {
        "schema_version": "realworld-author-ui-browser/v1",
        "status": status,
        "app_sha256": "0" * 64,
        "runner_version": "1",
        "browser_sandbox": False,
        "isolation": "offline container",
        "error": "bounded runner failure",
        "browser_started": browser_started,
    }


def test_operational_reports_are_classified_without_target_failures():
    interface = operational_report("interface_failure", False)
    browser = operational_report("browser_failure", True)
    assert oracle.classify_report(encoded(interface), 20) == {
        "category": "interface_failure", "reason": interface["error"]}
    assert oracle.classify_report(encoded(browser), 21) == {
        "category": "browser_failure", "reason": browser["error"]}


@pytest.mark.parametrize(("value", "returncode"), [
    (operational_report("interface_failure", True), 20),
    (operational_report("interface_failure", False), 21),
    (operational_report("browser_failure", False), 20),
    ({**operational_report("browser_failure", True), "observations": []}, 21),
    ({key: item for key, item in operational_report("browser_failure", True).items()
      if key != "error"}, 21),
    ({**operational_report("browser_failure", True), "error": "x" * 1501}, 21),
    ({**operational_report("browser_failure", True), "browser_started": 1}, 21),
    (operational_report("interface_failure", False), 20.0),
    (operational_report("browser_failure", True), 21.0),
])
def test_wrong_operational_shapes_or_return_codes_are_rejected(value, returncode):
    assert oracle.classify_report(encoded(value), returncode) == INVALID


@pytest.mark.parametrize(("mutation", "returncode"), [
    (None, 10),
    (None, 11),
    (lambda value: value["observations"][0].update(
        delete_buttons={"matched": 0, "perceptible": 0}), 0),
    (lambda value: value["observations"][0].update(
        delete_buttons={"matched": 0, "perceptible": 0}), 11),
    (lambda value: value["observations"][0]["body"].update(perceptible=0), 0),
    (lambda value: value["observations"][0]["body"].update(perceptible=0), 10),
    (None, 20),
    (None, 21),
    (None, 99),
])
def test_complete_return_code_must_match_recomputed_category(mutation, returncode):
    value = complete_report(mutate=mutation)
    assert oracle.classify_report(encoded(value), returncode) == INVALID


PNG = b"\x89PNG\r\n\x1a\nimage"
IMAGE = "sha256:" + "a" * 64


def _write_complete_artifacts(output, value, *, screenshot_fault=None):
    (output / "report.json").write_bytes(encoded(value))
    for name in SCREENSHOTS:
        path = output / name
        if screenshot_fault == (name, "missing"):
            continue
        if screenshot_fault == (name, "symlink"):
            target = output.parent / f"outside-{name}"
            target.write_bytes(PNG)
            path.symlink_to(target)
        elif screenshot_fault == (name, "oversize"):
            path.write_bytes(PNG + b"x" * 4_000_000)
        elif screenshot_fault == (name, "bad_signature"):
            path.write_bytes(b"not a png")
        else:
            path.write_bytes(PNG)


def _execute_with_fake_process(monkeypatch, tmp_path, *, report=None, returncode=0,
                               screenshot_fault=None, run_error=None, call_log=None,
                               extra_png=False):
    app = b"<html></html>"
    inputs = tmp_path / "inputs"
    inputs.mkdir()
    (inputs / "app.html").write_bytes(app)
    output = tmp_path / "output"
    calls = call_log if call_log is not None else []

    def fake_run(command, **kwargs):
        calls.append((command, kwargs))
        if command[:3] == ["docker", "rm", "--force"]:
            return SimpleNamespace(returncode=0)
        if run_error is not None:
            raise run_error
        if report is not None:
            if report.get("status") == "complete":
                _write_complete_artifacts(
                    output, report, screenshot_fault=screenshot_fault)
                if extra_png:
                    (output / "unexpected.png").write_bytes(PNG)
            else:
                (output / "report.json").write_bytes(encoded(report))
        kwargs["stdout"].write(b"browser output\n")
        return SimpleNamespace(returncode=returncode)

    monkeypatch.setattr(oracle.subprocess, "run", fake_run)
    receipt = oracle.execute(IMAGE, inputs, output, timeout=7)
    return receipt, output, calls


def test_execute_accepts_complete_report_and_writes_auditable_receipts(monkeypatch, tmp_path):
    value = complete_report()
    receipt, output, calls = _execute_with_fake_process(
        monkeypatch, tmp_path, report=value)

    assert receipt == {
        "image": IMAGE,
        "app_sha256": value["app_sha256"],
        "returncode": 0,
        **expected_complete(value),
    }
    command = json.loads((output / "container-command.json").read_text())
    assert command == calls[0][0]
    assert command[:6] == ["docker", "run", "--rm", "--init", "--name",
                            calls[1][0][-1]]
    assert calls[0][1]["stderr"] is subprocess.STDOUT
    assert calls[0][1]["timeout"] == 7
    assert calls[0][1]["check"] is False
    assert (output / "container.log").read_bytes() == b"browser output\n"
    assert json.loads((output / "executor.json").read_text()) == receipt
    assert calls[1][0] == ["docker", "rm", "--force", command[5]]
    assert calls[1][1] == {"capture_output": True, "timeout": 30, "check": False}
    assert command[5].startswith("realworld-author-ui-")


def test_execute_timeout_is_diagnostic_and_always_cleans_up(monkeypatch, tmp_path):
    receipt, output, calls = _execute_with_fake_process(
        monkeypatch, tmp_path,
        run_error=subprocess.TimeoutExpired(["docker", "run"], 7),
    )

    assert receipt["category"] == "timeout"
    assert receipt["returncode"] == 124
    assert json.loads((output / "executor.json").read_text()) == receipt
    assert calls[-1][0][:3] == ["docker", "rm", "--force"]


def test_execute_cleans_up_when_process_invocation_fails(monkeypatch, tmp_path):
    calls = []
    with pytest.raises(OSError, match="docker unavailable"):
        _execute_with_fake_process(
            monkeypatch, tmp_path, run_error=OSError("docker unavailable"),
            call_log=calls)
    assert calls[-1][0][:3] == ["docker", "rm", "--force"]


@pytest.mark.parametrize("report_fault", ["missing", "symlink", "oversize", "malformed"])
def test_execute_rejects_missing_or_unsafe_report(monkeypatch, tmp_path, report_fault):
    app = b"<html></html>"
    inputs = tmp_path / "inputs"
    inputs.mkdir()
    (inputs / "app.html").write_bytes(app)
    output = tmp_path / "output"
    calls = []

    def fake_run(command, **kwargs):
        calls.append(command)
        if command[:3] == ["docker", "rm", "--force"]:
            return SimpleNamespace(returncode=0)
        report_path = output / "report.json"
        if report_fault == "symlink":
            target = tmp_path / "outside-report.json"
            target.write_bytes(encoded(complete_report()))
            report_path.symlink_to(target)
        elif report_fault == "oversize":
            report_path.write_bytes(b" " * 100_001)
        elif report_fault == "malformed":
            report_path.write_bytes(b"not json")
        return SimpleNamespace(returncode=0)

    monkeypatch.setattr(oracle.subprocess, "run", fake_run)
    receipt = oracle.execute(IMAGE, inputs, output)

    assert receipt["category"] == "malformed_report"
    assert receipt["returncode"] == 0
    assert calls[-1][:3] == ["docker", "rm", "--force"]


def test_execute_rejects_valid_json_with_inconsistent_schema(monkeypatch, tmp_path):
    receipt, _, _ = _execute_with_fake_process(
        monkeypatch, tmp_path, report={"schema_version": oracle.SCHEMA_VERSION})
    assert receipt["category"] == "malformed_report"


def test_execute_rejects_report_with_unrecognized_return_code(monkeypatch, tmp_path):
    receipt, _, _ = _execute_with_fake_process(
        monkeypatch, tmp_path, report=complete_report(), returncode=99)
    assert receipt["category"] == "malformed_report"


def _classified_report(category):
    if category == "pass":
        return complete_report(), 0
    if category == "target_only_failure":
        return complete_report(mutate=lambda value: value["observations"][0].update(
            delete_buttons={"matched": 0, "perceptible": 0})), 10
    if category == "target_not_evaluable":
        return complete_report(mutate=lambda value: value["observations"][0]["body"].update(
            perceptible=0)), 11
    if category == "interface_failure":
        return operational_report("interface_failure", False), 20
    return operational_report("browser_failure", True), 21


@pytest.mark.parametrize("category", [
    "pass", "target_only_failure", "target_not_evaluable",
    "interface_failure", "browser_failure",
])
def test_execute_accepts_report_return_codes_only_through_classifier(
        monkeypatch, tmp_path, category):
    value, returncode = _classified_report(category)
    value["app_sha256"] = hashlib.sha256(b"<html></html>").hexdigest()
    receipt, output, _ = _execute_with_fake_process(
        monkeypatch, tmp_path, report=value, returncode=returncode)
    assert receipt["category"] == category
    if category in {"interface_failure", "browser_failure"}:
        assert not any((output / name).exists() for name in SCREENSHOTS)
        assert "target_failed" not in receipt


@pytest.mark.parametrize("screenshot_name", SCREENSHOTS)
@pytest.mark.parametrize("fault", ["missing", "symlink", "oversize", "bad_signature"])
def test_complete_outcome_requires_each_bounded_png(
        monkeypatch, tmp_path, screenshot_name, fault):
    receipt, _, _ = _execute_with_fake_process(
        monkeypatch, tmp_path, report=complete_report(),
        screenshot_fault=(screenshot_name, fault))
    assert receipt == {
        "image": IMAGE,
        "app_sha256": hashlib.sha256(b"<html></html>").hexdigest(),
        "returncode": 0,
        "category": "browser_failure",
        "reason": f"invalid screenshot: {screenshot_name}",
    }


def test_complete_outcome_rejects_extra_png_output(monkeypatch, tmp_path):
    receipt, _, _ = _execute_with_fake_process(
        monkeypatch, tmp_path, report=complete_report(), extra_png=True)
    assert receipt["category"] == "browser_failure"
    assert receipt["reason"] == "unexpected screenshot: unexpected.png"


def test_complete_outcome_requires_report_to_match_executed_app(monkeypatch, tmp_path):
    value = complete_report()
    value["app_sha256"] = "b" * 64
    receipt, _, _ = _execute_with_fake_process(monkeypatch, tmp_path, report=value)
    assert receipt["category"] == "browser_failure"
    assert receipt["reason"] == "executed app hash mismatch"


def test_execute_uses_a_unique_container_name_each_time(monkeypatch, tmp_path):
    names = []
    for directory_name in ("first", "second"):
        directory = tmp_path / directory_name
        directory.mkdir()
        _, _, calls = _execute_with_fake_process(
            monkeypatch, directory, report=complete_report())
        names.append(calls[0][0][5])

    assert names[0].startswith("realworld-author-ui-")
    assert names[1].startswith("realworld-author-ui-")
    assert names[0] != names[1]


def test_execute_rejects_a_preexisting_output_directory(monkeypatch, tmp_path):
    inputs = tmp_path / "inputs"
    inputs.mkdir()
    (inputs / "app.html").write_bytes(b"<html></html>")
    output = tmp_path / "output"
    output.mkdir()
    run_called = False

    def fake_run(*args, **kwargs):
        nonlocal run_called
        run_called = True

    monkeypatch.setattr(oracle.subprocess, "run", fake_run)
    with pytest.raises(FileExistsError):
        oracle.execute(IMAGE, inputs, output)
    assert run_called is False
