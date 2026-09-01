"""Frozen trace-bound raw-feature manifests for confirmatory H2 runs."""

from __future__ import annotations

import hashlib
import json
import math
import re
from collections.abc import Mapping, Sequence
from pathlib import Path
from typing import Any

from feature_plane import DeployableFeatureInput, extract_deployable_features

FAMILIES = ("static_smell", "operational", "provenance_semantic")
_SHA256_RE = re.compile(r"^[0-9a-f]{64}$")
_CHECKPOINT_EVENT_TYPES = {
    "T1": "interpretation.completed",
    "T2": "plan.completed",
    "T3": "tool.completed",
}


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


def _event_type(event: Mapping[str, Any]) -> str:
    return str(event.get("checkpoint", event.get("event_type", event.get("name", ""))))


def _feature_families(
    episode: Mapping[str, Any],
    *,
    cutoff: str,
) -> dict[str, dict[str, float | int]]:
    extracted = extract_deployable_features(
        DeployableFeatureInput.from_episode(episode),
        str(episode.get("provenance_path", "")),
        cutoff=cutoff,
    )
    return {
        "static_smell": extracted["static"],
        "operational": extracted["operational"],
        "provenance_semantic": extracted["provenance"],
    }


def build_feature_manifest(
    episodes: Sequence[Mapping[str, Any]],
    *,
    feature_version: str = "pre-final/v4",
    analysis_version: str = "h2-confirmatory-v3",
) -> dict[str, Any]:
    """Derive an auditable H2 v3 manifest from frozen native traces."""

    rows: list[dict[str, Any]] = []
    for episode in episodes:
        episode_id = str(episode.get("episode_id", ""))
        path = Path(str(episode.get("provenance_path", "")))
        if not episode_id or not path.is_file():
            raise ValueError("feature manifest generation requires episode_id and existing trace")
        events = _trace_events(path)
        checkpoint_ids: dict[str, str] = {}
        checkpoint_cutoffs: dict[str, int] = {}
        for checkpoint, expected_type in _CHECKPOINT_EVENT_TYPES.items():
            event = next((item for item in events if _event_type(item) == expected_type), None)
            if event is None:
                raise ValueError(f"trace {episode_id} is missing {checkpoint}/{expected_type}")
            event_id = str(event.get("event_id", event.get("id", "")))
            sequence = event.get("sequence_number", event.get("sequence"))
            if not event_id or not isinstance(sequence, int):
                raise ValueError(f"trace {episode_id} has incomplete {checkpoint} identity")
            checkpoint_ids[checkpoint] = event_id
            checkpoint_cutoffs[checkpoint] = sequence
        checkpoint_features = {
            checkpoint: {
                "provenance_semantic": _feature_families(episode, cutoff=checkpoint)[
                    "provenance_semantic"
                ]
            }
            for checkpoint in ("T1", "T2", "T3")
        }
        rows.append(
            {
                "episode_id": episode_id,
                "trace_sha256": trace_sha256(path),
                "feature_version": feature_version,
                "checkpoint_event_ids": checkpoint_ids,
                "checkpoint_cutoff_sequences": checkpoint_cutoffs,
                "cutoff_sequence": checkpoint_cutoffs["T3"],
                "features": _feature_families(episode, cutoff="T3"),
                "checkpoint_features": checkpoint_features,
            }
        )
    manifest = {
        "schema_version": "h2-features/v3",
        "feature_version": feature_version,
        "source_plane": "pre_final",
        "analysis_version": analysis_version,
        "rows": rows,
    }
    return validate_feature_manifest(manifest, episodes, strict=True)


