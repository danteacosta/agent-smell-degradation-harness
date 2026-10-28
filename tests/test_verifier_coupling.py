"""Tests for scripts/verifier_coupling.py (offline, no model calls)."""
from __future__ import annotations

import json

import pytest

from scripts import verifier_coupling as vc
from scripts.mutation_adequacy import SOURCES


def row(call, case, slot, role, verdict, source="spec_incomplete", ref=False, project="p1"):
    return {"call_id": call, "case": case, "slot_id": slot, "role": role, "verdict": verdict,
            "source": source, "is_reference": ref, "project_id": project}


def tiny_rows():
    # one case: reference r, mutants m1 m2, recovered c1; two suites
    return [
        row("s1", "k", "r", "correct", "quiet", ref=True),
        row("s1", "k", "m1", "mutant", "assertion_alarm"),
        row("s1", "k", "m2", "mutant", "quiet"),
        row("s1", "k", "c1", "recovered", "quiet"),
        # s2 alarms on the reference: unsound, its alarms must not count as kills
        row("s2", "k", "r", "correct", "assertion_alarm", ref=True),
        row("s2", "k", "m1", "mutant", "assertion_alarm"),
        row("s2", "k", "m2", "mutant", "error_alarm"),
        row("s2", "k", "c1", "recovered", "assertion_alarm"),
    ]


def test_suites_soundness_and_alarms():
    ss = {s["call_id"]: s for s in vc.suites(tiny_rows())}
    assert ss["s1"]["sound"] and not ss["s2"]["sound"]
    assert ss["s1"]["alarms"] == {"m1"}
    assert ss["s2"]["alarms"] == {"r", "m1", "m2", "c1"}


def test_assertion_only_keeps_soundness_fixed():
    # An error alarm on the reference makes the suite unsound in every sensitivity;
    # --assertion-only changes only which alarms count on the other implementations.
    rows = [
        row("s3", "k", "r", "correct", "error_alarm", ref=True),
        row("s3", "k", "m1", "mutant", "assertion_alarm"),
        row("s4", "k", "r", "correct", "quiet", ref=True),
        row("s4", "k", "m1", "mutant", "error_alarm"),
        row("s4", "k", "m2", "mutant", "assertion_alarm"),
    ]
    for alarms in (vc.ALARMS, ("assertion_alarm",)):
        ss = {s["call_id"]: s for s in vc.suites(rows, alarms=alarms)}
        assert not ss["s3"]["sound"] and ss["s4"]["sound"]
    only = {s["call_id"]: s for s in vc.suites(rows, alarms=("assertion_alarm",))}
    assert only["s4"]["alarms"] == {"m2"}


def test_detection_ignores_unsound_suites():
    ss = vc.suites(tiny_rows())
    assert vc.detection_sets(ss, "k", "spec_incomplete", {"m1", "m2"}) == {"m1"}


def test_single_score_counts_unsound_as_zero():
    ss = vc.suites(tiny_rows())
    # s1 kills 1/2, s2 is unsound -> 0; mean 0.25
    assert vc.single_score(ss, "k", "spec_incomplete", {"m1", "m2"}) == pytest.approx(0.25)


def test_generation_failure_is_unsound():
    rows = tiny_rows()
    rows[1] = dict(rows[1], verdict="generation_failed")
    s1 = [s for s in vc.suites(rows) if s["call_id"] == "s1"][0]
    assert not s1["sound"]


def test_spearman_handles_ties_and_perfect_order():
    assert vc.spearman([1, 2, 3, 4], [10, 20, 30, 40]) == pytest.approx(1.0)
    assert vc.spearman([1, 2, 3, 4], [40, 30, 20, 10]) == pytest.approx(-1.0)
    assert vc.spearman([1, 1, 2, 2], [1, 1, 2, 2]) == pytest.approx(1.0)
    assert vc.spearman([1, 2], [1, 2]) is None


def test_permutation_is_deterministic_and_stratified_keeps_strata():
    x = [0, 1, 2, 3, 4, 5]
    y = [0, 1, 2, 3, 4, 5]
    assert vc.permutation_p(x, y, n=500) == vc.permutation_p(x, y, n=500)
    # one stratum per point: nothing can move, so every permutation equals the observed statistic
    assert vc.permutation_p(x, y, n=200, strata=list("abcdef")) == pytest.approx(1.0)


def test_case_roles_must_match_across_runs():
    a = {"tester": "a", "rows": tiny_rows()}
    b_rows = tiny_rows()
    b_rows[2] = dict(b_rows[2], role="recovered")
    b = {"tester": "b", "rows": b_rows}
    with pytest.raises(ValueError):
        vc.case_roles([a, b])


def test_q1_union_is_monotone_in_k():
    rows_a = tiny_rows()
    rows_b = [dict(r) for r in tiny_rows()]
    # tester b: sound suite kills m2 instead of m1
    rows_b[1]["verdict"], rows_b[2]["verdict"] = "quiet", "assertion_alarm"
    runs = [{"tester": "a", "rows": rows_a}, {"tester": "b", "rows": rows_b}]
    all_suites = {r["tester"]: vc.suites(r["rows"]) for r in runs}
    roles = vc.case_roles([{"tester": "x", "rows": rows_a}])
    rec = vc.q1_ensemble(runs, all_suites, roles)["per_requirement"]["k"]["spec_incomplete"]
    assert rec["union_detection_by_k_testers"]["1"] == pytest.approx(0.5)
    assert rec["union_detection_by_k_testers"]["2"] == pytest.approx(1.0)


# ---------------------------------------------------------------- published data

@pytest.fixture(scope="module")
def published():
    runs = vc.load_runs()
    return runs, {r["tester"]: vc.suites(r["rows"]) for r in runs}, vc.case_roles(runs)


def test_reproduces_published_per_tester_scores(published):
    """The per-requirement score used here equals each run's published mean_requirement_mutation_score."""
    runs, all_suites, roles = published
    spec = json.loads(vc.TESTERS_FILE.read_text())
    paths = {r["tester"]: r["results"] for r in spec["runs"] if r["status"] == "evaluated"}
    for run in runs:
        pub = json.loads((vc.ROOT / paths[run["tester"]]).read_text())["analysis"]["by_source"]
        for source in SOURCES:
            scores = []
            for case, info in roles.items():
                mutants = {s for s, role in info["slots"].items() if role == "mutant"}
                scores.append(vc.single_score(all_suites[run["tester"]], case, source, mutants))
            assert vc.mean(scores) == pytest.approx(pub[source]["mean_requirement_mutation_score"])


def test_published_results_file_reproduces():
    text = json.dumps(vc.analyse(), indent=2, sort_keys=True) + "\n"
    assert (vc.OUT / "results.json").read_text() == text


def test_five_evaluated_testers_and_25_requirements(published):
    runs, _, roles = published
    assert len(runs) == 5
    assert len(roles) == 25
