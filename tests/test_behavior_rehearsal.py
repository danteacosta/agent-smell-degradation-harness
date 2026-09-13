import copy
import json

import pytest

from label_plane.behavior_rehearsal import analyze, rehearse, verify


def pair(project="p1", replication="r1"):
    return {"run_id": "run", "replication_id": replication, "project_id": project,
            "intent_id": "intent", "constraint_id": "condition",
            "oracle_sha256": "a" * 64, "configuration_sha256": "b" * 64}


def outcomes(p, clean="passed", defective="failed"):
    return [{**p, "variant": v, "status": s} for v, s in (("clean", clean), ("defective", defective))]


def test_repetitions_are_preserved_and_projects_receive_equal_weight():
    plan = [pair(replication=f"r{i}") for i in range(5)] + [pair("p2")]
    rows = [r for p in plan[:-1] for r in outcomes(p)] + outcomes(plan[-1], "failed", "passed")
    report = analyze(plan, rows)
    assert report["complete_pairs"] == 6
    assert report["mean_project_delta"] == 0  # NOT 4/6: project means +1 and -1.
    assert report["project_means"] == {"p1": 1, "p2": -1}


@pytest.mark.parametrize("status", ["runtime_error", "timeout", "rejected", "worker_error", "not_executed"])
def test_execution_failure_is_not_semantic_failure_or_zero_effect(status):
    p = pair()
    report = analyze([p], outcomes(p, defective=status))
    assert report["complete_pairs"] == 0
    assert report["mean_project_delta"] is None
    assert report["diagnostic_project_bootstrap_ci"] is None
    assert report["status_counts"]["defective"] == {status: 1}


def test_missing_arm_never_becomes_degradation():
    p = pair()
    report = analyze([p], outcomes(p)[:1])
    assert report["complete_pairs"] == 0
    assert report["status_counts"]["defective"] == {"missing": 1}
    assert report["mean_project_delta"] is None


@pytest.mark.parametrize("fault", ["duplicate_plan", "duplicate_row", "oracle", "configuration", "identity"])
def test_invalid_pairs_fail_closed(fault):
    p = pair()
    plan, rows = [p], outcomes(p)
    if fault == "duplicate_plan":
        plan.append(copy.deepcopy(p))
    elif fault == "duplicate_row":
        rows.append(copy.deepcopy(rows[0]))
    elif fault == "identity":
        rows[0]["replication_id"] = "not-planned"
    else:
        rows[0][fault + "_sha256"] = "c" * 64
    with pytest.raises(ValueError):
        analyze(plan, rows)


def test_rehearsal_roundtrip_and_tampering(tmp_path):
    path = tmp_path / "run"
    result = rehearse(path)
    assert result["episodes"] == 36
    assert result["scenarios"] == {"positive": 1, "null": 0, "reverse": -1}
    assert verify(path)["analysis_recomputed"] == 3
    with pytest.raises(FileExistsError):
        rehearse(path)
    receipt = json.loads((path / "receipt.json").read_text())
    source = next(name for name in receipt["files"] if name.endswith("code.py"))
    (path / source).write_text("tampered")
    with pytest.raises(ValueError, match="identity"):
        verify(path)


def test_original_development_contract_checks_both_boolean_outcomes(tmp_path):
    from eval.codegen_sandbox import evaluate_trusted_fixture

    path = tmp_path / "run"
    rehearse(path)
    review = json.loads((path / "review/DEV-ACCESS-001.json").read_text())
    tests = review["executor_test_draft"]["hidden_tests"]
    assert len(tests) == 2
    assert evaluate_trusted_fixture("def evaluate(authorized):\n    return 'deny'", tests)["status"] == "failed"
    assert evaluate_trusted_fixture("def evaluate(authorized):\n    return 'allow'", tests)["status"] == "failed"
    assert review["confirmatory_eligible"] is False
