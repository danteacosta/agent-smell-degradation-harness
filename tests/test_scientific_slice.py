from __future__ import annotations

import pytest

from feature_plane import (
    DeployableFeatureInput,
    extract_deployable_features,
    static_import_guard,
)
from feature_plane.upper_bound import reject_upper_bound_features
from label_plane.datasets import validate_design_metadata


def _episode(intent: str, variant: str, replication: int, text: str, project: str | None = None) -> dict[str, object]:
    return {
        "intent_id": intent,
        "source_intent_id": intent,
        "project_id": project or "project-a",
        "variant": variant,
        "replication_id": replication,
        "defect_family": "ambiguity",
        "requirement_text": text,
        "source": f"sources/{intent}.json",
    }


def test_design_validator_rejects_silent_source_intent_duplicates() -> None:
    records = [
        _episode("i1", variant, replication, "The account expires after thirty days.")
        for variant in ("clean", "smelly")
        for replication in range(5)
    ]
    with pytest.raises(ValueError, match="12 distinct source intents"):
        validate_design_metadata({"records": records})


def test_design_validator_rejects_near_clone_source_text() -> None:
    records = []
    for index in range(12):
        text = "Refund the order after fifteen minutes."
        if index == 1:
            text = "Refund order after fifteen minutes."
        for variant in ("clean", "smelly"):
            for replication in range(5):
                records.append(_episode(f"i{index}", variant, replication, text, project=f"project-{index % 3}"))
    with pytest.raises(ValueError, match="near-clone"):
        validate_design_metadata({"records": records})


def test_design_validator_enforces_the_full_12_by_2_by_5_design() -> None:
    records = [
        _episode(
            f"i{index}",
            variant,
            replication,
            f"{['Approve invoices in the billing queue', 'Rotate service credentials weekly', 'Archive inactive sessions securely', 'Reconcile warehouse counts nightly', 'Send renewal notices before expiry', 'Validate shipment addresses at checkout', 'Record support escalation reasons', 'Purge expired access tokens', 'Schedule maintenance windows', 'Index customer receipts', 'Quarantine malformed uploads', 'Export audit summaries'][index]}.",
            project=f"project-{index % 3}",
        )
        for index in range(12)
        for variant in ("clean", "smelly")
        for replication in range(5)
    ]
    result = validate_design_metadata({"records": records})
    assert result["intent_count"] == 12
    assert result["episode_count"] == 120


def test_static_guard_and_upper_bound_rejection_are_fail_closed() -> None:
    assert static_import_guard() is True
    with pytest.raises(ValueError, match="upper-bound"):
        reject_upper_bound_features({"smell_type_code": 12, "source": "metadata-upper-bound"})


def test_deployable_input_has_only_allowlisted_fields() -> None:
    feature_input = DeployableFeatureInput.from_episode(
        {
            "intent_id": "i1",
            "task_family": "acceptance_criteria",
            "requirement_text": "Refund after fifteen minutes.",
            "variant": "smelly",
            "oracle_passed": False,
            "nested": {"artifact": {"secret": True}},
        }
    )
    assert feature_input.intent_id == "i1"
    assert not hasattr(feature_input, "variant")
    assert not hasattr(feature_input, "oracle_passed")
