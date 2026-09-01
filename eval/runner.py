from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Mapping, Sequence

from agents.stub import StubAgent
from agents.checkpoints import AgentExecution, validate_agent_execution
from agent_reliability_protocol import (
    LifecycleEventV3,
    check_contract,
    validate_lifecycle_sequence,
    validate_lifecycle_sequence_v3,
)
from arp_profiles import AGENT_SMELL_PROFILE, validate_agent_smell_run
from eval.identity import configuration_id_for, create_episode_identity, new_run_id
from eval.metrics import aggregate_metrics
from eval.provider_manifest import ProviderRunMetadata, summarize_provider_runs
from mitigation.pipeline import prepare_requirement
from observability.tracing import ProvenanceRecorder
from protocol.arp3 import write_confirmatory_manifest
from observability.semantic_lint import validate_events
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
    agent: Any,
    traces_dir: Path,
    skip_semantic_provenance: bool,
    policy: str,
    experiment_id: str,
    run_id: str,
    replication_id: int,
    configuration_id: str,
    confirmatory: bool,
    split: str | None,
    source_revision: str | None,
    clarification_answers: Mapping[str, str] | None,
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
    clarification_answer = None
    if clarification_answers is not None:
        clarification_answer = clarification_answers.get(intent_id)
    prepared = prepare_requirement(
        pair,
        variant=variant,
        policy=policy,
        clarification_answer=clarification_answer,
    )
    requirement_text = prepared.text
    generation_variant = prepared.generation_variant
    generation_pair = dict(pair)
    generation_pair[f"{generation_variant}_requirement"] = requirement_text
    smell = None if variant == "clean" else pair["smell"]
    smell_type = "" if variant == "clean" else pair["smell"]["type"]

    has_semantic_provenance = False
    arp_context = identity.as_dict()
    if confirmatory:
        arp_context = {**arp_context, "run_id": episode_id}
    rec = ProvenanceRecorder(
        trace_path,
        episode_identity=identity.as_dict(),
        arp_context=arp_context,
        wire_version="3.0.0" if confirmatory else "2.0.5",
        profile=AGENT_SMELL_PROFILE if confirmatory else None,
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
    checkpoint_meta: dict[str, Any] = {}
    artifact: Mapping[str, Any] | dict[str, Any]
    provider_meta: dict[str, Any]
    if confirmatory:
        executor = getattr(agent, "execute_with_checkpoints", None)
        if executor is None:
            raise ValueError("confirmatory run requires one native execution with runtime checkpoints")
        execution = executor(
            generation_pair,
            variant=generation_variant,
            task_family=task_family,
        )
        if not isinstance(execution, AgentExecution):
            raise ValueError("native checkpoint execution must return AgentExecution")
        execution = validate_agent_execution(
            execution,
            not_before=rec.last_ended_at,
            require_constraint_lineage=True,
            require_atomic_obligations=True,
        )
        for observation in execution.checkpoints:
            writer = rec.semantic if observation.checkpoint in {"interpretation.completed", "plan.completed"} else rec.operational
            writer(
                observation.checkpoint,
                dict(observation.payload),
                tier="A",
                started_at=observation.started_at,
                ended_at=observation.ended_at,
            )
        artifact = dict(execution.artifact)
        provider_meta = dict(execution.provider_meta)
        checkpoint_meta = {"provenance": "runtime_native", "count": len(execution.checkpoints)}
        has_semantic_provenance = not skip_semantic_provenance
    else:
        interpretation = _interpret_requirement(
            requirement_text,
            task_family,
            variant,
            policy,
        )
        rec.semantic("interpretation.completed", interpretation, tier="A")
        if not skip_semantic_provenance:
            rec.semantic("constraint_extract", _extract_constraints(interpretation), tier="A")
            has_semantic_provenance = True
        rec.semantic(
            "plan.completed",
            {"task_family": task_family, "generation_variant": generation_variant},
            tier="A",
        )
        rec.operational("execution.started", {"episode_id": episode_id}, tier="A")
        if hasattr(agent, "generate_with_meta"):
            artifact, provider_meta = agent.generate_with_meta(
                generation_pair,
                variant=generation_variant,
                task_family=task_family,
            )
        else:
            artifact = agent.generate(
                generation_pair,
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

    if confirmatory:
        rec.operational(
            "evaluation.completed",
            {
                "episode_id": episode_id,
                "passed": task_evaluation.passed,
                "task_family": task_family,
                "mutation_score": task_evaluation.mutation_score,
                "latency_ms": provider_meta.get("latency_ms", 0.0),
            },
            tier="B",
        )
    else:
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
    manifest_path: Path | None = None
    if confirmatory:
        if split is None or source_revision is None:
            raise ValueError("confirmatory execution requires split and source_revision")
        manifest_path = trace_path.with_suffix(".manifest.json")
        manifest = write_confirmatory_manifest(
            manifest_path,
            identity={**identity.as_dict(), "episode_id": episode_id},
            requirement_text=requirement_text,
            experiment_id=experiment_id,
            project_id=str(pair.get("project_id", pair.get("project", ""))),
            source_intent_id=str(pair.get("source_intent_id", pair["intent_id"])),
            variant=variant,
            split=split,
            source_revision=source_revision,
            configuration_hash=configuration_id,
            provider=str(provider_meta.get("provider", getattr(agent, "provider", "unknown"))),
            model_version=str(provider_meta.get("model", getattr(agent, "model_version", "unknown"))),
        )
        for event in trace_events:
            errors = check_contract("event", event)
            if errors:
                raise ValueError("invalid ARP 3.0 event: " + "; ".join(errors))
        validate_lifecycle_sequence_v3([LifecycleEventV3.from_dict(event) for event in trace_events])
        profile_errors = validate_agent_smell_run(manifest, trace_events)
        if profile_errors:
            raise ValueError("invalid confirmatory ARP profile: " + "; ".join(profile_errors))
    else:
        validate_lifecycle_sequence(trace_events)
    semantic_lint_findings = validate_events(trace_events)

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
        "arp_manifest_path": str(manifest_path) if manifest_path is not None else None,
        "has_semantic_provenance": has_semantic_provenance,
        "semantic_lint": {
            "finding_count": len(semantic_lint_findings),
            "findings": [finding.__dict__ for finding in semantic_lint_findings],
        },
        "degradation_mode": degradation.mode,
        "degradation_severity": degradation.severity,
        "provider_meta": {
            "provider": str(provider_meta.get("provider", "unknown")),
            "model": str(provider_meta.get("model", "unknown")),
            "latency_ms": float(provider_meta.get("latency_ms", 0.0)),
            "cost_usd": float(provider_meta.get("cost_usd", 0.0)),
            "cost_reported": "cost_usd" in provider_meta,
            "checkpoint": checkpoint_meta,
        },
    }
    for metadata_key in ("prompt_sha256", "prompt_template_version"):
        if metadata_key in provider_meta:
            episode["provider_meta"][metadata_key] = str(provider_meta[metadata_key])
    context_summary = provider_meta.get("context_management")
    pre_final_context_summary = provider_meta.get("pre_final_context_management")
    if isinstance(context_summary, Mapping):
        episode["provider_meta"]["context_management"] = dict(context_summary)
    else:
        episode["provider_meta"]["context_management"] = {
            "schema_version": "context-management/v1",
            "condition": "not_instrumented",
            "event_count": 0,
            "compaction_count": 0,
            "operation_counts": {},
            "context_size_unit": "utf8_bytes",
            "context_size_before": 0,
            "context_size_after": 0,
        }
    if isinstance(pre_final_context_summary, Mapping):
        episode["provider_meta"]["pre_final_context_management"] = dict(pre_final_context_summary)
    if task_evaluation.mutation_score is not None:
        episode["mutation_score"] = task_evaluation.mutation_score
    if task_evaluation.behavior_status is not None:
        episode["behavior_status"] = task_evaluation.behavior_status
        episode["target_condition_failures"] = task_evaluation.target_condition_failures
        episode["unrelated_condition_failures"] = task_evaluation.unrelated_condition_failures
        episode["behavior_report"] = task_evaluation.behavior_report
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
    confirmatory: bool = False,
    split: str | None = None,
    source_revision: str | None = None,
    clarification_answers: Mapping[str, str] | None = None,
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
        confirmatory=confirmatory,
        split=split,
        source_revision=source_revision,
        clarification_answers=clarification_answers,
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
    confirmatory: bool = False,
    split: str | None = None,
    source_revision: str | None = None,
    clarification_answers: Mapping[str, str] | None = None,
) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    run_mode = str(getattr(agent, "run_mode", "stub"))
    if confirmatory and run_mode not in {"live", "runtime"}:
        raise ValueError("confirmatory execution requires real provider checkpoints from a live/runtime run, not stub, mock, or replay")
    if confirmatory and str(getattr(agent, "checkpoint_provenance", "")) != "runtime_native":
        raise ValueError(
            "confirmatory execution requires runtime-native checkpoints; "
            "prompted checkpoint snapshots are non-confirmatory"
        )
    if confirmatory and not callable(getattr(agent, "execute_with_checkpoints", None)):
        raise ValueError("confirmatory run requires one native execution with runtime checkpoints")
    if confirmatory and split not in {"train", "calibration", "test"}:
        raise ValueError("confirmatory execution requires a frozen train/calibration/test split")
    if confirmatory and (source_revision is None or not source_revision.strip()):
        raise ValueError("confirmatory execution requires an immutable source_revision")
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
                        confirmatory,
                        split,
                        source_revision,
                        clarification_answers,
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
            extra={
                "cost_status": "reported_per_episode" if cost_reported else "not_reported",
                "prompt_template_versions": sorted(
                    {
                        str(ep["provider_meta"]["prompt_template_version"])
                        for ep in episodes
                        if ep["provider_meta"].get("prompt_template_version")
                    }
                ),
                "prompt_sha256s": sorted(
                    {
                        str(ep["provider_meta"]["prompt_sha256"])
                        for ep in episodes
                        if ep["provider_meta"].get("prompt_sha256")
                    }
                ),
            },
        )
    ]
    metrics["provider_run"] = summarize_provider_runs(provider_runs)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(metrics, indent=2) + "\n", encoding="utf-8")
    if episodes_path is not None:
        _write_episodes_jsonl(episodes, episodes_path)
    return metrics, episodes
