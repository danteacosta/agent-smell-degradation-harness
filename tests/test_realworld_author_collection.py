import json
import hashlib
from pathlib import Path
import shutil
import subprocess

import pytest

from scripts import realworld_author_collection as c


HTML = "<!DOCTYPE html><html><body>article</body></html>"
LOCAL_IMAGE = "sha256:" + "1" * 64


def _sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _write_qualification_bundle(root: Path) -> Path:
    root.mkdir()
    regular, operational = c._qualification_contract()
    cases = []
    operational_cases = []
    for case_id, expected in [*regular.items(), *operational.items()]:
        case_root = root / case_id
        output = case_root / "output"
        output.mkdir(parents=True)
        inputs = case_root / "input"
        inputs.mkdir()
        app = inputs / "app.html"
        app.write_text("<html></html>")
        app_hash = _sha(app)
        report = output / "report.json"
        receipt = output / "executor.json"
        report.write_text(json.dumps({"app_sha256": app_hash}) + "\n")
        receipt.write_text(json.dumps({"app_sha256": app_hash}) + "\n")
        (output / "container-command.json").write_text("[]\n")
        (output / "container.log").write_text("")
        public_expected = {key: value for key, value in expected.items() if key != "flag"}
        screenshots = {}
        if case_id in regular:
            for name in (
                "article-alice-author.png", "article-alice-non-author.png",
                "article-bob-author.png", "article-bob-non-author.png",
            ):
                screenshot = output / name
                screenshot.write_bytes(b"\x89PNG\r\n\x1a\n" + case_id.encode() + name.encode())
                screenshots[name] = _sha(screenshot)
            cases.append({
                "id": case_id, "expected": public_expected,
                "observed": public_expected, "matches": True,
                "receipt_fields_exact": True, "report_status": "complete",
                "receipt_sha256": _sha(receipt), "report_sha256": _sha(report),
                "screenshot_sha256": screenshots,
            })
        else:
            operational_cases.append({
                "id": case_id, "expected": public_expected,
                "observed": public_expected, "matches": True,
                "receipt_sha256": _sha(receipt), "report_sha256": _sha(report),
                "screenshot_sha256": {},
            })
    instrument_files = {
        path.relative_to(c.ROOT).as_posix(): c.hash_file(path)
        for path in c._instrument_paths()
    }
    head = subprocess.run(
        ["git", "rev-parse", "HEAD"], cwd=c.ROOT, check=True,
        capture_output=True, text=True,
    ).stdout.strip()
    manifest = {
        "schema_version": "realworld-author-ui-qualification/v1",
        "qualified": True, "matrix_matches": True,
        "custody": {"mode": "git-commit", "git_commit": head},
        "image_id": LOCAL_IMAGE, "instrument_sha256": c.INSTRUMENT_SHA256,
        "source": {"revision": c.admission.SOURCE_REVISION,
                   "sha256": c.admission.SOURCE_SHA256},
        "cases": cases, "operational_cases": operational_cases,
        "files": instrument_files, "limitations": "bounded controls only",
    }
    path = root / "qualification.json"
    path.write_text(json.dumps(manifest, indent=2) + "\n")
    return path


@pytest.fixture
def packet(tmp_path: Path, monkeypatch):
    parent = tmp_path / "admission"
    shutil.copytree(c.ADMISSION_DIRECTORY, parent)
    executable = tmp_path / "codex"
    executable.write_text(
        '#!/bin/sh\nif [ "$1" = "login" ]; then echo "Logged in using ChatGPT"; '
        'else echo codex-test-1.0; fi\n', encoding="utf-8"
    )
    executable.chmod(0o700)
    destination = tmp_path / "private" / "collection"
    qualification = _write_qualification_bundle(tmp_path / "qualification")
    monkeypatch.setattr(c, "LOCAL_IMAGE_ID", LOCAL_IMAGE)
    monkeypatch.setattr(c, "LOCAL_QUALIFICATION_SHA256", _sha(qualification))
    preflight = {
        "ordinary_usage_allowed": True,
        "checked_at_utc": c.now(),
        "chatgpt_auth": True,
        "required_cli_flags": True,
        "image_verified": True,
        "isolation_verified": True,
    }
    manifest = c.prepare(
        parent, destination, executable, preflight,
        image_id=LOCAL_IMAGE, qualification=qualification,
    )
    return destination, parent, executable, qualification, manifest


