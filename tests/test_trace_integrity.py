from observability.trace_integrity import trace_receipt, verify_trace_continuity
from observability.tracing import ProvenanceRecorder


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
