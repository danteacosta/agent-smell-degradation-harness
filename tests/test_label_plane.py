from __future__ import annotations

import ast
from pathlib import Path
import tomllib

from eval.mutation import score_test_gen_mutation as eval_score_test_gen_mutation
from eval.oracles import score_artifact as eval_score_artifact


def test_label_plane_reexports_existing_evaluation_scorers():
    from label_plane import score_artifact, score_test_gen_mutation

    assert score_artifact is eval_score_artifact
    assert score_test_gen_mutation is eval_score_test_gen_mutation


def test_production_scorer_callers_depend_on_label_plane():
    repo_root = Path(__file__).resolve().parents[1]
    for relative_path in ("eval/runner.py", "wedge/check.py"):
        tree = ast.parse((repo_root / relative_path).read_text(encoding="utf-8"))
        imports = [
            node
            for node in ast.walk(tree)
            if isinstance(node, ast.ImportFrom) and node.module == "label_plane"
        ]
        assert len(imports) == 1, relative_path
        assert {alias.name for alias in imports[0].names} == {
            "score_artifact",
            "score_test_gen_mutation",
        }


def test_label_plane_is_included_in_distribution_packages():
    repo_root = Path(__file__).resolve().parents[1]
    pyproject = tomllib.loads((repo_root / "pyproject.toml").read_text(encoding="utf-8"))

    assert "label_plane*" in pyproject["tool"]["setuptools"]["packages"]["find"]["include"]
