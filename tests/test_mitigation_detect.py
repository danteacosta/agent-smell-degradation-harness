from mitigation.detect import detect_smell
from pairs.loader import load_all_pairs


def test_detect_flags_smelly_pair():
    pair = next(p for p in load_all_pairs() if p["intent_id"] == "RF-09")
    d = detect_smell(pair["smelly_requirement"], pair["smell"])
    assert d.detected is True
    assert d.smell_type == "vague_threshold"
