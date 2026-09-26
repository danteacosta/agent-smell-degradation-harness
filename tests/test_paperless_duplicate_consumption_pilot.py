"""Observable admission and sample-frame contracts for the Paperless pilot."""
import runpy
from collections import Counter

import pytest

from scripts import paperless_duplicate_consumption_pilot as pilot


def test_eighteen_new_requests_are_balanced_and_use_one_frozen_page(monkeypatch):
    monkeypatch.setattr(pilot, "arms", lambda: {arm: f"requirement {arm}" for arm in pilot.ARMS})
    rows = pilot.schedule()
    assert len(rows) == len({row["slot_id"] for row in rows}) == 18
    assert Counter((row["model"], row["arm"]) for row in rows) == {
        (model, arm): 3 for model in pilot.MODELS for arm in pilot.ARMS}
    assert all("/* MODEL_BEHAVIOR */" in pilot.prompt(row["arm"]) for row in rows)


def test_generated_page_must_preserve_the_frozen_interface():
    with pytest.raises(ValueError):
        pilot.admit("<html><body>different page</body></html>")


def test_incomplete_or_malformed_browser_report_is_never_a_pass():
    classify = runpy.run_path("eval/fixtures/paperless-duplicate-consumption/qualify.py")["classify"]
    assert classify({}) == "malformed_report"
    assert classify({"schema_version": "paperless-duplicate-consumption-browser/v1",
                     "status": "complete", "assertions": {}}) == "malformed_report"
