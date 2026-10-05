import json

from scripts import confirmatory_frame as cf


def test_frame_options_are_disjoint_from_everything_screened():
    screened = {c["candidate_id"] for p in cf.SCREENED for c in json.loads(p.read_text())["candidates"]}
    registered = {r["candidate_id"] for p in cf.FRAMES for r in cf.read_jsonl(p)}
    for name in ("reserve", "w2024"):
        doc = json.loads((cf.SAMPLING / f"screening-confirmatory-{name}-20261005.json").read_text())
        ids = [c["candidate_id"] for c in doc["candidates"]]
        assert len(ids) == len(set(ids)) and not set(ids) & screened
        assert all(set(c) >= {"candidate_id", "project", "file", "removed", "added"} for c in doc["candidates"])
        counts = {}
        for c in doc["candidates"]:
            counts[c["project"]] = counts.get(c["project"], 0) + 1
        assert max(counts.values()) <= cf.CAP
        if name == "reserve":
            assert set(ids) <= registered
        else:
            assert not set(ids) & registered
            assert all("2024-01-01" <= c["date"] <= "2024-12-31" for c in doc["candidates"])


def test_sample_is_seeded_and_capped():
    rows = [{"candidate_id": f"c{i}", "project": "p" if i % 2 else "q"} for i in range(100)]
    a, b = cf.sample(rows, 7, cap=10), cf.sample(rows, 7, cap=10)
    assert a == b and len(a) == 20
