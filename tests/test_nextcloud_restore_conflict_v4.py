"""Observable report and arm contract for the Nextcloud conflict pilot."""
import importlib.util
import json
import hashlib
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location(
    "nextcloud_restore_conflict_v4_qualify",
    ROOT / "eval/fixtures/nextcloud-restore-conflict-v4/qualify.py",
)
qualifier = importlib.util.module_from_spec(spec)
spec.loader.exec_module(qualifier)


def test_complete_report_distinguishes_name_collision_from_restore_failure():
    report = {"schema_version": "nextcloud-restore-conflict-browser/v4", "status": "complete",
              "app_sha256": "0" * 64,
              "assertions": {key: True for key in qualifier.TARGET | qualifier.NON_TARGET},
              "console_errors": [], "screenshots": ["files-1.png", "files-2.png"]}
    assert qualifier.classify(report) == "pass"
    report["assertions"]["unique_name_1"] = False
    assert qualifier.classify(report) == "target_only_failure"
    report["assertions"]["restored_original_path_1"] = False
    assert qualifier.classify(report) == "non_target_failure"
    report["assertions"].pop("active_count_2")
    assert qualifier.classify(report) == "malformed_report"


def test_c_omits_only_the_unique_name_clause():
    arms = json.loads((ROOT / "data/e2e-nextcloud-restore-conflict/arms-20260926.json").read_text())
    assert arms["A"].replace(" If an active file already has the same name there, give the restored file a unique name.", "") == arms["C"]


def test_collector_accepts_oracles_named_proof_images(tmp_path):
    from scripts.nextcloud_restore_conflict_v4b_pilot import corrected_category

    artifact = tmp_path / "app.html"
    artifact.write_text("<html></html>")
    report = {"schema_version": "nextcloud-restore-conflict-browser/v4", "status": "complete",
              "app_sha256": hashlib.sha256(artifact.read_bytes()).hexdigest(),
              "assertions": {key: True for key in qualifier.TARGET | qualifier.NON_TARGET},
              "console_errors": [], "screenshots": ["files-1.png", "files-2.png"]}
    for name in report["screenshots"]:
        (tmp_path / name).write_bytes(b"\x89PNG\r\n\x1a\nproof")
    base = {"returncode": 0, "category": "browser_error"}
    oracle = ROOT / "eval/fixtures/nextcloud-restore-conflict-v4/qualify.py"
    assert corrected_category(base, report, tmp_path, artifact, oracle) == "pass"
    (tmp_path / "files-2.png").unlink()
    assert corrected_category(base, report, tmp_path, artifact, oracle) == "browser_error"
