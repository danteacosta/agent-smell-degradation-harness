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
