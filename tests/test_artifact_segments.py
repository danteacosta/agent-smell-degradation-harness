"""Exact evidence location, independently of any semantic judgment."""
import copy
import hashlib

import pytest


def api():
    from label_plane import artifact_segments
    return artifact_segments


@pytest.mark.parametrize("text", [
    "A short requirement.",
    "ação e\u0301 👩‍💻\r\n\r\n保持原文\t ",
    "Repeated text.\n" * 100,
    "x" * 20_000,
    "a\n" * 10_000,
    "\n" * 399 + "ü" * 500 + "\r\nend",
], ids=["short", "unicode-crlf", "repeated", "long-line", "many-lines", "whitespace"])
def test_snapshot_resolves_exact_original_bytes_deterministically(text):
    snapshot = api().build_snapshot(text)
    assert snapshot == api().build_snapshot(text)
    assert snapshot["artifact_sha256"] == hashlib.sha256(text.encode("utf-8")).hexdigest()
    spans = api().resolve_segments(snapshot, [s["id"] for s in snapshot["segments"]])
    assert "".join(s["text"] for s in spans) == text
    assert snapshot["byte_length"] == len(text.encode("utf-8"))
    cursor = 0
    for span in spans:
        assert span["start_byte"] == cursor
        assert text.encode("utf-8")[cursor:span["end_byte"]].decode("utf-8") == span["text"]
        assert 0 < len(span["text"]) <= 400
        cursor = span["end_byte"]
    assert cursor == snapshot["byte_length"]
    assert len({s["id"] for s in spans}) == len(spans)


def test_newline_boundary_is_preferred_without_dropping_long_line_suffix():
    text = "First line.\r\n" + "a" * 700
    spans = api().build_snapshot(text)["segments"]
    assert spans[0]["text"] == "First line.\r\n"
    assert "".join(s["text"] for s in spans[1:]) == "a" * 700


def test_same_phrase_in_different_artifact_cannot_reuse_evidence_id():
    first = api().build_snapshot("Shared phrase.\n" + "a" * 500)
    other = api().build_snapshot("Shared phrase.\n" + "b" * 500)
    with pytest.raises(ValueError, match="unknown_segment"):
        api().resolve_segments(other, [first["segments"][0]["id"]])


@pytest.mark.parametrize("mutation", [
    "text", "hash", "length", "policy", "schema", "offset", "id", "span_text",
    "removed", "duplicate", "reversed", "extra", "boolean_offset", "float_length",
])
def test_serialized_snapshot_tampering_is_rejected(mutation):
    snapshot = api().build_snapshot("PRIVATE sample.\n" + "x" * 600)
    bad = copy.deepcopy(snapshot)
    if mutation == "text": bad["text"] += "!"
    elif mutation == "hash": bad["artifact_sha256"] = "0" * 64
    elif mutation == "length": bad["byte_length"] += 1
    elif mutation == "policy": bad["policy"] = "other"
    elif mutation == "schema": bad["schema_version"] = "other"
    elif mutation == "offset": bad["segments"][0]["end_byte"] += 1
    elif mutation == "id": bad["segments"][0]["id"] = "invented"
    elif mutation == "span_text": bad["segments"][0]["text"] = "reference only"
    elif mutation == "removed": bad["segments"].pop()
    elif mutation == "duplicate": bad["segments"].append(bad["segments"][0])
    elif mutation == "reversed": bad["segments"].reverse()
    elif mutation == "extra": bad["oracle"] = "covered"
    elif mutation == "boolean_offset": bad["segments"][0]["start_byte"] = False
    elif mutation == "float_length": bad["byte_length"] = float(bad["byte_length"])
    with pytest.raises(ValueError) as error:
        api().resolve_segments(bad, [snapshot["segments"][0]["id"]])
    assert "PRIVATE" not in str(error.value)


@pytest.mark.parametrize("text", [None, 42, [], "", " \r\n\t", "x" * 20_001, "\ud800"],
                         ids=["null", "number", "list", "empty", "blank", "oversized", "surrogate"])
def test_invalid_or_oversized_text_is_rejected_without_normalization(text):
    with pytest.raises(ValueError, match="invalid_artifact"):
        api().build_snapshot(text)


@pytest.mark.parametrize("ids", [None, "seg-not-a-list", [False], ["unknown"], ["x"] * 257])
def test_bad_citation_inventory_fails_closed(ids):
    with pytest.raises(ValueError):
        api().resolve_segments(api().build_snapshot("content"), ids)


def test_duplicate_citation_rejected_and_returned_data_does_not_mutate_snapshot():
    snapshot = api().build_snapshot("content")
    identifier = snapshot["segments"][0]["id"]
    with pytest.raises(ValueError, match="duplicate_segment"):
        api().resolve_segments(snapshot, [identifier, identifier])
    api().resolve_segments(snapshot, [identifier])[0]["text"] = "changed"
    assert snapshot["segments"][0]["text"] == "content"
    assert api().resolve_segments(snapshot, []) == []
