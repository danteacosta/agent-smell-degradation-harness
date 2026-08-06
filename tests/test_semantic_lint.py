from observability.semantic_lint import lint_event, validate_events


def test_lint_reports_missing_provenance():
    findings = lint_event({"event_type": "tool.completed", "attributes": {}})
    assert any(item.code == "missing_source_refs" for item in findings)


def test_lint_reports_label_field_in_pre_final_plane():
    findings = lint_event(
        {
            "event_type": "handoff.created",
            "plane": "pre_final",
            "source_refs": [{"kind": "tool", "identifier": "t1"}],
            "attributes": {"oracle_verdict": "pass"},
        }
    )
    assert any(item.code == "cross_plane_label" for item in findings)


def test_validate_events_strict_raises_with_structured_codes():
    try:
        validate_events([{"event_type": "tool.completed", "attributes": {}}], strict=True)
    except ValueError as exc:
        assert "missing_source_refs" in str(exc)
    else:
        raise AssertionError("strict validation must reject missing provenance")
