"""Fail-closed study charter for future primary human annotation.

The charter makes staffing, hand-off, governance and exception handling
explicit before labels are collected.  It is a readiness artifact only: a
valid file cannot create labels or replace independent annotators.
"""

from __future__ import annotations

from hashlib import sha256
import json
from pathlib import Path
import re
from typing import Any, Mapping


_SHA256 = re.compile(r"^[0-9a-f]{64}$")
_SCENARIO_TYPES = frozenset({"standard", "edge_case", "exception"})


def file_sha256(path: Path | str) -> str:
    return sha256(Path(path).read_bytes()).hexdigest()


def _non_empty(value: Any) -> bool:
    return isinstance(value, str) and bool(value.strip())


def _scenario_blockers(scenarios: Any) -> list[str]:
    if not isinstance(scenarios, list):
        return ["annotation scenarios must be a list"]
    blockers: list[str] = []
    seen_ids: set[str] = set()
    seen_types: set[str] = set()
    required = {
        "requirement_id",
        "scenario_type",
        "vertical_trace",
        "stimulus",
        "context",
        "annotator_response",
        "rationale",
        "acceptance_criterion",
    }
    for index, scenario in enumerate(scenarios):
        prefix = f"annotation scenario {index + 1}"
        if not isinstance(scenario, Mapping):
            blockers.append(f"{prefix} must be an object")
            continue
        missing = sorted(required - set(scenario))
        if missing:
            blockers.append(f"{prefix} is missing fields: {missing}")
            continue
        if set(scenario) != required:
            blockers.append(f"{prefix} has an invalid field set")
        requirement_id = str(scenario.get("requirement_id", "")).strip()
        if not requirement_id:
            blockers.append(f"{prefix} requires requirement_id")
        elif requirement_id in seen_ids:
            blockers.append(f"duplicate annotation requirement_id: {requirement_id}")
        seen_ids.add(requirement_id)
        scenario_type = str(scenario.get("scenario_type", "")).strip()
        if scenario_type not in _SCENARIO_TYPES:
            blockers.append(f"{prefix} has unsupported scenario_type")
        else:
            seen_types.add(scenario_type)
        for field in required - {"requirement_id", "scenario_type"}:
            if not _non_empty(scenario.get(field)):
                blockers.append(f"{prefix} requires {field}")
    for missing_type in sorted(_SCENARIO_TYPES - seen_types):
        blockers.append(f"annotation scenarios require a {missing_type} rule")
    return blockers


def evaluate_annotation_charter(
    payload: Mapping[str, Any],
    *,
    rubric_path: Path | str,
    queue_manifest_path: Path | str | None = None,
) -> dict[str, Any]:
    """Return deterministic blockers without promoting the charter to ready."""

    blockers: list[str] = []
    if payload.get("schema_version") != "annotation-study-charter/v1":
        blockers.append("unsupported annotation charter schema")
    if payload.get("status") not in {"blocked", "ready"}:
        blockers.append("annotation charter status must be blocked or ready")

    boundary = payload.get("claim_boundary", {})
    if not isinstance(boundary, Mapping):
        blockers.append("claim_boundary must be an object")
    else:
        expected_boundary = {
            "purpose": "confirmatory_h1_h2",
            "human_labels_required": True,
            "model_judgments_secondary_only": True,
            "machine_signals_hidden_from_annotators": True,
        }
        for key, expected in expected_boundary.items():
            if boundary.get(key) != expected:
                blockers.append(f"claim_boundary.{key} must be {expected!r}")

    roles = payload.get("roles", {})
    annotator_ids: list[str] = []
    adjudicator_id = ""
    if not isinstance(roles, Mapping):
        blockers.append("roles must be an object")
    else:
        raw_ids = roles.get("primary_annotator_ids")
        if isinstance(raw_ids, list):
            annotator_ids = [str(value).strip() for value in raw_ids if str(value).strip()]
        if len(annotator_ids) < 2 or len(set(annotator_ids)) != len(annotator_ids):
            blockers.append("two distinct primary annotators are required")
        adjudicator_id = str(roles.get("adjudicator_id") or "").strip()
        if not adjudicator_id:
            blockers.append("a named adjudicator is required")
        if adjudicator_id in annotator_ids:
            blockers.append("the adjudicator must be independent of primary annotators")
        if roles.get("role_independence_confirmed") is not True:
            blockers.append("role independence is not confirmed")

    artifacts = payload.get("artifacts", {})
    if not isinstance(artifacts, Mapping):
        blockers.append("artifacts must be an object")
    else:
        declared_rubric = str(artifacts.get("rubric_sha256") or "")
        actual_rubric = file_sha256(rubric_path)
        if declared_rubric != actual_rubric:
            blockers.append("rubric_sha256 does not match the supplied rubric")
        queue_sha = str(artifacts.get("queue_manifest_sha256") or "")
        if not _SHA256.fullmatch(queue_sha):
            blockers.append("queue_manifest_sha256 must be a lowercase SHA-256")
        elif queue_manifest_path is not None and queue_sha != file_sha256(queue_manifest_path):
            blockers.append("queue_manifest_sha256 does not match the supplied manifest")
        if artifacts.get("queue_roles_separated") is not True:
            blockers.append("probability-audit and diagnostic queue roles are not separated")

    process = payload.get("process", {})
    if not isinstance(process, Mapping):
        blockers.append("process must be an object")
    else:
        if process.get("training_material_excludes_study_items") is not True:
            blockers.append("training material exclusion is not confirmed")
        rehearsal_ids = process.get("rehearsal_completed_by")
        rehearsal = {
            str(value).strip()
            for value in rehearsal_ids
            if str(value).strip()
        } if isinstance(rehearsal_ids, list) else set()
        missing_rehearsals = sorted(set(annotator_ids) - rehearsal)
        if missing_rehearsals:
            blockers.append(f"annotator rehearsal is incomplete: {missing_rehearsals}")
        for field in ("feedback_channel_ref", "guideline_owner", "guideline_version"):
            if not _non_empty(process.get(field)):
                blockers.append(f"process.{field} is required")

    governance = payload.get("governance", {})
    if not isinstance(governance, Mapping):
        blockers.append("governance must be an object")
    else:
        for field in (
            "ethics_privacy_decision_ref",
            "access_control_ref",
            "participation_terms_ref",
            "retention_and_deletion_ref",
        ):
            if not _non_empty(governance.get(field)):
                blockers.append(f"governance.{field} is required")
        if governance.get("approved_for_distribution") is not True:
            blockers.append("annotation packet distribution is not approved")

    blockers.extend(_scenario_blockers(payload.get("annotation_scenarios")))
    report = {
        "schema_version": "annotation-study-charter-readiness/v1",
        "declared_status": payload.get("status"),
        "ready": not blockers,
        "blockers": sorted(set(blockers)),
        "scientific_boundary": (
            "Readiness validates declared process evidence only; it creates no labels, "
            "does not verify semantic correctness, and does not replace independent review."
        ),
    }
    if payload.get("status") == "ready" and blockers:
        raise ValueError("ready annotation charter has unresolved blockers: " + "; ".join(report["blockers"]))
    return report


def load_annotation_charter(path: Path | str) -> dict[str, Any]:
    payload = json.loads(Path(path).read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError("annotation charter must be a JSON object")
    return payload


__all__ = ["evaluate_annotation_charter", "file_sha256", "load_annotation_charter"]
