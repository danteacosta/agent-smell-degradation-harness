"""Observable rules for the secondary ordinal audit."""
import json

import pytest

from scripts import h1_existing_artifacts_ordinal_audit as collector
from scripts import h1_ordinal_audit_results as results
from scripts.criteria_consensus import digest, inventory
from scripts.h1_existing_artifacts_ordinal_audit import judge_prompt
from scripts.h1_ordinal_audit_results import citation_valid, interval
from label_plane.exploratory_judge import ConstraintAssessment


def test_missing_severity_keeps_full_zero_to_three_range():
    assert interval({"A": 0, "C": None}) == (-3, 0)
    assert interval({"A": None, "C": 2}) == (-2, 1)
    assert interval({"A": None, "C": None}) == (-3, 3)
    assert interval({"A": 0, "C": 2}) == (-2, -2)


def test_blind_prompt_requires_string_evidence_and_exact_fields():
    request = {
        "schema_version": "acceptance-criteria-llm-judge/v1",
        "occurrence_id": "opaque-1",
        "generated_acceptance_criteria": "The item is saved.",
        "reference_constraints": [{"constraint_id": "c01", "text": "Saving stores the item."}],
    }
    prompt = judge_prompt(request, {"severity_anchors": {"clean": "All covered."}})
    assert "MUST be JSON strings, never arrays" in prompt
    assert '"occurrence_id": "opaque-1"' in prompt
    assert "gpt-" not in prompt
    assert '"variant"' not in prompt


def test_covered_constraint_requires_literal_quote_and_omission_requires_empty_evidence():
    criteria = "The author can delete the item."
    assert citation_valid((ConstraintAssessment("c01", "covered", "author can delete"),), criteria)
    assert not citation_valid((ConstraintAssessment("c01", "covered", "only the author deletes"),), criteria)
    assert citation_valid((ConstraintAssessment("c01", "omitted", ""),), criteria)
    assert not citation_valid((ConstraintAssessment("c01", "omitted", "some quote"),), criteria)


def test_prepare_freezes_the_runtime_required_by_derivation(tmp_path, monkeypatch):
    parent = tmp_path / "parent"
    (parent / "frozen").mkdir(parents=True)
    for name in ("receipt.json", "results.json", "frozen/schedule.json", "frozen/corpus.json"):
        (parent / name).write_text("{}")
    monkeypatch.setattr(collector, "source_rows", lambda _: ([], {}))
    packet = tmp_path / "private-packet"
    collector.prepare(parent, packet)
    manifest = json.loads((packet / "manifest.json").read_text())
    assert (packet / "frozen-runtime.py").read_bytes() == collector.Path(collector.__file__).read_bytes()
    assert manifest["script_sha256"] == collector.hash_file(packet / "frozen-runtime.py")


def test_sealed_replay_rejects_packet_and_result_tampering(tmp_path, monkeypatch):
    packet = tmp_path / "packet"
    packet.mkdir()
    (packet / "analysis.json").write_text(json.dumps({"cells": [[-3, 0]]}))
    (packet / "receipt.json").write_text(json.dumps({"files": inventory(packet)}))
    receipt_hash = digest((packet / "receipt.json").read_bytes())
    public = tmp_path / "public.json"
    public.write_text(json.dumps({"bounds": [-3, 0]}))
    monkeypatch.setattr(results, "derive", lambda *_: ({"bounds": (-3, 0)}, {"cells": [(-3, 0)]}))
    assert results.verify_sealed(packet, tmp_path, public, receipt_hash) == {"bounds": (-3, 0)}
    public.write_text(json.dumps({"bounds": [0, 0]}))
    with pytest.raises(ValueError, match="public result"):
        results.verify_sealed(packet, tmp_path, public, receipt_hash)
    public.write_text(json.dumps({"bounds": [-3, 0]}))
    (packet / "analysis.json").write_text(json.dumps({"cells": [[0, 0]]}))
    with pytest.raises(ValueError, match="inventory"):
        results.verify_sealed(packet, tmp_path, public, receipt_hash)
