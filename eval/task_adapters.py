"""Domain task and validation adapters for evaluation episodes."""

from __future__ import annotations

import json
import hashlib
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Protocol

from label_plane import score_artifact, score_test_gen_mutation
from eval.codegen_sandbox import (
    evaluate as evaluate_generated_code,
    evaluate_trusted_fixture,
)


@dataclass(frozen=True, slots=True)
class TaskEvaluation:
    passed: bool
    mutation_score: float | None = None
    behavior_status: str | None = None
    target_condition_failures: int = 0
    unrelated_condition_failures: int = 0
    behavior_report: dict[str, Any] | None = None


def _canonical_artifact(artifact: dict[str, Any]) -> bytes:
    return json.dumps(artifact, sort_keys=True, separators=(",", ":")).encode("utf-8")


class TaskAdapter(Protocol):
    """Generates and evaluates one benchmark task family."""

    task_family: str

    def evaluate(
        self,
        *,
        intent_id: str,
        artifact: dict[str, Any],
        oracle_spec: dict[str, Any],
    ) -> TaskEvaluation: ...


class EpisodeValidator(Protocol):
    """Validates evidence emitted by a completed evaluation episode."""

    name: str

    def validate(self, provenance_path: Path) -> bool: ...


class AcceptanceCriteriaAdapter:
    """Primary adapter for acceptance-criteria generation tasks."""

    task_family = "test_gen"

    def evaluate(
        self,
        *,
        intent_id: str,
        artifact: dict[str, Any],
        oracle_spec: dict[str, Any],
    ) -> TaskEvaluation:
        result = score_artifact(
            intent_id,
            self.task_family,
            artifact,
            oracle_spec[self.task_family],
        )
        return TaskEvaluation(
            passed=result.passed,
            mutation_score=score_test_gen_mutation(intent_id, artifact, oracle_spec),
        )


class CodeGenerationAdapter:
    """Optional adapter for implementation artifact generation."""

    task_family = "codegen"

    def evaluate(
        self,
        *,
        intent_id: str,
        artifact: dict[str, Any],
        oracle_spec: dict[str, Any],
    ) -> TaskEvaluation:
        result = score_artifact(
            intent_id,
            self.task_family,
            artifact,
            oracle_spec[self.task_family],
        )
        return TaskEvaluation(passed=result.passed)


class BehavioralCodeGenerationAdapter:
    """Execute the small, restricted implementation used by discovery cases."""

    task_family = "behavior_codegen"

    def __init__(self, *, allow_trusted_fixture: bool = False) -> None:
        self.allow_trusted_fixture = allow_trusted_fixture

    @staticmethod
    def _hidden_tests(execution_spec: dict[str, Any]) -> list[dict[str, Any]]:
        tests: list[dict[str, Any]] = []
        argument_names = list(
            execution_spec.get("argument_names", [])
            or execution_spec.get("input_schema", {}).get("required", [])
        )
        for case in execution_spec.get("hidden_tests", []):
            if not isinstance(case, dict):
                continue
            if "args" in case:
                args = case.get("args", [])
                kwargs = case.get("kwargs", {})
            else:
                value = case.get("input")
                if isinstance(value, dict) and argument_names and all(name in value for name in argument_names):
                    args = [value[name] for name in argument_names]
                else:
                    args = [value]
                kwargs = {}
            expected = case.get("expected", case.get("expected_output"))
            tests.append(
                {
                    "id": str(case.get("id", len(tests))),
                    "args": args,
                    "kwargs": kwargs,
                    "expected": expected,
                }
            )
        return tests

    def evaluate(
        self,
        *,
        intent_id: str,
        artifact: dict[str, Any],
        oracle_spec: dict[str, Any],
    ) -> TaskEvaluation:
        del intent_id
        spec = oracle_spec.get(self.task_family, {})
        execution_spec = spec.get("_execution", {}) if isinstance(spec, dict) else {}
        source = artifact.get("source_code") if isinstance(artifact, dict) else None
        if not isinstance(execution_spec, dict) or not isinstance(source, str):
            return TaskEvaluation(False, behavior_status="invalid")

        hidden_tests = self._hidden_tests(execution_spec)
        report = evaluate_generated_code(
            source,
            hidden_tests,
            timeout_seconds=float(execution_spec.get("timeout_seconds", 1.0)),
        )
        references = execution_spec.get("reference_implementations", {})
        if (
            report.get("status") == "unsafe_not_run"
            and self.allow_trusted_fixture
            and isinstance(references, dict)
            and source in references.values()
        ):
            report = evaluate_trusted_fixture(source, hidden_tests)
        case_ids = {
            index: str(case.get("id", index))
            for index, case in enumerate(execution_spec.get("hidden_tests", []))
            if isinstance(case, dict)
        }
        target_ids = {
            str(value) for value in execution_spec.get("removed_condition_test_ids", [])
        }
        failed_ids = {
            case_ids.get(index, str(index))
            for index, case in enumerate(report.get("cases", []))
            if case.get("status") != "passed"
        }
        target_failures = len(failed_ids & target_ids)
        unrelated_failures = len(failed_ids - target_ids)
        status = str(report.get("status", "invalid"))
        if status == "passed":
            behavior_status = "passed"
        elif status == "timeout":
            behavior_status = "timeout"
        elif status in {"rejected", "unsafe_not_run"}:
            behavior_status = status
        elif report.get("errors"):
            behavior_status = "crash"
        elif target_failures and not unrelated_failures:
            behavior_status = "failed_target_condition"
        elif unrelated_failures:
            behavior_status = "failed_unrelated_condition"
        else:
            behavior_status = "invalid"
        return TaskEvaluation(
            passed=behavior_status == "passed",
            behavior_status=behavior_status,
            target_condition_failures=target_failures,
            unrelated_condition_failures=unrelated_failures,
            behavior_report=report,
        )


