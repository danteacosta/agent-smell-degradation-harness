"""Strict, provider-neutral contract for blinded acceptance-criteria judges."""

from __future__ import annotations

from dataclasses import dataclass
import json
import math
import re
from typing import Any, Mapping


JUDGE_SCHEMA_VERSION = "acceptance-criteria-llm-judge/v1"
_REQUEST_FIELDS = frozenset(
    {"schema_version", "occurrence_id", "generated_acceptance_criteria", "reference_constraints"}
)
_RESPONSE_FIELDS = frozenset(
    {
        "schema_version",
        "occurrence_id",
        "label",
        "constraint_assessments",
        "confidence",
        "rationale",
        "evidence",
    }
)
_ASSESSMENT_FIELDS = frozenset({"constraint_id", "status", "evidence"})
_LABELS = frozenset({"clean", "minor", "moderate", "severe", "not_visible"})
_STATUSES = frozenset({"covered", "omitted", "uncertain"})
_FORBIDDEN_KEYS = frozenset(
    {
        "target_family",
        "variant",
        "provider",
        "provider_id",
        "model",
        "model_id",
        "oracle",
        "oracle_result",
        "detector",
        "detector_output",
        "checkpoint",
        "checkpoint_id",
        "t4",
        "source_label",
        "source_labels",
        "credentials",
        "api_key",
        "secret",
    }
)
_FORBIDDEN_VALUES = frozenset({"incompleteness_missing_condition"})
_ID_PATTERN = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_.:-]{0,127}$")
_MAX_OCCURRENCE_ID = 128
_MAX_CRITERIA = 20_000
_MAX_CONSTRAINT_TEXT = 4_000
_MAX_EVIDENCE = 2_000
_MAX_RATIONALE = 10_000


@dataclass(frozen=True, slots=True)
class ReferenceConstraint:
    constraint_id: str
    text: str


@dataclass(frozen=True, slots=True)
class JudgeRequest:
    occurrence_id: str
    generated_acceptance_criteria: str
    reference_constraints: tuple[ReferenceConstraint, ...]
    schema_version: str = JUDGE_SCHEMA_VERSION


@dataclass(frozen=True, slots=True)
class ConstraintAssessment:
    constraint_id: str
    status: str
    evidence: str


@dataclass(frozen=True, slots=True)
class JudgeResponse:
    occurrence_id: str
    label: str
    constraint_assessments: tuple[ConstraintAssessment, ...]
    confidence: float
    rationale: str
    evidence: str
    schema_version: str = JUDGE_SCHEMA_VERSION


@dataclass(frozen=True, slots=True)
class ConsolidatedJudgment:
    occurrence_id: str
    label: str
    consensus: bool
    schema_version: str = JUDGE_SCHEMA_VERSION


def _reject_private_metadata(value: Any) -> None:
    if isinstance(value, Mapping):
        for key, nested in value.items():
            if str(key).strip().lower() in _FORBIDDEN_KEYS:
                raise ValueError("judge payload contains forbidden metadata")
            _reject_private_metadata(nested)
    elif isinstance(value, (list, tuple)):
        for nested in value:
            _reject_private_metadata(nested)
    elif isinstance(value, str) and value in _FORBIDDEN_VALUES:
        raise ValueError("judge payload contains forbidden metadata")


def _bounded_text(value: Any, *, maximum: int, required: bool = True) -> str:
    if not isinstance(value, str) or len(value) > maximum or (required and not value.strip()):
        raise ValueError("judge payload contains invalid text")
    return value


def _opaque_id(value: Any, *, occurrence: bool = False) -> str:
    maximum = _MAX_OCCURRENCE_ID if occurrence else 128
    if not isinstance(value, str) or not value.strip() or len(value) > maximum:
        raise ValueError("judge payload contains invalid opaque identifier")
    if not occurrence and not _ID_PATTERN.fullmatch(value):
        raise ValueError("judge payload contains invalid opaque identifier")
    return value


def validate_judge_request(payload: Mapping[str, Any] | JudgeRequest) -> JudgeRequest:
    """Validate and normalize the exact serialized request boundary."""

    if isinstance(payload, JudgeRequest):
        payload = {
            "schema_version": payload.schema_version,
            "occurrence_id": payload.occurrence_id,
            "generated_acceptance_criteria": payload.generated_acceptance_criteria,
            "reference_constraints": [
                {"constraint_id": item.constraint_id, "text": item.text}
                for item in payload.reference_constraints
            ],
        }
    if not isinstance(payload, Mapping) or set(payload) != _REQUEST_FIELDS:
        raise ValueError("judge request has an invalid field set")
    _reject_private_metadata(payload)
    if payload["schema_version"] != JUDGE_SCHEMA_VERSION:
        raise ValueError("judge request has an unsupported schema")
    occurrence_id = _opaque_id(payload["occurrence_id"], occurrence=True)
    criteria = _bounded_text(payload["generated_acceptance_criteria"], maximum=_MAX_CRITERIA)
    constraints = payload["reference_constraints"]
    if not isinstance(constraints, list) or not constraints:
        raise ValueError("judge request requires reference constraints")
    parsed: list[ReferenceConstraint] = []
    ids: set[str] = set()
    for item in constraints:
        if not isinstance(item, Mapping) or set(item) != {"constraint_id", "text"}:
            raise ValueError("judge request contains an invalid constraint")
        constraint_id = _opaque_id(item["constraint_id"])
        if constraint_id in ids:
            raise ValueError("judge request contains duplicate constraint IDs")
        ids.add(constraint_id)
        parsed.append(ReferenceConstraint(constraint_id, _bounded_text(item["text"], maximum=_MAX_CONSTRAINT_TEXT)))
    return JudgeRequest(occurrence_id, criteria, tuple(parsed))


