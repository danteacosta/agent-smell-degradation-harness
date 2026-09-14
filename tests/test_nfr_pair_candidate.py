import hashlib
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def test_candidate_is_single_deletion_bound_to_unchanged_source_pair():
    candidate = json.loads((ROOT / "data/oracle_review/nfr-single-deletion-candidate-v1.json").read_text())
    legacy = ROOT / "data/pairs/discovery/arta-nfr-002.json"
    assert hashlib.sha256(legacy.read_bytes()).hexdigest() == candidate["legacy_pair_sha256"]
    plane = candidate["generation_plane"]
    review = candidate["review_plane"]
    assert plane["clean_requirement"] == plane["defective_requirement"] + " " + review["removed_sentence"]
    assert candidate["review_status"] == "pending_independent_review"
    assert candidate["live_authorized"] is False
    assert candidate["confirmatory_eligible"] is False
    assert set(plane) == {"clean_requirement", "defective_requirement"}


def test_candidate_leaves_authorized_admission_unscored():
    candidate = json.loads((ROOT / "data/oracle_review/nfr-single-deletion-candidate-v1.json").read_text())
    oracle = candidate["review_plane"]["common_oracle"]
    assert len(oracle["scored_points"]) == 1
    point = oracle["scored_points"][0]
    assert point["input"] == {"authorized": False}
    assert point["expected_decision"] == "deny"
    assert oracle["unscored_points"][0]["input"] == {"authorized": True}
    assert "expected_decision" not in oracle["unscored_points"][0]
