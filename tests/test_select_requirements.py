import json
import random

import pytest

from scripts import select_requirements as sel


def _vote(decision, rule=None):
    return {"status": "ok", "vote": {"decision": decision, "target_rule": rule, "pass_observation": "p",
                                     "fail_observation": "f", "probe_question": "q"}}


def _row(cid, project, consensus="admit"):
    return {"candidate_id": cid, "project": project, "consensus": consensus, "route": "agreement",
            "target_rule": f"rule {cid}", "pass_observation": "p", "fail_observation": "f", "probe_question": "q",
            "votes": {"m1": _vote("admit", f"rule {cid}"), "m2": _vote("admit", f"other {cid}")}}


def _frame_row(cid, project, commit="c", file="f.md", added=None):
    return {"candidate_id": cid, "project": project, "commit": commit, "file": file,
            "removed": [], "added": added or [f"A distinct sentence about behavior {cid} here."]}


def _write(tmp_path, rows, frame, decisions):
    screening = tmp_path / "results.json"
    screening.write_text(json.dumps({"status": "complete", "rows": rows}))
    frame_path = tmp_path / "frame.jsonl"
    frame_path.write_text("\n".join(json.dumps(r) for r in frame))
    dec = tmp_path / "decisions.json"
    dec.write_text(json.dumps(decisions))
    return screening, frame_path, dec


def _many(projects, per_project):
    rows, frame = [], []
    for p in range(projects):
        for i in range(per_project):
            cid = f"rc-{p:02d}{i:02d}"
            rows.append(_row(cid, f"proj{p}"))
            frame.append(_frame_row(cid, f"proj{p}", commit=f"{p}-{i}"))
    return rows, frame


def test_draw_consumes_generator_only_for_projects_over_cap():
    units = {f"a{i}": {"project": "alpha"} for i in range(3)}
    units |= {f"b{i:02d}": {"project": "beta"} for i in range(10)}
    units |= {f"c{i:02d}": {"project": "gamma"} for i in range(8)}
    chosen = sel.draw(units, seed=7)
    rng = random.Random(7)
    assert chosen["alpha"] == ["a0", "a1", "a2"]
    assert chosen["beta"] == sorted(rng.sample(sorted(f"b{i:02d}" for i in range(10)), 6))
    assert chosen["gamma"] == sorted(rng.sample(sorted(f"c{i:02d}" for i in range(8)), 6))


def test_draw_is_independent_of_input_order():
    units = {f"x{i:02d}": {"project": "p"} for i in range(12)}
    reversed_units = dict(reversed(list(units.items())))
    assert sel.draw(units) == sel.draw(reversed_units)


def test_select_blocks_unapproved_and_missing_decisions(tmp_path):
    rows, frame = _many(8, 4)
    s, f, d = _write(tmp_path, rows, frame, {"status": "proposed", "probe_outcomes_consulted": False,
                                              "mappings": {}})
    result = sel.select([s], [f], d, unresolved=["rc-0000"])
    assert result["status"] == "blocked"
    assert "no mapping decision for rc-0000" in result["problems"]
    assert any("not 'approved'" in p for p in result["problems"])


def test_select_requires_probe_blindness_statement(tmp_path):
    rows, frame = _many(8, 4)
    s, f, d = _write(tmp_path, rows, frame, {"status": "approved", "mappings": {}})
    assert "probe_outcomes_consulted" in sel.select([s], [f], d, [])["problems"][0]


def test_select_applies_exclusions_duplicates_and_votes(tmp_path):
    rows, frame = _many(8, 4)
    decisions = {"status": "approved", "probe_outcomes_consulted": False,
                 "mappings": {"rc-0000": {"decision": "exclude", "reason": "label only"},
                              "rc-0001": {"decision": "use_vote", "vote_model": "m2", "reason": "valid"}},
                 "duplicate_groups": [{"candidates": ["rc-0103", "rc-0102"], "reason": "same text"}]}
    s, f, d = _write(tmp_path, rows, frame, decisions)
    result = sel.select([s], [f], d, unresolved=["rc-0000", "rc-0001"])
    assert result["status"] == "selected"
    proj0 = {u["candidate_id"]: u for u in result["selected"]["proj0"]}
    assert "rc-0000" not in proj0
    assert proj0["rc-0001"]["target_rule"] == "other rc-0001"
    assert proj0["rc-0001"]["rule_source"] == "vote:m2"
    proj1 = [u["candidate_id"] for u in result["selected"]["proj1"]]
    assert "rc-0102" in proj1 and "rc-0103" not in proj1
    assert result["selected_count"] == 30


