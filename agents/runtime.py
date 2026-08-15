"""Model-neutral adapter for one runtime-native confirmatory execution."""

from __future__ import annotations

from collections.abc import Callable
from typing import Any

from .checkpoints import AgentExecution, validate_agent_execution


NativeExecutor = Callable[[dict[str, Any], str, str], AgentExecution]


class RuntimeCheckpointAgent:
    """Adapt an instrumented agent runtime without prompting for checkpoints.

    The supplied executor must run the task once and return the artifact plus
    the checkpoints captured by that same runtime execution. This seam can be
    implemented by MergeWave/ACP, Orca, or another runtime without coupling
    the harness to a model provider.
    """

    run_mode = "runtime"
    checkpoint_provenance = "runtime_native"

    def __init__(
        self,
        executor: NativeExecutor,
        *,
        provider: str,
        model: str,
        model_version: str,
    ) -> None:
        if not all(value.strip() for value in (provider, model, model_version)):
            raise ValueError("provider, model, and model_version are required")
        self._executor = executor
        self.provider = provider
        self.model = model
        self.model_version = model_version

    def execute_with_checkpoints(
        self,
        pair: dict[str, Any],
        *,
        variant: str,
        task_family: str,
    ) -> AgentExecution:
        execution = validate_agent_execution(self._executor(pair, variant, task_family))
        metadata = {
            "provider": self.provider,
            "model": self.model,
            "model_version": self.model_version,
            **dict(execution.provider_meta),
        }
        return AgentExecution(execution.checkpoints, execution.artifact, metadata)


__all__ = ["NativeExecutor", "RuntimeCheckpointAgent"]
