"""Provider/run metadata kept separate from thesis labels and deployable features."""

from __future__ import annotations

import hashlib
import json
import re
from dataclasses import dataclass, field
from typing import Any, Mapping


_SECRET_MARKERS = ("secret", "token", "password", "api_key", "apikey", "authorization")


def _assert_no_secrets(value: Any, *, path: str = "metadata") -> None:
    if isinstance(value, Mapping):
        for key, item in value.items():
            key_text = str(key).lower()
            if any(marker in key_text for marker in _SECRET_MARKERS):
                raise ValueError(f"secret-like field cannot be exported: {path}.{key}")
            _assert_no_secrets(item, path=f"{path}.{key}")
    elif isinstance(value, (list, tuple)):
        for index, item in enumerate(value):
            _assert_no_secrets(item, path=f"{path}[{index}]")


@dataclass(frozen=True, slots=True)
class ProviderRunMetadata:
    """Auditable provider metadata for one run, without prompts or secrets."""

    run_id: str
    mode: str
    provider: str
    model: str
    model_version: str
    seed: int | None
    configuration_hash: str
    episode_count: int
    total_latency_ms: float
    total_cost_usd: float
    extra: Mapping[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        for name in ("run_id", "mode", "provider", "model", "model_version", "configuration_hash"):
            if not str(getattr(self, name)).strip():
                raise ValueError(f"{name} is required")
        if self.mode not in {"stub", "replay", "mock", "live", "runtime"}:
            raise ValueError("mode must be stub, replay, mock, live, or runtime")
        if self.episode_count < 0 or self.total_latency_ms < 0 or self.total_cost_usd < 0:
            raise ValueError("provider counters must be non-negative")
        _assert_no_secrets(self.extra)

    def to_dict(self) -> dict[str, Any]:
        return {
            "run_id": self.run_id,
            "mode": self.mode,
            "provider": self.provider,
            "model": self.model,
            "model_version": self.model_version,
            "seed": self.seed,
            "configuration_hash": self.configuration_hash,
            "episode_count": self.episode_count,
            "total_latency_ms": round(self.total_latency_ms, 3),
            "total_cost_usd": round(self.total_cost_usd, 8),
            "extra": dict(self.extra),
        }


def summarize_provider_runs(runs: list[ProviderRunMetadata]) -> dict[str, Any]:
    return {
        "runs": len(runs),
        "metadata": [run.to_dict() for run in runs],
        "total_latency_ms": round(sum(run.total_latency_ms for run in runs), 3),
        "total_cost_usd": round(sum(run.total_cost_usd for run in runs), 8),
    }


_SHA256_HEX = re.compile(r"[0-9a-f]{64}")


def configuration_identity_digest(
    *,
    provider: str,
    model: str,
    model_version: str,
    instructions_sha256: str,
    tool_definitions: list[Mapping[str, Any]],
    runtime_config: Mapping[str, Any],
) -> str:
    """Content-address the executed configuration (model, instructions, tools, runtime).

    A nominal version string can sit behind a mutable pointer; hashing the
    instructions, tool definitions and runtime settings together makes a silent
    change visible. The digest records identity only: it does not authenticate who
    produced it or prove the provider served the named model. Non-finite or
    non-JSON configuration values are rejected rather than stringified.
    """

    if not _SHA256_HEX.fullmatch(instructions_sha256):
        raise ValueError("instructions_sha256 must be a lowercase SHA-256 hex digest")
    _assert_no_secrets(runtime_config, path="runtime_config")
    _assert_no_secrets(list(tool_definitions), path="tool_definitions")
    canonical = json.dumps(
        {
            "provider": provider,
            "model": model,
            "model_version": model_version,
            "instructions_sha256": instructions_sha256,
            "tool_definitions": sorted(
                (dict(tool) for tool in tool_definitions),
                key=lambda tool: json.dumps(tool, sort_keys=True, allow_nan=False),
            ),
            "runtime_config": dict(runtime_config),
        },
        sort_keys=True,
        separators=(",", ":"),
        allow_nan=False,
    )
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


def identity_binding_gaps(run: ProviderRunMetadata) -> list[str]:
    """Report why a live/runtime run's identity is not content-addressed.

    Offline readiness check for confirmatory runs; it does not reject legacy
    metadata, which keeps free-form ``configuration_hash`` values.
    """

    gaps: list[str] = []
    if run.mode in {"live", "runtime"}:
        if not _SHA256_HEX.fullmatch(run.configuration_hash):
            gaps.append("configuration_hash is not a SHA-256 hex digest")
        if run.model_version.strip() == run.model.strip():
            gaps.append("model_version repeats the model alias; no pinned snapshot recorded")
        if not run.extra.get("prompt_sha256s"):
            gaps.append("no prompt_sha256s recorded")
    return gaps
