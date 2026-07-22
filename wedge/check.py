from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

from eval.mutation import score_test_gen_mutation
from eval.oracles import score_artifact
from mitigation.detect import detect_smell
from observability.features import extract_tier_a_features
from wedge.decisions import Decision

FIXTURES: dict[str, dict[str, Any]] = {
    "demo-clean": {
        "requirement_text": "Refunds must be processed within 10 minutes of approval.",
        "smell": None,
        "policy": "direct",
        "intent_id": "RF-11",
        "task_family": "codegen",
        "artifact": {"refund_window_minutes": 10},
        "oracle_spec": {
            "codegen": {"refund_window_minutes": 10},
            "test_gen": {
                "must_reject_minutes": [15],
                "must_accept_minutes": [10],
                "criterion": "refund_window_minutes == 10",
            },
        },
        "provenance_events": [
            {
                "kind": "operational",
                "name": "latency",
                "payload": {"ms": 1},
                "tier": "A",
            },
            {
                "kind": "semantic",
                "name": "constraint_extract",
                "payload": {"refund_window_minutes": 10},
                "tier": "A",
            },
            {
                "kind": "semantic",
                "name": "oracle_verdict",
                "payload": {"passed": True},
                "tier": "B",
            },
        ],
    },
    "demo-smelly": {
        "requirement_text": "Refunds must be processed within 10 minutes. Late refunds after 15 minutes are escalated.",
        "smell": {
            "category": "semantic",
            "type": "numerical_inconsistency",
            "injection_rule": "conflicting windows",
        },
        "policy": "direct",
        "intent_id": "RF-11",
        "task_family": "codegen",
        "artifact": {"refund_window_minutes": 10},
        "oracle_spec": {
            "codegen": {"refund_window_minutes": 10},
            "test_gen": {
                "must_reject_minutes": [15],
                "must_accept_minutes": [10],
                "criterion": "refund_window_minutes == 10",
            },
        },
        "provenance_events": [
            {
                "kind": "operational",
                "name": "latency",
                "payload": {"ms": 1},
                "tier": "A",
            },
            {
                "kind": "semantic",
                "name": "constraint_extract",
                "payload": {"refund_window_minutes": 10},
                "tier": "A",
            },
            {
                "kind": "semantic",
                "name": "oracle_verdict",
                "payload": {"passed": True},
                "tier": "B",
            },
        ],
    },
    "demo-degraded": {
        "requirement_text": "Refunds must be processed within 10 minutes. Late refunds after 15 minutes are escalated.",
        "smell": {
            "category": "semantic",
            "type": "numerical_inconsistency",
            "injection_rule": "conflicting windows",
        },
        "policy": "direct",
        "intent_id": "RF-11",
        "task_family": "test_gen",
        "artifact": {
            "must_reject_minutes": [],
            "must_accept_minutes": [15],
            "criterion": "refund within reasonable time",
        },
        "oracle_spec": {
            "codegen": {"refund_window_minutes": 10},
            "test_gen": {
                "must_reject_minutes": [15],
                "must_accept_minutes": [10],
                "criterion": "refund_window_minutes == 10",
            },
        },
        "provenance_events": [
            {
                "kind": "operational",
                "name": "latency",
                "payload": {"ms": 1},
                "tier": "A",
            },
            {
                "kind": "semantic",
                "name": "constraint_extract",
                "payload": {
                    "must_reject_minutes": [],
                    "must_accept_minutes": [15],
                    "criterion": "refund within reasonable time",
                },
                "tier": "A",
            },
            {
                "kind": "semantic",
                "name": "oracle_verdict",
                "payload": {"passed": False, "mutation_score": 0.0},
                "tier": "B",
            },
        ],
    },
}


