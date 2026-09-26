"""Acceptance checks for the prospectively frozen Kanboard successor."""
from collections import Counter

from scripts import kanboard_duplicate_freeze as original
from scripts.kanboard_duplicate_secure_replication import qualified_browser, schedule


def test_new_schedule_has_eighteen_unique_balanced_positions():
    rows = schedule()
    assert len(rows) == len({row["slot_id"] for row in rows}) == 18
    assert {row["slot_id"] for row in rows}.isdisjoint(
        {row["slot_id"] for row in original.schedule()})
    assert Counter((row["model"], row["arm"]) for row in rows) == {
        (model, arm): 3 for model in original.MODELS for arm in original.ARMS}


def test_new_browser_origin_was_qualified_before_generation():
    qualified_browser()
