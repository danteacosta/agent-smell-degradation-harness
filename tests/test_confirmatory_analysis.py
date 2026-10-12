import json

import pytest

from scripts import confirmatory_analysis as ca


def small(**kw):
    params = dict(fail_a=0.05, fail_b=0.05, fail_c=0.6, projects=8, per_project=5)
    params.update(kw)
    return ca.synthetic(**params)


def test_effect_scenario_is_supported():
    rows, selection = small(w2024_per_project=1)
    r = ca.analyse(rows, selection, n_boot=500)
    assert r["status"] == "complete"
    assert r["design"] == {"requirements": 40, "projects": 8, "models": ["model-1", "model-2"],
                           "replications": [1, 2], "slots": 480}
    assert r["h1a"]["decision"] == "supported"
    assert r["h1a"]["p_exact_project_sign_flip"] == 2 / 256
    assert not r["b_control"]["wording_effect_flag"]
    assert r["exploratory"]["without_w2024"]["n_requirements"] == 32
    assert "does not keep" in r["exploratory"]["without_w2024"]["note"]


def test_identical_arms_are_inconclusive():
    rows, selection = small(fail_c=0.05)
    for r in rows:
        if r["arm"] == "C":
            twin = next(x for x in rows if x["arm"] == "A" and x["intent_id"] == r["intent_id"]
                        and x["model"] == r["model"] and x["replication"] == r["replication"])
            r["outcome"] = twin["outcome"]
    result = ca.analyse(rows, selection, n_boot=200)
    assert result["h1a"]["estimate"] == 0.5
    assert result["h1a"]["p_exact_project_sign_flip"] == 1.0
    assert result["h1a"]["decision"] == "inconclusive"


def test_reversal_is_reported_as_reversal():
    rows, selection = small(fail_a=0.6, fail_b=0.6, fail_c=0.05)
    assert ca.analyse(rows, selection, n_boot=300)["h1a"]["decision"] == "reversal"


def test_stop_rule_blocks_estimation():
    for status in ("stopped_insufficient", "in_progress"):
        r = ca.analyse([], {"status": status, "selected": {}})
        assert r["status"] == status and r["h1a"] is None


def test_too_few_projects_cannot_reach_significance():
    rows, selection = small(projects=4)
    r = ca.analyse(rows, selection, n_boot=200)
    assert r["h1a"]["decision"] == "inconclusive"
    assert "too few projects" in r["h1a"]["note"]


def test_unknown_bounds_bracket_primary():
    rows, selection = small(unknown=0.2)
    r = ca.analyse(rows, selection, n_boot=200)
    worst, best = r["h1a_unknown_bounds"]["worst"]["estimate"], r["h1a_unknown_bounds"]["best"]["estimate"]
    assert best <= r["h1a"]["estimate"] <= worst


def test_validation_rejects_missing_duplicate_and_foreign_slots():
    rows, selection = small()
    with pytest.raises(ValueError, match="missing"):
        ca.analyse(rows[1:], selection)
    with pytest.raises(ValueError, match="duplicate"):
        ca.analyse(rows + [rows[0]], selection)
    foreign = {**rows[0], "intent_id": "other-req"}
    with pytest.raises(ValueError, match="not selected"):
        ca.analyse(rows + [foreign], selection)
    moved = {**rows[0], "project_id": "proj7"}
    with pytest.raises(ValueError, match="belongs to"):
        ca.analyse([moved] + rows[1:], selection)
    bad = {**rows[0], "outcome": "maybe"}
    with pytest.raises(ValueError, match="outcome"):
        ca.analyse([bad] + rows[1:], selection)


def test_dry_run_files_match_committed(tmp_path):
    summary = ca.dry_run(tmp_path)
    assert summary["effect"]["decision"] == "supported"
    assert summary["null"]["decision"] == "inconclusive"
    assert summary["reversal"]["decision"] == "reversal"
    committed = ca.ROOT / "data/confirmatory-planning/analysis-dry-run"
    for name in ("effect", "null", "reversal", "stopped_insufficient"):
        assert json.loads((tmp_path / f"{name}.json").read_text()) == json.loads((committed / f"{name}.json").read_text())
