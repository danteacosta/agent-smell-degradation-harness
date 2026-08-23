from __future__ import annotations

import json
from pathlib import Path

import pytest

from eval.feature_manifest import build_feature_manifest
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
    for row in episodes:
        path = root / f"{row['episode_id']}.jsonl"
        degraded = int(row["variant"] == "smelly")
        events = [
            {
                "event_id": f"event-{row['episode_id']}-t1",
                "checkpoint": "interpretation.completed",
                "event_type": "interpretation.completed",
                "sequence_number": 1,
                "attributes": {
                    "constraints": ["x"],
                    "unresolved_references": ["x"] if degraded else [],
                },
            },
            {
                "event_id": f"event-{row['episode_id']}-t2",
                "checkpoint": "plan.completed",
                "event_type": "plan.completed",
                "sequence_number": 2,
                "attributes": {"validation_checks": [] if degraded else ["check x"]},
            },
            {
                "event_id": f"event-{row['episode_id']}-t3",
                "checkpoint": "tool.completed",
                "event_type": "tool.completed",
                "sequence_number": 3,
                "attributes": {"errors": ["lost x"] if degraded else []},
            },
        ]
        path.write_text("".join(json.dumps(event) + "\n" for event in events), encoding="utf-8")
        row["provenance_path"] = str(path)
    return build_feature_manifest(episodes)


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


def test_confirmatory_h2_rejects_non_finite_raw_feature(tmp_path: Path):
    episodes = _episodes()
    for row in episodes:
        row.pop("h2_scores", None)
    feature_manifest = _feature_manifest(episodes, tmp_path)
    feature_manifest["rows"][0]["features"]["provenance_semantic"]["constraint_count"] = float("nan")  # type: ignore[index]
    with pytest.raises(ValueError, match="finite"):
        evaluate_confirmatory(
            episodes,
            confirmatory=True,
            primary_labels=_labels(episodes),
            feature_manifest=feature_manifest,
            enforce_design=False,
        )


def test_confirmatory_h2_fits_bound_raw_features_and_never_uses_oracle_label(tmp_path: Path):
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
    assert report["features"]["schema_version"] == "h2-features/v3"
    assert report["features"]["representation"] == "trace-bound-raw-numeric"
    assert all(model["fit_split"] == "train" for model in report["fitted_models"].values())
    assert set(report["checkpoint_boundary"]) == {"T1", "T2", "T3"}
    assert all(
        boundary["held_out_split"] == "test"
        for boundary in report["checkpoint_boundary"].values()
    )


def test_confirmatory_h2_rejects_precomputed_scores_in_v3(tmp_path: Path):
    episodes = _episodes()
    for row in episodes:
        row.pop("h2_scores", None)
    feature_manifest = _feature_manifest(episodes, tmp_path)
    feature_manifest["rows"][0]["scores"] = {  # type: ignore[index]
        "static_smell": 0.1,
        "operational": 0.2,
        "provenance_semantic": 0.3,
    }
    with pytest.raises(ValueError, match="precomputed scores"):
        evaluate_confirmatory(
            episodes,
            confirmatory=True,
            primary_labels=_labels(episodes),
            feature_manifest=feature_manifest,
            enforce_design=False,
        )


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
    assert effect["baseline_model"] == "B0"
    assert effect["provenance_model"] == "B3"
    assert effect["delta_pr_auc"] == pytest.approx(
        effect["provenance_pr_auc"] - effect["baseline_pr_auc"]
    )
    assert effect["margin"] == pytest.approx(0.05)
    assert effect["bootstrap"]["clusters"] == 3
    assert effect["claim"] in {"supported", "not_supported", "descriptive_only"}
    assert set(report["test_pr_auc_by_model"]) == {"B0", "B1", "B2", "B3"}
    assert report["model_selection"]["in_sample_selection"] is False
    assert 0.0 <= report["test_label_prevalence"] <= 1.0
    assert report["claim_decision"] == effect["claim"]
