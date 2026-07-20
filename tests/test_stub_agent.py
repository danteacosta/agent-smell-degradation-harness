from agents.stub import StubAgent
from pairs.loader import load_all_pairs


def test_stub_codegen_clean_rf09_emits_exact_threshold():
    pair = next(p for p in load_all_pairs() if p["intent_id"] == "RF-09")
    agent = StubAgent(failure_mode=None)
    art = agent.generate(pair, variant="clean", task_family="codegen")
    assert art == pair["oracle_spec"]["codegen"]


def test_stub_smell_blind_weakens_rf09():
    pair = next(p for p in load_all_pairs() if p["intent_id"] == "RF-09")
    agent = StubAgent(failure_mode="smell-blind")
    art = agent.generate(pair, variant="smelly", task_family="codegen")
    assert art["comparator"] != ">"


def test_stub_smell_blind_weakens_rf09_test_gen():
    pair = next(p for p in load_all_pairs() if p["intent_id"] == "RF-09")
    agent = StubAgent(failure_mode="smell-blind")
    art = agent.generate(pair, variant="smelly", task_family="test_gen")
    assert art["must_reject_minutes"] == []
