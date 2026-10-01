"""Portable schedule contract for the full post-interruption collection."""
from collections import Counter
import hashlib

from scripts import paperless_inbox_suggestions_pilot_v2 as prior
from scripts import paperless_inbox_suggestions_pilot_v3 as current


def test_v3_preserves_prompts_and_uses_distinct_balanced_positions():
    rows = current.schedule()
    assert len(rows) == len({row["slot_id"] for row in rows}) == 18
    assert Counter((row["model"], row["arm"]) for row in rows) == {
        (model, arm): 3 for model in current.MODELS for arm in current.ARMS}
    assert {row["slot_id"] for row in rows}.isdisjoint({row["slot_id"] for row in prior.schedule()})
    assert current.SEED != prior.SEED
    assert {arm: hashlib.sha256(current.prompt(arm).encode()).hexdigest() for arm in current.ARMS} == {
        arm: hashlib.sha256(prior.prompt(arm).encode()).hexdigest() for arm in prior.ARMS}
