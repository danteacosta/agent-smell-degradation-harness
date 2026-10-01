"""Observable classification for the inbox-suggestion browser journey."""
import runpy
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
classify = runpy.run_path(str(ROOT / "eval/fixtures/paperless-inbox-suggestions/qualify.py"))["classify"]


def report(*, target=True, neutral=True):
    assertions = {}
    for index in (1, 2):
        assertions[f"request_once_{index}"] = target
        assertions[f"suggestion_visible_{index}"] = target
        assertions[f"document_title_{index}"] = neutral
        assertions[f"document_id_{index}"] = neutral
        assertions[f"suggest_button_{index}"] = neutral
    return {"schema_version": "paperless-inbox-suggestions-browser/v1", "status": "complete",
            "app_sha256": "a" * 64, "assertions": assertions, "console_errors": [],
            "screenshots": ["fixture-1.png", "fixture-2.png"]}


def test_missing_auto_request_is_a_target_failure_when_page_is_assessable():
    assert classify(report()) == "pass"
    assert classify(report(target=False)) == "target_only_failure"
    assert classify(report(neutral=False)) == "non_target_only_failure"


def test_incomplete_report_cannot_become_a_defect():
    data = report(target=False)
    del data["assertions"]["request_once_2"]
    assert classify(data) == "malformed_report"
    data = report(target=False)
    data["console_errors"] = ["script failed"]
    assert classify(data) == "browser_error"
