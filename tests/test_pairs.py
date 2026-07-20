from pairs.loader import load_all_pairs, list_intent_ids


def test_loads_mesaflow_intents_plus_extensions():
    pairs = load_all_pairs()
    intent_ids = set(list_intent_ids(pairs))
    assert {"RF-04", "RF-07", "RF-09", "RF-13"}.issubset(intent_ids)
    assert "RF-09-ALT" in intent_ids
    assert "RF-13-SOFT" in intent_ids
    assert len(pairs) >= 6
    rf09 = next(p for p in pairs if p["intent_id"] == "RF-09")
    assert "5" in rf09["clean_requirement"]
    assert rf09["smell"]["type"] == "vague_threshold"