def provider_factory(calls, *, invalid_at=None, error_at=None):
    class Provider:
        def __init__(self, **kwargs):
            self.kwargs = kwargs
            self.last_call_metadata = {"billing_mode": "chatgpt_subscription"}

        def complete(self, request):
            calls.append((request.prompt, self.kwargs))
            if len(calls) == error_at:
                raise RuntimeError("provider unavailable")
            if len(calls) == invalid_at:
                return "```html\n" + HTML + "\n```"
            return HTML

    return Provider


def test_prepare_freezes_canonical_parent_runtime_cli_and_policy(packet) -> None:
    destination, parent, executable, qualification, manifest = packet
    frozen = destination / "frozen"

    assert manifest["schema_version"] == "realworld-author-collection/v1"
    assert manifest["image_id"] == LOCAL_IMAGE
    assert manifest["local_qualification_sha256"] == c.hash_file(qualification)
    assert manifest["max_calls"] == 18
    assert manifest["concurrency"] == 1
    assert manifest["reasoning_effort"] == "low"
    assert manifest["retry_policy"] == "no_retry_no_resume_no_repair"
    assert manifest["api_key_fallback"] is False
    assert manifest["billing_mode"] == "chatgpt_subscription"
    assert manifest["cli_version"] == "codex-test-1.0"
    assert manifest["executable"] == str(executable.resolve())
    assert (destination.stat().st_mode & 0o077) == 0
    assert (frozen / "schedule.json").read_bytes() == (
        parent / "schedule.json"
    ).read_bytes()
    for row in json.loads((parent / "schedule.json").read_text()):
        name = row["slot_id"] + ".json"
        assert (frozen / "requests" / name).read_bytes() == (
            parent / "requests" / name
        ).read_bytes()
    assert manifest["runtime_hashes"] == c.runtime_hashes()
    c.verify_execution(destination)


def test_run_calls_exact_prompts_once_before_any_browser_and_cannot_resume(packet) -> None:
    destination, _, _, _, _ = packet
    slots = json.loads((destination / "frozen/schedule.json").read_text())
    calls = []
    executed = []

    def executor(**kwargs):
        assert len(calls) == 18
        assert (kwargs["inputs"] / "app.html").read_text() == HTML
        assert kwargs["image"] == LOCAL_IMAGE
        executed.append(kwargs)
        return {"category": "pass", "target_failed": []}

    report = c.run(destination, provider_factory(calls), executor)

    expected = [
        json.loads(
            (destination / "frozen/requests" / f"{row['slot_id']}.json").read_text()
        )["prompt"]
        for row in slots
    ]
    assert [prompt for prompt, _ in calls] == expected
    assert all(kwargs["model"] == row["model"] for (_, kwargs), row in zip(calls, slots))
    assert len(executed) == 18
    assert report["planned"] == report["executable"] == 18
    assert report["unknown"] == 0
    with pytest.raises(FileExistsError):
        c.run(destination, provider_factory(calls), executor)
    assert len(calls) == 18


def test_invalid_output_and_provider_failure_preserve_fixed_denominator(packet) -> None:
    destination, _, _, _, _ = packet
    calls = []
    executed = []

    def executor(**kwargs):
        executed.append(kwargs)
        return {"category": "pass", "target_failed": []}

    report = c.run(
        destination,
        provider_factory(calls, invalid_at=2, error_at=3),
        executor,
    )
    rows = json.loads((destination / "results.json").read_text())["rows"]
    assert [row["category"] for row in rows[:4]] == [
        "pass",
        "invalid_output",
        "provider_error",
        "not_attempted",
    ]
    assert len(calls) == 3
    assert len(executed) == 1
    assert report["planned"] == 18
    assert report["executable"] == 1
    assert report["unknown"] == 17
    assert (destination / "calls" / rows[1]["slot_id"] / "response.txt").read_text().startswith("```")


