"""Private exploratory generation-and-judge pre-pilot runner.

This workflow is deliberately separate from official readiness.  It accepts a
frozen redacted corpus plus private source records, generates artifacts through
the runtime-native path, and cross-judges them only after the complete artifact
set exists.  Public output contains hashes, counts, bounded metadata, and
terminal state; raw prompts, responses, and requirements stay in the private
run directory.
"""

from __future__ import annotations

import hashlib
import json
import os
import subprocess
import tempfile
from collections import Counter
from collections.abc import Mapping, Sequence
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from agents.providers import Provider, ProviderRequest
from agents.runtime import RuntimeCheckpointAgent
from eval.corpus_intake import (
    CorpusIntakeError,
    load_private_records,
    validate_private_records_against_frozen_manifest,
)
from eval.exploratory_call_plan import (
    ExploratoryCallPlan,
    _PrivateReferenceConstraint,
    build_exploratory_call_plan,
    load_reference_constraints,
)
from eval.exploratory_cost import (
    AmbiguousInFlightError,
    BudgetExhaustedError,
    CostLedger,
    CostUnverifiedError,
    DurabilityError,
    budgeted_provider,
)
from eval.protocol_hashes import ProtocolHashError, sha256_json, verify_protocol_hashes
from eval.provider_runtime_config import (
    ExploratoryRuntimeConfig,
    ProviderRuntimeConfigError,
    build_provider_from_slot,
    load_exploratory_runtime_config,
)
from label_plane.exploratory_judge import (
    JudgeRequest,
    ReferenceConstraint,
    build_judge_prompt,
    consolidate_two_judges,
    parse_judge_response,
    serialize_judge_request,
)
from protocol.context_management import NoCompactionManager


SCHEMA_VERSION = "exploratory-llm-judged-prepilot/v1"
CANONICAL_FROZEN_MANIFEST = Path("data/prepilot/corpus-manifest.json")
TERMINAL_STATES = frozenset(
    {
        "completed",
        "completed_with_uncertainty",
        "incomplete_generation",
        "stopped_budget_exhausted",
        "stopped_cost_unverified",
        "stopped_protocol_violation",
    }
)


class ExploratoryPrepilotError(ValueError):
    """Raised when private inputs cannot pass the exploratory preflight."""


def _canonical_json(value: Any) -> str:
    return json.dumps(
        value,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
        allow_nan=False,
    )


