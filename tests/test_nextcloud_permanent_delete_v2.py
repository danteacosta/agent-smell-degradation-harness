"""Browser report contract for the deferred permanent-delete instrument."""
import importlib.util
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location(
    "nextcloud_permanent_delete_v2_qualify",
    ROOT / "eval/fixtures/nextcloud-permanent-delete-v2/qualify.py",
)
qualifier = importlib.util.module_from_spec(spec)
spec.loader.exec_module(qualifier)


def test_deletion_and_preservation_are_separate_observations():
    report = {"schema_version": "nextcloud-permanent-delete-browser/v2", "status": "complete",
              "app_sha256": "0" * 64,
              "assertions": {key: True for key in qualifier.TARGET | qualifier.NON_TARGET},
              "console_errors": [], "screenshots": ["fixture-1.png", "fixture-2.png"]}
    assert qualifier.classify(report) == "pass"
    report["assertions"]["selected_absent_1"] = False
    assert qualifier.classify(report) == "target_only_failure"
    report["assertions"]["control_preserved_2"] = False
    assert qualifier.classify(report) == "mixed_failure"
    report["assertions"].pop("no_extra_rows_2")
    assert qualifier.classify(report) == "malformed_report"
