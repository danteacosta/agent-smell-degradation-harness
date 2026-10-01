"""Frozen schedule and public prompt contract for TodoMVC Clear completed."""
from collections import Counter
import json

import pytest

from scripts import todomvc_clear_button_replication as pilot


def test_balanced_schedule_and_bounded_page():
    rows = pilot.schedule()
    assert len(rows) == len({row["slot_id"] for row in rows}) == 18
    assert Counter((row["model"], row["arm"]) for row in rows) == {
        (model, arm): 3 for model in pilot.MODELS for arm in pilot.ARMS}
    assert all(row["slot_id"].startswith("todomvc-clear-replication-20261001-") for row in rows)
    assert pilot.SEED == 2026100101
    for arm in pilot.ARMS:
        prompt = pilot.prompt(arm)
        assert prompt.count("/* MODEL_BEHAVIOR */") >= 1
        assert f"Requirement:\n{pilot.arms()[arm]}\n" in prompt


def test_generated_page_cannot_replace_the_scaffold():
    with pytest.raises(ValueError):
        pilot.admit("<html>different page</html>")


def test_unattempted_slots_stay_explicit(tmp_path):
    rows = pilot.generated_rows(tmp_path, pilot.schedule())
    assert len(rows) == 18
    assert {row["category"] for row in rows} == {"not_attempted"}


def test_batch_never_retries_a_slot_with_an_attempt_receipt(tmp_path, monkeypatch):
    slot = pilot.schedule()[0]
    call = tmp_path / "calls" / slot["slot_id"]
    call.mkdir(parents=True)
    (call / "attempt.json").write_text(json.dumps({"slot_id": slot["slot_id"]}))
    (call / "generation-result.json").write_text(json.dumps({
        **slot, "category": "not_attempted", "generation_valid": True}))
    request = tmp_path / "frozen" / "requests" / (slot["slot_id"] + ".json")
    request.parent.mkdir(parents=True)
    request.write_text("{}")
    (tmp_path / "run-started.json").write_text("{}")
    monkeypatch.setattr(pilot, "verify", lambda _: {"schedule": [slot]})
    assert pilot.generate_batch(tmp_path, 1)["batch_attempted"] == 0
