"""Frozen feature-score manifests for confirmatory H2 runs."""

from __future__ import annotations

import hashlib
import json
from collections.abc import Mapping, Sequence
from pathlib import Path
from typing import Any

FAMILIES = ("static_smell", "operational", "provenance_semantic")


def trace_sha256(path: str | Path) -> str:
    digest = hashlib.sha256()
    with Path(path).open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def validate_feature_manifest(
    manifest: Mapping[str, Any], episodes: Sequence[Mapping[str, Any]]
) -> dict[str, Any]:
    if manifest.get("schema_version") != "h2-features/v1":
        raise ValueError("feature manifest schema_version must be h2-features/v1")
    rows = manifest.get("rows")
    if not isinstance(rows, list):
        raise ValueError("feature manifest rows are required")
    by_id: dict[str, Mapping[str, Any]] = {}
    for row in rows:
        if not isinstance(row, Mapping) or not str(row.get("episode_id", "")).strip():
            raise ValueError("feature manifest rows require episode_id")
        episode_id = str(row["episode_id"])
        if episode_id in by_id:
            raise ValueError(f"duplicate feature manifest row {episode_id}")
        scores = row.get("scores")
        if not isinstance(scores, Mapping) or set(FAMILIES) - set(scores):
            raise ValueError(f"feature manifest row {episode_id} has incomplete scores")
        by_id[episode_id] = row
    expected_ids = {str(episode.get("episode_id", "")) for episode in episodes}
    if expected_ids - set(by_id):
        raise ValueError("feature manifest is missing episode rows")
    for episode in episodes:
        episode_id = str(episode["episode_id"])
        expected_hash = by_id[episode_id].get("trace_sha256")
        path = episode.get("provenance_path")
        if path and expected_hash and Path(str(path)).is_file():
            if trace_sha256(str(path)) != str(expected_hash):
                raise ValueError(f"feature manifest trace hash mismatch for {episode_id}")
    return dict(manifest)


__all__ = ("FAMILIES", "trace_sha256", "validate_feature_manifest")
