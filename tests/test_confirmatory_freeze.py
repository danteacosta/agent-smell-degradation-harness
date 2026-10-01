from __future__ import annotations

import json
from pathlib import Path

import pytest

from eval.freeze import DEFAULT_FREEZE_FILES, build_freeze_manifest, main, validate_freeze


ROOT = Path(__file__).resolve().parents[1]


def test_default_freeze_includes_primary_irr_policy_and_implementation():
    assert "tasks/annotation_rubric.json" in DEFAULT_FREEZE_FILES
    assert "label_plane/annotation_protocol.py" in DEFAULT_FREEZE_FILES
    assert "protocol/irr.py" in DEFAULT_FREEZE_FILES


def test_candidate_freeze_matches_the_current_repository():
    manifest = json.loads(
        (ROOT / "docs/thesis/confirmatory-freeze.json").read_text(encoding="utf-8")
    )
    assert set(manifest["files"]) == set(DEFAULT_FREEZE_FILES)
    assert validate_freeze(manifest, repository_root=ROOT)["status"] == "candidate"


def test_freeze_manifest_detects_file_drift_and_requires_confirmation(tmp_path):
    path = tmp_path / "protocol.md"
    path.write_text("v1\n", encoding="utf-8")
    manifest = build_freeze_manifest(repository_root=tmp_path, relative_files=["protocol.md"])
    with pytest.raises(ValueError, match="confirmed freeze"):
        validate_freeze(manifest, repository_root=tmp_path, require_confirmed=True)
    assert validate_freeze(manifest, repository_root=tmp_path)["status"] == "candidate"
    path.write_text("v2\n", encoding="utf-8")
    with pytest.raises(ValueError, match="hash:protocol.md"):
        validate_freeze(manifest, repository_root=tmp_path)


def test_confirmed_freeze_requires_explicit_outcome_blind_acknowledgement(tmp_path):
    with pytest.raises(ValueError, match="acknowledge-outcome-blind-freeze"):
        main(["--repository-root", str(tmp_path), "--status", "confirmed"])
