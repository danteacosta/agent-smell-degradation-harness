"""Public browser-result and A/B/C contracts for nested tags."""
import importlib.util
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location(
    "paperless_nested_qualify", ROOT / "eval/fixtures/paperless-nested-tags/qualify.py")
qualifier = importlib.util.module_from_spec(spec)
spec.loader.exec_module(qualifier)


def test_complete_browser_report_distinguishes_only_parent_omission():
    report = {"schema_version": "paperless-nested-tags-browser/v1", "status": "complete",
              "app_sha256": "0" * 64,
              "assertions": {key: True for key in qualifier.TARGET | qualifier.NON_TARGET},
              "console_errors": [], "screenshots": ["fixture-1.png", "fixture-2.png"]}
    assert qualifier.classify(report) == "pass"
    report["assertions"]["parent_visible_1"] = False
    assert qualifier.classify(report) == "target_only_failure"
    report["assertions"]["child_visible_1"] = False
    assert qualifier.classify(report) == "mixed_failure"
    report["assertions"].pop("child_visible_2")
    assert qualifier.classify(report) == "malformed_report"


def test_c_deletes_only_parent_propagation():
    arms = json.loads((ROOT / "data/e2e-paperless-nested-tags/arms-20260927.json").read_text())
    assert arms["A"].replace(" Also add every ancestor tag automatically.", "") == arms["C"]
