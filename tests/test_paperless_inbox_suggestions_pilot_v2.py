"""Portable checks for the versioned Paperless browser collection."""
from collections import Counter
import hashlib

from scripts import paperless_inbox_suggestions_pilot as prior
from scripts import paperless_inbox_suggestions_pilot_v2 as current


def test_successor_keeps_prompts_but_gets_new_balanced_slot_ids():
    rows = current.schedule()
    assert len(rows) == len({row["slot_id"] for row in rows}) == 18
    assert Counter((row["model"], row["arm"]) for row in rows) == {
        (model, arm): 3 for model in current.MODELS for arm in current.ARMS}
    assert {row["slot_id"] for row in rows}.isdisjoint({row["slot_id"] for row in prior.schedule()})
    assert current.SEED != prior.SEED
    assert {arm: hashlib.sha256(current.prompt(arm).encode()).hexdigest() for arm in current.ARMS} == {
        arm: hashlib.sha256(prior.prompt(arm).encode()).hexdigest() for arm in prior.ARMS}
