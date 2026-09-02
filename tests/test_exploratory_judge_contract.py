import json
from dataclasses import FrozenInstanceError

import pytest

from label_plane.exploratory_judge import (
    JUDGE_SCHEMA_VERSION,
    JudgeRequest,
    ReferenceConstraint,
    build_judge_prompt,
    consolidate_two_judges,
    parse_judge_response,
    serialize_judge_request,
    validate_judge_request,
)


def request() -> JudgeRequest:
    return JudgeRequest(
        occurrence_id="occ-opaque-17",
        generated_acceptance_criteria="Given a delayed order, the system shows its status.",
        reference_constraints=(
            ReferenceConstraint("c-opaque-a", "The status is shown when the order is delayed."),
            ReferenceConstraint("c-opaque-b", "The requirement states how delay is determined."),
        ),
    )


def response(*, label="moderate", constraint_ids=None, confidence=0.75):
    ids = constraint_ids or ["c-opaque-a", "c-opaque-b"]
    return {
        "schema_version": JUDGE_SCHEMA_VERSION,
        "occurrence_id": "occ-opaque-17",
        "label": label,
        "constraint_assessments": [
            {"constraint_id": value, "status": "covered", "evidence": "status is shown"}
            for value in ids
        ],
        "confidence": confidence,
        "rationale": "The criteria operationalize the supplied constraints.",
        "evidence": "The output states the observable status behavior.",
    }


def test_serialized_request_has_only_blinded_public_inputs():
    payload = serialize_judge_request(request())
    payload["reference_constraints"][0]["text"] = "A missing status is visible to the user."
    validate_judge_request(payload)
    assert set(payload) == {
        "schema_version", "occurrence_id", "generated_acceptance_criteria", "reference_constraints"
    }

    for forbidden in (
        "target_family", "variant", "provider_id", "model_id", "oracle_result", "detector_output",
        "checkpoint", "T4", "source_label", "credentials",
    ):
        leaked = dict(payload)
        leaked[forbidden] = "incompleteness_missing_condition"
        with pytest.raises(ValueError):
            validate_judge_request(leaked)

    validate_judge_request(payload)  # ordinary language remains allowed


def test_prompt_names_visible_inputs_and_explains_constraint_coverage_without_hidden_family():
    prompt = build_judge_prompt(request())
    assert "occ-opaque-17" in prompt
    assert "c-opaque-a" in prompt
    assert "operationalize" in prompt.lower()
    assert "target_family" not in prompt
    assert "incompleteness_missing_condition" not in prompt


def test_request_and_response_representations_are_immutable():
    item = request()
    with pytest.raises(FrozenInstanceError):
        item.occurrence_id = "changed"
    parsed = parse_judge_response(json.dumps(response()), request())
    with pytest.raises(FrozenInstanceError):
        parsed.label = "clean"


@pytest.mark.parametrize(
    "mutate",
    [
        lambda value: value.update(extra="nope"),
        lambda value: value.pop("label"),
        lambda value: value.update(label="smelly"),
        lambda value: value.update(confidence=float("nan")),
        lambda value: value.update(confidence=float("inf")),
        lambda value: value.update(constraint_assessments=response()["constraint_assessments"][:1]),
        lambda value: value.update(constraint_assessments=response()["constraint_assessments"] + [response()["constraint_assessments"][0]]),
        lambda value: value["constraint_assessments"].__setitem__(0, {"constraint_id": "c-opaque-a", "status": "unknown", "evidence": "x"}),
        lambda value: value.update(rationale="x" * 10001),
    ],
)
def test_response_parser_rejects_malformed_or_unsafe_public_responses(mutate):
    payload = response()
    mutate(payload)
    raw = json.dumps(payload, allow_nan=True)
    with pytest.raises(ValueError):
        parse_judge_response(raw, request())


def test_parser_rejects_invalid_json_and_does_not_echo_private_values():
    with pytest.raises(ValueError) as error:
        parse_judge_response("not-json incompleteness_missing_condition", request())
    assert "incompleteness_missing_condition" not in str(error.value)


def test_exact_agreement_is_consensus_and_disagreement_is_uncertain():
    first = parse_judge_response(json.dumps(response(label="moderate")), request())
    same = parse_judge_response(json.dumps(response(label="moderate")), request())
    different = parse_judge_response(json.dumps(response(label="severe")), request())

    agreed = consolidate_two_judges(first, same)
    assert agreed.label == "moderate"
    assert agreed.consensus is True
    assert not hasattr(agreed, "adjudicator")
    assert not hasattr(agreed, "majority")

    disagreed = consolidate_two_judges(first, different)
    assert disagreed.label == "uncertain"
    assert disagreed.consensus is False
