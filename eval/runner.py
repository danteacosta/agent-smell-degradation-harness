from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Sequence

from agents.stub import StubAgent
from agent_reliability_protocol import validate_lifecycle_sequence
from eval.identity import configuration_id_for, create_episode_identity, new_run_id
from eval.metrics import aggregate_metrics
from eval.provider_manifest import ProviderRunMetadata, summarize_provider_runs
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
    experiment_id: str,
    run_id: str,
    replication_id: int,
    configuration_id: str,
) -> dict[str, Any]:
    task_family = task_adapter.task_family
    intent_id = pair["intent_id"]
    identity = create_episode_identity(
        experiment_id=experiment_id,
        run_id=run_id,
        replication_id=replication_id,
        intent_id=intent_id,
        workload_id=str(pair.get("workload_id", intent_id)),
        variant_id=variant,
        task_id=task_family,
        configuration_id=configuration_id,
    )
    episode_id = identity.episode_id
    trace_path = traces_dir / identity.trace_name

    # `direct` is the only core policy.  The optional clarification extension
    # may explicitly request another policy for its separate experiments.
    prepared = prepare_requirement(pair, variant=variant, policy=policy)
    requirement_text = prepared.text
    generation_variant = prepared.generation_variant
    smell = None if variant == "clean" else pair["smell"]
    smell_type = "" if variant == "clean" else pair["smell"]["type"]

    has_semantic_provenance = False
    rec = ProvenanceRecorder(
        trace_path,
        episode_identity=identity.as_dict(),
        arp_context=identity.as_dict(),
    )
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
    provider_meta: dict[str, Any]
    if hasattr(agent, "generate_with_meta"):
        artifact, provider_meta = agent.generate_with_meta(
            pair,
            variant=generation_variant,
            task_family=task_family,
        )
    else:
        artifact = agent.generate(
            pair,
            variant=generation_variant,
            task_family=task_family,
        )
        provider_meta = {
            "provider": getattr(agent, "provider", "deterministic-stub"),
            "model": getattr(agent, "model", "stub-v1"),
            "latency_ms": 0.0,
            "cost_usd": 0.0,
        }
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

    rec.operational(
        "latency",
        {"ms": provider_meta.get("latency_ms", 0.0), "episode_id": episode_id},
        tier="A",
    )
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
    trace_events = [
        json.loads(line)
        for line in trace_path.read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]
    validate_lifecycle_sequence(trace_events)

    episode: dict[str, Any] = {
        **identity.as_dict(),
        "source_intent_id": pair.get("source_intent_id", pair["intent_id"]),
        "project_id": pair.get("project_id", pair.get("project", "")),
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
        "provider_meta": {
            "provider": str(provider_meta.get("provider", "unknown")),
            "model": str(provider_meta.get("model", "unknown")),
            "latency_ms": float(provider_meta.get("latency_ms", 0.0)),
            "cost_usd": float(provider_meta.get("cost_usd", 0.0)),
            "cost_reported": "cost_usd" in provider_meta,
        },
    }
    if task_evaluation.mutation_score is not None:
        episode["mutation_score"] = task_evaluation.mutation_score
    return episode


def _write_episodes_jsonl(episodes: list[dict[str, Any]], path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(json.dumps(episode, sort_keys=True) for episode in episodes) + "\n", encoding="utf-8")


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
    experiment_id: str = "evaluation",
    run_id: str | None = None,
    replication_id: int = 0,
    configuration_id: str | None = None,
) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    agent = StubAgent(failure_mode=failure_mode)
    if configuration_id is None:
        configuration_id = configuration_id_for(
            {
                "policy": policy,
                "failure_mode": failure_mode,
                "skip_semantic_provenance": skip_semantic_provenance,
                "task_ids": [adapter.task_family for adapter in task_adapters],
            }
        )
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
        experiment_id=experiment_id,
        run_id=run_id,
        replication_id=replication_id,
        configuration_id=configuration_id,
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
    experiment_id: str = "evaluation",
    run_id: str | None = None,
    replication_id: int = 0,
    configuration_id: str | None = None,
) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    traces_dir.mkdir(parents=True, exist_ok=True)
    if pairs is None:
        pairs = load_all_pairs()
    if run_id is None:
        run_id = new_run_id()
    if configuration_id is None:
        configuration_id = configuration_id_for({"policy": policy})
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
                        experiment_id,
                        run_id,
                        replication_id,
                        configuration_id,
                    )
                )

    for episode in episodes:
        validation = {
            validator.name: validator.validate(Path(episode["provenance_path"]))
            for validator in validators
        }
        if "traceability" in validation:
            episode["traceability_valid"] = validation["traceability"]
            episode["has_semantic_provenance"] = validation["traceability"]

    metrics = aggregate_metrics(episodes)
    provider_name = str(getattr(agent, "provider", "deterministic-stub"))
    mode = str(
        getattr(
            agent,
            "run_mode",
            "live" if hasattr(agent, "generate_with_meta") else "stub",
        )
    )
    provider_model = str(getattr(agent, "model", "stub-v1"))
    cost_reported = all(bool(ep["provider_meta"].get("cost_reported")) for ep in episodes)
    provider_runs = [
        ProviderRunMetadata(
            run_id=run_id,
            mode=mode,
            provider=provider_name,
            model=provider_model,
            model_version=str(getattr(agent, "model_version", provider_model)),
            seed=getattr(agent, "seed", None),
            configuration_hash=configuration_id,
            episode_count=len(episodes),
            total_latency_ms=sum(float(ep["provider_meta"]["latency_ms"]) for ep in episodes),
            total_cost_usd=sum(float(ep["provider_meta"]["cost_usd"]) for ep in episodes),
            extra={"cost_status": "reported_per_episode" if cost_reported else "not_reported"},
        )
    ]
    metrics["provider_run"] = summarize_provider_runs(provider_runs)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(metrics, indent=2) + "\n", encoding="utf-8")
    if episodes_path is not None:
        _write_episodes_jsonl(episodes, episodes_path)
    return metrics, episodes
