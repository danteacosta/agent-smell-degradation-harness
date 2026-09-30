"""Observable contracts for the Nextcloud restore-name conflict instrument."""
import json
import importlib.util
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location("nextcloud_restore_qualify", ROOT / "eval/fixtures/nextcloud-restore-conflict/qualify.py")
qualifier = importlib.util.module_from_spec(spec)
spec.loader.exec_module(qualifier)
classify, NON_TARGET, TARGET = qualifier.classify, qualifier.NON_TARGET, qualifier.TARGET


def test_malformed_or_partial_browser_report_cannot_be_a_pass():
    assert classify({}) == "malformed_report"
    report = {"schema_version": "nextcloud-restore-conflict-browser/v1", "status": "complete",
              "app_sha256": "0" * 64, "assertions": {key: True for key in TARGET | NON_TARGET},
              "console_errors": [], "screenshots": ["files-1.png", "files-2.png"]}
    assert classify(report) == "pass"
    del report["assertions"]["unique_name_2"]
    assert classify(report) == "malformed_report"


def test_omission_arm_removes_only_the_unique_name_rule():
    arms = json.loads((ROOT / "data/e2e-nextcloud-restore-conflict/arms-20260926.json").read_text())
    clause = " If an active file already has the same name there, give the restored file a unique name."
    assert arms["A"].replace(clause, "") == arms["C"]
