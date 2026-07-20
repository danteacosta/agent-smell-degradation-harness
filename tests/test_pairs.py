from pairs.loader import load_all_pairs, list_intent_ids


def test_loads_four_mesaflow_intents():
    pairs = load_all_pairs()
    assert set(list_intent_ids(pairs)) == {"RF-04", "RF-07", "RF-09", "RF-13"}
    rf09 = next(p for p in pairs if p["intent_id"] == "RF-09")
    assert "5" in rf09["clean_requirement"]
    assert rf09["smell"]["type"] == "vague_threshold"
