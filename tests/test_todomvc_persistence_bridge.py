"""Observable sample-frame and manipulation contracts for the TodoMVC bridge."""
from collections import Counter

from eval.persistence_executor import classify_report
from scripts import todomvc_persistence_bridge as bridge


def test_bridge_schedule_is_balanced_and_does_not_count_as_new_obligation():
    rows = bridge.schedule()
    assert len(rows) == len({row["slot_id"] for row in rows}) == 18
    assert Counter((row["model"], row["arm"]) for row in rows) == {
        (model, arm): 3 for model in bridge.MODELS for arm in bridge.ARMS}
    assert {row["intent_id"] for row in rows} == {"todo-edit-state-not-persisted"}


def test_c_removes_only_editing_persistence_clause():
    a, c = bridge.prompt("A"), bridge.prompt("C")
    clause = "Editing mode should not be persisted."
    assert a.replace(" " + clause, "") == c


def test_malformed_browser_report_cannot_pass():
    assert classify_report(b"{}", 0)["category"] == "browser_error"
