from __future__ import annotations

import copy
from pathlib import Path

from replay.runner import benchmark, load_fixture, run_bundle

FIXTURES = Path(__file__).parents[1] / "replay" / "fixtures"


def report(case_id: str) -> dict:
    return run_bundle(load_fixture(case_id, FIXTURES))


def test_decisions_and_evidence_cover_clean_warning_loss() -> None:
    assert report("clean")["decision"] == "approve"
    warning = report("constraint-warning")
    assert warning["decision"] == "warn"
    assert warning["exit_code"] == 10
    loss = report("constraint-loss")
    assert loss["decision"] == "block"
    assert loss["exit_code"] == 20
    assert loss["semantic_evidence"]
    for item in loss["semantic_evidence"]:
        assert 0 <= item["confidence"] <= 1
        assert item["recommended_action"] in {"review", "clarify", "block"}


def test_negative_controls_are_approvals_and_baselines_are_namespaced() -> None:
    for case_id in ("negative-control", "latency-only"):
        result = report(case_id)
        assert result["decision"] == "approve"
    result = report("latency-only")
    assert result["baselines"]["diagnostic"]["operational"]["latency_ms"] > 0
    assert "output_only" in result["baselines"]["diagnostic"]
    assert "output_only" not in result["features"]


def test_report_hash_is_stable_and_expected_sidecar_is_not_an_input() -> None:
    first = report("clean")
    second = report("clean")
    assert first["report_sha256"] == second["report_sha256"]
    mutated = copy.deepcopy(load_fixture("clean", FIXTURES))
    mutated["manifest"]["case_id"] = "renamed-fixture"
    assert run_bundle(mutated)["decision"] == first["decision"]
    assert run_bundle(mutated)["features"] == first["features"]
    assert run_bundle(mutated)["baselines"]["deployable"] == first["baselines"]["deployable"]


def test_terminal_and_output_only_mutations_do_not_feed_gate() -> None:
    baseline = load_fixture("clean", FIXTURES)
    original = run_bundle(baseline)
    mutated = copy.deepcopy(baseline)
    mutated["terminal_label"] = "failure"
    mutated["final_artifact"] = {"status": "failed"}
    mutated["diagnostic"] = {"output_only": {"score": 0.01}}
    result = run_bundle(mutated)
    assert result["decision"] == original["decision"]
    assert result["features"] == original["features"]
    assert result["baselines"]["deployable"] == original["baselines"]["deployable"]


def test_benchmark_reports_zero_false_alerts_over_negative_cases() -> None:
    summary = benchmark(FIXTURES)
    assert summary["negative_cases"] == 2
    assert summary["false_alerts"] == 0
    assert summary["false_alert_rate"] == 0.0
    assert summary["status"] == "non_confirmatory_demo"
