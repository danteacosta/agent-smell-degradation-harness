from __future__ import annotations

import json
from pathlib import Path

import pytest

from eval.feature_manifest import trace_sha256
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
                    "task_family": "acceptance_criteria",
                    "requirement_text": "Reject requests after 5 minutes.",
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


def _feature_manifest(episodes: list[dict[str, object]], root: Path) -> dict[str, object]:
    rows = []
    for row in episodes:
        path = root / f"{row['episode_id']}.jsonl"
        path.write_text(
            json.dumps(
                {
                    "event_id": f"event-{row['episode_id']}",
                    "checkpoint": "interpretation.completed",
                    "event_type": "interpretation.completed",
                    "sequence_number": 1,
                    "attributes": {"constraints": ["x"]},
                }
            )
            + "\n",
            encoding="utf-8",
        )
        row["provenance_path"] = str(path)
        rows.append(
            {
                "episode_id": row["episode_id"],
                "trace_sha256": trace_sha256(path),
                "feature_version": "pre-final/v2",
                "checkpoint_event_ids": [f"event-{row['episode_id']}"],
                "cutoff_sequence": 1,
                "scores": {
                    "static_smell": 0.1,
                    "operational": 0.2,
                    "provenance_semantic": 0.3,
                },
            }
        )
    return {
        "schema_version": "h2-features/v2",
        "feature_version": "pre-final/v2",
        "source_plane": "pre_final",
        "analysis_version": "h2-confirmatory-v1",
        "rows": rows,
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


def test_confirmatory_h2_rejects_embedded_scores_even_with_manifest(tmp_path: Path):
    episodes = _episodes()
    feature_manifest = _feature_manifest(episodes, tmp_path)
    with pytest.raises(ValueError, match="embedded feature scores"):
        evaluate_confirmatory(
            episodes,
            confirmatory=True,
            primary_labels=_labels(episodes),
            feature_manifest=feature_manifest,
            enforce_design=False,
        )


@pytest.mark.parametrize(
    ("field", "value", "message"),
    [
        ("trace_sha256", "", "SHA-256"),
        ("checkpoint_event_ids", [], "checkpoint_event_ids"),
        ("cutoff_sequence", -1, "cutoff_sequence"),
    ],
)
def test_confirmatory_h2_rejects_incomplete_trace_binding(
    tmp_path: Path,
    field: str,
    value: object,
    message: str,
):
    episodes = _episodes()
    for row in episodes:
        row.pop("h2_scores", None)
    feature_manifest = _feature_manifest(episodes, tmp_path)
    feature_manifest["rows"][0][field] = value  # type: ignore[index]
    with pytest.raises(ValueError, match=message):
        evaluate_confirmatory(
            episodes,
            confirmatory=True,
            primary_labels=_labels(episodes),
            feature_manifest=feature_manifest,
            enforce_design=False,
        )


def test_confirmatory_h2_rejects_non_finite_score(tmp_path: Path):
    episodes = _episodes()
    for row in episodes:
        row.pop("h2_scores", None)
    feature_manifest = _feature_manifest(episodes, tmp_path)
    feature_manifest["rows"][0]["scores"]["provenance_semantic"] = float("nan")  # type: ignore[index]
    with pytest.raises(ValueError, match="finite"):
        evaluate_confirmatory(
            episodes,
            confirmatory=True,
            primary_labels=_labels(episodes),
            feature_manifest=feature_manifest,
            enforce_design=False,
        )


def test_confirmatory_h2_accepts_bound_scores_and_never_uses_oracle_label(tmp_path: Path):
    episodes = _episodes()
    for row in episodes:
        row.pop("h2_scores", None)
    feature_manifest = _feature_manifest(episodes, tmp_path)
    report = evaluate_confirmatory(
        episodes,
        confirmatory=True,
        primary_labels=_labels(episodes),
        feature_manifest=feature_manifest,
        enforce_design=False,
    )
    assert report["labels"]["source"] == "primary_human_adjudicated"
    assert report["features"]["schema_version"] == "h2-features/v2"


def test_confirmatory_h2_reports_delta_ci_and_claim_decision(tmp_path: Path):
    episodes = _episodes()
    for row in episodes:
        row.pop("h2_scores", None)
    feature_manifest = _feature_manifest(episodes, tmp_path)
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
    assert set(report["test_pr_auc_by_family"]) == {
        "static_smell",
        "operational",
        "provenance_semantic",
    }
    assert 0.0 <= report["test_label_prevalence"] <= 1.0
    assert report["claim_decision"] == effect["claim"]
