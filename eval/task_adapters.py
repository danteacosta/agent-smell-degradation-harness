"""Domain task and validation adapters for evaluation episodes."""

from __future__ import annotations

import json
import hashlib
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Protocol

from label_plane import score_artifact, score_test_gen_mutation


@dataclass(frozen=True, slots=True)
class TaskEvaluation:
    passed: bool
    mutation_score: float | None = None


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
