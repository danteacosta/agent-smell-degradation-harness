"""Freeze-before-data validation for confirmatory runs."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Any

FREEZE_SCHEMA_VERSION = "confirmatory-freeze/v1"
DEFAULT_FREEZE_FILES = (
    "agents/checkpoints.py",
    "agents/live.py",
    "agents/runtime.py",
    "agents/staged_runtime.py",
    "baselines/features.py",
    "data/confirmatory/precision-plan.candidate.json",
    "data/confirmatory/precision-sensitivity.candidate.json",
    "docs/thesis-product-boundary.md",
    "eval/confirmatory_report.py",
    "eval/experiment.py",
    "eval/feature_manifest.py",
    "eval/h2_detection.py",
    "eval/runner.py",
    "eval/sample_gate.py",
    "eval/splits.py",
    "feature_plane/deployable.py",
    "label_plane/human_annotation/__init__.py",
    "protocol/power.py",
    "tasks/annotation_rubric.json",
)


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


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Regenerate the confirmatory freeze manifest")
    parser.add_argument("--repository-root", type=Path, default=Path("."))
    parser.add_argument(
        "--output", type=Path, default=Path("docs/thesis/confirmatory-freeze.json")
    )
    parser.add_argument("--status", choices=("candidate", "confirmed"), default="candidate")
    parser.add_argument("--acknowledge-outcome-blind-freeze", action="store_true")
    args = parser.parse_args(argv)
    if args.status == "confirmed" and not args.acknowledge_outcome_blind_freeze:
        raise ValueError(
            "confirmed freeze requires --acknowledge-outcome-blind-freeze before provider runs"
        )
    manifest = build_freeze_manifest(
        repository_root=args.repository_root,
        relative_files=list(DEFAULT_FREEZE_FILES),
        status=args.status,
    )
    output = args.repository_root / args.output
    output.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    validate_freeze(manifest, repository_root=args.repository_root)
    return 0


__all__ = ("DEFAULT_FREEZE_FILES", "FREEZE_SCHEMA_VERSION", "build_freeze_manifest", "sha256_file", "validate_freeze")


if __name__ == "__main__":
    raise SystemExit(main())
