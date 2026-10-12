from observability.trace_integrity import trace_receipt, verify_trace_continuity
from observability.tracing import ProvenanceRecorder
import pytest


def _trace(tmp_path, n=4, wire_version="2.0.5", profile=None):
    path = tmp_path / "trace.jsonl"
    rec = ProvenanceRecorder(path, wire_version=wire_version, profile=profile)
    for i in range(n):
        rec.operational("latency", {"ms": i})
    rec.close()
    return path


def test_intact_trace_has_no_problems(tmp_path):
    path = _trace(tmp_path)
    assert verify_trace_continuity(path, receipt=trace_receipt(path)) == []


def test_intact_v3_trace_has_no_problems(tmp_path):
    path = _trace(tmp_path, wire_version="3.0.0", profile="thesis")
    assert verify_trace_continuity(path) == []


def test_deleted_middle_event_is_detected_without_receipt(tmp_path):
    path = _trace(tmp_path)
    lines = path.read_text().splitlines()
    path.write_text("\n".join(lines[:1] + lines[2:]) + "\n")
    assert verify_trace_continuity(path)


def test_truncated_suffix_needs_the_receipt(tmp_path):
    path = _trace(tmp_path)
    receipt = trace_receipt(path)
    path.write_text("\n".join(path.read_text().splitlines()[:2]) + "\n")
    assert verify_trace_continuity(path) == []
    assert verify_trace_continuity(path, receipt=receipt)


def test_emptied_or_missing_trace_is_detected_with_receipt(tmp_path):
    path = _trace(tmp_path)
    receipt = trace_receipt(path)
    path.write_text("")
    assert verify_trace_continuity(path, receipt=receipt)
    path.unlink()
    assert verify_trace_continuity(path, receipt=receipt) == ["trace file is missing"]


def test_invalid_event_ids_are_reported_instead_of_accepted_or_crashing(tmp_path):
    import json
    for event_id in (None, '', [], {}, 7):
        path = tmp_path / 'bad.jsonl'
        path.write_text(json.dumps({'event_id': event_id, 'sequence_number': 0,
                                    'parent_event_id': None}) + '\n')
        assert verify_trace_continuity(path)


def test_boolean_sequence_number_is_rejected(tmp_path):
    path = tmp_path / 'bad.jsonl'
    path.write_text('{"event_id":"a","sequence_number":false,"parent_event_id":null}\n')
    assert verify_trace_continuity(path)


def test_invalid_utf8_is_reported(tmp_path):
    path = tmp_path / 'bad.jsonl'
    path.write_bytes(b'{"event_id":"\xff","sequence_number":0,"parent_event_id":null}\n')
    assert verify_trace_continuity(path)


@pytest.mark.parametrize("count", [True, 1.0, "1", -1, None])
def test_receipt_count_requires_a_nonnegative_integer(tmp_path, count):
    path = _trace(tmp_path, n=1)
    receipt = {**trace_receipt(path), "event_count": count}
    assert "receipt event_count must be a nonnegative integer" in verify_trace_continuity(path, receipt=receipt)


@pytest.mark.parametrize("receipt", [[], "receipt", 7])
def test_nonobject_receipt_is_reported_without_crashing(tmp_path, receipt):
    path = _trace(tmp_path)
    assert verify_trace_continuity(path, receipt=receipt) == ["receipt must be an object"]


@pytest.mark.parametrize("digest", [None, [], "", "g" * 64, "a" * 63])
def test_receipt_digest_requires_sha256_hex(tmp_path, digest):
    path = _trace(tmp_path)
    receipt = {**trace_receipt(path), "sha256": digest}
    assert "receipt sha256 must be 64 lowercase hexadecimal characters" in verify_trace_continuity(path, receipt=receipt)