def _sha256_text(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def _git_revision(repository_root: Path) -> str | None:
    try:
        result = subprocess.run(
            ["git", "rev-parse", "HEAD"],
            cwd=repository_root,
            capture_output=True,
            text=True,
            check=True,
        )
    except (OSError, subprocess.CalledProcessError):
        return None
    value = result.stdout.strip()
    return value if value else None


def _safe_error(error: Exception) -> str:
    return type(error).__name__


def _assert_private_output(path: Path, repository_root: Path) -> None:
    try:
        path.resolve().relative_to(repository_root.resolve())
    except ValueError:
        return
    raise ExploratoryPrepilotError(
        "exploratory output must remain outside the repository"
    )


def _atomic_json_write(path: Path, value: Mapping[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    encoded = (_canonical_json(value) + "\n").encode("utf-8")
    descriptor, temporary_name = tempfile.mkstemp(
        prefix=f".{path.name}.", suffix=".tmp", dir=path.parent
    )
    try:
        with os.fdopen(descriptor, "wb") as handle:
            handle.write(encoded)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temporary_name, path)
        directory_fd = os.open(path.parent, os.O_RDONLY)
        try:
            os.fsync(directory_fd)
        finally:
            os.close(directory_fd)
    except Exception:
        try:
            os.unlink(temporary_name)
        except OSError:
            pass
        raise


def _append_private_evidence(path: Path, value: Mapping[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as handle:
        handle.write(_canonical_json(value) + "\n")
        handle.flush()
        os.fsync(handle.fileno())


def _load_frozen_manifest(repository_root: Path) -> dict[str, Any]:
    path = repository_root / CANONICAL_FROZEN_MANIFEST
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as error:
        raise ExploratoryPrepilotError(
            "canonical frozen corpus manifest is unavailable or invalid"
        ) from error
    if not isinstance(payload, Mapping):
        raise ExploratoryPrepilotError("canonical frozen corpus manifest must be an object")
    return dict(payload)


def _record_pairs(
    private_records: Sequence[Mapping[str, Any]],
    redacted_records: Sequence[Mapping[str, Any]],
) -> tuple[dict[str, Any], ...]:
    redacted_by_intent = {
        str(item["source_intent_id"]): item for item in redacted_records
    }
    pairs: list[dict[str, Any]] = []
    for record in private_records:
        intent_id = str(record.get("source_intent_id", ""))
        redacted = redacted_by_intent.get(intent_id)
        if redacted is None:
            raise ExploratoryPrepilotError("private corpus join is incomplete")
        contract = record.get("generation_contract")
        if not isinstance(contract, Mapping):
            raise ExploratoryPrepilotError("private record generation contract is missing")
        task_contract = contract.get("test_gen")
        if not isinstance(task_contract, Mapping):
            raise ExploratoryPrepilotError("private record test_gen contract is missing")
        output_keys = task_contract.get("output_keys")
        if (
            not isinstance(output_keys, list)
            or not output_keys
            or any(type(value) is not str or not value.strip() for value in output_keys)
            or len(set(output_keys)) != len(output_keys)
        ):
            raise ExploratoryPrepilotError("private record test_gen output keys are invalid")
        clean = record.get("clean_requirement")
        smelly = record.get("defective_requirement")
        if (
            not isinstance(clean, str)
            or not clean.strip()
            or not isinstance(smelly, str)
            or not smelly.strip()
        ):
            raise ExploratoryPrepilotError("private record requirements are missing")
        pairs.append(
            {
                "intent_id": intent_id,
                "source_intent_id": intent_id,
                "clean_requirement": clean,
                "smelly_requirement": smelly,
                "generation_contract": {"test_gen": {"output_keys": list(output_keys)}},
                "redacted": dict(redacted),
            }
        )
    return tuple(sorted(pairs, key=lambda value: value["source_intent_id"]))


def _reference_map(
    constraints: Sequence[_PrivateReferenceConstraint],
) -> dict[str, tuple[ReferenceConstraint, ...]]:
    return {
        str(item.source_intent_id): (ReferenceConstraint(item.constraint_id, item.text),)
        for item in constraints
    }


def _provider_plan_slots(configuration: ExploratoryRuntimeConfig) -> list[dict[str, str]]:
    return [
        {
            "slot_id": slot.id,
            "provider": slot.kind,
            "model": slot.model,
            "model_version": slot.model_version,
        }
        for slot in configuration.providers
    ]


def _plan_join_by_artifact(plan: ExploratoryCallPlan) -> dict[str, Any]:
    return {str(item.artifact_id): item for item in plan._private_join}


def _configuration_public_hash(configuration: ExploratoryRuntimeConfig) -> str:
    return _sha256_text(_canonical_json(configuration.public_metadata()))


def _build_report_base(
    *,
    run_id: str,
    configuration: ExploratoryRuntimeConfig,
    source_revision: str | None,
    run_directory: Path,
) -> dict[str, Any]:
    return {
        "schema_version": SCHEMA_VERSION,
        "run_id": run_id,
        "state": "stopped_protocol_violation",
        "claim_level": "non_confirmatory_exploratory",
        "source_revision": source_revision,
        "configuration_sha256": _configuration_public_hash(configuration),
        "protocol_hashes": dict(configuration.protocol_hashes),
        "run_directory": str(run_directory),
        "pair_count": 0,
        "base_episode_count": 0,
        "artifact_count": 0,
        "judging_occurrence_count_per_judge": 0,
        "logical_judging_calls": 0,
        "logical_operations": 0,
        "provider_api_calls": 0,
        "generation_stage_count": 0,
        "judge_result_count": 0,
        "uncertain_judge_count": 0,
        "label_counts": {},
        "error_class": None,
        "cost": None,
    }


def _checkpoint(
    run_directory: Path,
    *,
    run_id: str,
    state: str,
    source_revision: str | None,
    corpus_manifest_sha256: str | None,
    configuration_sha256: str,
    rubric_sha256: str,
    ledger_head_hash: str | None,
    completed_artifact_count: int,
    completed_judge_count: int,
) -> None:
    _atomic_json_write(
        run_directory / "checkpoint.json",
        {
            "schema_version": "exploratory-checkpoint/v1",
            "run_id": run_id,
            "state": state,
            "source_revision": source_revision,
            "corpus_manifest_sha256": corpus_manifest_sha256,
            "configuration_sha256": configuration_sha256,
            "rubric_sha256": rubric_sha256,
            "ledger_head_hash": ledger_head_hash,
            "completed_artifact_count": completed_artifact_count,
            "completed_judge_count": completed_judge_count,
        },
    )


def _invoke_judge(
    *,
    budgeted: Any,
    provider_slot_id: str,
    occurrence_id: str,
    request: JudgeRequest,
    evidence_path: Path,
) -> tuple[Any | None, str | None]:
    serialized_request = serialize_judge_request(request)
    prompt = build_judge_prompt(request)
    provider_request = ProviderRequest(
        prompt=prompt,
        pair={"task_family": "judge", "output_keys": []},
        variant="opaque",
        task_family="judge",
    )
    last_error: Exception | None = None
    for attempt in range(1, 3):
        try:
            response = budgeted.complete(
                provider_request,
                call_id=f"judge:{occurrence_id}:{provider_slot_id}",
                phase="judge",
                attempt=attempt,
            )
            _append_private_evidence(
                evidence_path,
                {
                    "kind": "judge_call",
                    "provider_slot_id": provider_slot_id,
                    "occurrence_id": occurrence_id,
                    "attempt": attempt,
                    "request": serialized_request,
                    "prompt": prompt,
                    "response": response,
                },
            )
            return parse_judge_response(response, request), None
        except (BudgetExhaustedError, CostUnverifiedError, DurabilityError):
            raise
        except Exception as error:
            last_error = error
            if attempt == 2:
                break
    return None, _safe_error(last_error) if last_error is not None else "ValueError"


def run_exploratory_prepilot(
    config_path: str | Path,
    output_path: str | Path,
    *,
    private_corpus_path: str | Path,
    reference_constraints_path: str | Path,
    repository_root: Path | None = None,
    environ: Mapping[str, str] | None = None,
    provider_adapters: Mapping[str, Provider] | None = None,
    dry_run: bool = False,
    confirm_live: bool = False,
    resume_run: str | Path | None = None,
) -> dict[str, Any]:
    """Run or preflight the private exploratory workflow.

    ``provider_adapters`` exists only for offline tests and controlled replay;
    live execution resolves the two configured adapters from the private env.
    """

    root = repository_root or Path(__file__).resolve().parents[1]
    output = Path(output_path)
    _assert_private_output(output, root)
    configuration = load_exploratory_runtime_config(config_path)
    if resume_run is not None:
        resume_directory = Path(resume_run)
        if not resume_directory.is_dir() or not (resume_directory / "checkpoint.json").is_file():
            raise ExploratoryPrepilotError("resume requires a private run directory with a checkpoint")
        checkpoint = json.loads((resume_directory / "checkpoint.json").read_text(encoding="utf-8"))
        if checkpoint.get("state") in TERMINAL_STATES:
            raise ExploratoryPrepilotError("terminal exploratory runs cannot be resumed")
        if checkpoint.get("configuration_sha256") != _configuration_public_hash(configuration):
            raise ExploratoryPrepilotError("resume configuration identity does not match")

    run_id = f"exploratory-prepilot-{datetime.now(UTC).strftime('%Y%m%dT%H%M%SZ')}"
    run_directory = (
        Path(resume_run)
        if resume_run is not None
        else Path(f"{output}.run")
    )
    run_directory = run_directory.resolve()
    _assert_private_output(run_directory, root)
    evidence_path = run_directory / "raw-evidence.jsonl"
    source_revision = _git_revision(root)
    report = _build_report_base(
        run_id=run_id,
        configuration=configuration,
        source_revision=source_revision,
        run_directory=run_directory,
    )
    report["started_at"] = datetime.now(UTC).isoformat()
    ledger: CostLedger | None = None

    try:
        if source_revision is None or source_revision != configuration.source_revision:
            raise ExploratoryPrepilotError("source revision does not match frozen runtime configuration")
        verify_protocol_hashes(configuration.protocol_hashes, repository_root=root)
        frozen_manifest = _load_frozen_manifest(root)
        private_records = load_private_records(private_corpus_path)
        redacted_join = validate_private_records_against_frozen_manifest(
            private_records, frozen_manifest
        )
        pairs = _record_pairs(private_records, redacted_join)
        private_constraints = load_reference_constraints(reference_constraints_path)
        constraints_by_intent = _reference_map(private_constraints)
        plan = build_exploratory_call_plan(
            pairs,
            _provider_plan_slots(configuration),
            private_constraints,
        )
        if set(constraints_by_intent) != {
            str(pair["source_intent_id"]) for pair in pairs
        }:
            raise ExploratoryPrepilotError("reference constraints do not cover the private corpus")
        preflight = configuration.cost_configuration().preflight()
        report.update(
            {
                "corpus_manifest_sha256": _sha256_text(_canonical_json(frozen_manifest)),
                "reference_constraints_sha256": _sha256_text(
                    _canonical_json(
                        [
                            {
                                "source_intent_id": item.source_intent_id,
                                "constraint_id": item.constraint_id,
                                "text_sha256": _sha256_text(item.text),
                            }
                            for item in private_constraints
                        ]
                    )
                ),
                "pair_count": len(pairs),
                "base_episode_count": len(plan.episodes),
                "artifact_count": len(plan.artifacts),
                "judging_occurrence_count_per_judge": plan.judging_occurrence_count_per_judge,
                "logical_judging_calls": plan.logical_judging_calls,
                "logical_operations": plan.logical_operations,
                "provider_api_calls": plan.provider_api_calls,
                "duplicate_base_task_count": plan.duplicate_base_task_count,
                "preflight": preflight.to_dict(),
            }
        )
        _atomic_json_write(
            run_directory / "run-manifest.json",
            {
                "schema_version": "exploratory-run-manifest/v1",
                "run_id": run_id,
                "source_revision": source_revision,
                "corpus_manifest_sha256": report["corpus_manifest_sha256"],
                "configuration_sha256": report["configuration_sha256"],
                "rubric_sha256": configuration.protocol_hashes["rubric_sha256"],
                "reference_constraints_sha256": report["reference_constraints_sha256"],
                "provider_slots": [slot.public_metadata() for slot in configuration.providers],
                "plan_counts": {
                    "episodes": len(plan.episodes),
                    "artifacts": len(plan.artifacts),
                    "occurrences": len(plan.occurrences),
                    "provider_api_calls": plan.provider_api_calls,
                },
            },
        )
        _checkpoint(
            run_directory,
            run_id=run_id,
            state="preflight_ready" if preflight.passed else "stopped_budget_exhausted",
            source_revision=source_revision,
            corpus_manifest_sha256=report["corpus_manifest_sha256"],
            configuration_sha256=report["configuration_sha256"],
            rubric_sha256=configuration.protocol_hashes["rubric_sha256"],
            ledger_head_hash=None,
            completed_artifact_count=0,
            completed_judge_count=0,
        )
        if not preflight.passed:
            report["state"] = "stopped_budget_exhausted"
            report["error_class"] = "BudgetPreflightError"
        elif dry_run:
            report["state"] = "preflight_ready"
        elif not confirm_live:
            report["state"] = "stopped_protocol_violation"
            report["error_class"] = "LiveConfirmationRequired"
        else:
            ledger = CostLedger(
                run_directory / "cost-ledger.jsonl",
                configuration.cost_configuration(),
                preflight=preflight,
            )
            adapters: dict[str, Provider] = {}
            for slot in configuration.providers:
                if provider_adapters is not None and slot.id in provider_adapters:
                    adapters[slot.id] = provider_adapters[slot.id]
                else:
                    adapters[slot.id], _ = build_provider_from_slot(
                        slot, environ=dict(os.environ if environ is None else environ)
                    )
            joins = _plan_join_by_artifact(plan)
            artifacts: dict[str, dict[str, Any]] = {}
            generation_stage_count = 0
            for slot in configuration.providers:
                budgeted = budgeted_provider(adapters[slot.id], ledger)
                for artifact_id, join in joins.items():
                    if join.provider_slot_id != slot.id:
                        continue
                    pair = next(
                        item for item in pairs
                        if item["source_intent_id"] == join.source_intent_id
                    )
                    variant = "clean" if join.variant_index == 0 else "smelly"

                    def stage_completion(
                        request: ProviderRequest,
                        stage: str,
                        attempt: int,
                        *,
                        _artifact_id: str = artifact_id,
                        _slot_id: str = slot.id,
                    ) -> str:
                        phase = "generation.artifact" if stage == "artifact" else f"generation.{stage}"
                        response = budgeted.complete(
                            request,
                            call_id=f"{_artifact_id}:{phase}",
                            phase=phase,
                            attempt=attempt,
                        )
                        _append_private_evidence(
                            evidence_path,
                            {
                                "kind": "generation_call",
                                "provider_slot_id": _slot_id,
                                "artifact_id": _artifact_id,
                                "phase": phase,
                                "attempt": attempt,
                                "prompt": request.prompt,
                                "response": response,
                            },
                        )
                        return response

                    agent = RuntimeCheckpointAgent.from_provider(
                        budgeted,
                        model=slot.model,
                        model_version=slot.model_version,
                        context_manager=NoCompactionManager(),
                        stage_completion=stage_completion,
                        max_stage_attempts=2,
                    )
                    try:
                        execution = agent.execute_with_checkpoints(
                            pair,
                            variant=variant,
                            task_family=configuration.task_family,
                        )
                    except (BudgetExhaustedError, CostUnverifiedError, DurabilityError):
                        raise
                    except Exception:
                        report["state"] = "incomplete_generation"
                        report["error_class"] = "GenerationStageError"
                        report["generation_stage_count"] = generation_stage_count
                        report["cost"] = ledger.report()
                        _checkpoint(
                            run_directory,
                            run_id=run_id,
                            state=report["state"],
                            source_revision=source_revision,
                            corpus_manifest_sha256=report["corpus_manifest_sha256"],
                            configuration_sha256=report["configuration_sha256"],
                            rubric_sha256=configuration.protocol_hashes["rubric_sha256"],
                            ledger_head_hash=ledger.ledger_head_hash,
                            completed_artifact_count=len(artifacts),
                            completed_judge_count=0,
                        )
                        break
                    artifacts[join.base_task_id] = {
                        "artifact_id": artifact_id,
                        "artifact": dict(execution.artifact),
                        "execution": execution,
                        "join": join,
                    }
                    generation_stage_count += 3
                    _checkpoint(
                        run_directory,
                        run_id=run_id,
                        state="generating",
                        source_revision=source_revision,
                        corpus_manifest_sha256=report["corpus_manifest_sha256"],
                        configuration_sha256=report["configuration_sha256"],
                        rubric_sha256=configuration.protocol_hashes["rubric_sha256"],
                        ledger_head_hash=ledger.ledger_head_hash,
                        completed_artifact_count=len(artifacts),
                        completed_judge_count=0,
                    )
                if report["state"] == "incomplete_generation":
                    break
            report["generation_stage_count"] = generation_stage_count
            report["artifact_count"] = len(artifacts)
            if report["state"] != "incomplete_generation":
                judge_adapters = {
                    slot.id: budgeted_provider(adapters[slot.id], ledger)
                    for slot in configuration.providers
                }
                parsed_by_occurrence: dict[str, dict[str, Any]] = {}
                label_counts: Counter[str] = Counter()
                uncertain_count = 0
                for occurrence in plan.occurrences:
                    artifact_row = artifacts.get(occurrence.base_task_id)
                    if artifact_row is None:
                        raise ExploratoryPrepilotError("artifact join is incomplete")
                    join = artifact_row["join"]
                    reference = constraints_by_intent[join.source_intent_id]
                    request = JudgeRequest(
                        occurrence_id=occurrence.occurrence_id,
                        generated_acceptance_criteria=_canonical_json(artifact_row["artifact"]),
                        reference_constraints=reference,
                    )
                    responses: list[Any] = []
                    for slot in configuration.providers:
                        parsed, error_class = _invoke_judge(
                            budgeted=judge_adapters[slot.id],
                            provider_slot_id=slot.id,
                            occurrence_id=occurrence.occurrence_id,
                            request=request,
                            evidence_path=evidence_path,
                        )
                        if parsed is None:
                            uncertain_count += 1
                            responses = []
                            break
                        responses.append(parsed)
                    if len(responses) == 2:
                        consolidated = consolidate_two_judges(responses[0], responses[1])
                        label_counts[consolidated.label] += 1
                        parsed_by_occurrence[occurrence.occurrence_id] = {
                            "label": consolidated.label,
                            "consensus": consolidated.consensus,
                        }
                        if not consolidated.consensus:
                            uncertain_count += 1
                    else:
                        parsed_by_occurrence[occurrence.occurrence_id] = {
                            "label": "uncertain",
                            "consensus": False,
                        }
                    _checkpoint(
                        run_directory,
                        run_id=run_id,
                        state="judging",
                        source_revision=source_revision,
                        corpus_manifest_sha256=report["corpus_manifest_sha256"],
                        configuration_sha256=report["configuration_sha256"],
                        rubric_sha256=configuration.protocol_hashes["rubric_sha256"],
                        ledger_head_hash=ledger.ledger_head_hash,
                        completed_artifact_count=len(artifacts),
                        completed_judge_count=len(parsed_by_occurrence),
                    )
                report["judge_result_count"] = len(parsed_by_occurrence)
                report["uncertain_judge_count"] = uncertain_count
                report["label_counts"] = dict(sorted(label_counts.items()))
                report["state"] = (
                    "completed_with_uncertainty" if uncertain_count else "completed"
                )
            report["cost"] = ledger.report()
    except (BudgetExhaustedError,):
        report["state"] = "stopped_budget_exhausted"
        report["error_class"] = "BudgetExhaustedError"
    except (CostUnverifiedError, AmbiguousInFlightError, DurabilityError):
        report["state"] = "stopped_cost_unverified"
        report["error_class"] = "CostUnverifiedError"
    except (CorpusIntakeError, ProviderRuntimeConfigError, ProtocolHashError, ExploratoryPrepilotError, OSError, ValueError) as error:
        report["state"] = "stopped_protocol_violation"
        report["error_class"] = _safe_error(error)
    finally:
        if ledger is not None and report["cost"] is None:
            report["cost"] = ledger.report()
        report["finished_at"] = datetime.now(UTC).isoformat()
        report["status"] = report["state"]
        _atomic_json_write(run_directory / "report.json", report)
        output.parent.mkdir(parents=True, exist_ok=True)
        _atomic_json_write(output, report)
    return report


__all__ = [
    "CANONICAL_FROZEN_MANIFEST",
    "ExploratoryPrepilotError",
    "SCHEMA_VERSION",
    "TERMINAL_STATES",
    "run_exploratory_prepilot",
]
