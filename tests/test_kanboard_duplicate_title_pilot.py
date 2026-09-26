"""Observable contract for the Kanboard duplicate-title browser pilot."""

from __future__ import annotations

from pathlib import Path
import runpy
import subprocess
import pytest


ROOT = Path(__file__).resolve().parents[1]
FIXTURE = ROOT / "eval/fixtures/kanboard-duplicate-title-pilot"


def classify(report: dict) -> str:
    return runpy.run_path(str(FIXTURE / "qualify.py"))["classify"](report)


def report(*, target: bool = True, controls: bool = True) -> dict:
    return {
        "schema_version": "kanboard-duplicate-title-browser/v1",
        "status": "complete",
        "app_sha256": "a" * 64,
        "assertions": {
            "duplicate_title_1": target,
            "duplicate_title_2": target,
            "source_preserved_1": controls,
            "source_preserved_2": controls,
            "unrelated_preserved_1": controls,
            "unrelated_preserved_2": controls,
            "same_project_1": controls,
            "same_project_2": controls,
        },
        "console_errors": [],
        "screenshots": ["fixture-1.png", "fixture-2.png"],
    }


def test_browser_contract_distinguishes_target_and_controls() -> None:
    assert classify(report()) == "pass"
    assert classify(report(target=False)) == "target_only_failure"
    assert classify(report(controls=False)) == "non_target_only_failure"
    assert classify(report(target=False, controls=False)) == "mixed_failure"


def test_malformed_and_error_reports_fail_closed() -> None:
    bad = report()
    bad["assertions"]["duplicate_title_1"] = 1
    assert classify(bad) == "malformed_report"
    bad = report()
    bad["assertions"]["unexpected"] = True
    assert classify(bad) == "malformed_report"
    bad = report()
    bad["console_errors"] = ["script error"]
    assert classify(bad) == "browser_error"
    bad = {key: value for key, value in report().items() if key != "screenshots"}
    assert classify(bad) == "malformed_report"


def test_scaffold_has_one_behavior_insertion_point() -> None:
    page = (FIXTURE / "page.html").read_text()
    assert page.count("/* MODEL_BEHAVIOR */") == 1


def test_freeze_has_balanced_distinct_schedule_and_one_deleted_obligation() -> None:
    from scripts import kanboard_duplicate_freeze as freeze

    rows = freeze.schedule()
    assert len(rows) == len({row["slot_id"] for row in rows}) == 18
    assert {row["project_id"] for row in rows} == {"kanboard"}
    for model in freeze.MODELS:
        for arm in freeze.ARMS:
            assert sum(row["model"] == model and row["arm"] == arm for row in rows) == 3
    assert "title" in freeze.REQUIREMENTS["A"].lower()
    assert "title" in freeze.REQUIREMENTS["B"].lower()
    assert "title" not in freeze.REQUIREMENTS["C"].lower()
    manifest = freeze.manifest()
    assert manifest["planned_slots"] == 18
    assert manifest["qualification"]["image_id"].startswith("sha256:")


def test_frozen_requests_detect_drift(tmp_path: Path) -> None:
    from scripts import kanboard_duplicate_freeze as freeze

    packet = tmp_path / "freeze"
    freeze.materialize(packet)
    assert len(freeze.validate(packet)["schedule"]) == 18
    first = next((packet / "requests").iterdir())
    first.write_bytes(first.read_bytes() + b" ")
    with pytest.raises(ValueError, match="request drift"):
        freeze.validate(packet)


def test_checked_in_freeze_is_intact() -> None:
    from scripts import kanboard_duplicate_freeze as freeze

    packet = ROOT / "data/e2e-kanboard-duplicate-title/freeze-20260926"
    assert len(freeze.validate(packet)["schedule"]) == 18


def test_collection_admits_only_single_behavior_insertion() -> None:
    from scripts import kanboard_duplicate_collect as collect

    scaffold = (FIXTURE / "page.html").read_text()
    valid = scaffold.replace(
        "/* MODEL_BEHAVIOR */",
        "app.onDuplicate(task=>({...task,id:'new-'+task.id}));",
    )
    assert collect.admit(valid).decode() == valid
    without_final_newline = valid.rstrip("\n")
    assert collect.admit(without_final_newline).decode() == without_final_newline
    with pytest.raises(ValueError, match="frozen scaffold"):
        collect.admit(valid.replace("Project tasks", "Changed UI"))
    with pytest.raises(ValueError, match="invalid behavior"):
        collect.admit(scaffold.replace("/* MODEL_BEHAVIOR */", " "))


def test_collection_generates_before_browser_and_retains_unknowns(tmp_path: Path, monkeypatch) -> None:
    from scripts import kanboard_duplicate_collect as collect
    from scripts import kanboard_duplicate_freeze as freeze

    executable = tmp_path / "codex"
    executable.write_text(
        '#!/bin/sh\nif [ "$1" = "login" ]; then echo "Logged in using ChatGPT"; '
        'else echo codex-test-1.0; fi\n'
    )
    executable.chmod(0o700)
    real_run = subprocess.run

    def image_inspect(command, **kwargs):
        if command[:3] == ["docker", "image", "inspect"]:
            return subprocess.CompletedProcess(command, 0, stdout=freeze.IMAGE + "\n", stderr="")
        return real_run(command, **kwargs)

    monkeypatch.setattr(collect.subprocess, "run", image_inspect)
    packet = tmp_path / "private-packet"
    collect.prepare(ROOT / "data/e2e-kanboard-duplicate-title/freeze-20260926", packet, executable)
    arms = {row["slot_id"]: row["arm"] for row in freeze.schedule()}
    events = []

    class Provider:
        def __init__(self, **kwargs):
            self.last_call_metadata = {"billing_mode": "chatgpt_subscription"}

        def complete(self, request):
            events.append("generation")
            if events.count("generation") == 2:
                return "invalid output"
            page = request.prompt.split("Frozen page:\n", 1)[1]
            return page.replace(freeze.MARKER, "app.onDuplicate(task=>({...task,id:'copy-'+task.id}));")

    def executor(image, inputs, output, runner, qualifier):
        assert events.count("generation") == 18
        assert image == freeze.IMAGE
        assert runner == packet / "frozen/runtime/eval/fixtures/kanboard-duplicate-title-pilot/runner.cjs"
        assert qualifier == packet / "frozen/runtime/eval/fixtures/kanboard-duplicate-title-pilot/qualify.py"
        assert runner.is_file() and qualifier.is_file() and (inputs / "app.html").is_file()
        events.append("browser")
        return {"category": "target_only_failure" if arms[inputs.name] == "C" else "pass"}

    analysis = collect.run(packet, Provider, executor)
    rows = analysis["rows"]
    assert len(rows) == analysis["planned_slots"] == analysis["calls_attempted"] == 18
    assert events[:18] == ["generation"] * 18
    assert events[18:] == ["browser"] * 17
    assert sum(row["category"] == "invalid_output" for row in rows) == 1
    assert sum(row["target_failed"] is None for row in rows) == 1
    assert analysis["contrasts"]["C_minus_A"]["arm_counts"]["planned"] == 6
    assert analysis["contrasts"]["B_minus_A"]["arm_counts"]["planned"] == 6
    assert analysis["contrasts"]["C_minus_A"]["planned_denominator_difference"] > 0
    assert analysis["contrasts"]["B_minus_A"]["planned_denominator_difference"] == 0
    with pytest.raises(FileExistsError, match="no resume"):
        collect.run(packet, Provider, executor)
