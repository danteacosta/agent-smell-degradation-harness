"""Review packets are isolated, immutable, and admission-compatible."""
from __future__ import annotations

from copy import deepcopy
import json
import os
from pathlib import Path

import pytest

from eval.repository_case_review import (
    ROLES, assemble_responses, export_packets, record_response, verify_export,
)


def source() -> dict:
    return {
        "schema_version": "repository-review-source/v1",
        "case_id": "todomvc-escape-edit",
        "roles": {
            "mapping_review": {
                "canonical_requirement": "Escape discards the edit.",
                "source_revision": "a" * 40,
                "requirement_locator": "app-spec.md#editing",
                "implementation_paths": ["src/app.js"],
                "mapping_question": "Does the code implement this requirement?",
            },
            "manipulation_review": {
                "canonical_requirement": "Escape discards the edit.",
                "rewrite_control_requirement": "Pressing Escape cancels changes.",
                "smelly_requirement": "Escape handles the edit appropriately.",
                "changed_span": "discards -> handles appropriately",
                "targeted_mutant_diff": "- cancelEdit()\n+ commitEdit()",
                "manipulation_question": "Is only the intended condition weakened?",
            },
            "oracle_review": {
                "canonical_requirement": "Escape discards the edit.",
                "observable_interface": "browser",
                "interaction_contract": {
                    "initial_state": "todo exists",
                    "action": "edit then press Escape",
                    "observable_outcome": "original title remains",
                },
                "oracle_locator": "cypress/e2e/escape.cy.js",
                "oracle_sha256": "b" * 64,
                "oracle_question": "Does this oracle test the observable condition?",
            },
            "rights_review": {
                "repository_url": "https://github.com/tastejs/todomvc",
                "source_revision": "a" * 40,
                "license_locator": "LICENSE",
                "license_sha256": "c" * 64,
                "intended_use": "controlled research execution",
                "rights_question": "Is the intended research use permitted?",
            },
        },
    }


def private(tmp_path: Path, name: str) -> Path:
    root = tmp_path / name
    root.mkdir(mode=0o700)
    return root


def complete(export_root: Path, role: str, reviewer: str,
             root: Path, decision: str = "approved") -> Path:
    form = json.loads((export_root / "handoff" / role / "form.json").read_text())
    form.update({
        "status": "completed",
        "reviewer_id": reviewer,
        "prior_exposure_declared": False,
        "decision": decision,
        "confidence": "high",
        "rationale": "The supplied evidence supports this criterion.",
        "limitations": "Review is limited to the supplied material.",
    })
    completed = root / f"{role}-completed.json"
    completed.write_text(json.dumps(form), encoding="utf-8")
    os.chmod(completed, 0o600)
    response = root / f"{role}-response.json"
    record_response(export_root, completed, response)
    return response


def test_export_is_role_isolated_private_and_deterministic(tmp_path: Path) -> None:
    export = tmp_path / "review-export"
    receipt = export_packets(source(), export)
    assert verify_export(export) == receipt
    mapping = (export / "handoff/mapping_review/form.json").read_text()
    oracle = (export / "handoff/oracle_review/form.json").read_text()
    rights = (export / "handoff/rights_review/form.json").read_text()
    assert "smelly_requirement" not in mapping
    assert "targeted_mutant_diff" not in mapping
    assert "targeted_mutant_diff" not in oracle
    assert "gold_passed" not in oracle
    assert "canonical_requirement" not in rights
    assert receipt["confirmatory_eligible"] is False
    assert receipt["role_count"] == 4
    assert not (export.stat().st_mode & 0o077)
    assert all(not (path.stat().st_mode & 0o077)
               for path in export.rglob("*") if path.is_file())


def test_export_rejects_tampering_extra_files_and_symlinks(tmp_path: Path) -> None:
    export = tmp_path / "review-export"
    export_packets(source(), export)
    form = export / "handoff/mapping_review/form.json"
    form.write_text(form.read_text() + " ", encoding="utf-8")
    with pytest.raises(ValueError, match="digest mismatch"):
        verify_export(export)

    export2 = tmp_path / "review-export-2"
    export_packets(source(), export2)
    extra = export2 / "unexpected.txt"
    extra.write_text("unexpected", encoding="utf-8")
    os.chmod(extra, 0o600)
    with pytest.raises(ValueError, match="inventory mismatch"):
        verify_export(export2)

    export3 = tmp_path / "review-export-3"
    export_packets(source(), export3)
    original = export3 / "handoff/mapping_review/form.json"
    target = tmp_path / "target.json"
    target.write_bytes(original.read_bytes())
    original.unlink()
    original.symlink_to(target)
    with pytest.raises(ValueError, match="invalid export file|inventory mismatch"):
        verify_export(export3)


def test_record_rejects_changed_materials_and_is_immutable(tmp_path: Path) -> None:
    export = tmp_path / "review-export"
    export_packets(source(), export)
    root = private(tmp_path, "responses")
    form = json.loads((export / "handoff/mapping_review/form.json").read_text())
    form.update({
        "status": "completed", "reviewer_id": "reviewer-1",
        "prior_exposure_declared": True, "decision": "approved",
        "confidence": "medium", "rationale": "Reviewed.",
        "limitations": "Limited evidence.",
    })
    form["materials"]["canonical_requirement"] = "changed"
    completed = root / "completed.json"
    completed.write_text(json.dumps(form), encoding="utf-8")
    os.chmod(completed, 0o600)
    with pytest.raises(ValueError, match="not bound"):
        record_response(export, completed, root / "response.json")

    form["materials"] = json.loads(
        (export / "handoff/mapping_review/form.json").read_text()
    )["materials"]
    completed.write_text(json.dumps(form), encoding="utf-8")
    response = root / "response.json"
    record_response(export, completed, response)
    with pytest.raises(FileExistsError):
        record_response(export, completed, response)


def test_assembly_is_admission_compatible_and_preserves_rejection(tmp_path: Path) -> None:
    export = tmp_path / "review-export"
    export_packets(source(), export)
    root = private(tmp_path, "responses")
    paths = [complete(export, role, f"reviewer-{index}", root,
                      "rejected" if role == "rights_review" else "approved")
             for index, role in enumerate(ROLES, start=1)]
    assembly = assemble_responses(export, paths, root / "assembly.json")
    assert set(assembly["reviews"]) == set(ROLES)
    assert assembly["reviews"]["rights_review"]["status"] == "rejected"
    assert assembly["all_approved"] is False
    assert assembly["confirmatory_eligible"] is False
    for record in assembly["reviews"].values():
        assert set(record) == {"status", "reviewer_id", "evidence_sha256"}
        assert len(record["evidence_sha256"]) == 64


def test_assembly_rejects_duplicate_aliases_and_mixed_exports(tmp_path: Path) -> None:
    export = tmp_path / "review-export"
    export_packets(source(), export)
    root = private(tmp_path, "responses")
    reviewers = ["Mapping-Reviewer", "MAPPING-REVIEWER", "oracle", "rights"]
    paths = [complete(export, role, reviewer, root)
             for role, reviewer in zip(ROLES, reviewers)]
    with pytest.raises(ValueError, match="distinct"):
        assemble_responses(export, paths, root / "assembly.json")

    other_source = deepcopy(source())
    other_source["case_id"] = "other-case"
    other_export = tmp_path / "other-export"
    export_packets(other_source, other_export)
    other_root = private(tmp_path, "other-responses")
    mixed = complete(other_export, "rights_review", "other-rights", other_root)
    paths[-1] = mixed
    with pytest.raises(ValueError, match="binding failed"):
        assemble_responses(export, paths, root / "mixed.json")
