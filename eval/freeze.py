"""Freeze-before-data validation for confirmatory runs."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any

FREEZE_SCHEMA_VERSION = "confirmatory-freeze/v1"


def sha256_file(path: str | Path) -> str:
    digest = hashlib.sha256()
    with Path(path).open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def validate_freeze(
    manifest: dict[str, Any], *, repository_root: str | Path, require_confirmed: bool = False
) -> dict[str, Any]:
    if manifest.get("schema_version") != FREEZE_SCHEMA_VERSION:
        raise ValueError("confirmatory freeze schema_version is invalid")
    if require_confirmed and manifest.get("status") != "confirmed":
        raise ValueError("confirmatory provider execution requires a confirmed freeze")
    root = Path(repository_root)
    files = manifest.get("files")
    if not isinstance(files, dict) or not files:
        raise ValueError("confirmatory freeze files are required")
    mismatches: list[str] = []
    for relative, expected_hash in files.items():
        path = root / str(relative)
        if not path.is_file():
            mismatches.append(f"missing:{relative}")
        elif sha256_file(path) != str(expected_hash):
            mismatches.append(f"hash:{relative}")
    if mismatches:
        raise ValueError("confirmatory freeze mismatch: " + ", ".join(mismatches))
    return {"status": str(manifest.get("status", "candidate")), "files": dict(files)}


def build_freeze_manifest(
    *, repository_root: str | Path, relative_files: list[str], status: str = "candidate"
) -> dict[str, Any]:
    root = Path(repository_root)
    return {
        "schema_version": FREEZE_SCHEMA_VERSION,
        "status": status,
        "hash_algorithm": "sha256",
        "files": {relative: sha256_file(root / relative) for relative in sorted(relative_files)},
    }


__all__ = ("FREEZE_SCHEMA_VERSION", "build_freeze_manifest", "sha256_file", "validate_freeze")
