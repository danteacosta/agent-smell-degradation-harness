from __future__ import annotations

import copy
import hashlib

import pytest

from replay.schema import (
    ARP_PACKAGE_VERSION,
    ARP_WIRE_VERSION,
    CHECKPOINT_SCHEMA_VERSION,
    REPLAY_VERSION,
    ContractError,
    canonical_json_bytes,
    sha256_bytes,
    validate_bundle_mapping,
)


def _event(name: str, sequence: int, parent: str | None, attributes: dict) -> dict:
    return {
        "event_id": f"event-{sequence}",
        "schema_version": ARP_WIRE_VERSION,
        "experiment_id": "demo-project",
        "run_id": "demo-run",
        "episode_id": "demo-episode",
        "replication_id": 0,
        "sequence_number": sequence,
        "checkpoint": name,
        "event_type": name,
        "started_at": f"2026-08-10T00:00:0{sequence}+00:00",
        "ended_at": f"2026-08-10T00:00:0{sequence + 1}+00:00",
        "attributes": attributes,
        "content_reference": None,
        "parent_event_id": parent,
    }


def valid_bundle() -> dict:
    interpretation = {
        "constraints": ["must preserve 99% of records"],
        "quantities": [{"value": 99, "unit": "%"}],
        "unresolved_references": [],
        "assumptions": [],
        "contradictions": [],
    }
    plan = {
        "validation_checks": ["assert preservation"],
        "planned_tools": ["pytest"],
        "coverage_targets": ["requirement constraints"],
    }
    execution = {
        "revisions": 0,
        "validation_attempts": 1,
        "errors": [],
        "retrieval_events": 0,
    }
    events = [
        _event("interpretation.completed", 1, None, interpretation),
        _event("plan.completed", 2, "event-1", plan),
        _event("tool.completed", 3, "event-2", execution),
    ]
    return {
        "manifest": {
            "replay_version": REPLAY_VERSION,
            "checkpoint_schema_version": CHECKPOINT_SCHEMA_VERSION,
            "arp_wire_version": ARP_WIRE_VERSION,
            "arp_package_version": ARP_PACKAGE_VERSION,
            "case_id": "clean",
        },
        "requirement": {"text": "The service must preserve 99% of records.", "task_family": "acceptance"},
        "events": events,
    }


def test_valid_bundle_and_canonical_hash_are_stable() -> None:
    bundle = valid_bundle()
    validated = validate_bundle_mapping(bundle)
    assert validated["manifest"]["arp_wire_version"] == "2.0.5"
    first = sha256_bytes(canonical_json_bytes(bundle))
    second = sha256_bytes(canonical_json_bytes(copy.deepcopy(bundle)))
    assert first == second
    assert hashlib.sha256(canonical_json_bytes(bundle)).hexdigest() == first
    assert not canonical_json_bytes(bundle).endswith(b"\n")


@pytest.mark.parametrize(
    "mutation",
    [
        lambda b: b["events"].__setitem__(0, {**b["events"][0], "schema_version": "pre-final/v1"}),
        lambda b: b["events"].__setitem__(1, {**b["events"][1], "sequence_number": 1}),
        lambda b: b["events"].__setitem__(2, {**b["events"][2], "started_at": "2025-01-01T00:00:00+00:00"}),
        lambda b: b["events"].__setitem__(1, {**b["events"][1], "parent_event_id": None}),
        lambda b: b["events"].__setitem__(0, {**b["events"][0], "attributes": {"oracle_passed": True}}),
        lambda b: b["manifest"].__setitem__("arp_wire_version", "1.0.0"),
        lambda b: b["manifest"].__setitem__("replay_version", "constraint-replay/v0"),
    ],
)
def test_contract_mutations_fail_closed_as_typed_validation_errors(mutation) -> None:
    bundle = valid_bundle()
    mutation(bundle)
    with pytest.raises(ContractError):
        validate_bundle_mapping(bundle)


def test_unknown_manifest_and_requirement_fields_fail_closed() -> None:
    bundle = valid_bundle()
    bundle["manifest"]["audit_only"] = {"source": "test"}
    with pytest.raises(ContractError):
        validate_bundle_mapping(bundle)
    bundle = valid_bundle()
    bundle["requirement"]["mutation"] = "hidden"
    with pytest.raises(ContractError):
        validate_bundle_mapping(bundle)
