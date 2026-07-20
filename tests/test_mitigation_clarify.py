from mitigation.clarify import apply_clarification_answer, build_clarification
from pairs.loader import load_all_pairs


def test_clarify_rf09_restores_clean():
    pair = next(p for p in load_all_pairs() if p["intent_id"] == "RF-09")
    q = build_clarification(pair)
    assert "5" in q.question or "threshold" in q.question.lower()
    resolved = apply_clarification_answer(pair, q, answer=q.simulated_answer)
    assert resolved.text == pair["clean_requirement"]
