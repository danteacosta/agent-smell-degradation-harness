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
    wb.save(filled)
    result = has.score(filled)
    assert result["context_cue"]["agreement"] == 1.0 and result["context_cue"]["disagreements"] == []
    assert result["historical"]["answered"] == 0
    with pytest.raises(FileExistsError):
        has.build(filled)
