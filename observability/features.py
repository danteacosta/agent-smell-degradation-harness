from __future__ import annotations

from pathlib import Path
from typing import Any, Mapping

from feature_plane import FeatureEpisodeInput, extract_pre_final_features


def extract_tier_a_features(
    episode: Mapping[str, Any], provenance_path: str | Path
) -> dict[str, dict[str, float | int]]:
    provenance_jsonl = Path(provenance_path).read_text(encoding="utf-8")
    feature_input = FeatureEpisodeInput.from_episode(episode, provenance_jsonl)
    return extract_pre_final_features(feature_input)
