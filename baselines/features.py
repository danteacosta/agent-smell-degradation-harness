from __future__ import annotations

from pathlib import Path
from typing import Any

from feature_plane import FeatureEpisodeInput, extract_pre_final_features


def _extract_output_only(episode: dict[str, Any]) -> dict[str, int]:
    """Return retrospective outcome data, never deployable detector inputs."""
    return {"oracle_passed": int(bool(episode.get("oracle_passed")))}


def extract_features(episode: dict[str, Any], provenance_path: str | Path) -> dict[str, dict]:
    """Extract deployable pre-final features plus a separate offline outcome family."""
    pre_final_features = extract_pre_final_features(
        FeatureEpisodeInput.from_episode(episode), provenance_path
    )
    return {**pre_final_features, "output_only": _extract_output_only(episode)}
