from __future__ import annotations

import pytest

from eval.h2_detection import evaluate_confirmatory


def _episodes() -> list[dict[str, object]]:
    rows: list[dict[str, object]] = []
    for index in range(9):
        for variant in ("clean", "smelly"):
            rows.append(
                {
                    "episode_id": f"E-{index}-{variant}",
                    "intent_id": f"I-{index}",
                    "source_intent_id": f"I-{index}",
                    "project_id": f"P-{index % 3}",
                    "variant": variant,
                    "oracle_passed": True,
                    "h2_scores": {
                        "static_smell": float(index % 2),
                        "operational": float(index) / 10,
                        "provenance_semantic": float(index) / 10 + (0.4 if variant == "smelly" else 0),
                    },
                }
            )
    return rows


def _labels(episodes: list[dict[str, object]]) -> dict[str, int]:
    return {
        str(row["episode_id"]): int(row["variant"] == "smelly")
        for row in episodes
    }


def test_confirmatory_h2_requires_primary_human_labels():
    with pytest.raises(ValueError, match="primary human labels"):
        evaluate_confirmatory(_episodes(), confirmatory=True, enforce_design=False)


def test_confirmatory_h2_rejects_unbound_score_injection():
    episodes = _episodes()
    with pytest.raises(ValueError, match="feature manifest"):
        evaluate_confirmatory(
            episodes,
            confirmatory=True,
            primary_labels=_labels(episodes),
            enforce_design=False,
        )


def test_confirmatory_h2_accepts_bound_scores_and_never_uses_oracle_label():
    episodes = _episodes()
    feature_manifest = {
        "schema_version": "h2-features/v1",
        "rows": [
            {"episode_id": row["episode_id"], "trace_sha256": f"hash-{row['episode_id']}", "scores": row["h2_scores"]}
            for row in episodes
        ],
    }
    report = evaluate_confirmatory(
        episodes,
        confirmatory=True,
        primary_labels=_labels(episodes),
        feature_manifest=feature_manifest,
        enforce_design=False,
    )
    assert report["labels"]["source"] == "primary_human_adjudicated"
    assert report["features"]["schema_version"] == "h2-features/v1"


def test_confirmatory_h2_reports_delta_ci_and_claim_decision():
    episodes = _episodes()
    feature_manifest = {
        "schema_version": "h2-features/v1",
        "rows": [
            {"episode_id": row["episode_id"], "trace_sha256": f"hash-{row['episode_id']}", "scores": row["h2_scores"]}
            for row in episodes
        ],
    }
    report = evaluate_confirmatory(
        episodes,
        confirmatory=True,
        primary_labels=_labels(episodes),
        feature_manifest=feature_manifest,
        enforce_design=False,
    )
    effect = report["primary_effect"]
    assert effect["baseline_family"] in {"static_smell", "operational"}
    assert effect["delta_pr_auc"] == pytest.approx(
        effect["provenance_pr_auc"] - effect["baseline_pr_auc"]
    )
    assert effect["margin"] == pytest.approx(0.05)
    assert effect["bootstrap"]["clusters"] == 3
    assert effect["claim"] in {"supported", "not_supported", "descriptive_only"}
