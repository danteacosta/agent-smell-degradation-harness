from __future__ import annotations

import pytest

from eval.freeze import build_freeze_manifest, validate_freeze


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
