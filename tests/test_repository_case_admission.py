"""Repository E2E admission is evidence-bound and variant-blind."""
from copy import deepcopy
import json
import subprocess
import sys

import pytest

from eval.repository_case_admission import (admit_repository_case,
                                            assess_repository_case)


def digest(character: str, size: int = 64) -> str:
    return character * size


def eligible_case() -> dict:
    revision = digest("a", 40)
    return {
        "schema_version": "repository-e2e-case/v1",
        "case_id": "TODOMVC-EDIT-ESCAPE-001",
        "project_id": "tastejs-todomvc",
        "repository_url": "https://github.com/tastejs/todomvc",
        "source_revision_url": f"https://github.com/tastejs/todomvc/blob/{revision}/app-spec.md",
        "source_revision_id": revision,
        "requirement_locator": "app-spec.md#editing",
        "requirement_sha256": digest("b"),
        "base_commit": digest("c", 40),
        "gold_commit": digest("d", 40),
        "implementation_paths": ["examples/react/src/todo-item.jsx"],
        "upstream_test_paths": ["cypress/e2e/spec.cy.js"],
        "observable_interface": "browser",
        "interaction_contract": {
            "initial_state": "A persisted todo is visible.",
            "action": "Edit its title and press Escape.",
            "observable_outcome": "Editing closes and the original title remains after reload.",
        },
        "target_constraint_id": "editing.escape_discards_changes",
        "clean_requirement_sha256": digest("e"),
        "rewrite_control_requirement_sha256": digest("0"),
        "smelly_requirement_sha256": digest("f"),
        "changed_span_sha256": digest("1"),
        "scaffold_sha256": digest("a"),
        "shared_oracle_sha256": digest("2"),
        "oracle_frozen_at": "2026-09-16T08:00:00-03:00",
        "variant_assignment_frozen_at": "2026-09-16T08:05:00-03:00",
        "test_generation_source": "canonical_complete_requirement_only",
        "same_oracle_for_all_variants": True,
        "same_scaffold_for_all_variants": True,
        "rewrite_control_preserves_intent": True,
        "gold_passed": True,
        "mutation_killed": True,
        "gold_run_receipt_sha256": digest("3"),
        "mutant_run_receipt_sha256": digest("4"),
        "reviews": {
            "mapping_review": {
                "status": "approved", "reviewer_id": "mapping-reviewer-01",
                "evidence_sha256": digest("5"),
            },
            "manipulation_review": {
                "status": "approved", "reviewer_id": "manipulation-reviewer-01",
                "evidence_sha256": digest("8"),
            },
            "oracle_review": {
                "status": "approved", "reviewer_id": "oracle-reviewer-01",
                "evidence_sha256": digest("6"),
            },
            "rights_review": {
                "status": "approved", "reviewer_id": "rights-reviewer-01",
                "evidence_sha256": digest("7"),
            },
        },
        "status": "eligible",
    }


def test_complete_case_is_admitted_with_stable_receipt():
    case = eligible_case()
    first = admit_repository_case(case)
    second = admit_repository_case(deepcopy(case))
    assert first == second
    assert first["eligible"] is True
    assert first["blockers"] == []
    assert len(first["manifest_sha256"]) == 64
    assert first["scientific_claim"] == "admission_control_only"


