from __future__ import annotations

import copy

import pytest

from replay.policy import DEFAULT_POLICY, GatePolicy, POLICY_SCHEMA_VERSION
from replay.runner import load_fixture, run_bundle

FIXTURES = __import__("pathlib").Path(__file__).parents[1] / "replay" / "fixtures"


def _document(**overrides):
    value = {
        "schema_version": POLICY_SCHEMA_VERSION,
        "version": "custom/v1",
        "block_when": ["unresolved_reference"],
        "warn_when": [],
    }
    value.update(overrides)
    return value


def test_policy_schema_and_hash_are_deterministic() -> None:
    first = GatePolicy.from_mapping(_document())
    second = GatePolicy.from_mapping({**_document(), "block_when": ["unresolved_reference"]})
    assert first.to_mapping()["schema_version"] == POLICY_SCHEMA_VERSION
    assert first.sha256 == second.sha256


@pytest.mark.parametrize(
    "document",
    [
        {**_document(), "unexpected": True},
        {**_document(), "block_when": ["unresolved_reference", "unresolved_reference"]},
        {**_document(), "block_when": ["no_such_rule"]},
        {**_document(), "warn_when": [1]},
    ],
)
def test_policy_rejects_malformed_documents(document) -> None:
    with pytest.raises(ValueError):
        GatePolicy.from_mapping(document)


def test_custom_policy_changes_decision_and_default_remains_immutable() -> None:
    fixture = load_fixture("constraint-warning", FIXTURES)
    original = run_bundle(fixture)
    custom = GatePolicy.from_mapping(_document())
    changed = run_bundle(copy.deepcopy(fixture), policy=custom)
    assert original["decision"] == "warn"
    assert changed["decision"] == "block"
    assert changed["policy_version"] == "custom/v1"
    assert changed["policy_hash"] != original["policy_hash"]
    assert DEFAULT_POLICY.version == "constraint-gate/v1"


def test_policy_facts_are_closed_and_typed() -> None:
    facts = {
        "constraint_count": 1,
        "validation_check_count": 1,
        "coverage_target_count": 1,
        "unresolved_reference_count": 0,
        "contradiction_count": 0,
        "error_count": 0,
    }
    assert DEFAULT_POLICY.evaluate(facts)[0] == "approve"
    with pytest.raises(ValueError):
        DEFAULT_POLICY.evaluate({**facts, "unexpected": 0})
    with pytest.raises(ValueError):
        DEFAULT_POLICY.evaluate({**facts, "error_count": True})
