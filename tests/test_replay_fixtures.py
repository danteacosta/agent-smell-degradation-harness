from __future__ import annotations

import json
from pathlib import Path

import pytest

from replay.runner import load_fixture
from replay.schema import validate_bundle_mapping

FIXTURES = Path(__file__).parents[1] / "replay" / "fixtures"


@pytest.mark.parametrize(
    ("case_id", "decision"),
    [
        ("clean", "approve"),
        ("constraint-loss", "block"),
        ("constraint-warning", "warn"),
        ("negative-control", "approve"),
        ("latency-only", "approve"),
    ],
)
def test_public_fixture_is_valid_and_expected_sidecar_pins_decision(case_id: str, decision: str) -> None:
    bundle = load_fixture(case_id, FIXTURES)
    validated = validate_bundle_mapping(bundle)
    assert validated["manifest"]["case_id"] == case_id
    sidecar = json.loads((FIXTURES / "expected.json").read_text(encoding="utf-8"))
    assert sidecar[case_id]["decision"] == decision
    assert sidecar[case_id]["trace"] == f"traces/{case_id}.jsonl"


def test_manifest_trace_hash_matches_raw_bytes() -> None:
    manifest = json.loads((FIXTURES / "manifest.json").read_text(encoding="utf-8"))
    assert manifest["checkpoint_schema_version"] == "pre-final/v1"
    for case in manifest["cases"]:
        raw = (FIXTURES / case["trace"]).read_bytes()
        assert case["trace_sha256"]
        assert len(case["trace_sha256"]) == 64
