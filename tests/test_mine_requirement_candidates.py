from __future__ import annotations

import subprocess
from pathlib import Path

import pytest

from scripts import mine_requirement_candidates as mine


def _git(repo: Path, *args: str) -> None:
    subprocess.run(["git", "-C", str(repo), *args], check=True, capture_output=True)


def _commit(repo: Path, path: str, text: str, date: str) -> None:
    file = repo / path
    file.parent.mkdir(parents=True, exist_ok=True)
    file.write_text(text)
    _git(repo, "add", path)
    env = {"GIT_COMMITTER_DATE": f"{date}T12:00:00", "GIT_AUTHOR_DATE": f"{date}T12:00:00"}
    subprocess.run(["git", "-C", str(repo), "commit", "-q", "-m", f"edit {path}"], check=True,
                   env={**env, "PATH": "/usr/bin:/bin", "HOME": str(repo)}, capture_output=True)


@pytest.fixture()
def repo(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    repo = tmp_path / "demo"
    repo.mkdir()
    _git(repo, "init", "-q")
    _git(repo, "config", "user.email", "t@example.org")
    _git(repo, "config", "user.name", "t")
    monkeypatch.setitem(mine.PROJECTS, "demo", {"paths": ["docs"], "exclude": []})
    _commit(repo, "docs/tasks.md", "Closing a task hides it from the board.\n", "2025-02-01")
    return repo


def test_an_added_rule_sentence_is_a_candidate(repo: Path) -> None:
    _commit(repo, "docs/tasks.md",
            "Closing a task hides it from the board.\nOpen subtasks are automatically marked done.\n",
            "2025-03-01")
    found = mine.candidates("demo", repo)
    assert len(found) == 1
    row = found[0]
    assert row["kind"] == "addition"
    assert row["added"] == ["Open subtasks are automatically marked done."]
    assert "automatically" in row["strong_cue_delta"]


def test_wording_polish_and_out_of_scope_paths_are_excluded(repo: Path) -> None:
    _commit(repo, "docs/tasks.md", "Closing a task hides it from the boards.\n", "2025-03-01")
    _commit(repo, "docs/install/setup.md", "You must install PostgreSQL 15 or newer.\n", "2025-03-02")
    _commit(repo, "docs/tasks.md", "Closing a task hides it from the boards. Images: :width: 50%\n", "2025-03-03")
    assert mine.candidates("demo", repo) == []


def test_version_numbers_are_not_rule_quantities(repo: Path) -> None:
    _commit(repo, "docs/tasks.md", "Closing a task hides it from the board in v2.1.0.\n", "2025-03-01")
    assert mine.candidates("demo", repo) == []


def test_screening_sample_is_capped_and_reproducible() -> None:
    rows = [{"project": "kanboard", "candidate_id": f"rc-{i:03d}"} for i in range(50)]
    first = mine.screening_sample(rows)
    assert len(first) == mine.SCREEN_CAP_PER_PROJECT
    assert first == mine.screening_sample(rows)
