from __future__ import annotations

import json
from pathlib import Path

from scripts import omission_bench as bench
from scripts import openproject_invalid_remaining_pilot as openproject


def test_build_materializes_every_case_and_the_reference_leaderboard(tmp_path: Path) -> None:
    result = bench.build(tmp_path / "bench")
    assert result == {"cases": 7, "rows": 42}
    manifest = json.loads((tmp_path / "bench/manifest.json").read_text())
    for case in manifest["cases"]:
        for arm in bench.ARMS:
            assert (tmp_path / "bench/cases" / case["case"] / f"{arm}.prompt.txt").is_file()
    board = (tmp_path / "bench/LEADERBOARD.md").read_text()
    assert "| gpt-5.6-luna | 1/21 | 0/21 | 13/21 | 5/7 |" in board
    assert "| gpt-5.6-sol | 0/21 | 0/21 | 15/21 | 5/7 |" in board


def test_score_checks_the_scaffold_before_running_the_oracle(tmp_path: Path) -> None:
    pages = tmp_path / "pages"
    pages.mkdir()
    scaffold = (openproject.FIXTURE / "page.html").read_text()
    valid = scaffold.replace(openproject.MARKER, "app.onSave(v=>app.persist(v));")
    (pages / "openproject-invalid-remaining__C__1.html").write_text(valid)
    (pages / "openproject-invalid-remaining__A__1.html").write_text("<html>changed scaffold</html>")
    seen = []

    def fake(case, html, out):
        seen.append(html.read_text())
        return {"category": "target_only_failure"}

    summary = bench.score(pages, tmp_path / "results", executor=fake)
    assert summary == {"openproject-invalid-remaining/A": {"invalid_output": 1},
                       "openproject-invalid-remaining/C": {"target_only_failure": 1}}
    assert len(seen) == 1
