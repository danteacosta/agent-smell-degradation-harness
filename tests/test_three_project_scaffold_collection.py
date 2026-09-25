import hashlib
import json
from pathlib import Path
import shutil

import pytest

from scripts import three_project_scaffold_collection as c


HTML = "<!DOCTYPE html><html><body>bounded</body></html>"
IMAGE = c.APPROVED_IMAGE_ID


def _sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


@pytest.fixture
def packet(tmp_path: Path, monkeypatch):
    parent = tmp_path / "freeze"
    shutil.copytree(c.PARENT_DIRECTORY, parent)
    qualification = tmp_path / "qualification"
    shutil.copytree(c.QUALIFICATION_DIRECTORY, qualification)
    executable = tmp_path / "codex"
    executable.write_text(
        '#!/bin/sh\nif [ "$1" = "login" ]; then echo "Logged in using ChatGPT"; '
        'else echo codex-test-1.0; fi\n', encoding="utf-8"
    )
    executable.chmod(0o700)
    destination = tmp_path / "private" / "collection"
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
        image_id=IMAGE, qualification=qualification,
    )
    return destination, executable, manifest


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
            scaffold = request.prompt.split("\n\nFrozen page:\n", 1)[1]
            return scaffold.replace(c.freeze.PLACEHOLDER, "")

    return Provider


def test_prepare_binds_54_requests_runtime_oracle_and_policy(packet) -> None:
    destination, executable, manifest = packet
    frozen = destination / "frozen"
    schedule = json.loads((frozen / "schedule.json").read_text())

    assert manifest["schema_version"] == "three-project-fixed-scaffold-collection/v1"
    assert manifest["max_calls"] == len(schedule) == 54
    assert manifest["image_id"] == IMAGE
    assert manifest["concurrency"] == 1
    assert manifest["retry_policy"] == "no_retry_no_resume_no_repair"
    assert manifest["billing_mode"] == "chatgpt_subscription"
    assert manifest["api_key_fallback"] is False
    assert manifest["executable_sha256"] == _sha(executable)
    assert (destination.stat().st_mode & 0o077) == 0
    assert len(list((frozen / "requests").glob("*.json"))) == 54
    assert manifest["runtime_hashes"] == c.runtime_hashes()
    c.verify_execution(destination)


def test_generation_finishes_before_browser_and_project_is_bound(packet) -> None:
    destination, _, _ = packet
    schedule = json.loads((destination / "frozen/schedule.json").read_text())
    calls = []
    executed = []

    def executor(*, image, inputs, output, project_id):
        assert len(calls) == 54
        assert image == IMAGE
        assert json.loads((inputs / "case.json").read_text()) == {
            "project_id": project_id, "mode": "generated"
        }
        executed.append(project_id)
        return {"category": "pass", "target_failed": []}

    report = c.run(destination, provider_factory(calls), executor)

    assert len(calls) == len(executed) == 54
    expected_prompts = [
        json.loads((destination / "frozen/requests" / f"{row['slot_id']}.json").read_text())["prompt"]
        for row in schedule
    ]
    assert [prompt for prompt, _ in calls] == expected_prompts
    assert [kwargs["model"] for _, kwargs in calls] == [row["model"] for row in schedule]
    assert executed == [row["project_id"] for row in schedule]
    assert report["planned"] == report["executable"] == 54
    assert report["unknown"] == 0
    with pytest.raises(FileExistsError):
        c.run(destination, provider_factory(calls), executor)


def test_invalid_output_and_provider_error_preserve_denominator(packet) -> None:
    destination, _, _ = packet
    calls = []
    executed = []

    def executor(**kwargs):
        executed.append(kwargs)
        return {"category": "pass", "target_failed": []}

    report = c.run(
        destination, provider_factory(calls, invalid_at=2, error_at=3), executor
    )
    rows = json.loads((destination / "results.json").read_text())["rows"]
    assert [row["category"] for row in rows[:4]] == [
        "pass", "invalid_output", "provider_error", "not_attempted"
    ]
    assert len(calls) == 3
    assert len(executed) == 1
    assert report["planned"] == 54
    assert report["unknown"] == 53


def test_output_admission_allows_only_behavior_region_changes() -> None:
    project = "paperless-ngx"
    scaffold = (
        c.ROOT / "eval/fixtures/three-project-scaffold" / f"{project}.html"
    ).read_text()
    valid = scaffold.replace(c.freeze.PLACEHOLDER, "app.register('upload',()=>{});")
    assert c.admit_fixed_scaffold(valid, project) == valid.encode()

    with pytest.raises(ValueError, match="changed frozen scaffold"):
        c.admit_fixed_scaffold(valid.replace("<title>Documents</title>", "<title>Changed</title>"), project)
    with pytest.raises(ValueError):
        c.admit_fixed_scaffold("```html\n" + valid + "\n```", project)
    escaped = scaffold.replace(
        c.freeze.PLACEHOLDER,
        "</script><div data-document-id='invented'>Changed DOM</div><script>",
    )
    with pytest.raises(ValueError, match="escape the behavior script"):
        c.admit_fixed_scaffold(escaped, project)


@pytest.mark.parametrize("drift", ["request", "executable", "runtime", "parent", "qualification"])
def test_drift_rejects_before_provider(packet, drift: str, monkeypatch) -> None:
    destination, executable, manifest = packet
    if drift == "request":
        request = next((destination / "frozen/requests").glob("*.json"))
        request.write_text('{"prompt":"changed"}\n')
    elif drift == "executable":
        executable.write_text("changed")
    elif drift == "runtime":
        monkeypatch.setattr(c, "runtime_hashes", lambda: {})
    elif drift == "parent":
        Path(manifest["parent"], "manifest.json").write_text("{}\n")
    else:
        Path(manifest["qualification"], "qualification.json").write_text("{}\n")
    calls = []
    with pytest.raises(ValueError):
        c.run(destination, provider_factory(calls), lambda **kwargs: {})
    assert calls == []
