from __future__ import annotations

import json

import pytest

from observability.handoff import SourceRef, build_handoff, write_handoff
from observability.tracing import ProvenanceRecorder


def test_pre_final_handoff_is_deterministic_and_keeps_source_references(tmp_path):
    handoff = build_handoff(
        experiment_id="exp-1",
        run_id="run-1",
        episode_id="ep-1",
        plane="pre_final",
        decision="generated artifact",
        next_step="run evaluator",
        risks=["missing traceability"],
        new_facts=["artifact hash recorded"],
        source_refs=[SourceRef(kind="tool", identifier="tool-1", content_hash="abc")],
    )
    path = write_handoff(tmp_path / "handoff.json", handoff)
    payload = json.loads(path.read_text())
    assert payload["plane"] == "pre_final"
    assert payload["source_refs"][0]["content_hash"] == "abc"
    assert "oracle" not in payload
    assert path.read_text() == write_handoff(tmp_path / "handoff-2.json", handoff).read_text()


def test_pre_final_handoff_rejects_label_plane_fields():
    with pytest.raises(ValueError, match="pre_final"):
        build_handoff(
            experiment_id="exp-1",
            run_id="run-1",
            episode_id="ep-1",
            plane="pre_final",
            decision="x",
            next_step="y",
            risks=[],
            new_facts=[],
            source_refs=[],
            extra={"oracle": "pass"},
        )


def test_pre_final_handoff_rejects_nested_outcome_aliases_and_malformed_refs():
    with pytest.raises(ValueError, match="pre_final"):
        build_handoff(
            experiment_id="exp-1",
            run_id="run-1",
            episode_id="ep-1",
            plane="pre_final",
            decision="x",
            next_step="y",
            risks=[],
            new_facts=[],
            source_refs=[SourceRef(kind="tool", identifier="t1")],
            extra={"summary": {"ground-truth": "pass"}},
        )
    with pytest.raises(ValueError, match="secret-like"):
        SourceRef(kind="tool", identifier="api_key=secret")


def test_handoff_extra_cannot_override_identity_fields():
    with pytest.raises(ValueError, match="reserved"):
        build_handoff(
            experiment_id="exp-1",
            run_id="run-1",
            episode_id="ep-1",
            plane="pre_final",
            decision="x",
            next_step="y",
            risks=[],
            new_facts=[],
            source_refs=[],
            extra={"run_id": "spoofed"},
        )


def test_recorder_preserves_explicit_source_refs(tmp_path):
    path = tmp_path / "trace.jsonl"
    rec = ProvenanceRecorder(path)
    rec.operational("tool.completed", {"source_refs": [{"kind": "command", "identifier": "c1"}]})
    rec.close()
    record = json.loads(path.read_text().strip())
    assert record["source_refs"] == [{"kind": "command", "identifier": "c1"}]
