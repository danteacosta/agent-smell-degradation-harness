from __future__ import annotations

from pathlib import Path
from typing import Any, Mapping

from feature_plane import FeatureEpisodeInput, extract_pre_final_features


def extract_tier_a_features(
    episode: Mapping[str, Any], provenance_path: str | Path
) -> dict[str, dict[str, float | int]]:
    feature_input = FeatureEpisodeInput.from_episode(episode)
    return extract_pre_final_features(feature_input, provenance_path)
