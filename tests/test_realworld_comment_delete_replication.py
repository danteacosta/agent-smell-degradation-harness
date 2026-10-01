"""Acceptance checks for the frozen RealWorld author-only Delete replication."""
from collections import Counter
import json

import pytest

from scripts import realworld_comment_delete_replication as pilot


def test_fresh_balanced_schedule_and_exact_prior_prompts():
    pilot.preflight()
    rows = pilot.schedule()
    assert len(rows) == len({row["slot_id"] for row in rows}) == 18
    assert Counter((row["model"], row["arm"]) for row in rows) == {
        (model, arm): 3 for model in pilot.MODELS for arm in pilot.ARMS}
    old = json.loads((pilot.PRIOR_PACKET / "frozen/manifest.json").read_text())
    assert {row["slot_id"] for row in rows}.isdisjoint({row["slot_id"] for row in old["schedule"]})


def test_altered_shell_is_rejected_and_unattempted_slots_are_explicit(tmp_path):
    with pytest.raises(ValueError):
        pilot.admit("<html>different shell</html>")
    rows = pilot.generated_rows(tmp_path, pilot.schedule())
    assert len(rows) == 18
    assert {row["category"] for row in rows} == {"not_attempted"}