@pytest.mark.parametrize(
    "drift", ["request", "schedule", "executable", "runtime", "parent", "qualification"]
)
def test_all_drift_including_self_consistent_tampering_rejects_before_provider(
    packet, drift: str, monkeypatch
) -> None:
    destination, parent, executable, qualification, _ = packet
    frozen = destination / "frozen"
    if drift == "request":
        row = json.loads((frozen / "schedule.json").read_text())[0]
        (frozen / "requests" / f"{row['slot_id']}.json").write_text('{"prompt":"changed"}\n')
        inventory = c.hash_inventory(frozen)
        inventory.pop("receipt.json")
        (frozen / "receipt.json").write_text(json.dumps({"files": inventory}) + "\n")
    elif drift == "schedule":
        rows = json.loads((frozen / "schedule.json").read_text())
        (frozen / "schedule.json").write_text(json.dumps(list(reversed(rows))) + "\n")
        inventory = c.hash_inventory(frozen)
        inventory.pop("receipt.json")
        (frozen / "receipt.json").write_text(json.dumps({"files": inventory}) + "\n")
    elif drift == "executable":
        executable.write_text("changed", encoding="utf-8")
    elif drift == "runtime":
        monkeypatch.setattr(c, "runtime_hashes", lambda: {})
    elif drift == "qualification":
        qualification.write_text('{"qualified":true}\n')
    else:
        bundle = json.loads((parent / "prompt-bundle.json").read_text())
        bundle["common_interface"] += "changed"
        (parent / "prompt-bundle.json").write_text(json.dumps(bundle))
        (parent / "receipt.json").write_bytes(
            c.admission.json_bytes(
                c.admission.inventory(parent, exclude={"receipt.json"})
            )
        )
    calls = []
    with pytest.raises(ValueError, match="drift|canonical|inventory|runtime|executable|mismatch"):
        c.run(destination, provider_factory(calls), lambda **kwargs: {})
    assert calls == []


def test_interruption_leaves_attempt_marker_and_forbids_resume(packet) -> None:
    destination, _, _, _, _ = packet
    slots = json.loads((destination / "frozen/schedule.json").read_text())

    class Interrupted:
        def __init__(self, **kwargs):
            pass

        def complete(self, request):
            raise KeyboardInterrupt()

    with pytest.raises(KeyboardInterrupt):
        c.run(destination, Interrupted, lambda **kwargs: {})
    assert (destination / "calls" / slots[0]["slot_id"] / "attempt.json").is_file()
    with pytest.raises(FileExistsError):
        c.run(destination, Interrupted, lambda **kwargs: {})


def test_prepare_rejects_stale_preflight_and_repository_destination(
    tmp_path: Path, monkeypatch
) -> None:
    executable = tmp_path / "codex"
    executable.write_text(
        '#!/bin/sh\nif [ "$1" = "login" ]; then echo "Logged in using ChatGPT"; '
        'else echo test; fi\n'
    )
    executable.chmod(0o700)
    stale = {
        "ordinary_usage_allowed": True,
        "checked_at_utc": "2020-01-01T00:00:00+00:00",
        "chatgpt_auth": True,
        "required_cli_flags": True,
        "image_verified": True,
        "isolation_verified": True,
    }
    with pytest.raises(ValueError, match="stale"):
        c.prepare(
            c.ADMISSION_DIRECTORY, tmp_path / "stale", executable, stale,
            image_id=LOCAL_IMAGE, qualification=tmp_path / "missing.json",
        )
    qualification = _write_qualification_bundle(tmp_path / "qualification")
    monkeypatch.setattr(c, "LOCAL_IMAGE_ID", LOCAL_IMAGE)
    monkeypatch.setattr(c, "LOCAL_QUALIFICATION_SHA256", _sha(qualification))
    with pytest.raises(ValueError, match="outside"):
        c.prepare(
            c.ADMISSION_DIRECTORY, c.ROOT / ".private-test", executable,
            {**stale, "checked_at_utc": c.now()},
            image_id=LOCAL_IMAGE, qualification=qualification,
        )


