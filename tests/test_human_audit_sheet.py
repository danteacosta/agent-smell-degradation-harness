import json
from pathlib import Path

import pytest

openpyxl = pytest.importorskip("openpyxl")

from scripts import human_audit_sheet as has  # noqa: E402

SHEET = has.ROOT / "data/human-audit/audit-sheet-20261005.xlsx"


def test_published_sheet_is_blind_and_complete():
    wb = openpyxl.load_workbook(SHEET, read_only=True)
    cue = list(wb["context_cue"].iter_rows(values_only=True))
    hist = list(wb["historico"].iter_rows(values_only=True))
    assert len(cue) == 47 and len(hist) == 41
    text = json.dumps([*cue, *hist], ensure_ascii=False, default=str)
    for leak in ("gpt-", "\"vote\"", "decided_by", "tiebreaker", "target_only_failure"):
        assert leak not in text
    assert all(row[-1] is None for row in cue[1:]) and all(row[-1] is None for row in hist[1:])


def test_score_round_trip(tmp_path: Path):
    filled = tmp_path / "filled.xlsx"
    has.build(filled)
    wb = openpyxl.load_workbook(filled)
    cues = {r["case"]: r["context_cue"] for r in json.loads(has.CUE_RESULTS.read_text())["rows"]}
    ws = wb["context_cue"]
    header = [c.value for c in ws[1]]
    for row in ws.iter_rows(min_row=2):
        row[header.index("context_cue")].value = "sim" if cues[row[1].value] == 1 else "não"
        if cues[row[1].value] == 1:
            row[header.index("citacao")].value = row[header.index("texto")].value.splitlines()[0]
    wb.save(filled)
    result = has.score(filled)
    assert result["context_cue"]["agreement"] == 1.0 and result["context_cue"]["disagreements"] == []
    assert result["historical"]["answered"] == 0
    with pytest.raises(FileExistsError):
        has.build(filled)


def fill_answer(sheet_path, title, values):
    wb = openpyxl.load_workbook(sheet_path)
    ws = wb[title]
    header = [c.value for c in ws[1]]
    case = ws.cell(2, 2).value
    for field, value in values.items():
        ws.cell(2, header.index(field) + 1).value = value
    wb.save(sheet_path)
    return case


@pytest.mark.parametrize("title,answers,field", [
    ("historico", {"funcionalidade_documentada": "não", "status_da_regra": "vague"}, "status_da_regra"),
    ("historico", {"funcionalidade_documentada": "maybe", "status_da_regra": "absent"}, "funcionalidade_documentada"),
    ("context_cue", {"context_cue": "maybe"}, "context_cue"),
])
def test_invalid_answer_label_is_rejected(tmp_path, title, answers, field):
    sheet = tmp_path / "invalid.xlsx"
    has.build(sheet)
    case = fill_answer(sheet, title, answers)
    with pytest.raises(ValueError, match=f"{case}.*{field}"):
        has.score(sheet)


@pytest.mark.parametrize("quote", [None, "This passage is not in the supplied documentation."])
@pytest.mark.parametrize("title,answers,field", [
    ("context_cue", {"context_cue": "sim"}, "citacao"),
    ("historico", {"funcionalidade_documentada": "sim", "status_da_regra": "absent"}, "citacao_funcionalidade"),
    ("historico", {"funcionalidade_documentada": "não", "status_da_regra": "vaguer"}, "citacao_regra"),
])
def test_positive_claims_require_literal_evidence(tmp_path, quote, title, answers, field):
    sheet = tmp_path / "unsupported.xlsx"
    has.build(sheet)
    case = fill_answer(sheet, title, {**answers, field: quote})
    with pytest.raises(ValueError, match=f"{case}.*{field}"):
        has.score(sheet)



def test_literal_historical_evidence_is_scored(tmp_path):
    sheet = tmp_path / "supported.xlsx"
    has.build(sheet)
    wb = openpyxl.load_workbook(sheet)
    text = wb["historico"].cell(2, 5).value
    quote = "  " + "\n".join(text.split()[:8]) + "  "
    fill_answer(sheet, "historico", {
        "funcionalidade_documentada": "sim", "status_da_regra": "vaguer",
        "citacao_funcionalidade": quote, "citacao_regra": quote,
    })
    assert has.score(sheet)["historical"]["answered"] == 1
