from __future__ import annotations

from pathlib import Path

import pytest

from scripts.prepare_natural_v8 import prepare, select_rows


def _row(source_row: int, project: str) -> dict[str, str]:
    return {"_source_row": str(source_row), "File": project}


def test_select_rows_excludes_previous_clean_controls() -> None:
    rows = [_row(index, "2007-eirene_fun_7-2.xml") for index in range(1, 7)]

    selected = select_rows(rows, count=2, exclude_source_rows={1, 2})

    assert [row["_source_row"] for row in selected] == ["3", "4"]


def test_prepare_rejects_private_text_output_inside_repository(tmp_path) -> None:
    repository_root = Path(__file__).resolve().parents[1]

    with pytest.raises(ValueError, match="outside the repository"):
        prepare(
            Path("/private/tmp/nonexistent-arta-workbook.xlsx"),
            repository_root / "data" / "private-cases.jsonl",
            tmp_path / "selection-manifest.json",
        )
