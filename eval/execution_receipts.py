"""Immutable restoration of complete runtime-native T1--T3 executions."""
from dataclasses import asdict
from pathlib import Path
from typing import Any, Mapping

from agents.checkpoints import AgentExecution, CheckpointObservation, validate_agent_execution
from eval.recoverable_calls import RecoveryBlocked, digest, durable_create, read_record


def _execution_value(execution: AgentExecution) -> dict[str, Any]:
    return {
        "checkpoints": [asdict(item) for item in execution.checkpoints],
        "artifact": dict(execution.artifact),
        "provider_meta": dict(execution.provider_meta),
    }


def _validated(value: Mapping[str, Any]) -> AgentExecution:
    if set(value) != {"checkpoints", "artifact", "provider_meta"}:
        raise RecoveryBlocked("execution receipt has an invalid field set")
    try:
        execution = AgentExecution(
            tuple(CheckpointObservation(**item) for item in value["checkpoints"]),
            value["artifact"], value["provider_meta"],
        )
        return validate_agent_execution(
            execution,
            require_conditional_semantics=True,
            require_constraint_lineage=True,
            require_atomic_obligations=True,
        )
    except (KeyError, TypeError, ValueError) as error:
        raise RecoveryBlocked("execution receipt is not a valid runtime execution") from error


class ExecutionReceipts:
    """Persist complete executions; partial stages are deliberately not replayable."""

    def __init__(self, directory: Path, scope: Mapping[str, str], ledger) -> None:
        self.directory = Path(directory)
        self.scope_sha256 = digest(dict(scope))
        self.ledger = ledger

    @staticmethod
    def _name(artifact_id: str) -> str:
        return f"execution-{digest(artifact_id)}.json"

    def binding(self, *, artifact_id: str, episode_id: str, base_task_id: str,
                provider_slot_id: str, provider: str, model: str,
                model_version: str, pair: Mapping[str, Any], variant: str,
                task_family: str) -> dict[str, Any]:
        return {
            "artifact_id": artifact_id, "episode_id": episode_id,
            "base_task_id": base_task_id, "provider_slot_id": provider_slot_id,
            "provider": provider, "model": model, "model_version": model_version,
            "pair_sha256": digest(pair), "variant": variant,
            "task_family": task_family, "scope_sha256": self.scope_sha256,
        }

    def load(self, binding: Mapping[str, Any]) -> AgentExecution | None:
        path = self.directory / self._name(str(binding["artifact_id"]))
        if not path.exists():
            return None
        record = read_record(path, 8_388_608)
        if set(record) != {"schema", "binding", "execution", "execution_sha256",
                           "ledger_head_hash"} or record["schema"] != "execution-receipt/v1":
            raise RecoveryBlocked("execution receipt has an invalid envelope")
        if record["binding"] != dict(binding):
            raise RecoveryBlocked("execution receipt binding changed")
        if record["execution_sha256"] != digest(record["execution"]):
            raise RecoveryBlocked("execution receipt checksum mismatch")
        heads = {event.get("event_hash") for event in self.ledger.events}
        if record["ledger_head_hash"] not in heads:
            raise RecoveryBlocked("execution receipt cost boundary is not in the ledger")
        execution = _validated(record["execution"])
        if any(execution.provider_meta.get(field) != binding[field]
               for field in ("provider", "model", "model_version")):
            raise RecoveryBlocked("execution receipt provider identity mismatch")
        return execution

    def validate_inventory(self, artifact_ids) -> None:
        expected = {self._name(str(value)) for value in artifact_ids}
        actual = {path.name for path in self.directory.glob("execution-*.json")}
        if not actual.issubset(expected):
            raise RecoveryBlocked("unexpected execution receipt in run directory")

    def save(self, binding: Mapping[str, Any], execution: AgentExecution) -> None:
        value = _execution_value(_validated(_execution_value(execution)))
        record = {
            "schema": "execution-receipt/v1", "binding": dict(binding),
            "execution": value, "execution_sha256": digest(value),
            "ledger_head_hash": self.ledger.ledger_head_hash,
        }
        durable_create(
            self.directory / self._name(str(binding["artifact_id"])), record)


__all__ = ["ExecutionReceipts"]
