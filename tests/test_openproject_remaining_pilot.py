from __future__ import annotations

import importlib.util
from pathlib import Path


QUALIFIER = (
    Path(__file__).parents[1]
    / "eval/fixtures/openproject-remaining-pilot/qualify.py"
)


def _classify(report: dict) -> str:
    spec = importlib.util.spec_from_file_location("remaining_qualify", QUALIFIER)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module.classify(report)


def _report() -> dict:
    return {
        "schema_version": "openproject-remaining-browser/v1",
        "status": "complete",
        "app_sha256": "a" * 64,
        "assertions": {
            "remaining_6h": True,
            "remaining_15h": True,
            "work_10h": True,
            "work_20h": True,
            "percent_40": True,
            "percent_25": True,
        },
        "console_errors": [],
        "screenshots": ["fixture-1.png", "fixture-2.png"],
    }


def test_browser_report_separates_target_and_control_failures() -> None:
    report = _report()
    assert _classify(report) == "pass"

    report["assertions"]["remaining_6h"] = False
    assert _classify(report) == "target_only_failure"

    report["assertions"]["work_10h"] = False
    assert _classify(report) == "mixed_failure"

    report["assertions"]["remaining_6h"] = True
    assert _classify(report) == "non_target_only_failure"


def test_browser_report_fails_closed_on_malformed_or_console_error() -> None:
    report = _report()
    report["assertions"].pop("remaining_15h")
    assert _classify(report) == "malformed_report"

    report = _report()
    report["assertions"]["percent_25"] = 1
    assert _classify(report) == "malformed_report"

    report = _report()
    report["console_errors"] = ["uncaught error"]
    assert _classify(report) == "browser_error"


def test_frozen_arms_and_schedule_preserve_one_omission() -> None:
    from scripts import openproject_remaining_freeze as freeze

    manifest = freeze.validate(
        Path(__file__).parents[1] / "data/e2e-openproject-remaining/freeze-20260926"
    )
    assert len(manifest["schedule"]) == 18
    assert len({row["slot_id"] for row in manifest["schedule"]}) == 18
    assert all(
        sum(row["model"] == model and row["arm"] == arm for row in manifest["schedule"]) == 3
        for model in freeze.MODELS for arm in freeze.ARMS
    )
    assert "Remaining work" in freeze.REQUIREMENTS["A"]
    assert "Remaining work" in freeze.REQUIREMENTS["B"]
    assert "Remaining work" not in freeze.REQUIREMENTS["C"]
    assert manifest["claims"]["confirmatory"] is False


def test_generated_page_admission_preserves_interface_and_rejects_rewrite() -> None:
    from scripts import openproject_remaining_collect as collect
    from scripts import openproject_remaining_freeze as freeze

    scaffold = (Path(__file__).parents[1] / freeze.FIXTURE / "page.html").read_text()
    accepted = scaffold.replace(freeze.MARKER, "app.onSave(values=>values);")
    assert collect.admit(accepted).decode() == accepted

    import pytest

    with pytest.raises(ValueError, match="changed frozen scaffold"):
        collect.admit(accepted.replace("Work package progress", "Other title"))
    with pytest.raises(ValueError, match="invalid behavior"):
        collect.admit(scaffold)
    with pytest.raises(ValueError, match="invalid behavior"):
        collect.admit(scaffold.replace(freeze.MARKER, "</script><script>evil()</script>"))


def test_collection_finishes_all_generations_before_opening_browser(tmp_path, monkeypatch) -> None:
    import json
    import pytest
    from scripts import openproject_remaining_collect as collect
    from scripts import openproject_remaining_freeze as freeze

    packet = tmp_path / "private"
    packet.mkdir(mode=0o700)
    slots = freeze.schedule()
    for row in slots:
        request = packet / "frozen/requests" / (row["slot_id"] + ".json")
        request.parent.mkdir(parents=True, exist_ok=True)
        request.write_text(json.dumps({"prompt": "requirement and frozen page"}))
    monkeypatch.setattr(collect, "verify", lambda _: ({
        "executable": "/unused/codex", "timeout_seconds": 240,
        "image_id": freeze.IMAGE, "artifact_limit_bytes": 200000,
        "claims": {"confirmatory": False},
    }, slots))
    scaffold = (Path(__file__).parents[1] / freeze.FIXTURE / "page.html").read_text()
    generated = scaffold.replace(freeze.MARKER, "app.onSave(values=>values);")
    events = []

    class FakeProvider:
        def __init__(self, **kwargs):
            self.last_call_metadata = {"provider": "fake"}

        def complete(self, request):
            events.append("generation")
            return generated

    def browser(image, inputs, output):
        events.append("browser")
        return {"category": "target_only_failure"}

    result = collect.run(packet, provider_factory=FakeProvider, executor=browser)
    assert events == ["generation"] * 18 + ["browser"] * 18
    assert result["calls_attempted"] == 18
    assert all(row["target_failed"] is True for row in result["rows"])
    with pytest.raises(FileExistsError, match="no resume"):
        collect.run(packet, provider_factory=FakeProvider, executor=browser)
