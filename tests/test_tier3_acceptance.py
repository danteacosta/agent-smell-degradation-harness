"""Tier 3 offline acceptance criteria (C3, C5, Tier 1–2 regression)."""

from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path

from eval.dissertation_bundle import write_dissertation_bundle
from eval.mitigation_report import write_mitigation_report
from eval.runner import run_eval
from gates.run import check_gate, load_thresholds
from mitigation.tradeoff import build_mitigation_report

ROOT = Path(__file__).resolve().parents[1]
THRESHOLDS = load_thresholds(ROOT / "eval" / "thresholds.yaml")

TIER1_KEYS = {
    "paired_degradation_rate",
    "oracle_pass_rate_clean",
    "oracle_pass_rate_smelly",
    "semantic_provenance_coverage",
    "degradation_detected",
    "episode_count",
    "task_families_exercised",
}


def test_tier3_rewrite_clarify_reduce_degradation_vs_direct(tmp_path):
    metrics_direct, _ = run_eval(
        failure_mode="smell-blind",
        policy="direct",
        output_path=tmp_path / "direct.json",
        traces_dir=tmp_path / "traces_direct",
    )
    metrics_rewrite, _ = run_eval(
        failure_mode="smell-blind",
        policy="rewrite",
        output_path=tmp_path / "rewrite.json",
        traces_dir=tmp_path / "traces_rewrite",
    )
    metrics_clarify, _ = run_eval(
        failure_mode="smell-blind",
        policy="clarify",
        output_path=tmp_path / "clarify.json",
        traces_dir=tmp_path / "traces_clarify",
    )

    assert metrics_direct["paired_degradation_rate"] > 0.0
    assert metrics_rewrite["paired_degradation_rate"] == 0.0
    assert metrics_clarify["paired_degradation_rate"] == 0.0


def test_tier3_mitigation_report_gate_fields(tmp_path):
    report = build_mitigation_report(tmp_path / "work")

    assert "mitigation_beneficial" in report
    assert report["gate"]["passed"] is True
    assert report["overhead"]["clarify_steps_mean"] == 1.0
    assert "rewrite_char_delta_mean" in report["overhead"]

    output_path = tmp_path / "mitigation_report.json"
    write_mitigation_report(tmp_path / "work2", output_path)
    written = json.loads(output_path.read_text(encoding="utf-8"))
    assert written["gate"]["passed"] is True


def test_tier3_dissertation_bundle_exports_without_secrets(tmp_path):
    output_path = tmp_path / "dissertation_bundle.json"
    summary_path = tmp_path / "BUNDLE_SUMMARY.md"
    bundle = write_dissertation_bundle(
        ROOT,
        tmp_path / "work",
        output_path,
        summary_path,
    )

    serialized = json.dumps(bundle)
    for secret_key in ("OPENAI_API_KEY", "AGENT_LIVE_API_KEY", "sk-"):
        assert secret_key not in serialized

    assert bundle["reliability"]["synthetic"] is True
    assert bundle["mitigation_summary"]["gate"]["passed"] is True
    assert output_path.exists()
    assert summary_path.exists()


def test_tier3_tier1_gate_keys_still_work(tmp_path):
    metrics_path = tmp_path / "last_run.json"
    metrics, _ = run_eval(output_path=metrics_path, traces_dir=tmp_path / "traces")
    assert TIER1_KEYS.issubset(metrics.keys())
    ok, failures = check_gate(metrics, THRESHOLDS)
    assert ok is True, failures


def test_tier3_no_secrets_required_for_eval_and_gate():
    for module in ("eval", "gates"):
        result = subprocess.run(
            [sys.executable, "-m", module],
            cwd=ROOT,
            capture_output=True,
            text=True,
            check=False,
            env={
                k: v
                for k, v in os.environ.items()
                if k not in ("OPENAI_API_KEY", "AGENT_LIVE_API_KEY")
            },
        )
        assert result.returncode == 0, f"{module}: {result.stdout}{result.stderr}"
