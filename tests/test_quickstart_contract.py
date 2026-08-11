from __future__ import annotations

import os
import subprocess
from pathlib import Path


ROOT = Path(__file__).parents[1]


def test_make_targets_use_project_interpreter_without_global_pytest() -> None:
    makefile = (ROOT / "Makefile").read_text(encoding="utf-8")
    assert "$(PYTHON) -m pytest" in makefile
    assert "\n\tpytest" not in makefile
    env = {**os.environ, "PYTHON": os.environ.get("PYTHON", "python3"), "PATH": "/usr/bin:/bin"}
    result = subprocess.run(["make", "-n", "test", "eval", "simulate", "gate"], cwd=ROOT, env=env, text=True, capture_output=True)
    assert result.returncode == 0
    assert "-m pytest" in result.stdout
    assert "\npython -m eval" not in result.stdout
    assert "\npytest" not in result.stdout


def test_readme_does_not_claim_empty_wheelhouse_bootstrap() -> None:
    readme = (ROOT / "README.md").read_text(encoding="utf-8")
    assert "one-time acquisition" in readme
    assert "PYTHON=.venv/bin/python make all" in readme
