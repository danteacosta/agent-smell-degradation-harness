"""Domain task and validation adapters for evaluation episodes."""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Protocol

from label_plane import score_artifact, score_test_gen_mutation


@dataclass(frozen=True, slots=True)
class TaskEvaluation:
    passed: bool
    mutation_score: float | None = None


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


# Preserve the historical benchmark coverage and episode ordering by default.
DEFAULT_TASK_ADAPTERS: tuple[TaskAdapter, ...] = (
    CodeGenerationAdapter(),
    AcceptanceCriteriaAdapter(),
)
DEFAULT_VALIDATORS: tuple[EpisodeValidator, ...] = (TraceabilityAdapter(),)
