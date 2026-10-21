"""Guard the literature matrix against duplicate scored entries.

Policy (docs/research/literature-matrix.md header): deduplicate by DOI, then by
normalized title. Pending-reading tables carry no credibility score and are
therefore excluded; a source may be scored once.
"""
from __future__ import annotations

import re
from collections import defaultdict
from pathlib import Path

MATRIX = Path(__file__).resolve().parents[1] / "docs" / "research" / "literature-matrix.md"
ID = re.compile(r"doi\.org/(10\.[^\s)\]]+)|arxiv\.org/(?:abs|pdf|html)/(\d{4}\.\d{4,5})")
SCORE = re.compile(r"^\s*\**\s*\d+(?:\.\d+)?\s*(?:/\s*10)?")


def scored_rows() -> list[list[str]]:
    rows = []
    for line in MATRIX.read_text(encoding="utf-8").splitlines():
        if not line.startswith("| ") or line.startswith("| ---"):
            continue
        cells = [c.strip() for c in line.strip().strip("|").split("|")]
        if len(cells) >= 4 and SCORE.match(cells[-1]):
            rows.append(cells)
    return rows


def test_matrix_has_scored_rows() -> None:
    assert len(scored_rows()) > 50


def test_no_source_is_scored_twice() -> None:
    seen: dict[str, list[str]] = defaultdict(list)
    for cells in scored_rows():
        for doi, arxiv in ID.findall(cells[0]):
            seen[(doi or arxiv).rstrip(".,;").lower()].append(cells[0][:60])
    dupes = {k: v for k, v in seen.items() if len(v) > 1}
    assert not dupes, f"sources scored more than once: {dupes}"
