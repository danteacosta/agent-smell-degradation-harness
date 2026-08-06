from __future__ import annotations

import pytest

from eval.sample_gate import validate_confirmatory_design
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
        validate_confirmatory_design(episodes, apply_split_manifest(episodes, manifest))


def test_confirmatory_design_accepts_frozen_minimum():
    episodes = _episodes()
    manifest = build_grouped_split_manifest(episodes)
    result = validate_confirmatory_design(episodes, apply_split_manifest(episodes, manifest))
    assert result["status"] == "confirmatory"
    assert result["counts"]["project_count"] == 6
    assert min(result["counts"]["split_intents"].values()) >= 8
