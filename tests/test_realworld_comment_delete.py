"""Public result contract for comment Delete visibility."""
import importlib.util
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location(
    "realworld_comment_delete_qualify", ROOT / "eval/fixtures/realworld-comment-delete/qualify.py")
qualifier = importlib.util.module_from_spec(spec)
spec.loader.exec_module(qualifier)


def test_browser_report_separates_visibility_and_prerequisites():
    report = {"schema_version": "realworld-comment-delete-browser/v1", "status": "complete",
              "app_sha256": "0" * 64,
              "assertions": {key: True for key in qualifier.TARGET | qualifier.NON_TARGET},
              "console_errors": [], "screenshots": ["fixture-1.png", "fixture-2.png", "fixture-3.png", "fixture-4.png"]}
    assert qualifier.classify(report) == "pass"
    report["assertions"]["author_delete_visible_1"] = False
    assert qualifier.classify(report) == "target_only_failure"
    report["assertions"]["comment_visible_1"] = False
    assert qualifier.classify(report) == "mixed_failure"
    report["assertions"].pop("comment_visible_2")
    assert qualifier.classify(report) == "malformed_report"


def test_c_deletes_only_author_visibility_rule():
    arms = json.loads((ROOT / "data/e2e-realworld-comment-delete/arms-20260927.json").read_text())
    assert arms["A"].replace(" if and only if the signed-in viewer is the comment's author", "") == arms["C"]