def serialize_judge_request(request: JudgeRequest) -> dict[str, Any]:
    validated = validate_judge_request(request)
    return {
        "schema_version": validated.schema_version,
        "occurrence_id": validated.occurrence_id,
        "generated_acceptance_criteria": validated.generated_acceptance_criteria,
        "reference_constraints": [
            {"constraint_id": item.constraint_id, "text": item.text}
            for item in validated.reference_constraints
        ],
    }


def build_judge_prompt(request: JudgeRequest) -> str:
    validated = validate_judge_request(request)
    constraints = "\n".join(
        f"- {item.constraint_id}: {item.text}" for item in validated.reference_constraints
    )
    return (
        "You are an independent judge of generated acceptance criteria.\n"
        "Use only the visible occurrence ID, generated criteria, and supplied reference constraints. "
        "For each constraint, assess whether the criteria cover it, omit it, or leave it uncertain. "
        "Coverage means the criteria operationalize the constraint with an observable behavior or testable condition. "
        "Do not infer any hidden defect family or private metadata.\n\n"
        f"Occurrence ID: {validated.occurrence_id}\n"
        f"Generated acceptance criteria:\n{validated.generated_acceptance_criteria}\n\n"
        f"Reference constraints:\n{constraints}\n\n"
        "Return exactly the JSON fields specified by the rubric."
    )


def parse_judge_response(raw: str | bytes, request: JudgeRequest) -> JudgeResponse:
    """Parse a response without adding provider or model identity."""

    validated_request = validate_judge_request(request)
    try:
        payload = json.loads(raw)
    except (TypeError, ValueError, json.JSONDecodeError) as exc:
        raise ValueError("judge response is not valid JSON") from exc
    if not isinstance(payload, Mapping) or set(payload) != _RESPONSE_FIELDS:
        raise ValueError("judge response has an invalid field set")
    if (
        payload["schema_version"] != JUDGE_SCHEMA_VERSION
        or payload["occurrence_id"] != validated_request.occurrence_id
    ):
        raise ValueError("judge response does not match the request")
    if not isinstance(payload["label"], str) or payload["label"] not in _LABELS:
        raise ValueError("judge response contains an invalid label")
    assessments = payload["constraint_assessments"]
    if not isinstance(assessments, list) or len(assessments) != len(validated_request.reference_constraints):
        raise ValueError("judge response has an invalid constraint cardinality")
    expected = {item.constraint_id for item in validated_request.reference_constraints}
    parsed: list[ConstraintAssessment] = []
    for item in assessments:
        if not isinstance(item, Mapping) or set(item) != _ASSESSMENT_FIELDS:
            raise ValueError("judge response contains an invalid assessment")
        identifier = item["constraint_id"]
        if not isinstance(identifier, str) or identifier not in expected or any(
            assessment.constraint_id == identifier for assessment in parsed
        ):
            raise ValueError("judge response contains invalid or duplicate constraint IDs")
        status = item["status"]
        if not isinstance(status, str) or status not in _STATUSES:
            raise ValueError("judge response contains an invalid constraint status")
        parsed.append(
            ConstraintAssessment(
                identifier,
                status,
                _bounded_text(item["evidence"], maximum=_MAX_EVIDENCE, required=False),
            )
        )
    if {item.constraint_id for item in parsed} != expected:
        raise ValueError("judge response is missing a constraint ID")
    confidence = payload["confidence"]
    if (
        isinstance(confidence, bool)
        or not isinstance(confidence, (int, float))
        or not math.isfinite(confidence)
        or not 0 <= confidence <= 1
    ):
        raise ValueError("judge response contains invalid confidence")
    rationale = _bounded_text(payload["rationale"], maximum=_MAX_RATIONALE)
    evidence = _bounded_text(payload["evidence"], maximum=_MAX_EVIDENCE, required=False)
    return JudgeResponse(
        validated_request.occurrence_id,
        payload["label"],
        tuple(parsed),
        float(confidence),
        rationale,
        evidence,
    )


def consolidate_two_judges(first: JudgeResponse, second: JudgeResponse) -> ConsolidatedJudgment:
    if not isinstance(first, JudgeResponse) or not isinstance(second, JudgeResponse):
        raise ValueError("consolidation requires two validated judge responses")
    if (
        first.schema_version != JUDGE_SCHEMA_VERSION
        or second.schema_version != JUDGE_SCHEMA_VERSION
        or first.occurrence_id != second.occurrence_id
    ):
        raise ValueError("judge responses do not match")
    if tuple(item.constraint_id for item in first.constraint_assessments) != tuple(
        item.constraint_id for item in second.constraint_assessments
    ):
        raise ValueError("judge responses do not match")
    agrees = first.label == second.label
    return ConsolidatedJudgment(first.occurrence_id, first.label if agrees else "uncertain", agrees)