def validate_feature_manifest(
    manifest: Mapping[str, Any],
    episodes: Sequence[Mapping[str, Any]],
    *,
    strict: bool = False,
) -> dict[str, Any]:
    expected_schema = "h2-features/v3" if strict else {
        "h2-features/v1",
        "h2-features/v2",
        "h2-features/v3",
    }
    if manifest.get("schema_version") not in (expected_schema if isinstance(expected_schema, set) else {expected_schema}):
        raise ValueError(
            "feature manifest schema_version must be "
            + ("h2-features/v3" if strict else "h2-features/v1, v2, or v3")
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
        if strict:
            if "scores" in row:
                raise ValueError(
                    f"confirmatory feature row {episode_id} cannot contain precomputed scores"
                )
            _validate_family_features(row.get("features"), episode_id)
            checkpoint_features = row.get("checkpoint_features")
            if not isinstance(checkpoint_features, Mapping) or set(("T1", "T2", "T3")) - set(checkpoint_features):
                raise ValueError(
                    f"confirmatory feature row {episode_id} requires T1/T2/T3 checkpoint_features"
                )
            for checkpoint in ("T1", "T2", "T3"):
                values = checkpoint_features[checkpoint]
                if not isinstance(values, Mapping):
                    raise ValueError(
                        f"confirmatory feature row {episode_id}/{checkpoint} must be an object"
                    )
                _validate_numeric_features(
                    values.get("provenance_semantic"),
                    f"{episode_id}/{checkpoint}/provenance_semantic",
                )
        else:
            scores = row.get("scores")
            features = row.get("features")
            if not isinstance(scores, Mapping) and not isinstance(features, Mapping):
                raise ValueError(f"feature manifest row {episode_id} requires scores or features")
            if isinstance(scores, Mapping) and set(FAMILIES) - set(scores):
                raise ValueError(f"feature manifest row {episode_id} has incomplete scores")
            if isinstance(features, Mapping):
                _validate_family_features(features, episode_id)
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
                not isinstance(checkpoint_ids, Mapping)
                or set(checkpoint_ids) != set(_CHECKPOINT_EVENT_TYPES)
                or not all(isinstance(value, str) and value.strip() for value in checkpoint_ids.values())
            ):
                raise ValueError(
                    f"confirmatory feature row {episode_id} requires T1/T2/T3 checkpoint_event_ids"
                )
            checkpoint_cutoffs = by_id[episode_id].get("checkpoint_cutoff_sequences")
            if (
                not isinstance(checkpoint_cutoffs, Mapping)
                or set(checkpoint_cutoffs) != set(_CHECKPOINT_EVENT_TYPES)
                or not all(isinstance(value, int) and value >= 0 for value in checkpoint_cutoffs.values())
            ):
                raise ValueError(
                    f"confirmatory feature row {episode_id} requires checkpoint_cutoff_sequences"
                )
            cutoff = by_id[episode_id].get("cutoff_sequence")
            if not isinstance(cutoff, int) or cutoff < 0:
                raise ValueError(f"confirmatory feature row {episode_id} requires cutoff_sequence")
            events = _trace_events(trace_path)
            event_ids = {
                str(event.get("event_id", event.get("id", ""))): event
                for event in events
            }
            for checkpoint, checkpoint_id in checkpoint_ids.items():
                event = event_ids.get(checkpoint_id)
                if event is None:
                    raise ValueError(
                        f"confirmatory feature row {episode_id} references a missing checkpoint event"
                    )
                sequence = event.get("sequence_number", event.get("sequence"))
                if _event_type(event) != _CHECKPOINT_EVENT_TYPES[checkpoint]:
                    raise ValueError(
                        f"confirmatory feature row {episode_id} binds {checkpoint} to the wrong event"
                    )
                if sequence != checkpoint_cutoffs[checkpoint] or sequence > cutoff:
                    raise ValueError(
                        f"confirmatory feature row {episode_id} has checkpoint after cutoff"
                    )
            if cutoff != checkpoint_cutoffs["T3"]:
                raise ValueError(f"confirmatory feature row {episode_id} has inconsistent T3 cutoff")
            expected_features = _feature_families(episode, cutoff="T3")
            if by_id[episode_id].get("features") != expected_features:
                raise ValueError(f"confirmatory feature row {episode_id} does not match its trace")
            checkpoint_features = by_id[episode_id]["checkpoint_features"]
            for checkpoint in ("T1", "T2", "T3"):
                expected_checkpoint = _feature_families(episode, cutoff=checkpoint)[
                    "provenance_semantic"
                ]
                if checkpoint_features[checkpoint]["provenance_semantic"] != expected_checkpoint:
                    raise ValueError(
                        f"confirmatory feature row {episode_id}/{checkpoint} does not match its trace"
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


def _validate_numeric_features(value: Any, location: str) -> None:
    if not isinstance(value, Mapping) or not value:
        raise ValueError(f"feature manifest features {location} must be a non-empty object")
    for name, feature in value.items():
        if not isinstance(name, str) or not name.strip():
            raise ValueError(f"feature manifest features {location} require named fields")
        if isinstance(feature, bool) or not isinstance(feature, (int, float)) or not math.isfinite(float(feature)):
            raise ValueError(f"feature manifest feature {location}/{name} must be finite numeric")


def _validate_family_features(value: Any, episode_id: str) -> None:
    if not isinstance(value, Mapping) or set(FAMILIES) - set(value):
        raise ValueError(f"feature manifest row {episode_id} has incomplete raw features")
    for family in FAMILIES:
        _validate_numeric_features(value[family], f"{episode_id}/{family}")


__all__ = (
    "FAMILIES",
    "build_feature_manifest",
    "feature_manifest_sha256",
    "trace_sha256",
    "validate_feature_manifest",
)