def _write_fixture_trace(path: Path, events: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    lines = [json.dumps(event) for event in events]
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def _tier_a_risk(features: dict[str, dict[str, float | int]]) -> float:
    semantic = features.get("provenance_semantic", {})
    static = features.get("static_smell", {})
    risk = float(static.get("smell_present", 0))
    if semantic.get("constraint_match") == 0:
        risk += 0.5
    if semantic.get("is_weak_comparator"):
        risk += 0.5
    return min(risk, 1.0)


def evaluate_episode(
    *,
    requirement_text: str,
    smell: dict[str, Any] | None,
    policy: str,
    intent_id: str,
    task_family: str,
    artifact: dict[str, Any],
    oracle_spec: dict[str, dict[str, Any]],
    provenance_path: str | Path,
    mitigation_meta: dict[str, Any] | None = None,
) -> dict[str, Any]:
    mitigation_meta = mitigation_meta or {}
    smell_meta = smell or {}
    detection = detect_smell(requirement_text, smell_meta) if smell else detect_smell("", {})

    oracle_result = score_artifact(
        intent_id,
        task_family,
        artifact,
        oracle_spec[task_family],
    )
    mutation_score = None
    if task_family == "test_gen":
        mutation_score = score_test_gen_mutation(intent_id, artifact, oracle_spec)

    episode = {
        "intent_id": intent_id,
        "task_family": task_family,
        "variant": "smelly" if smell else "clean",
        "smell": smell,
        "requirement_text": requirement_text,
        "policy": policy,
        "mitigation_meta": mitigation_meta,
        "artifact": artifact,
        "oracle_passed": oracle_result.passed,
    }

    tier_a = extract_tier_a_features(episode, provenance_path)
    tier_a_risk = _tier_a_risk(tier_a)
    tier_b_degraded = (not oracle_result.passed) or (
        mutation_score is not None and mutation_score < 1.0
    )

    reasons: list[str] = []
    decision = Decision.APPROVE

    if tier_b_degraded:
        decision = Decision.WARN
        if not oracle_result.passed:
            reasons.append("independent oracle failed")
        if mutation_score is not None and mutation_score < 1.0:
            reasons.append("mutation score below full catch rate")
    elif detection.detected and policy == "direct" and not mitigation_meta:
        decision = Decision.CLARIFY
        reasons.append("static smell detected without clarification or rewrite")
    elif tier_a_risk >= 0.5:
        decision = Decision.WARN
        reasons.append("tier A provenance risk elevated")

    return {
        "decision": decision.value,
        "reasons": reasons,
        "static_smell": detection.detected,
        "tier_a_risk": tier_a_risk,
        "tier_b_degraded": tier_b_degraded,
        "oracle_passed": oracle_result.passed,
        "mutation_score": mutation_score,
    }


def run_fixture(name: str, *, traces_dir: Path | None = None) -> dict[str, Any]:
    if name not in FIXTURES:
        raise ValueError(f"unknown fixture: {name}")

    fixture = FIXTURES[name]
    traces_dir = traces_dir or Path("eval/traces")
    trace_path = traces_dir / f"wedge_{name}.jsonl"
    _write_fixture_trace(trace_path, fixture["provenance_events"])

    return evaluate_episode(
        requirement_text=fixture["requirement_text"],
        smell=fixture["smell"],
        policy=fixture["policy"],
        intent_id=fixture["intent_id"],
        task_family=fixture["task_family"],
        artifact=fixture["artifact"],
        oracle_spec=fixture["oracle_spec"],
        provenance_path=trace_path,
        mitigation_meta=fixture.get("mitigation_meta"),
    )


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Wedge reliability check")
    parser.add_argument("--fixture", choices=sorted(FIXTURES), help="Run built-in demo fixture")
    parser.add_argument("--traces-dir", type=Path, default=Path("eval/traces"))
    args = parser.parse_args(argv)

    if not args.fixture:
        parser.error("--fixture is required")

    result = run_fixture(args.fixture, traces_dir=args.traces_dir)
    print(json.dumps(result, indent=2))
    return 0 if result["decision"] == Decision.APPROVE.value else 1


if __name__ == "__main__":
    sys.exit(main())
