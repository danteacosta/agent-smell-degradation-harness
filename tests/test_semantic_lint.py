from observability.semantic_lint import lint_event, validate_events
from eval.runner import run_eval_with_agent


def test_eval_exports_semantic_lint_summary(tmp_path):
    class FakeAgent:
        provider = "replay"
        model = "model"

        def generate_with_meta(self, pair, variant, task_family):
            return pair["oracle_spec"][task_family], {
                "provider": self.provider,
                "model": self.model,
                "latency_ms": 1.0,
                "cost_usd": 0.0,
            }

    pair = {
        "intent_id": "I-1",
        "workload_id": "w-1",
        "clean_requirement": "Do the thing.",
        "smelly_requirement": "Do the thing.",
        "smell": {"type": "vague", "category": "ambiguity"},
        "oracle_spec": {"codegen": {"ok": True}, "test_gen": {"ok": True}},
    }
    _, episodes = run_eval_with_agent(
        FakeAgent(), pairs=[pair], output_path=tmp_path / "metrics.json", traces_dir=tmp_path / "traces"
    )
    assert episodes[0]["semantic_lint"]["finding_count"] == 0


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
