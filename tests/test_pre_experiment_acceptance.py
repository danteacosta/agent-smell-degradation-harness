"""Pre-experiment offline acceptance criteria."""

from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path

import pytest

from agents.live import LiveAgent
from agents.mock_transport import MockTransport
from eval.experiment import run_dry_run
from eval.oracles import score_artifact
from eval.runner import run_eval
from eval.thesis_analysis import write_thesis_analysis
from mitigation.rewrite import rewrite_requirement
from pairs.loader import load_all_pairs
from protocol.irr import compare_annotations

ROOT = Path(__file__).resolve().parents[1]


def test_live_agent_mock_transport_generates_parseable_artifact():
    pair = next(p for p in load_all_pairs() if p["intent_id"] == "RF-09")
    oracle = pair["oracle_spec"]["codegen"]
    agent = LiveAgent(transport=MockTransport([json.dumps(oracle)]))
    artifact = agent.generate(pair, variant="clean", task_family="codegen")
    assert artifact["delay_threshold_minutes"] == 5


def test_dry_run_writes_manifest(tmp_path):
    repo = tmp_path / "repo"
    (repo / "eval").mkdir(parents=True)
    report = run_dry_run(repo_root=repo)
    manifest = repo / "runs" / report["run_id"] / "manifest.json"
    assert manifest.is_file()
    data = json.loads(manifest.read_text(encoding="utf-8"))
    assert data["config"]["mode"] == "dry-run"


def test_tolerant_oracle_ignores_extra_keys():
    spec = {"delay_threshold_minutes": 5, "comparator": ">"}
    artifact = {**spec, "notes": "extra"}
    result = score_artifact("RF-09", "codegen", artifact, spec)
    assert result.passed is True


def test_irr_kappa_on_example_files():
    result = compare_annotations(
        ROOT / "data" / "annotation" / "example_ann_a.csv",
        ROOT / "data" / "annotation" / "example_ann_b.csv",
    )
    assert result["n_items"] == 6
    assert 0.0 <= result["mode_kappa"] <= 1.0


def test_thesis_analysis_runs_on_eval_episodes(tmp_path):
    episodes_path = tmp_path / "episodes.jsonl"
    run_eval(
        failure_mode="smell-blind",
        output_path=tmp_path / "metrics.json",
        traces_dir=tmp_path / "traces",
        episodes_path=episodes_path,
    )
    report = write_thesis_analysis(episodes_path)
    assert "H1_paired_degradation" in report
    assert report["H1_paired_degradation"]["effect_detected"] is True


def test_template_rewrite_not_verbatim_clean_copy():
    pair = next(p for p in load_all_pairs() if p["intent_id"] == "RF-09")
    out = rewrite_requirement(pair["smelly_requirement"], pair, mode="template")
    assert out.text != pair["clean_requirement"]
    assert "5" in out.text


def test_make_all_still_green():
    """Run the non-test make targets; pytest is already the test runner."""
    venv_bin = ROOT / ".venv" / "bin"
    env = {**os.environ, "PATH": f"{venv_bin}:{os.environ.get('PATH', '')}"}
    for target in ("eval", "simulate", "gate"):
        result = subprocess.run(
            ["make", target],
            cwd=ROOT,
            capture_output=True,
            text=True,
            env=env,
        )
        assert result.returncode == 0, f"make {target} failed:\n{result.stdout}{result.stderr}"
