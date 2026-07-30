"""Replication-safe identity created before an evaluation episode executes."""

from __future__ import annotations

import hashlib
import json
import re
from uuid import uuid4
from dataclasses import asdict, dataclass
from typing import Any, Mapping


def configuration_id_for(configuration: Mapping[str, Any]) -> str:
    """Return a stable identifier for the execution configuration."""
    encoded = json.dumps(configuration, sort_keys=True, separators=(",", ":"), default=str)
    return f"cfg-{hashlib.sha256(encoded.encode('utf-8')).hexdigest()[:12]}"


def new_run_id() -> str:
    """Return a collision-resistant ID when a caller did not supply one."""
    return f"run-{uuid4().hex}"


def _name_part(value: object) -> str:
    return re.sub(r"[^A-Za-z0-9._-]+", "-", str(value)).strip("-") or "unknown"


@dataclass(frozen=True, slots=True)
class EpisodeIdentity:
    experiment_id: str
    run_id: str
    episode_id: str
    replication_id: int
    intent_id: str
    workload_id: str
    variant_id: str
    task_id: str
    configuration_id: str

    @property
    def trace_name(self) -> str:
        return f"{self.episode_id}.jsonl"

    def as_dict(self) -> dict[str, str | int]:
        return asdict(self)


def create_episode_identity(
    *,
    experiment_id: str,
    run_id: str,
    replication_id: int,
    intent_id: str,
    workload_id: str,
    variant_id: str,
    task_id: str,
    configuration_id: str,
) -> EpisodeIdentity:
    """Build the immutable identity used by trace, events, and exports."""
    parts = (
        _name_part(experiment_id),
        _name_part(run_id),
        f"rep-{replication_id}",
        _name_part(workload_id),
        _name_part(intent_id),
        _name_part(variant_id),
        _name_part(task_id),
        _name_part(configuration_id),
    )
    return EpisodeIdentity(
        experiment_id=experiment_id,
        run_id=run_id,
        episode_id="__".join(parts),
        replication_id=replication_id,
        intent_id=intent_id,
        workload_id=workload_id,
        variant_id=variant_id,
        task_id=task_id,
        configuration_id=configuration_id,
    )
