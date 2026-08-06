from __future__ import annotations

import pytest

from eval.experiment import run_experiment


def test_confirmatory_experiment_requires_confirmed_freeze(tmp_path):
    with pytest.raises(ValueError, match="confirmatory-freeze.json"):
        run_experiment(confirmatory=True, repo_root=tmp_path, replications=1)


def test_confirmatory_experiment_rejects_stub_mode(tmp_path):
    with pytest.raises(ValueError, match="stub-as-live"):
        run_experiment(confirmatory=True, stub_as_live=True, repo_root=tmp_path)