def test_prepare_rejects_cli_without_chatgpt_auth(tmp_path: Path, monkeypatch) -> None:
    executable = tmp_path / "codex"
    executable.write_text("#!/bin/sh\necho not-authenticated\n")
    executable.chmod(0o700)
    qualification = _write_qualification_bundle(tmp_path / "qualification")
    monkeypatch.setattr(c, "LOCAL_IMAGE_ID", LOCAL_IMAGE)
    monkeypatch.setattr(c, "LOCAL_QUALIFICATION_SHA256", _sha(qualification))
    preflight = {
        "ordinary_usage_allowed": True, "checked_at_utc": c.now(),
        "chatgpt_auth": True, "required_cli_flags": True,
        "image_verified": True, "isolation_verified": True,
    }
    with pytest.raises(ValueError, match="ChatGPT authentication"):
        c.prepare(
            c.ADMISSION_DIRECTORY, tmp_path / "collection", executable, preflight,
            image_id=LOCAL_IMAGE, qualification=qualification,
        )


def test_prepare_requires_exact_approved_local_qualification(
    tmp_path: Path, monkeypatch
) -> None:
    executable = tmp_path / "codex"
    executable.write_text(
        '#!/bin/sh\nif [ "$1" = "login" ]; then echo "Logged in using ChatGPT"; '
        'else echo test; fi\n'
    )
    executable.chmod(0o700)
    qualification = _write_qualification_bundle(tmp_path / "qualification")
    approved_hash = _sha(qualification)
    monkeypatch.setattr(c, "LOCAL_IMAGE_ID", LOCAL_IMAGE)
    monkeypatch.setattr(c, "LOCAL_QUALIFICATION_SHA256", approved_hash)
    value = json.loads(qualification.read_text())
    value["limitations"] = "self-consistent but not the approved qualification"
    qualification.write_text(json.dumps(value, indent=2) + "\n")
    preflight = {
        "ordinary_usage_allowed": True, "checked_at_utc": c.now(),
        "chatgpt_auth": True, "required_cli_flags": True,
        "image_verified": True, "isolation_verified": True,
    }
    with pytest.raises(ValueError, match="approved local qualification"):
        c.prepare(
            c.ADMISSION_DIRECTORY, tmp_path / "collection", executable, preflight,
            image_id=LOCAL_IMAGE, qualification=qualification,
        )


def test_known_target_failure_survives_partial_not_evaluable_outcome() -> None:
    assert c._analysis_category({
        "category": "target_not_evaluable",
        "target_failed": ["author_sees_delete_article"],
    }) == ("target_only_failure", True)


def test_instrument_custody_accepts_unchanged_ancestral_commit(monkeypatch) -> None:
    custody = "a" * 40
    head = "b" * 40
    calls = []

    def fake_run(command, **kwargs):
        calls.append(command)
        if command[:3] == ["git", "rev-parse", "HEAD"]:
            return subprocess.CompletedProcess(command, 0, head + "\n", "")
        return subprocess.CompletedProcess(command, 0, "", "")

    monkeypatch.setattr(c.subprocess, "run", fake_run)
    c._validate_instrument_custody(custody, c._instrument_paths())
    assert ["git", "merge-base", "--is-ancestor", custody, head] in calls
    assert any(command[:3] == ["git", "diff", "--quiet"] for command in calls)


