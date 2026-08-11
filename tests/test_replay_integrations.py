from __future__ import annotations

import copy

import pytest

from replay.integrations import build_replay_bundle, normalize_trace_export
from replay.runner import run_bundle


REQUIREMENT = {"text": "The service must preserve 99% of records.", "task_family": "acceptance-criteria"}
CONTEXT = {"experiment_id": "p", "run_id": "r", "episode_id": "e", "replication_id": 0}


def _export(source: str = "phoenix") -> dict:
    events = [
        {
            "name": "interpretation.completed", "event_id": "event-1",
            "started_at": "2026-08-10T00:00:01+00:00", "ended_at": "2026-08-10T00:00:02+00:00",
            "parent_event_id": None,
            "attributes": {"constraints": ["must preserve 99%"], "quantities": [{"value": 99, "unit": "%"}], "unresolved_references": [], "assumptions": [], "contradictions": []},
        },
        {
            "name": "plan.completed", "event_id": "event-2",
            "started_at": "2026-08-10T00:00:02+00:00", "ended_at": "2026-08-10T00:00:03+00:00",
            "parent_event_id": "event-1",
            "attributes": {"validation_checks": ["assert"], "planned_tools": ["pytest"], "coverage_targets": ["constraints"]},
        },
        {
            "name": "tool.completed", "event_id": "event-3",
            "started_at": "2026-08-10T00:00:03+00:00", "ended_at": "2026-08-10T00:00:04+00:00",
            "parent_event_id": "event-2",
            "attributes": {"revisions": 0, "validation_attempts": 1, "errors": [], "retrieval_events": 0},
        },
    ]
    key = "observations" if source == "langfuse" else "spans"
    return {key: events}


@pytest.mark.parametrize("source", ["phoenix", "langfuse", "braintrust"])
def test_complete_vendor_export_builds_and_replays(source: str) -> None:
    bundle = build_replay_bundle(source, _export(source), requirement=REQUIREMENT, case_id="adapter", context=CONTEXT)
    assert bundle["manifest"]["status"] == "non_confirmatory_adapter_demo"
    assert bundle["manifest"]["trace_sha256"]
    assert bundle["_trace_raw"].endswith(b"\n")
    assert run_bundle(bundle)["decision"] == "approve"
    assert "provider" not in bundle["manifest"]
    assert "model" not in bundle["manifest"]


def test_partial_normalization_is_diagnostic_but_builder_requires_full_trace() -> None:
    partial = {"spans": [{"name": "interpretation.completed", "attributes": {"constraints": ["x"]}}]}
    assert normalize_trace_export("phoenix", partial)["events"]
    with pytest.raises(ValueError):
        build_replay_bundle("phoenix", partial, requirement=REQUIREMENT, case_id="partial", context=CONTEXT)


@pytest.mark.parametrize(
    "mutation",
    [
        lambda payload: payload["spans"].append(copy.deepcopy(payload["spans"][0])),
        lambda payload: payload["spans"].append({"name": "artifact.completed", "metadata": {"label": "bad"}}),
        lambda payload: payload["spans"][1].__setitem__("parent_event_id", None),
        lambda payload: payload["spans"][1].__setitem__("started_at", "2025-01-01T00:00:00+00:00"),
    ],
)
def test_builder_rejects_duplicate_terminal_or_order_mutations(mutation) -> None:
    payload = _export()
    mutation(payload)
    with pytest.raises((ValueError, TypeError)):
        build_replay_bundle("phoenix", payload, requirement=REQUIREMENT, case_id="bad", context=CONTEXT)


def test_requirement_terminal_fields_fail_closed() -> None:
    with pytest.raises(ValueError):
        build_replay_bundle(
            "phoenix", _export(), requirement={**REQUIREMENT, "mutation": "bad"}, case_id="bad", context=CONTEXT
        )
