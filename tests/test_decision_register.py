"""Structural guard for the pending-human-decisions register (non-confirmatory)."""
from __future__ import annotations

from pathlib import Path

REG = Path(__file__).resolve().parents[1] / "docs" / "preregistration" / "2026-11-07-pending-human-decisions.md"


def _rows() -> list[list[str]]:
    rows = []
    for line in REG.read_text(encoding="utf-8").splitlines():
        if line.startswith("| ") and not line.startswith("| ---") and line[2:3].isdigit():
            rows.append([c.strip() for c in line.strip().strip("|").split("|")])
    return rows


def test_register_states_nothing_is_adopted() -> None:
    assert "Nothing below is adopted" in REG.read_text(encoding="utf-8")


def test_every_row_has_recommendation_and_decider() -> None:
    rows = _rows()
    assert len(rows) >= 10
    for cells in rows:
        assert len(cells) == 8, cells[:2]
        assert cells[5] and cells[7], cells[:2]


def test_row_numbers_are_unique_and_consecutive() -> None:
    nums = [int(r[0]) for r in _rows()]
    assert nums == list(range(1, len(nums) + 1))


MATRIX = Path(__file__).resolve().parents[1] / "docs" / "research" / "literature-matrix.md"


def test_raised_by_dates_resolve_to_matrix_entries() -> None:
    """Each dated 'Raised by' reference must name a dated heading in the matrix (traceability)."""
    import re

    headings = [l for l in MATRIX.read_text(encoding="utf-8").splitlines() if l.startswith("## ")]
    for cells in _rows():
        for date in re.findall(r"20\d\d-\d\d-\d\d", cells[2]):
            assert any(date in h for h in headings), (cells[0], date)


def test_register_arxiv_ids_are_present_in_matrix() -> None:
    """arXiv identifiers cited by the register must have been read and recorded in the matrix."""
    import re

    matrix = MATRIX.read_text(encoding="utf-8")
    for aid in set(re.findall(r"\b2\d{3}\.\d{4,5}\b", REG.read_text(encoding="utf-8"))):
        assert aid in matrix, aid
