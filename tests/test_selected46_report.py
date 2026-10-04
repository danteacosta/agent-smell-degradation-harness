import json

import pytest

from scripts import selected46_report as rep


def _config(case, project, candidate):
    return {"case": case, "intent_id": case, "project_id": project, "candidate_id": candidate,
            "models": ["m1", "m2"], "repetitions": 2}


def _rows(case, project, outcomes):
    """outcomes: {(model, rep, arm): category}"""
    return [{"slot_id": f"{case}-{i}", "intent_id": case, "project_id": project, "model": m, "replication": r,
             "arm": a, "category": c} for i, ((m, r, a), c) in enumerate(sorted(outcomes.items()))]


def _write(tmp_path, cases):
    cases_dir, results = tmp_path / "cases", tmp_path / "results"
    cases_dir.mkdir()
    results.mkdir()
    for case, project, candidate, outcomes in cases:
        (cases_dir / f"{case}.json").write_text(json.dumps(_config(case, project, candidate)))
        if outcomes is not None:
            (results / case).mkdir()
            (results / case / "results.json").write_text(json.dumps({"case": case, "rows": _rows(case, project, outcomes)}))
    (cases_dir / "legacy.json").write_text(json.dumps({"case": "legacy", "project_id": "p"}))
    return cases_dir, results


def _full(a, b, c):
    return {(m, r, arm): cat for m in ("m1", "m2") for r in (1, 2) for arm, cat in (("A", a), ("B", b), ("C", c))}


def test_severity_mapping():
    assert rep.severity("pass") == 0 and rep.severity("non_target_only_failure") == 0
    assert rep.severity("target_only_failure") == 1 and rep.severity("mixed_failure") == 1
    assert rep.severity("browser_error") is None and rep.severity(None) is None


def test_report_counts_progress_and_estimands(tmp_path, monkeypatch):
    monkeypatch.setattr(rep, "covariates", lambda configs: {c: {"numeric": False, "derived_state": True,
                                                              "memorized": {"m1": 1}, "context_cue": None}
                                                          for c in configs})
    cases_dir, results = _write(tmp_path, [
        ("case-a", "p1", "rc-1", _full("pass", "pass", "target_only_failure")),
        ("case-b", "p2", "rc-2", _full("pass", "pass", "pass")),
        ("case-c", "p3", "rc-3", None),
    ])
    report = rep.build(results, cases_dir)
    assert report["progress"]["selected_cases"] == 3 and report["progress"]["finished_cases"] == 2
    assert report["progress"]["runs"] == 24 and report["progress"]["planned_runs"] == 36
    h1 = report["h1a_c_vs_a"]["drop"]
    assert h1["n_pairs"] == 8 and h1["n_intents"] == 2 and h1["n_projects"] == 2
    assert h1["estimate"] == pytest.approx(0.75)  # one requirement always worse (1.0), one tie (0.5)
    assert report["wording_control_b_vs_a"]["drop"]["estimate"] == pytest.approx(0.5)
    by_mem = report["h1b_c_violation_by_covariate"]["memorized"]
    assert by_mem["1"] == {"violated": 2, "held": 2}  # model m1 in both cases
    assert by_mem["not coded"] == {"violated": 2, "held": 2}  # model m2 has no probe value
    assert report["h1a_c_vs_a"]["worst"]["n_intents"] == 3
    assert report["h1a_c_vs_a"]["best"]["n_pairs"] == 12
    assert report["h1a_c_vs_a"]["worst"]["paired_randomization_pvalue"] is None
    assert report["h1a_c_vs_a"]["worst"]["valid_for_inference"] is False


def test_unknowns_are_kept_out_or_assigned_worst_and_best(tmp_path, monkeypatch):
    monkeypatch.setattr(rep, "covariates", lambda configs: {c: {"numeric": None, "derived_state": None,
                                                              "memorized": {}, "context_cue": None} for c in configs})
    outcomes = _full("pass", "pass", "pass")
    outcomes[("m1", 1, "C")] = "browser_error"
    cases_dir, results = _write(tmp_path, [("case-a", "p1", "rc-1", outcomes)])
    report = rep.build(results, cases_dir)
    e = report["h1a_c_vs_a"]
    assert e["drop"]["n_pairs"] == 3
    assert e["worst"]["n_pairs"] == 4 and e["worst"]["pair_outcomes"]["defective_worse"] == 1
    assert e["best"]["pair_outcomes"]["defective_worse"] == 0
    assert report["counts_by_model_and_arm"]["m1"]["C"]["unknown"] == 1


def test_unknown_case_folder_is_rejected(tmp_path):
    cases_dir, results = _write(tmp_path, [("case-a", "p1", "rc-1", None)])
    (results / "other").mkdir()
    (results / "other" / "results.json").write_text(json.dumps({"case": "other", "rows": []}))
    with pytest.raises(ValueError):
        rep.build(results, cases_dir)


def test_duplicate_or_missing_frozen_slot_is_rejected(tmp_path):
    outcomes = _full("pass", "pass", "pass")
    cases_dir, results = _write(tmp_path, [("case-a", "p1", "rc-1", outcomes)])
    path = results / "case-a" / "results.json"
    data = json.loads(path.read_text())
    data["rows"][-1] = dict(data["rows"][0], slot_id="another-slot")
    path.write_text(json.dumps(data))
    with pytest.raises(ValueError, match="duplicate model/replication/arm"):
        rep.build(results, cases_dir)

    data["rows"] = data["rows"][:-1]
    path.write_text(json.dumps(data))
    with pytest.raises(ValueError, match="missing frozen slots"):
        rep.build(results, cases_dir)


def test_unfinished_cases_are_included_in_collection_sensitivity_bounds(tmp_path, monkeypatch):
    monkeypatch.setattr(rep, "covariates", lambda configs: {c: {"numeric": None, "derived_state": None,
                                                              "memorized": {}, "context_cue": None} for c in configs})
    cases_dir, results = _write(tmp_path, [
        ("case-a", "p1", "rc-1", _full("pass", "pass", "target_only_failure")),
        ("case-b", "p2", "rc-2", None),
    ])
    report = rep.build(results, cases_dir)
    assert report["h1a_c_vs_a"]["drop"]["n_intents"] == 1
    assert report["h1a_c_vs_a"]["worst"]["n_intents"] == 2
    assert report["h1a_c_vs_a"]["worst"]["n_pairs"] == 8
    assert report["h1a_c_vs_a"]["worst"]["estimate"] == pytest.approx(1.0)
    assert report["h1a_c_vs_a"]["best"]["estimate"] == pytest.approx(0.5)


def test_published_packets_match_the_collection_progress_counts():
    import json
    from collections import Counter
    root = rep.ROOT / "data/selection-abc-results/20261003"
    report = rep.build(root)
    assert report["progress"]["finished_cases"] == 46 and report["progress"]["runs"] == 552
    progress = json.loads((root / "collection-progress.json").read_text())
    expected = {}
    for case in progress["cases"]:
        for model, arms in case["counts"].items():
            for arm, categories in arms.items():
                cell = expected.setdefault(model, {}).setdefault(arm, Counter())
                for category, n in categories.items():
                    sev = rep.severity(category)
                    cell["held" if sev == 0 else "violated" if sev == 1 else "unknown"] += n
    assert report["counts_by_model_and_arm"] == {m: {a: dict(c) for a, c in arms.items()} for m, arms in expected.items()}
