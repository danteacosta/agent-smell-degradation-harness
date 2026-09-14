import json

import pytest

from label_plane.draft_packets import DRAFTS, export, prepare, sha, prompt


def test_export_projects_only_prompt_text_and_verifies_hashes(tmp_path):
    out = tmp_path / "drafts"
    result = export(out)
    assert result["file_count"] == 7
    assert result["live_authorized"] is False
    receipt = json.loads((out / "review/receipt.json").read_text())
    for name, digest in receipt["files"].items():
        assert sha((out / name).read_bytes()) == digest
    for path in DRAFTS:
        draft = json.loads(path.read_text())
        for variant in ("clean", "defective"):
            text = (out / "generation" / draft["intent_id"] / (variant + ".txt")).read_text()
            assert text == prompt(draft["generation_plane"][variant + "_requirement"], draft["intent_id"])
            assert "expected_decision" not in text
            assert "removed_sentence" not in text
        clean = (out / "generation" / draft["intent_id"] / "clean.txt").read_text()
        defective = (out / "generation" / draft["intent_id"] / "defective.txt").read_text()
        assert clean.replace(" " + draft["review_plane"]["removed_sentence"], "", 1) == defective
    assert (out.stat().st_mode & 0o777) == 0o700
    assert all(p.stat().st_mode & 0o777 == 0o600 for p in out.rglob("*") if p.is_file())
    original = (out / "review/receipt.json").read_bytes()
    with pytest.raises(FileExistsError):
        export(out)
    assert (out / "review/receipt.json").read_bytes() == original


@pytest.mark.parametrize("fault", ["oracle_in_prompt", "approved", "second_change", "source", "unscored_label"])
def test_invalid_second_candidate_creates_no_output(tmp_path, fault):
    draft = json.loads(DRAFTS[1].read_text())
    if fault == "oracle_in_prompt":
        draft["generation_plane"]["oracle"] = "secret"
    elif fault == "approved":
        draft["live_authorized"] = True
    elif fault == "second_change":
        draft["generation_plane"]["clean_requirement"] += " Another condition."
    elif fault == "source":
        draft["source_revision"] = "other"
    else:
        draft["review_plane"]["common_oracle"]["unscored_points"][0]["expected_decision"] = "allow"
    bad = tmp_path / "bad.json"
    bad.write_text(json.dumps(draft))
    out = tmp_path / "result"
    with pytest.raises(ValueError):
        export(out, [DRAFTS[0], bad])
    assert not out.exists()


def test_preparation_is_deterministic_and_keeps_draft_status():
    assert prepare() == prepare()
    receipt = json.loads(prepare()["review/receipt.json"])
    assert receipt["confirmatory_eligible"] is False
    assert len(receipt["candidates"]) == 2


def test_partial_oracles_admit_constant_rejection_without_validating_full_behavior():
    receipt = json.loads(prepare()["review/receipt.json"])
    for candidate, decision in zip(receipt["candidates"], ("deny", "reject")):
        diagnostic = candidate["oracle_scope_diagnostic"]
        assert diagnostic["possible_tables"] == 4
        assert diagnostic["compatible_tables"] == 2
        assert diagnostic["constant_responses_compatible"] == [decision]
        assert diagnostic["full_behavior_validated"] is False


@pytest.mark.parametrize("fault", ["overlap", "integer_boolean", "wrong_argument", "invalid_decision", "wrong_constraint"])
def test_malformed_partial_oracle_creates_no_output(tmp_path, fault):
    draft = json.loads(DRAFTS[0].read_text())
    oracle = draft["review_plane"]["common_oracle"]
    point = oracle["scored_points"][0]
    if fault == "overlap":
        oracle["unscored_points"][0]["input"] = point["input"].copy()
    elif fault == "integer_boolean":
        point["input"]["authorized"] = 0
    elif fault == "wrong_argument":
        point["input"] = {"malicious": False}
    elif fault == "invalid_decision":
        point["expected_decision"] = "maybe"
    else:
        point["constraint_id"] = "unrelated-condition"
    bad = tmp_path / "bad.json"
    bad.write_text(json.dumps(draft))
    out = tmp_path / "result"
    with pytest.raises(ValueError):
        export(out, [bad])
    assert not out.exists()


@pytest.mark.parametrize("intent,good,bad", [
    ("ARTA-NFR-002", "def evaluate(authorized):\n    return 'deny'", "def evaluate(authorized):\n    return 'allow'"),
    ("ARTA-PEERING-001", "def evaluate(malicious):\n    return 'reject'", "def evaluate(malicious):\n    return 'allow'"),
])
def test_native_test_projection_distinguishes_original_control_outputs(intent, good, bad):
    # These literal controls test format compatibility, not a model or source semantics.
    from eval.codegen_sandbox import evaluate_trusted_fixture

    files = prepare()
    review = json.loads(files[f"review/{intent}.json"])
    native = review["executor_test_draft"]
    point = review["review_plane"]["common_oracle"]["scored_points"][0]
    assert native["live_authorized"] is False
    assert native["hidden_tests"] == [{"id": point["constraint_id"], "constraint_id": point["constraint_id"],
                                       "args": [], "kwargs": point["input"], "expected": point["expected_decision"]}]
    assert evaluate_trusted_fixture(good, native["hidden_tests"])["status"] == "passed"
    assert evaluate_trusted_fixture(bad, native["hidden_tests"])["status"] == "failed"
    assert len(native["unscored_points"]) == 1
    for variant in ("clean", "defective"):
        assert b"hidden_tests" not in files[f"generation/{intent}/{variant}.txt"]
        assert b"constraint_id" not in files[f"generation/{intent}/{variant}.txt"]
