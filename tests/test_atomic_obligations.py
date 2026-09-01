from __future__ import annotations

import hashlib

import pytest

from protocol.atomic_obligations import (
    ATOMIC_OBLIGATION_SCHEMA_VERSION,
    materialize_atomic_obligation_observations,
    summarize_atomic_obligations,
    validate_atomic_obligation_observations,
    validate_atomic_obligations,
)


def _lineage() -> list[dict[str, str | list[str]]]:
    digest = hashlib.sha256(b"reject after five minutes").hexdigest()
    return [
        {
            "constraint_id": "c001-example",
            "constraint_sha256": digest,
            "planned_check_ids": ["check-001"],
            "observation_id": "semantic-plan-contract-validator/v3",
            "status": "covered",
            "available_at": "T3",
        }
    ]


def test_atomic_obligations_are_bounded_and_hash_bound_at_t3() -> None:
    constraints = ["reject after five minutes"]
    provider_atoms = [
        {"constraint_index": 1, "atom_type": "condition", "status": "present"},
        {"constraint_index": 1, "atom_type": "threshold", "status": "present"},
    ]

    observations = materialize_atomic_obligation_observations(
        constraints,
        provider_atoms,
        _lineage(),
    )

    assert len(observations) == 2
    assert all(
        item["schema_version"] == ATOMIC_OBLIGATION_SCHEMA_VERSION
        and item["available_at"] == "T3"
        and item["source_checkpoint"] == "T1"
        and item["preservation_class"] == "constraint_hard_lane"
        for item in observations
    )
    assert all("reject after five minutes" not in str(item) for item in observations)
    assert summarize_atomic_obligations(observations)["present_count"] == 2


@pytest.mark.parametrize(
    "bad",
    [
        [{"constraint_index": 1, "atom_type": "condition", "status": "present", "text": "secret"}],
        [{"constraint_index": 2, "atom_type": "condition", "status": "present"}],
        [{"constraint_index": 1, "atom_type": "unknown", "status": "present"}],
        [{"constraint_index": 1, "atom_type": "condition", "status": "present"},
         {"constraint_index": 1, "atom_type": "condition", "status": "uncertain"}],
    ],
)
def test_atomic_obligation_provider_contract_fails_closed(bad) -> None:
    with pytest.raises(ValueError):
        validate_atomic_obligations(bad, ["one constraint"])


def test_atomic_obligation_observation_rejects_terminal_like_shape() -> None:
    observation = materialize_atomic_obligation_observations(
        ["one constraint"],
        [{"constraint_index": 1, "atom_type": "action", "status": "uncertain"}],
        _lineage_for("one constraint"),
    )[0]
    observation["oracle"] = False
    with pytest.raises(ValueError, match="invalid field set"):
        validate_atomic_obligation_observations([observation])


def _lineage_for(text: str) -> list[dict[str, str | list[str]]]:
    digest = hashlib.sha256(text.encode("utf-8")).hexdigest()
    return [
        {
            "constraint_id": "c001-example",
            "constraint_sha256": digest,
            "planned_check_ids": [],
            "observation_id": "semantic-plan-contract-validator/v3",
            "status": "uncovered",
            "available_at": "T3",
        }
    ]
