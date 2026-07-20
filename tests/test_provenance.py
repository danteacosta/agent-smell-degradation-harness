from observability.tracing import ProvenanceRecorder


def test_records_semantic_and_operational_events(tmp_path):
    path = tmp_path / "trace.jsonl"
    rec = ProvenanceRecorder(path)
    rec.operational("latency", {"ms": 10})
    rec.semantic("constraint_extract", {"delay_threshold_minutes": 5})
    rec.close()
    lines = path.read_text().strip().splitlines()
    assert len(lines) == 2
    assert '"kind": "semantic"' in lines[1]
