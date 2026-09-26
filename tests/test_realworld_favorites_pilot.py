"""Observable admission and sample-frame contracts for the RealWorld pilot."""
import runpy
from collections import Counter

import pytest

from scripts import realworld_favorites_pilot as pilot


def test_balanced_schedule_and_frozen_page():
    rows = pilot.schedule()
    assert len(rows) == len({row["slot_id"] for row in rows}) == 18
    assert Counter((row["model"], row["arm"]) for row in rows) == {
        (model, arm): 3 for model in pilot.MODELS for arm in pilot.ARMS}
    assert all("/* MODEL_BEHAVIOR */" in pilot.prompt(row["arm"]) for row in rows)


def test_generation_cannot_change_route_interface():
    with pytest.raises(ValueError):
        pilot.admit("<html><body>different page</body></html>")


def test_incomplete_browser_report_cannot_pass():
    classify = runpy.run_path("eval/fixtures/realworld-favorites/qualify.py")["classify"]
    assert classify({}) == "malformed_report"
    assert classify({"schema_version": "realworld-favorites-browser/v2",
                     "status": "complete", "assertions": {}}) == "malformed_report"