class TraceabilityAdapter:
    """Validate that a completed episode retains its semantic trace checkpoint."""

    name = "traceability"

    def validate(self, provenance_path: Path) -> bool:
        if not provenance_path.exists():
            return False
        return any(
            isinstance(event, dict)
            and event.get("kind") == "semantic"
            and event.get("name") == "constraint_extract"
            for line in provenance_path.read_text(encoding="utf-8").splitlines()
            if line.strip()
            for event in (json.loads(line),)
        )


class TraceabilityTaskAdapter:
    """Resolve requirement claims to hashed spans in a generated artifact.

    This adapter is intentionally independent of the terminal oracle.  The
    task reference contains claim-to-path links, while the generated artifact
    is the observable target. Missing, stale, tampered, and self-reported
    links are failures rather than silently accepted evidence.
    """

    task_family = "traceability"

    @staticmethod
    def artifact_hash(artifact: dict[str, Any]) -> str:
        return hashlib.sha256(_canonical_artifact(artifact)).hexdigest()

    def evaluate(
        self,
        *,
        intent_id: str,
        artifact: dict[str, Any],
        oracle_spec: dict[str, Any],
    ) -> TaskEvaluation:
        del intent_id
        traceability_spec = oracle_spec.get("traceability", {})
        links = oracle_spec.get("links", traceability_spec.get("links", []))
        if not isinstance(links, list) or not links:
            return TaskEvaluation(False)
        expected_hash = self.artifact_hash(artifact)
        for link in links:
            if not isinstance(link, dict) or link.get("self_reported"):
                return TaskEvaluation(False)
            path = str(link.get("artifact_path", ""))
            if not path.startswith("/"):
                return TaskEvaluation(False)
            value: Any = artifact
            for segment in path.strip("/").split("/"):
                if not isinstance(value, dict) or segment not in value:
                    return TaskEvaluation(False)
                value = value[segment]
            if str(link.get("artifact_sha256")) != expected_hash:
                return TaskEvaluation(False)
        return TaskEvaluation(True)


def load_traceability_manifest(path: Path | str | None = None) -> dict[str, Any]:
    """Load the versioned adversarial traceability task contract."""
    manifest_path = Path(path) if path else Path(__file__).resolve().parents[1] / "tasks" / "traceability.json"
    payload = json.loads(manifest_path.read_text(encoding="utf-8"))
    if payload.get("schema_version") != "traceability/v1":
        raise ValueError("unsupported traceability task manifest")
    cases = payload.get("cases")
    if not isinstance(cases, list) or not cases:
        raise ValueError("traceability task manifest requires cases")
    if not all(case.get("oracle_independent") is True for case in cases):
        raise ValueError("traceability cases must be oracle-independent")
    return payload


# Preserve the historical benchmark coverage and episode ordering by default.
DEFAULT_TASK_ADAPTERS: tuple[TaskAdapter, ...] = (
    CodeGenerationAdapter(),
    AcceptanceCriteriaAdapter(),
)
# External acceptance runs opt into this adapter explicitly; the historical
# benchmark remains unchanged until a traceability task manifest is supplied.
EXTERNAL_TASK_ADAPTERS: tuple[TaskAdapter, ...] = (TraceabilityTaskAdapter(),)
DEFAULT_VALIDATORS: tuple[EpisodeValidator, ...] = (TraceabilityAdapter(),)
