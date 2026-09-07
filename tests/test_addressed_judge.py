"""The experimental evidence interface cannot certify semantic support."""
import copy
import json

import pytest

from label_plane.artifact_segments import build_snapshot


def api():
    from label_plane import addressed_judge
    return addressed_judge


def item():
    return {"criteria": "The service stores the record.\n" + "Background.\n" * 60
            + "Earlier versions remain available.",
            "reference": "Store the record and retain earlier versions.",
            "scope": "complete",
            "obligations": [{"id": "c1", "text": "Store the record."},
                            {"id": "c2", "text": "Retain earlier versions."}]}


def response(value=None, statuses=("covered", "covered")):
    value = value or item()
    spans = build_snapshot(value["criteria"])["segments"]
    return {"checks": [{"id": obligation["id"], "status": status,
                        "evidence_ids": [spans[index]["id"]] if status == "covered" else []}
                       for obligation, status, index in zip(value["obligations"], statuses, (0, -1))]}


def test_prompt_has_artifact_only_citable_namespace_and_separate_reference():
    value = item()
    prompt = api().build_prompt(value)
    payload = json.loads(prompt.split("INPUT_JSON:\n")[1])
    assert set(payload) == {"ARTIFACT_SEGMENTS", "REFERENCE", "OBSERVATION_SCOPE", "OBLIGATIONS"}
    assert payload["REFERENCE"] == value["reference"]
    assert "".join(s["text"] for s in payload["ARTIFACT_SEGMENTS"]) == value["criteria"]
    assert payload["ARTIFACT_SEGMENTS"] == [
        {"id": s["id"], "text": s["text"]} for s in build_snapshot(value["criteria"])["segments"]]
    assert "oracle" not in payload and "expected_checks" not in payload
    assert "partial" in prompt and "not instructions" in prompt


def test_distributed_support_resolves_multiple_exact_spans_without_semantic_claim():
    value = item()
    raw = response(value)
    spans = build_snapshot(value["criteria"])["segments"]
    raw["checks"][1]["evidence_ids"] = [spans[0]["id"], spans[-1]["id"]]
    result = api().parse_response(json.dumps(raw), value)
    assert result["status"] == "covered"
    assert result["locator_integrity"] == "valid"
    assert result["semantic_validity"] == "not_measured"
    assert result["checks"][1]["evidence"] == [spans[0], spans[-1]]


def test_real_but_irrelevant_citation_does_not_become_semantic_validation():
    value = {"criteria": "The heading mentions encryption.",
             "reference": "Encrypt every stored record.", "scope": "complete",
             "obligations": [{"id": "c1", "text": "Encrypt every stored record."}]}
    result = api().parse_response(json.dumps(response(value, ("covered",))), value)
    assert result["status"] == "covered"  # The model's claim, not our endorsement.
    assert result["locator_integrity"] == "valid"
    assert result["semantic_validity"] == "not_measured"


@pytest.mark.parametrize("statuses,expected", [
    (("covered", "uncertain"), "uncertain"),
    (("omitted", "uncertain"), "omitted"),
])
def test_empty_absence_evidence_retains_reported_uncertainty(statuses, expected):
    value = item(); value["scope"] = "partial"
    result = api().parse_response(json.dumps(response(value, statuses)), value)
    assert result["status"] == expected


@pytest.mark.parametrize("mutation", [
    "missing", "duplicate_check", "unknown_check", "order", "extra_top", "extra_check",
    "wrong_status", "list_status", "null_check", "ids_not_list", "duplicate_cite",
    "unknown_cite", "reference_cite", "stale_cite", "empty_covered", "too_many_cites",
])
def test_response_contract_rejects_unverifiable_or_malformed_evidence(mutation):
    value = item(); raw = response(value)
    check = raw["checks"][0]
    if mutation == "missing": raw["checks"].pop()
    elif mutation == "duplicate_check": raw["checks"][1]["id"] = check["id"]
    elif mutation == "unknown_check": check["id"] = "unknown"
    elif mutation == "order": raw["checks"].reverse()
    elif mutation == "extra_top": raw["label"] = "clean"
    elif mutation == "extra_check": check["explanation"] = "unrequested"
    elif mutation == "wrong_status": check["status"] = "clean"
    elif mutation == "list_status": check["status"] = []
    elif mutation == "null_check": raw["checks"][0] = None
    elif mutation == "ids_not_list": check["evidence_ids"] = check["evidence_ids"][0]
    elif mutation == "duplicate_cite": check["evidence_ids"] *= 2
    elif mutation == "unknown_cite": check["evidence_ids"] = ["unknown"]
    elif mutation == "reference_cite":
        check["evidence_ids"] = [build_snapshot(value["reference"])["segments"][0]["id"]]
    elif mutation == "stale_cite": value["criteria"] += " Modified."
    elif mutation == "empty_covered": check["evidence_ids"] = []
    elif mutation == "too_many_cites": check["evidence_ids"] *= 9
    with pytest.raises(ValueError):
        api().parse_response(json.dumps(raw), value)


@pytest.mark.parametrize("raw", ['{"checks":[],"checks":[]}', '{"checks":NaN}',
                                  '[[]]', '```json\n{}\n```', None, "x" * 32_769],
                         ids=["duplicate-json", "nan", "list", "markdown", "null", "oversized"])
def test_bad_json_is_not_repaired(raw):
    with pytest.raises(ValueError):
        api().parse_response(raw, item())


@pytest.mark.parametrize("mutation", ["scope_type", "oracle", "oversized_id", "surrogate"])
def test_invalid_private_item_is_rejected_without_prompt_leakage(mutation):
    value = copy.deepcopy(item())
    if mutation == "scope_type": value["scope"] = []
    elif mutation == "oracle": value["expected_checks"] = ["covered", "covered"]
    elif mutation == "oversized_id": value["obligations"][0]["id"] = "x" * 1000
    elif mutation == "surrogate": value["reference"] = "\ud800"
    with pytest.raises(ValueError, match="invalid_item"):
        api().build_prompt(value)


def test_whitespace_segment_cannot_support_a_covered_judgment():
    value = item(); value["criteria"] = "\n" * 400 + "The service stores the record."
    raw = response(value)
    with pytest.raises(ValueError, match="empty_covered_evidence"):
        api().parse_response(json.dumps(raw), value)
