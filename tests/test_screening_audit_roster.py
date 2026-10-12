import json

import pytest

openpyxl = pytest.importorskip("openpyxl")

from scripts import screening_audit_sample as sas


def audit_sheet(tmp_path, records):
    workbook = openpyxl.Workbook()
    sheet = workbook.active
    sheet.title = "triagem"
    sheet.append(["id", "decisao", "motivo", "regra_alvo"])
    for record in records:
        sheet.append(record)
    path = tmp_path / "audit.xlsx"
    workbook.save(path)
    return path


@pytest.mark.parametrize("decision", ["exclude", None])
def test_rejects_candidate_outside_frozen_audit_sample_even_when_unanswered(tmp_path, decision):
    selected = set(json.loads(sas.MANIFEST.read_text())["candidate_ids"])
    candidate_id = next(item["candidate_id"] for item in sas.load_options()
                        if item["candidate_id"] not in selected)
    path = audit_sheet(tmp_path, [(candidate_id, decision, "no_rule_change", None)])
    with pytest.raises(ValueError, match="outside frozen audit sample"):
        sas.score(path)


def test_rejects_unknown_candidate_before_computing_agreement(tmp_path):
    path = audit_sheet(tmp_path, [("unknown-candidate", "exclude", "no_rule_change", None)])
    with pytest.raises(ValueError, match="outside frozen audit sample"):
        sas.score(path)


@pytest.mark.parametrize("decisions", [("exclude", "exclude"), ("exclude", None), (None, None)])
def test_rejects_duplicate_candidate_even_when_rows_are_unanswered(tmp_path, decisions):
    candidate_id = json.loads(sas.MANIFEST.read_text())["candidate_ids"][0]
    path = audit_sheet(tmp_path, [(candidate_id, decisions[0], "no_rule_change", None),
                                 (candidate_id, decisions[1], "no_rule_change", None)])
    with pytest.raises(ValueError, match="duplicate audit candidate"):
        sas.score(path)


def test_accepts_partial_audit_without_counting_unanswered_or_empty_rows(tmp_path):
    candidate_ids = json.loads(sas.MANIFEST.read_text())["candidate_ids"]
    path = audit_sheet(tmp_path, [(candidate_ids[0], "exclude", "no_rule_change", None),
                                 (candidate_ids[1], None, None, None),
                                 (None, None, None, None)])
    result = sas.score(path)
    assert result["answered"] == 1
    assert result["of"] == 73
    assert result["malformed"] == []
