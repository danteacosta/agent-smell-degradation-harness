from __future__ import annotations
import json
from pathlib import Path

from protocol_next.contracts import DecisionReason, EpisodeIdentity, GateDecision, RunManifest


def test_portable_fixture_has_rag_compatible_neutral_contract_semantics():
    fixture = json.loads((Path(__file__).parent / "fixtures" / "protocol_next_equivalence.json").read_text())
    identity = EpisodeIdentity(**fixture["episode_identity"])
    manifest = RunManifest(**fixture["manifest"])
    decision = GateDecision("fail", (DecisionReason("threshold", "below floor"),))
    assert identity.to_dict() == fixture["episode_identity"]
    assert manifest.to_dict() == fixture["manifest"]
    assert decision.to_dict() == fixture["decision"]
