from mitigation.rewrite import rewrite_requirement
from mitigation.templates import rewrite_from_oracle_spec
from pairs.loader import load_all_pairs


def test_rewrite_oracle_mode_restores_clean_text():
    pair = next(p for p in load_all_pairs() if p["intent_id"] == "RF-09")
    out = rewrite_requirement(pair["smelly_requirement"], pair, mode="oracle")
    assert out.text == pair["clean_requirement"]
    assert out.changed is True


def test_rewrite_template_mode_reconstructs_from_oracle():
    pair = next(p for p in load_all_pairs() if p["intent_id"] == "RF-09")
    out = rewrite_requirement(
        pair["smelly_requirement"],
        pair,
        mode="template",
        task_family="codegen",
    )
    assert out.text != pair["smelly_requirement"]
    assert out.text != pair["clean_requirement"]
    assert "5" in out.text


def test_template_from_oracle_spec_includes_threshold():
    text = rewrite_from_oracle_spec(
        "vague_threshold",
        {"delay_threshold_minutes": 5, "comparator": ">"},
    )
    assert "5" in text
