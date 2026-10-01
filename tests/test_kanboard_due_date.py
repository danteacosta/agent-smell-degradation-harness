"""Observable Kanboard due-date color classification contract."""
import runpy
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
classify = runpy.run_path(str(ROOT / "eval/fixtures/kanboard-due-date/qualify.py"))["classify"]
CONTROLS = runpy.run_path(str(ROOT / "eval/fixtures/kanboard-due-date/qualify.py"))["CONTROLS"]


def report(*, target=True, neutral=True):
    assertions = {}
    for index in (1, 2):
        assertions[f"overdue_red_{index}"] = target
        assertions[f"upcoming_black_{index}"] = target
        assertions[f"task_titles_{index}"] = neutral
        assertions[f"due_text_{index}"] = neutral
    return {
        "schema_version": "kanboard-due-date-browser/v2",
        "status": "complete",
        "app_sha256": "a" * 64,
        "assertions": assertions,
        "console_errors": [],
        "screenshots": ["fixture-1.png", "fixture-2.png"],
    }


def test_target_failure_separate_from_neutral_failure():
    assert classify(report()) == "pass"
    assert classify(report(target=False)) == "target_only_failure"
    assert classify(report(neutral=False)) == "non_target_only_failure"
    assert classify(report(target=False, neutral=False)) == "mixed_failure"


def test_malformed_observation_cannot_become_success_or_defect():
    data = report()
    del data["assertions"]["upcoming_black_2"]
    assert classify(data) == "malformed_report"
    data = report()
    data["assertions"]["overdue_red_1"] = 1
    assert classify(data) == "malformed_report"


def test_console_error_with_complete_report_is_unknown():
    data = report()
    data["console_errors"] = ["uncaught exception"]
    assert classify(data) == "browser_error"


def test_nested_text_color_controls_are_part_of_browser_qualification():
    assert CONTROLS["nested-wrong-text-color"][1] == "target_only_failure"
    assert CONTROLS["nested-correct-text-color"][1] == "pass"
