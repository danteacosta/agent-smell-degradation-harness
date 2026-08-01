from __future__ import annotations

import json
from pathlib import Path

from eval.runner import run_eval_with_agent
from eval.task_adapters import AcceptanceCriteriaAdapter, TraceabilityTaskAdapter


class _Agent:
    def generate(self, pair, variant, task_family):
        return {"criterion": "refund after 15 minutes"}


def test_thesis_run_emits_arp_v2_ordered_lifecycle_events(tmp_path: Path) -> None:
    pair = {
        "intent_id": "I-ARP",
        "clean_requirement": "Refund orders after 15 minutes.",
        "smelly_requirement": "Refund old orders soon.",
        "smell": {"type": "vague_threshold"},
        "oracle_spec": {"test_gen": {"criterion": "refund after 15 minutes"}},
    }
    run_eval_with_agent(
        _Agent(),
        pairs=[pair],
        task_adapters=(AcceptanceCriteriaAdapter(),),
        output_path=tmp_path / "metrics.json",
        traces_dir=tmp_path / "traces",
    )

    trace = next((tmp_path / "traces").glob("*.jsonl"))
    events = [json.loads(line) for line in trace.read_text().splitlines() if line]
    assert events
    assert all(event["schema_version"] == "2.0.5" for event in events)
    assert [event["sequence_number"] for event in events] == list(range(len(events)))
    assert all(event["event_id"] and event["experiment_id"] for event in events)
    assert events[0]["checkpoint"] == "input.received"


def test_traceability_task_rejects_missing_tampered_and_self_reported_links() -> None:
    adapter = TraceabilityTaskAdapter()
    artifact = {"criterion": "refund after 15 minutes"}
    valid = {
        "links": [
            {
                "claim": "refund threshold",
                "artifact_path": "/criterion",
                "artifact_sha256": adapter.artifact_hash(artifact),
            }
        ]
    }
    assert adapter.evaluate(intent_id="I-1", artifact=artifact, oracle_spec=valid).passed

    missing = {"links": [{"claim": "refund threshold", "artifact_path": "/missing", "artifact_sha256": adapter.artifact_hash(artifact)}]}
    tampered = {"links": [{"claim": "refund threshold", "artifact_path": "/criterion", "artifact_sha256": "0" * 64}]}
    self_reported = {"links": [{"claim": "refund threshold", "artifact_path": "/criterion", "artifact_sha256": adapter.artifact_hash(artifact), "self_reported": True}]}
    assert not adapter.evaluate(intent_id="I-1", artifact=artifact, oracle_spec=missing).passed
    assert not adapter.evaluate(intent_id="I-1", artifact=artifact, oracle_spec=tampered).passed
    assert not adapter.evaluate(intent_id="I-1", artifact=artifact, oracle_spec=self_reported).passed
