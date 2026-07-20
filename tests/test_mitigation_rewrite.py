from mitigation.rewrite import rewrite_requirement
from pairs.loader import load_all_pairs


def test_rewrite_restores_clean_text():
    pair = next(p for p in load_all_pairs() if p["intent_id"] == "RF-09")
    out = rewrite_requirement(pair["smelly_requirement"], pair)
    assert out.text == pair["clean_requirement"]
    assert out.changed is True
