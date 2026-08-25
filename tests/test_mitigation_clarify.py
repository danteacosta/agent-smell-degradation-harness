from mitigation.clarify import (
    apply_clarification_answer,
    build_clarification,
    oracle_clarification_upper_bound,
)
from pairs.loader import load_all_pairs


def test_targeted_clarification_uses_text_signal_and_independent_answer():
    pair = next(p for p in load_all_pairs() if p["intent_id"] == "RF-09")
    q = build_clarification(pair["smelly_requirement"])
    assert "threshold" in q.question.lower()
    assert "5" not in q.question
    resolved = apply_clarification_answer(
        pair["smelly_requirement"], q, answer="Use a strict five-minute boundary."
    )
    assert pair["smelly_requirement"] in resolved.text
    assert "Independent answer" in resolved.text
    assert resolved.text != pair["clean_requirement"]


def test_oracle_clarification_is_explicit_upper_bound():
    pair = next(p for p in load_all_pairs() if p["intent_id"] == "RF-09")
    assert oracle_clarification_upper_bound(pair).text == pair["clean_requirement"]
