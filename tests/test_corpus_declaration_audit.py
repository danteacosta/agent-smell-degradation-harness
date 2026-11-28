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


def test_concentration_and_constraint_load_are_descriptive_warnings() -> None:
    report = audit_corpus_declarations(PLAN, MANIFEST)
    assert any(w.startswith("single_constraint_load") for w in report["warnings"])
    assert 0 < report["derived"]["max_project_share"] <= 1
    assert sum(report["derived"]["defect_family_counts"].values()) == 12


def test_shared_removed_constraint_id_is_flagged() -> None:
    m = copy.deepcopy(MANIFEST)
    m["records"][1]["removed_constraint_id"] = m["records"][0]["removed_constraint_id"]
    report = audit_corpus_declarations(PLAN, m)
    assert any("removed_constraint_id" in d for d in report["discrepancies"])


def test_single_project_corpus_triggers_concentration_warning() -> None:
    m = copy.deepcopy(MANIFEST)
    for r in m["records"]:
        r["project_id"] = "ONE"
    m["project_count"] = 1
    report = audit_corpus_declarations(PLAN, m)
    assert any(w.startswith("project_concentration") for w in report["warnings"])


def test_identical_or_malformed_pair_hashes_fail() -> None:
    m = copy.deepcopy(MANIFEST)
    m["records"][0]["defective_requirement_sha256"] = m["records"][0]["clean_requirement_sha256"]
    report = audit_corpus_declarations(PLAN, m)
    assert any("identical" in d for d in report["discrepancies"])
    m = copy.deepcopy(MANIFEST)
    m["records"][1]["clean_requirement_sha256"] = "not-a-hash"
    assert any("SHA-256" in d for d in audit_corpus_declarations(PLAN, m)["discrepancies"])
    del m["records"][2]["defective_requirement_sha256"]
    assert not audit_corpus_declarations(PLAN, m)["consistent"]


def test_near_clone_group_spanning_projects_is_a_leakage_discrepancy() -> None:
    m = copy.deepcopy(MANIFEST)
    other = next(r for r in m["records"] if r["project_id"] != m["records"][0]["project_id"])
    other["near_clone_group"] = m["records"][0]["near_clone_group"]
    report = audit_corpus_declarations(PLAN, m)
    assert any("holdout would leak" in d for d in report["discrepancies"])
