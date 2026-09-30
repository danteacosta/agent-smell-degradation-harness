"""Public behavior contracts for invalid Remaining work saves."""
import importlib.util
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location("openproject_invalid_qualify", ROOT / "eval/fixtures/openproject-invalid-remaining/qualify.py")
qualifier = importlib.util.module_from_spec(spec)
spec.loader.exec_module(qualifier)


def test_incomplete_browser_report_cannot_pass():
    assert qualifier.classify({}) == "malformed_report"
    report = {"schema_version": "openproject-invalid-remaining-browser/v1", "status": "complete",
              "app_sha256": "0" * 64,
              "assertions": {key: True for key in qualifier.TARGET | qualifier.NON_TARGET},
              "console_errors": [], "screenshots": ["fixture-1.png", "fixture-2.png"]}
    assert qualifier.classify(report) == "pass"
    report["assertions"].pop("invalid_rejected_2")
    assert qualifier.classify(report) == "malformed_report"


def test_omission_removes_only_invalid_save_guard():
    arms = json.loads((ROOT / "data/e2e-openproject-invalid-remaining/arms-20260926.json").read_text())
    clause = " A Remaining work value greater than Work cannot be saved."
    assert arms["A"].replace(clause, "") == arms["C"]