def test_select_reports_project_shortfall(tmp_path):
    rows, frame = _many(7, 6)
    s, f, d = _write(tmp_path, rows, frame, {"status": "approved", "probe_outcomes_consulted": False})
    result = sel.select([s], [f], d, [])
    assert result["status"] == "blocked"
    assert result["shortfall"] == ["7 projects, at least 8 required"]


def test_use_vote_must_name_an_admitting_model(tmp_path):
    rows, frame = _many(8, 4)
    rows[0]["votes"]["m2"] = _vote("exclude")
    decisions = {"status": "approved", "probe_outcomes_consulted": False,
                 "mappings": {"rc-0000": {"decision": "use_vote", "vote_model": "m2", "reason": "x"}}}
    s, f, d = _write(tmp_path, rows, frame, decisions)
    assert any("did not vote admit" in p for p in sel.select([s], [f], d, [])["problems"])


def test_candidate_admitted_twice_is_rejected(tmp_path):
    rows, frame = _many(1, 1)
    s, f, d = _write(tmp_path, rows, frame, {})
    with pytest.raises(ValueError):
        sel.load_admitted([s, s])


def test_audit_flags_shared_sentences_and_same_change():
    admitted = {c: _row(c, "p") for c in ("rc-a", "rc-b", "rc-c", "rc-d")}
    shared = "Duplication starts a new activity history for the copied board."
    frame = {"rc-a": _frame_row("rc-a", "p", commit="1", added=[shared]),
             "rc-b": {**_frame_row("rc-b", "p", commit="2"), "removed": [shared], "added": []},
             "rc-c": _frame_row("rc-c", "p", commit="3", file="x.md"),
             "rc-d": _frame_row("rc-d", "p", commit="3", file="x.md")}
    pairs = {(p["a"], p["b"]): p for p in sel.duplicate_candidates(admitted, frame)}
    assert pairs[("rc-a", "rc-b")]["shared_sentences"] == 1
    assert pairs[("rc-c", "rc-d")]["same_commit_and_file"] is True
    assert ("rc-a", "rc-c") not in pairs


def test_repository_selection_has_explicit_approval_and_bound_inputs():
    root = sel.ROOT
    decisions = json.loads((root / "data/requirement-selection/decisions-proposed.json").read_text())
    admitted = sel.load_admitted([root / "data/llm-screening-20261002/results.json",
                                  root / "data/llm-screening-round2-20261003/results.json"])
    unresolved = [c for path in ("data/llm-screening-20261002/mapping-audit.json",
                                 "data/requirement-selection/round2-mapping-audit.json")
                  for c in json.loads((root / path).read_text())["unresolved_target_selection"]]
    assert sel.check_decisions(decisions, admitted, unresolved) == []
    assert decisions["status"] == "approved" and decisions["approved_by"]
    assert decisions["approval_evidence"]["answer"] == "Aprovo a proposta revisada e autorizo a seleção"
    result = json.loads((root / "data/requirement-selection/selection.json").read_text())
    receipt = json.loads((root / "data/requirement-selection/selection-execution.json").read_text())
    assert result["status"] == "selected" and result["selected_count"] == 46
    assert len(result["selected"]) == 9 and result["units_before_cap"] == 82
    assert receipt["binding_draws"] == 1 and receipt["preview_draws"] == 0
    for rel, digest in {**result["inputs_sha256"], **receipt["additional_inputs_sha256"]}.items():
        assert sel.sha256_file(root / rel) == digest, rel