@pytest.mark.parametrize("failure", ["missing", "nonancestor", "drift"])
def test_instrument_custody_rejects_invalid_history_or_drift(
    monkeypatch, failure: str
) -> None:
    custody = "a" * 40
    head = "b" * 40

    def fake_run(command, **kwargs):
        if command[:3] == ["git", "rev-parse", "HEAD"]:
            return subprocess.CompletedProcess(command, 0, head + "\n", "")
        if command[:3] == ["git", "cat-file", "-e"]:
            return subprocess.CompletedProcess(command, 1 if failure == "missing" else 0, "", "")
        if command[:3] == ["git", "merge-base", "--is-ancestor"]:
            return subprocess.CompletedProcess(
                command, 1 if failure == "nonancestor" else 0, "", ""
            )
        if command[:3] == ["git", "diff", "--quiet"]:
            return subprocess.CompletedProcess(command, 1 if failure == "drift" else 0, "", "")
        return subprocess.CompletedProcess(command, 0, "", "")

    monkeypatch.setattr(c.subprocess, "run", fake_run)
    with pytest.raises(ValueError, match="custody|ancestral|changed"):
        c._validate_instrument_custody(custody, c._instrument_paths())


@pytest.mark.parametrize("attack", ["minimal", "report", "screenshot", "extra", "missing"])
def test_qualification_bundle_attacks_fail_closed(tmp_path: Path, attack: str) -> None:
    manifest_path = _write_qualification_bundle(tmp_path / "qualification")
    root = manifest_path.parent
    if attack == "minimal":
        manifest_path.write_text(json.dumps({
            "schema_version": "realworld-author-ui-qualification/v1",
            "qualified": True, "matrix_matches": True,
            "image_id": LOCAL_IMAGE, "instrument_sha256": c.INSTRUMENT_SHA256,
        }))
    elif attack == "report":
        (root / "reference-explicit/output/report.json").write_text('{"app_sha256":"changed"}\n')
    elif attack == "screenshot":
        screenshot = root / "reference-explicit/output/article-alice-author.png"
        screenshot.write_bytes(b"\x89PNG\r\n\x1a\ntampered")
    elif attack == "extra":
        (root / "extra.txt").write_text("extra")
    else:
        (root / "reference-explicit/output/container.log").unlink()
    with pytest.raises(ValueError, match="qualification|inventory|hash|mismatch"):
        c._validate_local_qualification(root, LOCAL_IMAGE)


def test_self_consistent_policy_tampering_rejects_before_provider(packet) -> None:
    destination, _, _, _, _ = packet
    frozen = destination / "frozen"
    manifest_path = frozen / "manifest.json"
    manifest = json.loads(manifest_path.read_text())
    manifest.update({
        "billing_mode": "api_key",
        "provider_calls": 18,
        "experimental_results": True,
        "h1_supported": True,
        "h2_supported": True,
        "output_admission": "repair anything",
        "artifact_limit_bytes": 999999,
    })
    manifest_path.write_text(json.dumps(manifest) + "\n")
    inventory = c.hash_inventory(frozen)
    inventory.pop("receipt.json")
    (frozen / "receipt.json").write_text(json.dumps({"files": inventory}) + "\n")
    calls = []
    with pytest.raises(ValueError, match="policy"):
        c.run(destination, provider_factory(calls), lambda **kwargs: {})
    assert calls == []


def test_self_consistent_semantic_qualification_tampering_is_rejected(packet) -> None:
    destination, _, _, qualification, _ = packet
    root = qualification.parent
    report = root / "reference-explicit/output/report.json"
    value = json.loads(report.read_text())
    value["semantic_forgery"] = True
    report.write_text(json.dumps(value) + "\n")
    qualification_value = json.loads(qualification.read_text())
    qualification_value["cases"][0]["report_sha256"] = _sha(report)
    qualification.write_text(json.dumps(qualification_value, indent=2) + "\n")

    frozen = destination / "frozen"
    (frozen / "local-qualification.json").write_bytes(qualification.read_bytes())
    manifest_path = frozen / "manifest.json"
    manifest = json.loads(manifest_path.read_text())
    manifest["local_qualification_sha256"] = _sha(qualification)
    manifest_path.write_text(json.dumps(manifest) + "\n")
    inventory = c.hash_inventory(frozen)
    inventory.pop("receipt.json")
    (frozen / "receipt.json").write_text(json.dumps({"files": inventory}) + "\n")

    calls = []
    with pytest.raises(ValueError, match="qualification|policy"):
        c.run(destination, provider_factory(calls), lambda **kwargs: {})
    assert calls == []
