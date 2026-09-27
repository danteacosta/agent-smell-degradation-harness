"""Public browser-result contract for Kanboard Closed tasks filter."""
import importlib.util
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location(
    "kanboard_closed_filter_qualify", ROOT / "eval/fixtures/kanboard-closed-filter/qualify.py")
qualifier = importlib.util.module_from_spec(spec)
spec.loader.exec_module(qualifier)


def test_complete_report_is_not_inferred_from_missing_or_broken_controls():
    report = {"schema_version": "kanboard-closed-filter-browser/v1", "status": "complete",
              "app_sha256": "0" * 64,
              "assertions": {key: True for key in qualifier.TARGET | qualifier.NON_TARGET},
              "console_errors": [], "screenshots": ["fixture-1.png", "fixture-2.png"]}
    assert qualifier.classify(report) == "pass"
    report["assertions"]["closed_visible_1"] = False
    assert qualifier.classify(report) == "target_only_failure"
    report["assertions"]["open_on_board_1"] = False
    assert qualifier.classify(report) == "mixed_failure"
    report["assertions"].pop("closed_visible_2")
    assert qualifier.classify(report) == "malformed_report"


def test_c_deletes_only_filter_retrieval_clause():
    arms = json.loads((ROOT / "data/e2e-kanboard-closed-filter/arms-20260927.json").read_text())
    assert arms["A"].replace(" The Closed tasks filter shows closed tasks.", "") == arms["C"]
