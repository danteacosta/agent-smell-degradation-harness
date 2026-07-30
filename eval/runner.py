from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Sequence

from agents.stub import StubAgent
from eval.metrics import aggregate_metrics
from mitigation.pipeline import prepare_requirement
from observability.tracing import ProvenanceRecorder
from pairs.loader import load_all_pairs
from taxonomy.label import label_degradation
from eval.task_adapters import (
    DEFAULT_TASK_ADAPTERS,
    DEFAULT_VALIDATORS,
    EpisodeValidator,
    TaskAdapter,
)

VARIANTS = ("clean", "smelly")


def _episode_id(intent_id: str, task_family: str, variant: str) -> str:
    return f"{intent_id}_{task_family}_{variant}"


def _interpret_requirement(
    requirement_text: str,
    task_family: str,
    variant: str,
    policy: str,
) -> dict[str, str]:
    """Capture the input-derived interpretation available before generation."""
    return {
        "requirement_text": requirement_text,
        "task_family": task_family,
        "variant": variant,
        "policy": policy,
    }


def _extract_constraints(interpretation: dict[str, str]) -> dict[str, str]:
    """Expose the stable T1 semantic signal without terminal-artifact data."""
    return {
        "requirement_text": interpretation["requirement_text"],
        "task_family": interpretation["task_family"],
    }


def _run_episode(
    pair: dict[str, Any],
    task_adapter: TaskAdapter,
    variant: str,
    agent: StubAgent,
    traces_dir: Path,
    skip_semantic_provenance: bool,
    policy: str,
) -> dict[str, Any]:
    task_family = task_adapter.task_family
    intent_id = pair["intent_id"]
    episode_id = _episode_id(intent_id, task_family, variant)
    trace_path = traces_dir / f"{episode_id}.jsonl"

    prepared = prepare_requirement(pair, variant=variant, policy=policy)
    requirement_text = prepared.text
    generation_variant = prepared.generation_variant
    smell = None if variant == "clean" else pair["smell"]
    smell_type = "" if variant == "clean" else pair["smell"]["type"]

    has_semantic_provenance = False
    rec = ProvenanceRecorder(trace_path)
    rec.operational(
        "input.received",
        {
            "episode_id": episode_id,
            "intent_id": intent_id,
            "task_family": task_family,
            "variant": variant,
        },
        tier="A",
    )
    interpretation = _interpret_requirement(
        requirement_text,
        task_family,
        variant,
        policy,
    )
    rec.semantic("interpretation.completed", interpretation, tier="A")
    if not skip_semantic_provenance:
        # Retain the existing semantic-provenance signal, but make it a real
        # T1 checkpoint derived solely from available requirement input.
        rec.semantic("constraint_extract", _extract_constraints(interpretation), tier="A")
        has_semantic_provenance = True
    rec.semantic(
        "plan.completed",
        {"task_family": task_family, "generation_variant": generation_variant},
        tier="A",
    )
    rec.operational("execution.started", {"episode_id": episode_id}, tier="A")
    artifact = agent.generate(
        pair,
        variant=generation_variant,
        task_family=task_family,
    )
    rec.operational(
        "artifact.completed",
        {"episode_id": episode_id, "artifact_field_count": len(artifact)},
        tier="A",
    )
    task_evaluation = task_adapter.evaluate(
        intent_id=intent_id,
        artifact=artifact,
        oracle_spec=pair["oracle_spec"],
    )
    semantic_label = "ok" if task_evaluation.passed else "degraded"
    degradation = label_degradation(
        intent_id=intent_id,
        smell_type=smell_type,
        oracle_passed=task_evaluation.passed,
        task_family=task_family,
    )

    rec.operational("latency", {"ms": 0, "episode_id": episode_id}, tier="A")
    rec.oracle_verdict(
        {
            "passed": task_evaluation.passed,
            "task_family": task_family,
            "mutation_score": task_evaluation.mutation_score,
        }
    )
    rec.operational(
        "evaluation.completed",
        {"episode_id": episode_id, "passed": task_evaluation.passed},
        tier="B",
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
        "oracle_passed": task_evaluation.passed,
        "semantic_label": semantic_label,
        "provenance_path": str(trace_path),
        "has_semantic_provenance": has_semantic_provenance,
        "degradation_mode": degradation.mode,
        "degradation_severity": degradation.severity,
    }
    if task_evaluation.mutation_score is not None:
        episode["mutation_score"] = task_evaluation.mutation_score
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
    task_adapters: Sequence[TaskAdapter] = DEFAULT_TASK_ADAPTERS,
    validators: Sequence[EpisodeValidator] = DEFAULT_VALIDATORS,
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
        task_adapters=task_adapters,
        validators=validators,
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
    task_adapters: Sequence[TaskAdapter] = DEFAULT_TASK_ADAPTERS,
    validators: Sequence[EpisodeValidator] = DEFAULT_VALIDATORS,
) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    traces_dir.mkdir(parents=True, exist_ok=True)
    if pairs is None:
        pairs = load_all_pairs()
    episodes: list[dict[str, Any]] = []

    for pair in pairs:
        for task_adapter in task_adapters:
            for variant in VARIANTS:
                episodes.append(
                    _run_episode(
                        pair,
                        task_adapter,
                        variant,
                        agent,
                        traces_dir,
                        skip_semantic_provenance,
                        policy,
                    )
                )

    for episode in episodes:
        validation = {
            validator.name: validator.validate(Path(episode["provenance_path"]))
            for validator in validators
        }
        if "traceability" in validation:
            episode["traceability_valid"] = validation["traceability"]

    metrics = aggregate_metrics(episodes)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(metrics, indent=2) + "\n", encoding="utf-8")
    if episodes_path is not None:
        _write_episodes_jsonl(episodes, episodes_path)
    return metrics, episodes
