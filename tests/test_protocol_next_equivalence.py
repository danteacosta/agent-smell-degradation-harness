from __future__ import annotations
import json
from pathlib import Path

from agent_reliability_protocol import DecisionReason, GateDecision, RunManifest


def test_portable_fixture_has_rag_compatible_neutral_contract_semantics():
    fixture = json.loads((Path(__file__).parent / "fixtures" / "protocol_next_equivalence.json").read_text())
    manifest = RunManifest(
        run_id="run-1", started_at="2026-01-01T00:00:00Z", decision=GateDecision.passed(),
        identifiers={"experiment_id": "portable"}, hashes={"input": "abc"}, configuration={"mode": "offline"}, metadata={"format": "protocol_next"},
    )
    decision = GateDecision("fail", (DecisionReason("threshold", "below floor"),))
    assert manifest.identifiers["experiment_id"] == "portable"
    assert decision.to_dict() == fixture["decision"]
