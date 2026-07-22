from __future__ import annotations

import json
from pathlib import Path

import pytest

from pairs.loader import load_all_pairs
from pairs.validate import validate_pair


def test_load_all_pairs_validates_schema():
    pairs = load_all_pairs()
    assert len(pairs) >= 7


def test_missing_intent_id_raises():
    with pytest.raises(ValueError, match="intent_id"):
        validate_pair({"smelly_requirement": "x"}, source="test")


def test_missing_oracle_family_raises():
    pair = {
        "intent_id": "X",
        "clean_requirement": "c",
        "smelly_requirement": "s",
        "smell": {"category": "semantic", "type": "t", "injection_rule": "r"},
        "oracle_spec": {"codegen": {}},
    }
    with pytest.raises(ValueError, match="test_gen"):
        validate_pair(pair, source="test")


def test_invalid_pair_file_rejected(tmp_path):
    bad = tmp_path / "bad.json"
    bad.write_text(json.dumps({"intent_id": "BAD"}), encoding="utf-8")
    with pytest.raises(ValueError):
        load_all_pairs(tmp_path)


def test_rf09_alt_shares_oracle_with_rf09():
    pairs = load_all_pairs()
    rf09 = next(p for p in pairs if p["intent_id"] == "RF-09")
    alt = next(p for p in pairs if p["intent_id"] == "RF-09-ALT")
    assert rf09["oracle_spec"] == alt["oracle_spec"]
    assert alt["clean_requirement"] != rf09["clean_requirement"]