def test_screening_case_reports_all_unresolved_controls():
    case = eligible_case()
    case.update({
        "status": "screening",
        "test_generation_source": "smelly_variant",
        "same_oracle_for_all_variants": False,
        "same_scaffold_for_all_variants": False,
        "rewrite_control_preserves_intent": False,
        "gold_passed": False,
        "mutation_killed": False,
        "gold_run_receipt_sha256": None,
        "mutant_run_receipt_sha256": None,
        "reviews": {
            "mapping_review": {
                "status": "pending", "reviewer_id": None, "evidence_sha256": None,
            },
            "manipulation_review": {
                "status": "pending", "reviewer_id": None, "evidence_sha256": None,
            },
            "oracle_review": {
                "status": "rejected", "reviewer_id": "oracle-reviewer-02",
                "evidence_sha256": digest("8"),
            },
            "rights_review": {
                "status": "pending", "reviewer_id": None, "evidence_sha256": None,
            },
        },
    })
    result = assess_repository_case(case)
    assert result["eligible"] is False
    assert result["blockers"] == [
        "tests_not_generated_from_canonical_complete_requirement",
        "oracle_not_shared_across_variants",
        "scaffold_not_shared_across_variants",
        "rewrite_control_not_intent_preserving",
        "gold_implementation_not_verified",
        "oracle_did_not_kill_targeted_mutant",
        "manipulation_review:pending",
        "mapping_review:pending",
        "oracle_review:rejected",
        "rights_review:pending",
        "case_status:screening",
    ]
    with pytest.raises(ValueError, match="not eligible"):
        admit_repository_case(case)


@pytest.mark.parametrize("field,value,match", [
    ("source_revision_url", "https://github.com/tastejs/todomvc/blob/main/app-spec.md",
     "source_revision_id"),
    ("base_commit", digest("d", 40), "must differ"),
    ("clean_requirement_sha256", digest("f"), "requirements must differ"),
    ("rewrite_control_requirement_sha256", digest("e"), "requirements must differ"),
    ("variant_assignment_frozen_at", "2026-09-16T07:00:00-03:00",
     "must not precede"),
])
def test_identity_and_freeze_invariants_fail_closed(field, value, match):
    case = eligible_case()
    case[field] = value
    with pytest.raises(ValueError, match=match):
        assess_repository_case(case)


@pytest.mark.parametrize("field,value,match", [
    ("implementation_paths", ["../outside.py"], "normalized relative"),
    ("upstream_test_paths", ["tests/e2e.py", "tests/e2e.py"], "duplicates"),
    ("gold_passed", 1, "boolean"),
    ("same_scaffold_for_all_variants", 1, "boolean"),
    ("observable_interface", "database", "unsupported"),
])
def test_malformed_evidence_is_rejected(field, value, match):
    case = eligible_case()
    case[field] = value
    with pytest.raises(ValueError, match=match):
        assess_repository_case(case)


def test_variant_specific_oracle_and_unknown_fields_are_rejected():
    case = eligible_case()
    case["clean_oracle"] = {"expected": "old title"}
    with pytest.raises(ValueError, match="variant-specific"):
        assess_repository_case(case)


def test_execution_and_review_claims_require_bound_evidence():
    case = eligible_case()
    case["gold_run_receipt_sha256"] = None
    with pytest.raises(ValueError, match="gold_run_receipt_sha256"):
        assess_repository_case(case)
    case = eligible_case()
    case["reviews"]["oracle_review"]["evidence_sha256"] = None
    with pytest.raises(ValueError, match="evidence_sha256"):
        assess_repository_case(case)
    case = eligible_case()
    case["reviews"]["mapping_review"] = {
        "status": "pending", "reviewer_id": "claimed", "evidence_sha256": digest("9")}
    with pytest.raises(ValueError, match="must not claim evidence"):
        assess_repository_case(case)
    case = eligible_case()
    case["reviews"]["manipulation_review"]["evidence_sha256"] = None
    with pytest.raises(ValueError, match="evidence_sha256"):
        assess_repository_case(case)
    case = eligible_case()
    case["notes"] = "not part of the frozen contract"
    with pytest.raises(ValueError, match="keys mismatch"):
        assess_repository_case(case)


def test_cli_returns_two_for_valid_but_blocked_manifest(tmp_path):
    case = eligible_case()
    case["status"] = "screening"
    path = tmp_path / "case.json"
    path.write_text(json.dumps(case), encoding="utf-8")
    run = subprocess.run(
        [sys.executable, "-m", "eval.repository_case_admission",
         "--manifest", str(path)], capture_output=True, text=True)
    assert run.returncode == 2
    result = json.loads(run.stdout)
    assert result["eligible"] is False
    assert result["blockers"] == ["case_status:screening"]
