from __future__ import annotations

import json
from pathlib import Path

import pytest

from eval.discovery_verifier import (
    compute_efficacy_metrics,
    deduplicate_repeated_rows,
    derive_observable_signals,
    score_observable_episode,
    verify_bundle,
)


def _trace(path: Path, *, terminal: bool = False) -> Path:
    events = [
        {
            "event_id": "event-0",
            "checkpoint": "input.received",
            "event_type": "input.received",
            "started_at": "2026-08-26T12:00:00+00:00",
            "ended_at": "2026-08-26T12:00:00+00:00",
            "attributes": {"intent_id": "I-1", "task_family": "behavior_codegen"},
        },
        {
            "event_id": "event-1",
            "checkpoint": "interpretation.completed",
            "event_type": "interpretation.completed",
            "started_at": "2026-08-26T12:00:01+00:00",
            "ended_at": "2026-08-26T12:00:01+00:00",
            "attributes": {
                "constraints": ["detect malicious requests"],
                "quantities": [],
                "unresolved_references": [],
                "assumptions": [],
                "contradictions": [],
            },
        },
        {
            "event_id": "event-2",
            "checkpoint": "plan.completed",
            "event_type": "plan.completed",
            "started_at": "2026-08-26T12:00:02+00:00",
            "ended_at": "2026-08-26T12:00:02+00:00",
            "attributes": {
                "validation_checks": ["behavior"],
                "planned_tools": [],
                "coverage_targets": ["response"],
            },
        },
    ]
    if terminal:
        events[1]["attributes"]["oracle_passed"] = False
    path.write_text("\n".join(json.dumps(event) for event in events) + "\n", encoding="utf-8")
    return path


def _episode(*, intent_id: str = "I-1", variant: str = "smelly", requirement: str) -> dict:
    return {
        "episode_id": f"episode-{intent_id}-{variant}",
        "intent_id": intent_id,
        "task_family": "behavior_codegen",
        "variant": variant,
        "smell": {"type": "incomplete_response"},
        "requirement_text": requirement,
        "artifact": {"source_code": "return True"},
        "oracle_passed": False,
        "behavior_status": "failed_target_condition",
        "project_id": "project-a",
        "provider_meta": {"latency_ms": 12.0, "cost_usd": 0.01},
    }


def test_observable_score_ignores_terminal_episode_fields(tmp_path: Path):
    trace = _trace(tmp_path / "trace.jsonl")
    episode = _episode(requirement="The system shall detect malicious requests.")

    result = score_observable_episode(episode, trace)

    assert result["decision"] in {"warn", "block"}
    serialized = json.dumps(result, sort_keys=True)
    assert "oracle_passed" not in serialized
    assert "failed_target_condition" not in serialized
    assert "incomplete_response" not in serialized
    assert "source_code" not in serialized


def test_completeness_scope_uses_word_boundaries_for_all_marker():
    smelly = derive_observable_signals(
        "The system shall consider anticipated user requests.", {}
    )
    clean = derive_observable_signals(
        "The system shall consider both anticipated and unanticipated user requests.",
        {},
    )

    assert "incomplete_completeness_scope" in {signal["code"] for signal in smelly}
    assert "incomplete_completeness_scope" not in {signal["code"] for signal in clean}


def test_observable_score_is_independent_of_variant_and_smell_metadata(tmp_path: Path):
    trace = _trace(tmp_path / "trace.jsonl")
    requirement = "The system shall detect malicious requests."
    smelly = score_observable_episode(
        _episode(variant="smelly", requirement=requirement), trace
    )
    clean_metadata = _episode(variant="clean", requirement=requirement)
    clean_metadata["smell"] = None
    clean_metadata["oracle_passed"] = True
    clean_metadata["behavior_status"] = "passed"
    clean = score_observable_episode(clean_metadata, trace)

    assert smelly["risk_score"] == clean["risk_score"]
    assert smelly["signal_codes"] == clean["signal_codes"]
    assert smelly["decision"] == clean["decision"]


def test_terminal_field_in_observable_trace_fails_closed(tmp_path: Path):
    with pytest.raises(ValueError, match="terminal|label|oracle"):
        score_observable_episode(
            _episode(requirement="The system shall detect malicious requests."),
            _trace(tmp_path / "unsafe.jsonl", terminal=True),
        )


