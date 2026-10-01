"""Public contract checks for Paperless inbox-suggestion generation."""
from collections import Counter

import pytest

from scripts import paperless_inbox_suggestions_pilot as pilot


def test_balanced_schedule_and_single_sentence_omission():
    rows = pilot.schedule()
    assert len(rows) == len({row["slot_id"] for row in rows}) == 18
    assert Counter((row["model"], row["arm"]) for row in rows) == {
        (model, arm): 3 for model in pilot.MODELS for arm in pilot.ARMS}
    assert {row["project_id"] for row in rows} == {"paperless-ngx"}
    arms = pilot.arms()
    assert "automatically" in arms["A"] and "automatically" in arms["B"]
    assert "automatically" not in arms["C"]
    assert all("requestSuggestions(id)" in pilot.prompt(arm) for arm in pilot.ARMS)


def test_scaffold_alteration_and_unattempted_slots_are_explicit(tmp_path):
    with pytest.raises(ValueError):
        pilot.admit("<html>not the frozen page</html>")
    assert {row["category"] for row in pilot.generated_rows(tmp_path, pilot.schedule())} == {"not_attempted"}
