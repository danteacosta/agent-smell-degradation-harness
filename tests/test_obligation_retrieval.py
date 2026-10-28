"""Tests for scripts/obligation_retrieval.py (no network; the documentation cache is not needed)."""
import json

from scripts import obligation_retrieval as ob


def test_omitted_span_is_the_removed_words():
    a = "Saving edits updates values. A Remaining value greater than Work cannot be saved."
    c = "Saving edits updates values."
    assert ob.omitted_span(a, c)[:3] == ["a", "remaining", "value"]


def test_bm25_ranks_the_matching_passage_first():
    docs = [ob.content(ob.words(t)) for t in
            ["closing a task completes pending subtasks", "the board shows columns", "users can upload files"]]
    bm = ob.BM25(docs)
    sc = bm.scores(ob.content(ob.words("close task pending subtasks")))
    assert sc.index(max(sc)) == 0


def test_strip_markup_keeps_link_text():
    assert "docs" in ob.strip_markup("see [the docs](http://x) and <b>bold</b>")


def test_source_files_are_relative_to_root():
    d = {"source": {"file": "help/en/docs/a.md", "snapshot_file": "help/en/docs/b.md"}}
    assert ob.source_files(d, "help/en/docs") == ["b.md"]


def test_published_results_cover_all_qp4_requirements():
    r = json.loads(ob.OUT.read_text())
    assert r["requirements"] == 25 and r["model_calls"] == 0
    assert set(r["recall_query_incomplete"]) == {"1", "3", "5", "10", "20"}


# ---------------------------------------------------------------- snapshot verification (offline)

import subprocess  # noqa: E402

import pytest  # noqa: E402


def _repo(tmp_path, name="snap"):
    d = tmp_path / name
    d.mkdir()
    g = lambda *a: subprocess.run(["git", "-C", str(d), *a], check=True, capture_output=True, text=True).stdout.strip()  # noqa: E731
    g("init", "-q")
    g("config", "user.email", "t@example.org")
    g("config", "user.name", "t")
    (d / "docs").mkdir()
    (d / "docs" / "a.md").write_text("Closing a task completes pending subtasks.\n")
    (d / "other.txt").write_text("outside the sparse paths\n")
    g("add", ".")
    g("commit", "-q", "-m", "one")
    sha = g("rev-parse", "HEAD")
    g("remote", "add", "origin", "https://example.org/repo")
    g("sparse-checkout", "set", "--no-cone", "/docs/")
    return d, {"url": "https://example.org/repo", "sha": sha, "paths": ["/docs/"]}, g


def test_verify_accepts_the_pinned_clean_snapshot(tmp_path):
    d, spec, _ = _repo(tmp_path)
    ob.verify_snapshot(d, spec)


def test_verify_rejects_other_commit(tmp_path):
    d, spec, g = _repo(tmp_path)
    (d / "docs" / "a.md").write_text("changed\n")
    g("commit", "-q", "-am", "two")
    with pytest.raises(ob.SnapshotError, match="HEAD"):
        ob.verify_snapshot(d, spec)


def test_verify_rejects_dirty_or_untracked_tree(tmp_path):
    d, spec, _ = _repo(tmp_path)
    (d / "docs" / "a.md").write_text("edited in place\n")
    with pytest.raises(ob.SnapshotError, match="working tree"):
        ob.verify_snapshot(d, spec)
    d2, spec2, _ = _repo(tmp_path, "snap2")
    (d2 / "docs" / "extra.md").write_text("planted passage\n")
    with pytest.raises(ob.SnapshotError, match="working tree"):
        ob.verify_snapshot(d2, spec2)


def test_verify_rejects_wrong_origin_and_sparse_paths(tmp_path):
    d, spec, _ = _repo(tmp_path)
    with pytest.raises(ob.SnapshotError, match="origin"):
        ob.verify_snapshot(d, {**spec, "url": "https://example.org/other"})
    with pytest.raises(ob.SnapshotError, match="sparse"):
        ob.verify_snapshot(d, {**spec, "paths": ["/help/"]})


def test_verify_rejects_partial_fetch_and_non_repo(tmp_path):
    d = tmp_path / "partial"
    d.mkdir()
    subprocess.run(["git", "-C", str(d), "init", "-q"], check=True)  # interrupted before checkout: no HEAD
    with pytest.raises(ob.SnapshotError):
        ob.verify_snapshot(d, {"url": "u", "sha": "0" * 40, "paths": []})
    plain = tmp_path / "plain"
    plain.mkdir()
    with pytest.raises(ob.SnapshotError, match="not a git checkout"):
        ob.verify_snapshot(plain, {"url": "u", "sha": "0" * 40, "paths": []})


def test_fetch_refuses_to_reuse_an_unverified_directory(tmp_path, monkeypatch):
    (tmp_path / "cache").mkdir()
    d, spec, _ = _repo(tmp_path / "cache", "grist")
    manifest = tmp_path / "sources.json"
    manifest.write_text(json.dumps({"snapshots": {"grist": {**spec, "sha": "f" * 40}}, "cases": {}}))
    monkeypatch.setattr(ob, "SOURCES", manifest)
    with pytest.raises(ob.SnapshotError, match="HEAD"):
        ob.fetch(tmp_path / "cache")


def test_ignored_file_passes_verification_but_is_not_indexed(tmp_path):
    # Reproduces Codex's 28/10 case: an ignored document leaves HEAD and status
    # unchanged, so the corpus must come from committed blobs, not the working tree.
    d, spec, g = _repo(tmp_path)
    g("sparse-checkout", "disable")
    (d / ".gitignore").write_text("docs/ignored.md\n")
    g("add", ".gitignore")
    g("commit", "-q", "-m", "ignore")
    g("sparse-checkout", "set", "--no-cone", "/docs/", "/.gitignore")
    spec = {**spec, "sha": g("rev-parse", "HEAD"), "paths": ["/docs/", "/.gitignore"]}
    (d / "docs" / "ignored.md").write_text("Planted passage about pending subtasks and closing tasks.\n")
    ob.verify_snapshot(d, spec)  # status does not see ignored files
    texts = [p["text"] for p in ob.snapshot_passages(d, "docs", spec["paths"])]
    assert any("closing a task completes pending subtasks" in t for t in texts)
    assert not any("planted" in t for t in texts)
    assert any("planted" in p["text"] for p in ob.passages(d / "docs"))  # the old path would have indexed it


def test_snapshot_passages_read_committed_content_and_pinned_paths_only(tmp_path):
    d, spec, g = _repo(tmp_path)
    files = dict(ob.snapshot_files(d, "", ["/docs/"]))
    assert list(files) == ["docs/a.md"]  # other.txt is outside the pinned paths and not a doc
    assert files["docs/a.md"].startswith("Closing a task")