def test_efficacy_metrics_report_confusion_pairing_and_strata():
    rows = [
        {"episode_id": "i1-clean", "intent_id": "I-1", "project_id": "P-1", "smell_type": None, "task_family": "behavior_codegen", "variant": "clean", "risk_score": 0.1, "decision": "approve", "label": 0, "first_signal_checkpoint": None},
        {"episode_id": "i1-smelly", "intent_id": "I-1", "project_id": "P-1", "smell_type": "vague_threshold", "task_family": "behavior_codegen", "variant": "smelly", "risk_score": 0.8, "decision": "block", "label": 1, "first_signal_checkpoint": "T0"},
        {"episode_id": "i2-clean", "intent_id": "I-2", "project_id": "P-2", "smell_type": None, "task_family": "behavior_codegen", "variant": "clean", "risk_score": 0.2, "decision": "approve", "label": 0, "first_signal_checkpoint": None},
        {"episode_id": "i2-smelly", "intent_id": "I-2", "project_id": "P-2", "smell_type": "loophole", "task_family": "behavior_codegen", "variant": "smelly", "risk_score": 0.7, "decision": "warn", "label": 1, "first_signal_checkpoint": "T0"},
    ]

    metrics = compute_efficacy_metrics(rows)

    assert metrics["confusion"] == {"tp": 2, "fp": 0, "tn": 2, "fn": 0}
    assert metrics["recall"] == 1.0
    assert metrics["precision"] == 1.0
    assert metrics["f1"] == 1.0
    assert metrics["false_alert_rate"] == 0.0
    assert metrics["paired_discrimination"]["rate"] == 1.0
    assert metrics["strata"]["project_id"]["P-1"]["recall"] == 1.0
    assert metrics["status"] == "promising"
    intervals = metrics["confidence_intervals"]
    assert intervals["recall"]["successes"] == 2
    assert intervals["recall"]["trials"] == 2
    assert intervals["precision"]["trials"] == 2
    assert intervals["specificity"]["trials"] == 2
    assert intervals["false_alert_rate"]["trials"] == 2
    assert intervals["paired_discrimination"]["trials"] == 2
    assert intervals["recall"]["method"] == "wilson"
    assert intervals["recall"]["confidence"] == 0.95
    assert intervals["recall"]["lower"] < intervals["recall"]["estimate"] < intervals["recall"]["upper"]


def test_repeated_rows_are_deduplicated_and_stability_checks_replication_ids():
    rows = []
    for replication_id in range(5):
        for variant, label, score, decision in (
            ("clean", 0, 0.1, "approve"),
            ("smelly", 1, 0.8, "block"),
        ):
            rows.append(
                {
                    "episode_id": f"episode-{replication_id}-{variant}",
                    "intent_id": "I-1",
                    "task_family": "behavior_codegen",
                    "variant": variant,
                    "replication_id": replication_id,
                    "label": label,
                    "risk_score": score,
                    "decision": decision,
                }
            )

    unique_rows, stability = deduplicate_repeated_rows(rows, expected_replications=5)

    assert len(unique_rows) == 2
    assert stability["key_count"] == 2
    assert stability["observed_replications"] == [0, 1, 2, 3, 4]
    assert stability["missing_replications"] == []
    assert stability["duplicate_replications"] == []
    assert stability["unstable_key_count"] == 0
    assert stability["all_repetitions_agree"] is True


def test_repeated_rows_report_missing_and_duplicate_replications():
    base = {
        "episode_id": "episode",
        "intent_id": "I-1",
        "task_family": "behavior_codegen",
        "variant": "smelly",
        "label": 1,
        "risk_score": 0.8,
        "decision": "block",
    }
    rows = [
        {**base, "replication_id": 0, "episode_id": "episode-0"},
        {**base, "replication_id": 0, "episode_id": "episode-0-duplicate"},
        {**base, "replication_id": 2, "episode_id": "episode-2"},
    ]

    _unique_rows, stability = deduplicate_repeated_rows(rows, expected_replications=3)

    assert stability["observed_replications"] == [0, 2]
    assert stability["missing_replications"] == [1]
    assert stability["duplicate_replications"] == [0]
    assert stability["all_repetitions_agree"] is False


def test_efficacy_metrics_are_inconclusive_without_both_classes():
    metrics = compute_efficacy_metrics(
        [{"episode_id": "only-positive", "intent_id": "I-1", "variant": "smelly", "risk_score": 0.8, "decision": "block", "label": 1}]
    )

    assert metrics["status"] == "inconclusive"
    assert metrics["eligible_count"] == 1
    assert metrics["false_alert_rate"] is None


def test_verify_bundle_writes_decisions_without_labels_and_metrics(tmp_path: Path):
    bundle = tmp_path / "bundle"
    traces = bundle / "observable-traces"
    traces.mkdir(parents=True)
    clean_trace = _trace(traces / "clean.jsonl")
    smelly_trace = _trace(traces / "smelly.jsonl")
    episodes = [
        {
            **_episode(intent_id="I-1", variant="clean", requirement="The system shall detect malicious requests and reject them."),
            "behavior_status": "passed",
            "oracle_passed": True,
            "observable_trace_path": "observable-traces/clean.jsonl",
        },
        {
            **_episode(intent_id="I-1", variant="smelly", requirement="The system shall detect malicious requests."),
            "observable_trace_path": "observable-traces/smelly.jsonl",
        },
    ]
    (bundle / "episodes.jsonl").write_text(
        "\n".join(json.dumps(episode) for episode in episodes) + "\n", encoding="utf-8"
    )

    report = verify_bundle(bundle)

    assert report["metrics"]["eligible_count"] == 2
    decisions = [
        json.loads(line)
        for line in (bundle / "verification" / "decisions.jsonl").read_text().splitlines()
        if line.strip()
    ]
    assert len(decisions) == 2
    assert all("label" not in decision and "variant" not in decision for decision in decisions)
    assert (bundle / "verification" / "metrics.json").is_file()
    assert (bundle / "verification" / "labels.jsonl").is_file()
    assert (bundle / "verification" / "README.md").is_file()
