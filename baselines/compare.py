from __future__ import annotations

from typing import Any

from baselines.features import extract_features
from baselines.score import mann_whitney_auroc
from feature_plane import semantic_risk

FAMILIES = ("static_smell", "output_only", "operational", "provenance_semantic")


def _episode_label(episode: dict[str, Any]) -> int:
    return 1 if episode.get("variant") == "smelly" and not episode.get("oracle_passed") else 0


def _family_score(family: str, features: dict[str, Any]) -> float:
    family_features = features[family]
    if family == "static_smell":
        return float(family_features.get("requirement_length", 0)) / 1000.0
    if family == "output_only":
        return float(1 - family_features["oracle_passed"])
    if family == "operational":
        return float(family_features["event_count"]) + float(family_features["latency_ms"]) / 1000.0
    if family == "provenance_semantic":
        return semantic_risk(family_features)
    return 0.0


def compare_baselines(episodes: list[dict[str, Any]]) -> dict[str, dict[str, float]]:
    if not episodes:
        return {family: {"auroc": 0.5} for family in FAMILIES}

    labels = [_episode_label(episode) for episode in episodes]
    report: dict[str, dict[str, float]] = {}

    for family in FAMILIES:
        scores: list[float] = []
        for episode in episodes:
            provenance_path = episode.get("provenance_path", "")
            features = extract_features(episode, provenance_path)
            scores.append(_family_score(family, features))
        report[family] = {"auroc": mann_whitney_auroc(scores, labels)}

    return report
