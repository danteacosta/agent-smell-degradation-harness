import json

from eval.duplicate_selection_audit import audit_selection, main
from label_plane.annotation_protocol import _selection_manifest, select_duplicate_subset

IDS = [f"item-{i:03d}" for i in range(40)]


def _manifest(ids=IDS, seed=7):
    dup = set(select_duplicate_subset(ids, fraction=0.2, seed=seed))
    return _selection_manifest(item_count=len(ids), duplicate_ids=dup, fraction=0.2,
                               seed=seed, rubric_version="v1", task_kind="x")


def test_valid_manifest_passes():
    assert audit_selection(_manifest(), IDS) == {"errors": [], "warnings": []}


def test_tampered_selection_detected():
    m = _manifest()
    m["duplicate_item_ids"] = sorted(set(IDS[:8]))
    r = audit_selection(m, IDS)
    assert any("reproducible" in e or "sha256" in e for e in r["errors"])


def test_wrong_fraction_and_missing_ids():
    m = _manifest()
    m["duplicate_subset_fraction"] = 0.3
    assert any("0.2" in e for e in audit_selection(m, IDS)["errors"])
    assert any("item_count" in e for e in audit_selection(_manifest(), IDS[:-1])["errors"])


def test_outcome_like_ids_warn():
    ids = [f"p{i}-defective" for i in range(10)]
    r = audit_selection(_manifest(ids), ids)
    assert r["errors"] == [] and r["warnings"]


def test_cli_exit_codes(tmp_path):
    (tmp_path / "ids.json").write_text(json.dumps(IDS))
    (tmp_path / "m.json").write_text(json.dumps(_manifest()))
    assert main(["--manifest", str(tmp_path / "m.json"), "--item-ids", str(tmp_path / "ids.json")]) == 0
    bad = _manifest(); bad["duplicate_subset_seed"] = 99
    (tmp_path / "b.json").write_text(json.dumps(bad))
    assert main(["--manifest", str(tmp_path / "b.json"), "--item-ids", str(tmp_path / "ids.json")]) == 1
