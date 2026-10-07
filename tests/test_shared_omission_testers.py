import copy
import json

import pytest

from scripts import shared_omission_testers as st


def registry():
    return json.loads(st.REGISTRY.read_text())


def test_summary_matches_committed_file():
    committed = json.loads((st.ROOT / "data/shared-omission-e2e/testers-summary.json").read_text())
    assert st.summarise(registry()) == committed


def test_every_evaluated_run_reported_and_failed_runs_listed():
    result = st.summarise(registry())
    reg = registry()
    assert result["evaluated_runs"] == sum(r["status"] == "evaluated" for r in reg["runs"])
    assert len(result["excluded_runs"]) == sum(r["status"] == "failed_evaluation" for r in reg["runs"])
    assert [t["tester"] for t in result["testers"]] == [r["tester"] for r in reg["runs"] if r["status"] == "evaluated"]
    dist = result["requirements_complete_higher_in_k_of_n_testers"]["distribution"]
    assert sum(dist.values()) == result["requirements"] == 25


def test_failed_run_needs_reason_and_status_is_closed():
    reg = registry()
    bad = copy.deepcopy(reg)
    del next(r for r in bad["runs"] if r["status"] == "failed_evaluation")["reason"]
    with pytest.raises(ValueError, match="reason"):
        st.summarise(bad)
    bad = copy.deepcopy(reg)
    bad["runs"][0]["status"] = "skipped"
    with pytest.raises(ValueError, match="status"):
        st.summarise(bad)


def test_run_with_different_design_is_refused(tmp_path, monkeypatch):
    reg = registry()
    first = next(r for r in reg["runs"] if r["status"] == "evaluated")
    manifest = json.loads((st.ROOT / first["manifest"]).read_text())
    case = next(iter(manifest["selected_mutants"]))
    manifest["selected_mutants"][case] = "another-slot"
    path = tmp_path / "manifest.json"
    path.write_text(json.dumps(manifest))
    extra = {**first, "tester": "other", "manifest": str(path)}
    reg["runs"].append(extra)
    monkeypatch.setattr(st, "ROOT", st.ROOT)
    with pytest.raises(ValueError, match="different requirements"):
        st.summarise(reg)
