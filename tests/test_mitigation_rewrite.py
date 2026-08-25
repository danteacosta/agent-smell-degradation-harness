from mitigation.rewrite import oracle_rewrite_upper_bound, rewrite_requirement
from mitigation.templates import rewrite_from_oracle_spec
from pairs.loader import load_all_pairs


def test_oracle_rewrite_upper_bound_restores_clean_text():
    pair = next(p for p in load_all_pairs() if p["intent_id"] == "RF-09")
    out = oracle_rewrite_upper_bound(pair["smelly_requirement"], pair)
    assert out.text == pair["clean_requirement"]
    assert out.changed is True


def test_oracle_template_upper_bound_reconstructs_from_oracle():
    pair = next(p for p in load_all_pairs() if p["intent_id"] == "RF-09")
    out = oracle_rewrite_upper_bound(
        pair["smelly_requirement"],
        pair,
        mode="oracle_template",
        task_family="codegen",
    )
    assert out.text != pair["smelly_requirement"]
    assert out.text != pair["clean_requirement"]
    assert "5" in out.text


def test_structured_rewrite_uses_only_received_text():
    smelly = "New orders delayed after significant time."
    out = rewrite_requirement(smelly)
    assert smelly in out.text
    assert "5" not in out.text
    assert "do not invent missing values" in out.text


def test_template_from_oracle_spec_includes_threshold():
    text = rewrite_from_oracle_spec(
        "vague_threshold",
        {"delay_threshold_minutes": 5, "comparator": ">"},
    )
    assert "5" in text
