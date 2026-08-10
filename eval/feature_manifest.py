"""Frozen feature-score manifests for confirmatory H2 runs."""

from __future__ import annotations

import hashlib
import json
import math
import re
from collections.abc import Mapping, Sequence
from pathlib import Path
from typing import Any

FAMILIES = ("static_smell", "operational", "provenance_semantic")
_SHA256_RE = re.compile(r"^[0-9a-f]{64}$")


def trace_sha256(path: str | Path) -> str:
    digest = hashlib.sha256()
    with Path(path).open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def feature_manifest_sha256(manifest: Mapping[str, Any]) -> str:
    canonical = {
        key: value for key, value in manifest.items() if key != "manifest_sha256"
    }
    encoded = json.dumps(canonical, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def _trace_events(path: Path) -> list[Mapping[str, Any]]:
    events: list[Mapping[str, Any]] = []
    for line in path.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        value = json.loads(line)
        if not isinstance(value, Mapping):
            raise ValueError("feature trace events must be objects")
        events.append(value)
    return events


def validate_feature_manifest(
    manifest: Mapping[str, Any],
    episodes: Sequence[Mapping[str, Any]],
    *,
    strict: bool = False,
) -> dict[str, Any]:
    expected_schema = "h2-features/v2" if strict else {"h2-features/v1", "h2-features/v2"}
    if manifest.get("schema_version") not in (expected_schema if isinstance(expected_schema, set) else {expected_schema}):
        raise ValueError(
            "feature manifest schema_version must be "
            + ("h2-features/v2" if strict else "h2-features/v1 or h2-features/v2")
        )
    if strict:
        if manifest.get("source_plane") != "pre_final":
            raise ValueError("confirmatory feature manifest must declare source_plane=pre_final")
        if not str(manifest.get("feature_version", "")).strip():
            raise ValueError("confirmatory feature manifest requires feature_version")
        if not str(manifest.get("analysis_version", "")).strip():
            raise ValueError("confirmatory feature manifest requires analysis_version")
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
    if strict and set(by_id) != expected_ids:
        raise ValueError("confirmatory feature manifest contains rows for unknown episodes")
    for episode in episodes:
        episode_id = str(episode["episode_id"])
        expected_hash = by_id[episode_id].get("trace_sha256")
        path = episode.get("provenance_path")
        if strict:
            if not isinstance(expected_hash, str) or not _SHA256_RE.fullmatch(expected_hash):
                raise ValueError(f"confirmatory feature row {episode_id} requires a SHA-256 trace hash")
            if not path or not Path(str(path)).is_file():
                raise ValueError(f"confirmatory feature row {episode_id} requires an existing trace")
            trace_path = Path(str(path))
            if trace_sha256(trace_path) != expected_hash:
                raise ValueError(f"feature manifest trace hash mismatch for {episode_id}")
            checkpoint_ids = by_id[episode_id].get("checkpoint_event_ids")
            if (
                not isinstance(checkpoint_ids, list)
                or not checkpoint_ids
                or not all(isinstance(value, str) and value.strip() for value in checkpoint_ids)
            ):
                raise ValueError(f"confirmatory feature row {episode_id} requires checkpoint_event_ids")
            cutoff = by_id[episode_id].get("cutoff_sequence")
            if not isinstance(cutoff, int) or cutoff < 0:
                raise ValueError(f"confirmatory feature row {episode_id} requires cutoff_sequence")
            events = _trace_events(trace_path)
            event_ids = {
                str(event.get("event_id", event.get("id", ""))): event
                for event in events
            }
            for checkpoint_id in checkpoint_ids:
                event = event_ids.get(checkpoint_id)
                if event is None:
                    raise ValueError(
                        f"confirmatory feature row {episode_id} references a missing checkpoint event"
                    )
                sequence = event.get("sequence_number", event.get("sequence"))
                if not isinstance(sequence, int) or sequence > cutoff:
                    raise ValueError(
                        f"confirmatory feature row {episode_id} has checkpoint after cutoff"
                    )
        scores = by_id[episode_id].get("scores")
        if isinstance(scores, Mapping):
            for family in FAMILIES:
                value = scores.get(family)
                if not isinstance(value, (int, float)) or not math.isfinite(float(value)):
                    raise ValueError(f"feature manifest score {episode_id}/{family} must be finite")
        if strict and by_id[episode_id].get("feature_version") != manifest.get("feature_version"):
            raise ValueError(f"feature manifest feature version mismatch for {episode_id}")
    result = dict(manifest)
    result["manifest_sha256"] = feature_manifest_sha256(manifest)
    return result


__all__ = ("FAMILIES", "feature_manifest_sha256", "trace_sha256", "validate_feature_manifest")
