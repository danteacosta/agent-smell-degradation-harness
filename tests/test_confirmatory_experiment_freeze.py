from __future__ import annotations

import pytest

import eval.experiment as experiment
from eval.experiment import run_experiment


def test_confirmatory_experiment_requires_confirmed_freeze(tmp_path):
    with pytest.raises(ValueError, match="confirmatory-freeze.json"):
        run_experiment(confirmatory=True, repo_root=tmp_path, replications=1)


def test_confirmatory_experiment_rejects_stub_mode(tmp_path):
    with pytest.raises(ValueError, match="stub-as-live"):
        run_experiment(confirmatory=True, stub_as_live=True, repo_root=tmp_path)


def test_confirmatory_experiment_promotes_live_provider_to_runtime(tmp_path, monkeypatch):
    freeze = tmp_path / "docs/thesis/confirmatory-freeze.json"
    freeze.parent.mkdir(parents=True)
    freeze.write_text("{}", encoding="utf-8")
    promoted = object()
    seen = []

    class FakeLiveAgent:
        def __init__(self, **_kwargs):
            pass

        def as_runtime_checkpoint_agent(self):
            return promoted

    monkeypatch.setattr(experiment, "LiveAgent", FakeLiveAgent)
    monkeypatch.setattr(experiment, "validate_freeze", lambda *_args, **_kwargs: {})

    def fake_run(agent, **_kwargs):
        seen.append(agent)
        return {"provider_run": None}, []

    monkeypatch.setattr(experiment, "run_eval_with_agent", fake_run)
    result = run_experiment(
        confirmatory=True,
        repo_root=tmp_path,
        confirmatory_split="train",
        source_revision="abc123",
        run_id="qualified-runtime-test",
    )
    assert seen == [promoted]
    assert result["run_id"] == "qualified-runtime-test"
