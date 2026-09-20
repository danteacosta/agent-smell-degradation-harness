"""Role-isolated, tamper-evident human review packets for E2E cases.

The workflow is deliberately separate from labels and provider execution.  It
turns four completed human reviews into records accepted by
``repository_case_admission``; it does not decide whether a review is correct.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import stat
from typing import Any


SOURCE_SCHEMA = "repository-review-source/v1"
FORM_SCHEMA = "repository-review-form/v1"
RESPONSE_SCHEMA = "repository-review-response/v1"
ASSEMBLY_SCHEMA = "repository-review-assembly/v1"
RECEIPT_SCHEMA = "repository-review-export-receipt/v1"
ROLES = (
    "mapping_review",
    "manipulation_review",
    "oracle_review",
    "rights_review",
)
SOURCE_KEYS = {"schema_version", "case_id", "roles"}
FORM_KEYS = {
    "schema_version", "status", "case_id", "role", "reviewer_id",
    "prior_exposure_declared", "materials", "decision", "confidence",
    "rationale", "limitations",
}
ROLE_MATERIAL_KEYS = {
    "mapping_review": {
        "canonical_requirement", "source_revision", "requirement_locator",
        "implementation_paths", "mapping_question",
    },
    "manipulation_review": {
        "canonical_requirement", "rewrite_control_requirement",
        "smelly_requirement", "changed_span", "targeted_mutant_diff",
        "manipulation_question",
    },
    "oracle_review": {
        "canonical_requirement", "observable_interface",
        "interaction_contract", "oracle_locator", "oracle_sha256",
        "oracle_question",
    },
    "rights_review": {
        "repository_url", "source_revision", "license_locator",
        "license_sha256", "intended_use", "rights_question",
    },
}
CONFIDENCE = {"low", "medium", "high"}
DECISIONS = {"approved", "rejected"}


def _canonical(value: Any) -> bytes:
    return json.dumps(value, ensure_ascii=False, sort_keys=True,
                      separators=(",", ":")).encode("utf-8")


def _sha(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def _require_exact(value: dict, expected: set[str], label: str) -> None:
    if not isinstance(value, dict):
        raise ValueError(f"{label} must be an object")
    if set(value) != expected:
        raise ValueError(
            f"{label} keys mismatch; missing={sorted(expected - set(value))}, "
            f"extra={sorted(set(value) - expected)}"
        )


def _text(value: Any, label: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{label} must contain text")
    if any(ord(character) < 32 for character in value):
        raise ValueError(f"{label} must not contain control characters")
    return value.strip()


def _validate_materials(role: str, materials: Any) -> dict:
    _require_exact(materials, ROLE_MATERIAL_KEYS[role], f"{role}.materials")
    for key, value in materials.items():
        if key == "implementation_paths":
            if (not isinstance(value, list) or not value or
                    any(not isinstance(item, str) or not item.strip()
                        for item in value)):
                raise ValueError("implementation_paths must contain paths")
        elif key == "interaction_contract":
            if not isinstance(value, dict) or not value:
                raise ValueError("interaction_contract must be a non-empty object")
        else:
            _text(value, f"{role}.materials.{key}")
    return materials


def validate_source(source: Any) -> dict:
    _require_exact(source, SOURCE_KEYS, "source")
    if source["schema_version"] != SOURCE_SCHEMA:
        raise ValueError("unsupported source schema")
    _text(source["case_id"], "case_id")
    _require_exact(source["roles"], set(ROLES), "roles")
    for role in ROLES:
        _validate_materials(role, source["roles"][role])
    return source


def _assert_private_root(path: Path) -> None:
    if not path.is_absolute():
        raise ValueError("output path must be absolute")
    repository = Path.cwd().resolve()
    resolved = path.resolve(strict=False)
    if resolved == repository or repository in resolved.parents:
        raise ValueError("review artifacts must be stored outside the repository")


def _write_new(path: Path, payload: bytes) -> None:
    path.parent.mkdir(mode=0o700, parents=True, exist_ok=True)
    os.chmod(path.parent, 0o700)
    descriptor = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
    try:
        with os.fdopen(descriptor, "wb") as stream:
            stream.write(payload)
            stream.flush()
            os.fsync(stream.fileno())
    except BaseException:
        path.unlink(missing_ok=True)
        raise


def _form(source: dict, role: str) -> dict:
    return {
        "schema_version": FORM_SCHEMA,
        "status": "draft",
        "case_id": source["case_id"],
        "role": role,
        "reviewer_id": "",
        "prior_exposure_declared": None,
        "materials": source["roles"][role],
        "decision": None,
        "confidence": None,
        "rationale": "",
        "limitations": "",
    }


def _render_markdown(form: dict) -> bytes:
    title = form["role"].replace("_", " ").title()
    materials = json.dumps(form["materials"], ensure_ascii=False, indent=2,
                           sort_keys=True)
    return (
        f"# {title}\n\n"
        "Review only the supplied criterion. Do not infer omitted evidence or "
        "coordinate decisions with the other role reviewers.\n\n"
        f"Case: `{form['case_id']}`\n\n"
        "## Materials\n\n```json\n" + materials + "\n```\n\n"
        "Complete `form.json`; declare prior exposure and record decision, "
        "confidence, rationale, and limitations.\n"
    ).encode("utf-8")


def export_packets(source: dict, output: Path) -> dict:
    validate_source(source)
    _assert_private_root(output)
    output.mkdir(mode=0o700, parents=True, exist_ok=False)
    os.chmod(output, 0o700)
    inventory: dict[str, str] = {}
    forms: dict[str, dict] = {}
    for role in ROLES:
        form = _form(source, role)
        role_dir = output / "handoff" / role
        form_path = role_dir / "form.json"
        guide_path = role_dir / "README.md"
        form_bytes = _canonical(form) + b"\n"
        guide_bytes = _render_markdown(form)
        _write_new(form_path, form_bytes)
        _write_new(guide_path, guide_bytes)
        inventory[str(form_path.relative_to(output))] = _sha(form_bytes)
        inventory[str(guide_path.relative_to(output))] = _sha(guide_bytes)
        forms[role] = {
            "form_path": str(form_path.relative_to(output)),
            "form_sha256": _sha(form_bytes),
            "materials_sha256": _sha(_canonical(form["materials"])),
        }
    manifest = {
        "schema_version": "repository-review-export-manifest/v1",
        "case_id": source["case_id"],
        "source_sha256": _sha(_canonical(source)),
        "confirmatory_eligible": False,
        "forms": forms,
    }
    manifest_bytes = _canonical(manifest) + b"\n"
    manifest_path = output / "custodian" / "manifest.json"
    _write_new(manifest_path, manifest_bytes)
    inventory[str(manifest_path.relative_to(output))] = _sha(manifest_bytes)
    receipt = {
        "schema_version": RECEIPT_SCHEMA,
        "case_id": source["case_id"],
        "confirmatory_eligible": False,
        "role_count": len(ROLES),
        "inventory": dict(sorted(inventory.items())),
    }
    receipt_path = output / "receipt.json"
    _write_new(receipt_path, _canonical(receipt) + b"\n")
    _sync_tree(output)
    return receipt


def _sync_tree(root: Path) -> None:
    for directory, _, _ in os.walk(root, topdown=False):
        descriptor = os.open(directory, os.O_RDONLY)
        try:
            os.fsync(descriptor)
        finally:
            os.close(descriptor)


def _load_json(path: Path) -> dict:
    if path.is_symlink():
        raise ValueError(f"symlink not allowed: {path}")
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as error:
        raise ValueError(f"cannot read JSON: {path}") from error
    if not isinstance(value, dict):
        raise ValueError(f"JSON root must be an object: {path}")
    return value


def verify_export(output: Path) -> dict:
    _assert_private_root(output)
    if output.is_symlink() or not output.is_dir():
        raise ValueError("export root must be a real directory")
    if stat.S_IMODE(output.stat().st_mode) & 0o077:
        raise ValueError("export root must not be group/world accessible")
    receipt = _load_json(output / "receipt.json")
    _require_exact(receipt, {"schema_version", "case_id",
                             "confirmatory_eligible", "role_count", "inventory"},
                   "receipt")
    if receipt["schema_version"] != RECEIPT_SCHEMA:
        raise ValueError("unsupported receipt schema")
    if receipt["confirmatory_eligible"] is not False:
        raise ValueError("review export cannot be confirmatory evidence")
    if receipt["role_count"] != len(ROLES):
        raise ValueError("unexpected role count")
    expected = set(receipt["inventory"]) | {"receipt.json"}
    observed = {
        str(path.relative_to(output)) for path in output.rglob("*") if path.is_file()
    }
    if observed != expected:
        raise ValueError("export inventory mismatch")
    for relative, expected_sha in receipt["inventory"].items():
        path = output / relative
        if path.is_symlink() or not path.is_file():
            raise ValueError(f"invalid export file: {relative}")
        if stat.S_IMODE(path.stat().st_mode) & 0o077:
            raise ValueError(f"export file is not private: {relative}")
        if _sha(path.read_bytes()) != expected_sha:
            raise ValueError(f"export digest mismatch: {relative}")
    manifest = _load_json(output / "custodian" / "manifest.json")
    if manifest.get("case_id") != receipt["case_id"]:
        raise ValueError("manifest and receipt case mismatch")
    for role in ROLES:
        form = _load_json(output / "handoff" / role / "form.json")
        _validate_form(form, completed=False)
        if form["case_id"] != receipt["case_id"] or form["role"] != role:
            raise ValueError("form identity mismatch")
        expected_sha = manifest["forms"][role]["materials_sha256"]
        if _sha(_canonical(form["materials"])) != expected_sha:
            raise ValueError("form materials mismatch")
    return receipt


def _validate_form(form: Any, completed: bool) -> dict:
    _require_exact(form, FORM_KEYS, "form")
    if form["schema_version"] != FORM_SCHEMA:
        raise ValueError("unsupported form schema")
    role = _text(form["role"], "role")
    if role not in ROLES:
        raise ValueError("unknown review role")
    _text(form["case_id"], "case_id")
    _validate_materials(role, form["materials"])
    if completed:
        if form["status"] != "completed":
            raise ValueError("completed form must have completed status")
        _text(form["reviewer_id"], "reviewer_id")
        if not isinstance(form["prior_exposure_declared"], bool):
            raise ValueError("prior exposure must be declared")
        if form["decision"] not in DECISIONS:
            raise ValueError("decision must be approved or rejected")
        if form["confidence"] not in CONFIDENCE:
            raise ValueError("confidence must be low, medium, or high")
        _text(form["rationale"], "rationale")
        _text(form["limitations"], "limitations")
    else:
        if (form["status"] != "draft" or form["reviewer_id"] != "" or
                form["prior_exposure_declared"] is not None or
                form["decision"] is not None or form["confidence"] is not None or
                form["rationale"] != "" or form["limitations"] != ""):
            raise ValueError("exported form is not a clean draft")
    return form


def record_response(export_root: Path, completed_path: Path,
                    response_path: Path) -> dict:
    receipt = verify_export(export_root)
    completed = _validate_form(_load_json(completed_path), completed=True)
    role = completed["role"]
    original_path = export_root / "handoff" / role / "form.json"
    original = _load_json(original_path)
    if (completed["case_id"] != receipt["case_id"] or
            completed["materials"] != original["materials"]):
        raise ValueError("completed response is not bound to the exported form")
    _assert_private_root(response_path.parent)
    envelope = {
        "schema_version": RESPONSE_SCHEMA,
        "case_id": completed["case_id"],
        "role": role,
        "export_receipt_sha256": _sha((export_root / "receipt.json").read_bytes()),
        "source_form_sha256": _sha(original_path.read_bytes()),
        "evidence_sha256": _sha(_canonical(completed)),
        "response": completed,
    }
    _write_new(response_path, _canonical(envelope) + b"\n")
    _sync_tree(response_path.parent)
    return envelope


def assemble_responses(export_root: Path, response_paths: list[Path],
                       output_path: Path) -> dict:
    receipt = verify_export(export_root)
    if len(response_paths) != len(ROLES):
        raise ValueError("exactly four response files are required")
    receipt_sha = _sha((export_root / "receipt.json").read_bytes())
    responses: dict[str, dict] = {}
    reviewer_ids: list[str] = []
    for path in response_paths:
        envelope = _load_json(path)
        _require_exact(envelope, {
            "schema_version", "case_id", "role", "export_receipt_sha256",
            "source_form_sha256", "evidence_sha256", "response",
        }, "response envelope")
        if envelope["schema_version"] != RESPONSE_SCHEMA:
            raise ValueError("unsupported response schema")
        role = envelope["role"]
        if role not in ROLES or role in responses:
            raise ValueError("response roles must be exact and unique")
        response = _validate_form(envelope["response"], completed=True)
        original_path = export_root / "handoff" / role / "form.json"
        original = _load_json(original_path)
        if (envelope["case_id"] != receipt["case_id"] or
                response["case_id"] != receipt["case_id"] or
                response["role"] != role or
                envelope["export_receipt_sha256"] != receipt_sha or
                envelope["source_form_sha256"] != _sha(original_path.read_bytes()) or
                envelope["evidence_sha256"] != _sha(_canonical(response)) or
                response["materials"] != original["materials"]):
            raise ValueError("response binding failed")
        reviewer_ids.append(response["reviewer_id"].strip().casefold())
        responses[role] = envelope
    if set(responses) != set(ROLES):
        raise ValueError("all four review roles are required")
    if len(set(reviewer_ids)) != len(reviewer_ids):
        raise ValueError("reviewer identities must be distinct")
    reviews = {
        role: {
            "status": responses[role]["response"]["decision"],
            "reviewer_id": responses[role]["response"]["reviewer_id"].strip(),
            "evidence_sha256": responses[role]["evidence_sha256"],
        }
        for role in ROLES
    }
    assembly = {
        "schema_version": ASSEMBLY_SCHEMA,
        "status": "review_assembly_verified",
        "case_id": receipt["case_id"],
        "export_receipt_sha256": receipt_sha,
        "confirmatory_eligible": False,
        "all_approved": all(record["status"] == "approved"
                            for record in reviews.values()),
        "reviews": reviews,
    }
    _assert_private_root(output_path.parent)
    _write_new(output_path, _canonical(assembly) + b"\n")
    _sync_tree(output_path.parent)
    return assembly


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--source", type=Path)
    parser.add_argument("--export", type=Path, required=True)
    parser.add_argument("--verify", action="store_true")
    parser.add_argument("--completed-form", type=Path)
    parser.add_argument("--response-output", type=Path)
    parser.add_argument("--responses", type=Path, nargs=4)
    parser.add_argument("--assembly-output", type=Path)
    args = parser.parse_args()
    try:
        if args.verify:
            result = verify_export(args.export)
        elif args.completed_form or args.response_output:
            if not args.completed_form or not args.response_output:
                parser.error("recording requires completed-form and response-output")
            result = record_response(args.export, args.completed_form,
                                     args.response_output)
        elif args.responses or args.assembly_output:
            if not args.responses or not args.assembly_output:
                parser.error("assembly requires four responses and assembly-output")
            result = assemble_responses(args.export, args.responses,
                                        args.assembly_output)
        else:
            if not args.source:
                parser.error("export requires source")
            result = export_packets(_load_json(args.source), args.export)
    except (OSError, ValueError) as error:
        parser.error(str(error))
    print(json.dumps(result, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
