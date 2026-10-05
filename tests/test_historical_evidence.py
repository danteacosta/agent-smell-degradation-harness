import hashlib
import json

from scripts import historical_evidence as he


def test_table_matches_the_frozen_pair_counts():
    data = he.table(None)
    verdicts = [p["verdict"] for r in data["rows"] for p in r["pairs"]]
    assert data["requirements"] == 17 and data["requirements_where_t1_and_tn_differ"] == 8
    assert verdicts.count("t1_worse") == 25 and verdicts.count("t1_better") == 0
    assert verdicts.count("both_held") == 27 and verdicts.count("both_violated") == 13
    assert verdicts.count("unknown") == 3
    for r in data["rows"]:
        assert r["change"]["url"].startswith("https://github.com/") and r["omitted_rule"] in r["tn"]


def test_screenshot_copy_checks_hashes(tmp_path, monkeypatch):
    monkeypatch.setattr(he, "OUT", tmp_path / "out")
    good, bad = b"\x89PNG good", b"\x89PNG tampered"
    digest = hashlib.sha256(good).hexdigest()
    row = {"case": "c", "pairs": [{"model": "m", "replication": 1, "verdict": "t1_worse",
                                   "t1": {"slot_id": "s1", "screenshots": {"a.png": digest}},
                                   "tn": {"slot_id": "s2", "screenshots": {"a.png": digest}}}]}
    (tmp_path / "p/c/execution/s1/x").mkdir(parents=True)
    (tmp_path / "p/c/execution/s1/x/a.png").write_bytes(good)
    (tmp_path / "p/c/execution/s2").mkdir(parents=True)
    (tmp_path / "p/c/execution/s2/a.png").write_bytes(bad)
    result = he.collect_screenshots({"rows": [row]}, tmp_path / "p")
    assert result == {"copied": 1, "missing": ["screenshots/c/m-r1-tn-a.png"]}
    page = he.gallery({"requirements": 1, "requirements_where_t1_and_tn_differ": 1,
                       "rows": [{**row, "differs": True, "change": {"commit": "abc", "url": "https://x"},
                                 "omitted_rule": "r", "t1_kind": "rule absent", "t1_old_passage": None}]})
    assert page.count("data:image/png;base64") == 1 and "print não publicado" in page
    json.dumps(result)
