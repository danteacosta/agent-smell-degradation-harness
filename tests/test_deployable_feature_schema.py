from __future__ import annotations

import json
from pathlib import Path

from feature_plane import DeployableFeatureInput, extract_deployable_features


def _trace(path: Path, *, unresolved: list[str], revisions: int) -> Path:
    events = [
        {
            "event_type": "interpretation.completed",
            "checkpoint": "interpretation.completed",
            "attributes": {
                "constraints": ["delay_minutes > 5"],
                "quantities": [{"value": 5, "unit": "minutes"}],
                "unresolved_references": unresolved,
                "assumptions": [],
                "contradictions": [],
            },
        },
        {
            "event_type": "plan.completed",
            "checkpoint": "plan.completed",
            "attributes": {
                "validation_checks": ["boundary"],
                "planned_tools": ["validator"],
                "coverage_targets": ["threshold"],
            },
        },
        {
            "event_type": "tool.completed",
            "checkpoint": "tool.completed",
            "attributes": {
                "revisions": revisions,
                "validation_attempts": 1,
                "errors": [],
                "retrieval_events": 0,
            },
        },
    ]
    path.write_text("\n".join(json.dumps(event) for event in events) + "\n", encoding="utf-8")
    return path


def test_pre_final_provenance_features_capture_checkpoint_variation(tmp_path: Path):
    feature_input = DeployableFeatureInput(
        intent_id="I-1",
        task_family="acceptance_criteria",
        requirement_text="Reject requests after 5 minutes.",
    )
    clean = extract_deployable_features(feature_input, _trace(tmp_path / "clean.jsonl", unresolved=[], revisions=0))
    uncertain = extract_deployable_features(
        feature_input,
        _trace(tmp_path / "uncertain.jsonl", unresolved=["old"], revisions=2),
    )

    assert clean["provenance"]["constraint_count"] == 1
    assert clean["provenance"]["quantity_count"] == 1
    assert uncertain["provenance"]["unresolved_reference_count"] == 1
    assert uncertain["provenance"]["revision_count"] == 2
    assert clean["provenance"] != uncertain["provenance"]


def test_pre_final_feature_extractor_ignores_legacy_payload_metadata(tmp_path: Path):
    path = tmp_path / "trace.jsonl"
    path.write_text(
        json.dumps(
            {
                "event_type": "interpretation.completed",
                "attributes": {"constraints": ["x"]},
                "payload": {"variant": "smelly", "oracle_passed": False},
            }
        )
        + "\n",
        encoding="utf-8",
    )
    features = extract_deployable_features(
        DeployableFeatureInput("I-1", "acceptance_criteria", "x"), path
    )
    assert "smelly" not in str(features)
    assert "oracle" not in str(features)
