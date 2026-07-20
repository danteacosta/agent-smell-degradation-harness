from __future__ import annotations

import hashlib
import json
import subprocess
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from pairs.loader import DEFAULT_PAIRS_DIR


def _try_git_sha(repo_root: Path) -> str | None:
    try:
        result = subprocess.run(
            ["git", "rev-parse", "HEAD"],
            cwd=repo_root,
            capture_output=True,
            text=True,
            check=True,
        )
        return result.stdout.strip()
    except (subprocess.CalledProcessError, FileNotFoundError):
        return None


def _pairs_file_hashes(pairs_dir: Path) -> dict[str, str]:
    hashes: dict[str, str] = {}
    for path in sorted(pairs_dir.glob("*.json")):
        digest = hashlib.sha256(path.read_bytes()).hexdigest()
        hashes[path.name] = digest
    return hashes


def _pairs_aggregate_hash(file_hashes: dict[str, str]) -> str:
    payload = json.dumps(file_hashes, sort_keys=True).encode("utf-8")
    return hashlib.sha256(payload).hexdigest()


def build_manifest(
    config: dict[str, Any],
    *,
    repo_root: Path | None = None,
    pairs_dir: Path | None = None,
) -> dict[str, Any]:
    if repo_root is None:
        repo_root = Path(__file__).resolve().parents[1]
    if pairs_dir is None:
        pairs_dir = DEFAULT_PAIRS_DIR

    file_hashes = _pairs_file_hashes(pairs_dir)
    return {
        "timestamp": datetime.now(UTC).isoformat(),
        "git_sha": _try_git_sha(repo_root),
        "pairs_files": file_hashes,
        "pairs_hash": _pairs_aggregate_hash(file_hashes),
        "config": config,
    }
