import json

import pytest

openpyxl = pytest.importorskip("openpyxl")

from scripts import screening_audit_sample as sas  # noqa: E402


def test_published_sample_is_blind_and_twenty_percent():
    manifest = json.loads(sas.MANIFEST.read_text())
    assert manifest["population"] == 365 and manifest["sample"] == 73 == len(set(manifest["candidate_ids"]))
    assert not {"admit", "exclude", "panel"} & set(json.dumps(manifest).split('"'))
    rows = list(openpyxl.load_workbook(sas.SHEET, read_only=True)["triagem"].iter_rows(values_only=True))
    assert len(rows) == 74 and all(r[6:] == (None,) * 4 for r in rows[1:])
    text = json.dumps(rows, ensure_ascii=False, default=str)
    for leak in ("gpt-", "consensus", "tiebreaker", "target_rule", "pass_observation"):
        assert leak not in text
    assert {r[1] for r in rows[1:]} == set(manifest["candidate_ids"])


def test_allocation_is_proportional_with_one_per_stratum():
    alloc = sas.allocate({"a": 100, "b": 50, "c": 1}, 30)
    assert sum(alloc.values()) == 30 and alloc["c"] == 1 and alloc["a"] > alloc["b"]


def test_score_round_trip(tmp_path):
    panel = {i["candidate_id"]: i["panel"] for i in sas.load_options()}
    wb = openpyxl.load_workbook(sas.SHEET)
    ws = wb["triagem"]
    for n, row in enumerate(ws.iter_rows(min_row=2)):
        d = panel[row[1].value]
        if n == 0:
            d = "exclude" if d == "admit" else "admit"
        row[6].value = d
        row[7].value = "admit" if d == "admit" else "no_rule_change"
    filled = tmp_path / "filled.xlsx"
    wb.save(filled)
    result = sas.score(filled)
    assert result["answered"] == 73 and result["malformed"] == [] and len(result["disagreements"]) == 1
