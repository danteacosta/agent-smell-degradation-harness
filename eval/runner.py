from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from agents.stub import StubAgent
from eval.metrics import aggregate_metrics
from eval.oracles import score_artifact
from observability.tracing import ProvenanceRecorder
from pairs.loader import load_all_pairs

TASK_FAMILIES = ("codegen", "test_gen")
VARIANTS = ("clean", "smelly")


def _episode_id(intent_id: str, task_family: str, variant: str) -> str:
    return f"{intent_id}_{task_family}_{variant}"


def _run_episode(
    pair: dict[str, Any],
    task_family: str,
    variant: str,
    agent: StubAgent,
    traces_dir: Path,
    skip_semantic_provenance: bool,
) -> dict[str, Any]:
    intent_id = pair["intent_id"]
    episode_id = _episode_id(intent_id, task_family, variant)
    trace_path = traces_dir / f"{episode_id}.jsonl"

    artifact = agent.generate(pair, variant=variant, task_family=task_family)
    oracle_spec = pair["oracle_spec"][task_family]
    oracle_result = score_artifact(intent_id, task_family, artifact, oracle_spec)
    semantic_label = "ok" if oracle_result.passed else "degraded"

    has_semantic_provenance = False
    rec = ProvenanceRecorder(trace_path)
    rec.operational("latency", {"ms": 0, "episode_id": episode_id})
    if not skip_semantic_provenance:
        rec.semantic("constraint_extract", dict(artifact))
        has_semantic_provenance = True
    rec.close()

    return {
        "episode_id": episode_id,
        "intent_id": intent_id,
        "task_family": task_family,
        "variant": variant,
        "oracle_passed": oracle_result.passed,
        "semantic_label": semantic_label,
        "has_semantic_provenance": has_semantic_provenance,
        "provenance_path": str(trace_path),
    }


def run_eval(
    *,
    failure_mode: str | None = None,
    skip_semantic_provenance: bool = False,
    output_path: Path,
    traces_dir: Path,
) -> dict[str, Any]:
    traces_dir.mkdir(parents=True, exist_ok=True)
    agent = StubAgent(failure_mode=failure_mode)
    episodes: list[dict[str, Any]] = []

    for pair in load_all_pairs():
        for task_family in TASK_FAMILIES:
            for variant in VARIANTS:
                episodes.append(
                    _run_episode(
                        pair,
                        task_family,
                        variant,
                        agent,
                        traces_dir,
                        skip_semantic_provenance,
                    )
                )

    metrics = aggregate_metrics(episodes)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(metrics, indent=2) + "\n", encoding="utf-8")
    return metrics
