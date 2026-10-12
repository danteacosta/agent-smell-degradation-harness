import json

import pytest

from scripts import confirmatory_selection as cs


def test_published_order_is_reserve_first_and_complete():
    order = json.loads(cs.ORDER.read_text())
    assert order["status"] == "proposal_not_approved" and order["seed"] == cs.SEED
    assert order == cs.build_order()  # reproducible from the published screening results
    total = 0
    for project, info in order["projects"].items():
        options = [r["option"] for r in info["order"]]
        assert options == sorted(options, key=["reserve", "w2024"].index)  # reserve before 2024
        assert [r["rank"] for r in info["order"]] == list(range(1, len(options) + 1))
        total += len(options)
    assert total == 162 and "mealie" not in order["projects"]
    assert cs.read_ledger(cs.LEDGER) == []  # no selection has been made


def _order(n_reserve=3, n_2024=3, target=2):
    rows = [{"candidate_id": f"r{i}", "option": "reserve", "rank": i} for i in range(1, n_reserve + 1)]
    rows += [{"candidate_id": f"w{i}", "option": "w2024", "rank": n_reserve + i} for i in range(1, n_2024 + 1)]
    return {"target_per_project": target, "allowed_exclusion_reasons": cs.ALLOWED_REASONS,
            "projects": {"p": {"order": rows}}}


def _ev(seq, cid, rank, action, reason=None, **extra):
    e = {"seq": seq, "project": "p", "candidate_id": cid, "rank": rank, "action": action,
         "decided_by": "Dante", "date": "2026-10-06", "evidence": "notes/x.md", **extra}
    if reason:
        e["reason"] = reason
    return e


def test_walk_selects_in_order_and_counts_2024_fill():
    events = [_ev(1, "r1", 1, "qualified"), _ev(2, "r2", 2, "excluded", "mapping_invalid"),
              _ev(3, "r3", 3, "excluded", "duplicate_semantic", duplicate_of="r1"), _ev(4, "w1", 4, "qualified")]
    result = cs.walk(_order(), events)
    assert result["status"] == "complete" and result["selected"]["p"] == ["r1", "w1"]
    assert result["selected_from_w2024"]["p"] == 1
    assert result["exclusions"]["p"] == {"mapping_invalid": 1, "duplicate_semantic": 1}


def test_walk_stops_and_records_insufficiency():
    events = [_ev(i, cid, i, "excluded", "not_constructible") for i, cid in enumerate(["r1", "r2", "r3"], 1)]
    events += [_ev(4, "w1", 4, "qualified")] + [_ev(i, f"w{i - 3}", i, "excluded", "oracle_not_qualified")
                                                for i in (5, 6)]
    result = cs.walk(_order(), events)
    assert result["status"] == "stopped_insufficient" and result["project_status"]["p"] == "insufficient"


@pytest.mark.parametrize("events", [
    [_ev(1, "r2", 2, "qualified")],                                   # skips rank 1
    [_ev(1, "r1", 1, "excluded", "too_hard")],                       # reason not allowed
    [_ev(1, "r1", 1, "excluded", "duplicate_semantic")],             # duplicate without duplicate_of
    [_ev(1, "r1", 1, "qualified"), _ev(3, "r2", 2, "qualified")],    # gap in seq
    [_ev(1, "r1", 1, "qualified"), _ev(2, "r2", 2, "qualified"), _ev(3, "r3", 3, "qualified")],  # past target
    [{**_ev(1, "r1", 1, "qualified"), "evidence": ""}],              # no evidence
])
def test_walk_rejects_rule_violations(events):
    with pytest.raises(ValueError):
        cs.walk(_order(), events)
