from __future__ import annotations

import copy
import json
from pathlib import Path

from eval.corpus_declaration_audit import audit_corpus_declarations, main

ROOT = Path(__file__).parents[1]
PLAN = json.loads((ROOT / "data/prepilot/launch-plan.candidate.json").read_text())
MANIFEST = json.loads((ROOT / "data/prepilot/corpus-manifest.json").read_text())


def test_checked_in_declarations_match_manifest() -> None:
    report = audit_corpus_declarations(PLAN, MANIFEST)
    assert report["consistent"], report["discrepancies"]
    assert report["derived"]["unique_intents"] == 12
    assert report["approves_nothing"] is True


def test_llm_only_review_is_surfaced_as_warning() -> None:
    report = audit_corpus_declarations(PLAN, MANIFEST)
    assert any(w.startswith("llm_only_manipulation_review") for w in report["warnings"])


def test_declared_count_mismatch_and_duplicates_are_flagged() -> None:
    m = copy.deepcopy(MANIFEST)
    m["records"][1]["source_intent_id"] = m["records"][0]["source_intent_id"]
    report = audit_corpus_declarations(PLAN, m)
    assert not report["consistent"]
    assert any("duplicate source_intent_id" in d for d in report["discrepancies"])
    assert any("unique_intents=12" in d for d in report["discrepancies"])


def test_float_or_bool_declared_count_fails() -> None:
    for bad in (12.0, True):
        plan = copy.deepcopy(PLAN)
        plan["corpus"]["unique_intents"] = bad
        assert not audit_corpus_declarations(plan, MANIFEST)["consistent"]


def test_unlicensed_unreviewed_and_failed_checks_are_flagged() -> None:
    m = copy.deepcopy(MANIFEST)
    m["records"][0]["license_evidence_url"] = ""
    m["records"][1]["rights_review"]["external_provider_processing_allowed"] = False
    m["records"][2]["near_clone_reviewed"] = False
    m["records"][3]["manipulation_check"]["intent_preserved"] = False
    report = audit_corpus_declarations(PLAN, m)
    assert len(report["discrepancies"]) == 4


def test_cli_exit_codes(tmp_path: Path, capsys) -> None:
    assert main([]) == 0
    bad = copy.deepcopy(MANIFEST)
    bad["records"][0]["project_id"] = ""
    path = tmp_path / "m.json"
    path.write_text(json.dumps(bad))
    assert main(["--manifest", str(path)]) == 2
    capsys.readouterr()
