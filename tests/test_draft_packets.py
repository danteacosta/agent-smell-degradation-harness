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
