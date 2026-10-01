"""Acceptance checks for the frozen RealWorld author-only Delete replication."""
from collections import Counter
import hashlib

import pytest

from scripts import realworld_comment_delete_replication as pilot


def test_fresh_balanced_schedule_and_exact_prior_prompts():
    rows = pilot.schedule()
    assert len(rows) == len({row["slot_id"] for row in rows}) == 18
    assert Counter((row["model"], row["arm"]) for row in rows) == {
        (model, arm): 3 for model in pilot.MODELS for arm in pilot.ARMS}
    assert pilot.SEED == 2026100103
    assert {arm: hashlib.sha256(pilot.prompt(arm).encode()).hexdigest() for arm in pilot.ARMS} == {
        "A": "ed469dda355ec0ed7ff1802704279ddc02ddc8929a8c621d7b6c0ca1396ec60a",
        "B": "54a11f2ee27b12a9fafbe2e69d8afc266adc64d287d6a67c2bcf7d0a0f91edbb",
        "C": "5f737a7c017d8f9d1228821d72d08d63713b3e8316fbb1d3cb84d4c322be0854",
    }


def test_altered_shell_is_rejected_and_unattempted_slots_are_explicit(tmp_path):
    with pytest.raises(ValueError):
        pilot.admit("<html>different shell</html>")
    rows = pilot.generated_rows(tmp_path, pilot.schedule())
    assert len(rows) == 18
    assert {row["category"] for row in rows} == {"not_attempted"}
