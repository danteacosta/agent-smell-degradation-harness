from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from agents.stub import StubAgent
from eval.metrics import aggregate_metrics
from eval.mutation import score_test_gen_mutation
from eval.oracles import score_artifact
from mitigation.pipeline import prepare_requirement
from observability.tracing import ProvenanceRecorder
from pairs.loader import load_all_pairs
from taxonomy.label import label_degradation

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
    policy: str,
) -> dict[str, Any]:
    intent_id = pair["intent_id"]
    episode_id = _episode_id(intent_id, task_family, variant)
    trace_path = traces_dir / f"{episode_id}.jsonl"

    prepared = prepare_requirement(pair, variant=variant, policy=policy)
    requirement_text = prepared.text
    generation_variant = prepared.generation_variant
    smell = None if variant == "clean" else pair["smell"]
    smell_type = "" if variant == "clean" else pair["smell"]["type"]

    artifact = agent.generate(
        pair,
        variant=generation_variant,
        task_family=task_family,
    )
    oracle_spec = pair["oracle_spec"][task_family]
    oracle_result = score_artifact(intent_id, task_family, artifact, oracle_spec)
    semantic_label = "ok" if oracle_result.passed else "degraded"
    degradation = label_degradation(
        intent_id=intent_id,
        smell_type=smell_type,
        oracle_passed=oracle_result.passed,
        task_family=task_family,
    )

    has_semantic_provenance = False
    rec = ProvenanceRecorder(trace_path)
    rec.operational("latency", {"ms": 0, "episode_id": episode_id}, tier="A")
    if not skip_semantic_provenance:
        rec.semantic("constraint_extract", dict(artifact), tier="A")
        has_semantic_provenance = True

    mutation_score = None
    if task_family == "test_gen":
        mutation_score = score_test_gen_mutation(intent_id, artifact, pair["oracle_spec"])

    rec.oracle_verdict(
        {
            "passed": oracle_result.passed,
            "task_family": task_family,
            "mutation_score": mutation_score,
        }
    )
    rec.close()

    episode: dict[str, Any] = {
        "episode_id": episode_id,
        "intent_id": intent_id,
        "variant": variant,
        "task_family": task_family,
        "smell": smell,
        "requirement_text": requirement_text,
        "policy": policy,
        "mitigation_meta": prepared.mitigation_meta,
        "artifact": artifact,
        "oracle_passed": oracle_result.passed,
        "semantic_label": semantic_label,
        "provenance_path": str(trace_path),
        "has_semantic_provenance": has_semantic_provenance,
        "degradation_mode": degradation.mode,
        "degradation_severity": degradation.severity,
    }
    if mutation_score is not None:
        episode["mutation_score"] = mutation_score
    return episode


def _write_episodes_jsonl(episodes: list[dict[str, Any]], path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    lines = [json.dumps(ep, sort_keys=True) for ep in episodes]
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def run_eval(
    *,
    failure_mode: str | None = None,
    policy: str = "direct",
    skip_semantic_provenance: bool = False,
    output_path: Path,
    traces_dir: Path,
    episodes_path: Path | None = None,
) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    agent = StubAgent(failure_mode=failure_mode)
    return run_eval_with_agent(
        agent,
        pairs=load_all_pairs(),
        policy=policy,
        skip_semantic_provenance=skip_semantic_provenance,
        output_path=output_path,
        traces_dir=traces_dir,
        episodes_path=episodes_path,
    )


def run_eval_with_agent(
    agent: Any,
    *,
    pairs: list[dict[str, Any]] | None = None,
    policy: str = "direct",
    skip_semantic_provenance: bool = False,
    output_path: Path,
    traces_dir: Path,
    episodes_path: Path | None = None,
) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    traces_dir.mkdir(parents=True, exist_ok=True)
    if pairs is None:
        pairs = load_all_pairs()
    episodes: list[dict[str, Any]] = []

    for pair in pairs:
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
                        policy,
                    )
                )

    metrics = aggregate_metrics(episodes)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(metrics, indent=2) + "\n", encoding="utf-8")
    if episodes_path is not None:
        _write_episodes_jsonl(episodes, episodes_path)
    return metrics, episodes
