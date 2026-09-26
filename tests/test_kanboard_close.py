"""Public behavior contracts for the Kanboard close-task instrument."""
import json
import importlib.util
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location("kanboard_close_qualify", ROOT / "eval/fixtures/kanboard-close/qualify.py")
qualifier = importlib.util.module_from_spec(spec)
spec.loader.exec_module(qualifier)
classify, TARGET, NON_TARGET = qualifier.classify, qualifier.TARGET, qualifier.NON_TARGET


def test_partial_browser_report_cannot_pass():
    assert classify({}) == "malformed_report"
    report = {"schema_version": "kanboard-close-browser/v1", "status": "complete",
              "app_sha256": "0" * 64, "assertions": {key: True for key in TARGET | NON_TARGET},
              "console_errors": [], "screenshots": ["board-1.png", "closed-1.png", "board-2.png", "closed-2.png"]}
    assert classify(report) == "pass"
    report["assertions"].pop("target_hidden_2")
    assert classify(report) == "malformed_report"


def test_c_removes_only_board_visibility():
    arms = json.loads((ROOT / "data/e2e-kanboard-close/arms-20260926.json").read_text())
    assert "board" in arms["A"] and "board" in arms["B"]
    assert "board" not in arms["C"]
    assert "Closed tasks" in arms["A"] and "Closed tasks" in arms["B"] and "Closed tasks" in arms["C"]
