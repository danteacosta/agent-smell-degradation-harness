from __future__ import annotations

import pytest

from eval.sample_gate import validate_confirmatory_design, validate_pilot_design
from eval.splits import apply_split_manifest, build_grouped_split_manifest


def _episodes(intent_count: int = 24) -> list[dict[str, str]]:
    return [
        {
            "source_intent_id": f"I-{index}",
            "intent_id": f"I-{index}",
            "project_id": f"P-{index // 4}",
            "variant": variant,
        }
        for index in range(intent_count)
        for variant in ("clean", "smelly")
    ]


def test_confirmatory_design_requires_project_and_intent_precision():
    episodes = _episodes(12)
    manifest = build_grouped_split_manifest(episodes)
    with pytest.raises(ValueError, match="at least 24 independent intents"):
        validate_pilot_design(episodes, apply_split_manifest(episodes, manifest))


def _precision_plan() -> dict[str, object]:
    return {
        "schema_version": "h2-precision-plan/v2",
        "status": "frozen",
        "design": {
            "intents": 120,
            "projects": 30,
            "minimum_test_projects": 6,
            "minimum_test_intents": 24,
        },
        "simulation": {
            "evaluation_scope": "test_partition_only",
            "cluster_key": "project_id",
            "median_ci_width": 0.18,
            "degenerate_rate": 0.01,
            "estimated_margin_power": 0.82,
        },
        "thresholds": {
            "max_median_ci_width": 0.20,
            "max_degenerate_rate": 0.05,
            "target_margin_power": 0.80,
        },
    }


def test_confirmatory_design_requires_frozen_precision_plan():
    episodes = _episodes(60)
    manifest = build_grouped_split_manifest(episodes, min_groups_per_split=2)
    with pytest.raises(ValueError, match="frozen H2 precision plan"):
        validate_confirmatory_design(episodes, apply_split_manifest(episodes, manifest))


def test_confirmatory_design_accepts_precision_governed_minimum():
    episodes = _episodes(120)
    manifest = build_grouped_split_manifest(episodes)
    result = validate_confirmatory_design(
        episodes,
        apply_split_manifest(episodes, manifest),
        precision_plan=_precision_plan(),
    )
    assert result["status"] == "confirmatory"
    assert result["counts"]["project_count"] == 30
    assert result["counts"]["split_projects"]["test"] >= 6
    assert result["counts"]["split_intents"]["test"] >= 24


def test_confirmatory_design_rejects_intent_clustered_precision_plan():
    episodes = _episodes(120)
    manifest = build_grouped_split_manifest(episodes)
    plan = _precision_plan()
    plan["simulation"]["cluster_key"] = "source_intent_id"  # type: ignore[index]
    with pytest.raises(ValueError, match="project_id clusters"):
        validate_confirmatory_design(
            episodes,
            apply_split_manifest(episodes, manifest),
            precision_plan=plan,
        )
