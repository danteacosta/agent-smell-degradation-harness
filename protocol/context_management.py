"""Explicit context-management conditions for reproducible agent runs.

The core thesis condition is no_compaction. The deterministic compactor is
only a protocol/stress-test implementation; it is not evidence about a
production provider's compaction algorithm. All measurements are redacted
metadata and never include the context text.
"""

from __future__ import annotations

from collections import Counter
from dataclasses import dataclass
from hashlib import sha256
from typing import Any, Literal, Mapping, Protocol

CONTEXT_MANAGEMENT_SCHEMA_VERSION = "context-management/v1"
CONTEXT_SIZE_UNIT = "utf8_bytes"
ContextOperation = Literal["none", "compact", "decompose", "retrieve", "evict", "truncate"]


@dataclass(frozen=True, slots=True)
class ContextTransformation:
    """A transformed provider context plus redacted size metadata."""

    prompt: str
    operation: str
    trigger: str
    context_size_before: int
    context_size_after: int
    context_size_unit: str = CONTEXT_SIZE_UNIT


class ContextManager(Protocol):
    """The runtime seam for a provider/orchestrator context manager."""

    condition: str

    def prepare(self, prompt: str, *, stage: str) -> ContextTransformation:
        """Return the provider-visible context and its redacted transformation."""


@dataclass(frozen=True, slots=True)
class NoCompactionManager:
    """Identity context manager used by the primary pre-pilot condition."""

    condition: str = "no_compaction"

    def prepare(self, prompt: str, *, stage: str) -> ContextTransformation:
        size = _utf8_size(prompt)
        return ContextTransformation(
            prompt=prompt,
            operation="none",
            trigger="policy_disabled",
            context_size_before=size,
            context_size_after=size,
        )


@dataclass(frozen=True, slots=True)
class DeterministicCompactionManager:
    """Deterministic truncation used only for the secondary stress-test cell."""

    max_context_bytes: int = 256
    condition: str = "compaction_stress_test"

    def __post_init__(self) -> None:
        if self.max_context_bytes < 64:
            raise ValueError("max_context_bytes must be at least 64 bytes")

    def prepare(self, prompt: str, *, stage: str) -> ContextTransformation:
        before = _utf8_size(prompt)
        if before <= self.max_context_bytes:
            return ContextTransformation(
                prompt=prompt,
                operation="none",
                trigger="below_test_budget",
                context_size_before=before,
                context_size_after=before,
            )
        compacted = _compact_text(prompt, self.max_context_bytes)
        return ContextTransformation(
            prompt=compacted,
            operation="compact",
            trigger="deterministic_test_budget",
            context_size_before=before,
            context_size_after=_utf8_size(compacted),
        )


class UnsafeCompactionError(RuntimeError):
    """Raised when the typed hard lane cannot fit the configured budget."""


@dataclass(frozen=True, slots=True)
class TypedCompactionManager:
    """Article-inspired hard-lane proxy for a secondary mechanism check.

    Lines belonging to a requirement or typed pre-final summary are retained
    verbatim when they fit the budget. Other context is compacted with the
    deterministic prefix/suffix transform. This is a protocol proxy, not a
    reimplementation of the paper's learned classifier.
    """

    max_context_bytes: int = 512
    condition: str = "typed_compaction_stress_test"
    hard_lane_markers: tuple[str, ...] = (
        "requirement:",
        "constraints",
        "conditional_semantics",
        "validation_checks",
        "coverage_targets",
    )

    def __post_init__(self) -> None:
        if self.max_context_bytes < 64:
            raise ValueError("max_context_bytes must be at least 64 bytes")
        if not self.hard_lane_markers:
            raise ValueError("hard_lane_markers must not be empty")

    def prepare(self, prompt: str, *, stage: str) -> ContextTransformation:
        before = _utf8_size(prompt)
        if before <= self.max_context_bytes:
            return ContextTransformation(
                prompt=prompt,
                operation="none",
                trigger="below_test_budget",
                context_size_before=before,
                context_size_after=before,
            )
        compacted = _typed_compact_text(
            prompt,
            self.max_context_bytes,
            self.hard_lane_markers,
        )
        return ContextTransformation(
            prompt=compacted,
            operation="compact",
            trigger="typed_hard_lane_v1",
            context_size_before=before,
            context_size_after=_utf8_size(compacted),
        )

def build_context_event(
    transformation: ContextTransformation,
    *,
    event_id: str,
    stage: str,
    checkpoint_id: str,
    started_at: str,
    ended_at: str,
) -> dict[str, Any]:
    """Materialize one hash-bound, prompt-free context-management event."""

    if transformation.context_size_before < 0 or transformation.context_size_after < 0:
        raise ValueError("context sizes must be non-negative")
    if transformation.context_size_after > transformation.context_size_before:
        raise ValueError("context management cannot increase the measured context size")
    return {
        "schema_version": CONTEXT_MANAGEMENT_SCHEMA_VERSION,
        "event_id": event_id,
        "stage": stage,
        "operation": transformation.operation,
        "trigger": transformation.trigger,
        "started_at": started_at,
        "ended_at": ended_at,
        "context_size_before": transformation.context_size_before,
        "context_size_after": transformation.context_size_after,
        "context_size_unit": transformation.context_size_unit,
        "checkpoint_id": checkpoint_id,
        "checkpoint_sha256": sha256(transformation.prompt.encode("utf-8")).hexdigest(),
    }


def summarize_context_events(
    events: list[Mapping[str, Any]],
    *,
    condition: str,
) -> dict[str, Any]:
    """Return a compact condition summary for episode/provider metadata."""

    operations = Counter(str(event.get("operation", "")) for event in events)
    return {
        "schema_version": CONTEXT_MANAGEMENT_SCHEMA_VERSION,
        "condition": condition,
        "event_count": len(events),
        "compaction_count": operations.get("compact", 0),
        "operation_counts": dict(sorted(operations.items())),
        "context_size_unit": CONTEXT_SIZE_UNIT,
        "context_size_before": sum(
            int(event.get("context_size_before", 0))
            for event in events
            if isinstance(event.get("context_size_before"), int)
        ),
        "context_size_after": sum(
            int(event.get("context_size_after", 0))
            for event in events
            if isinstance(event.get("context_size_after"), int)
        ),
    }


def _typed_compact_text(
    value: str,
    max_bytes: int,
    hard_lane_markers: tuple[str, ...],
) -> str:
    """Keep marked hard-lane blocks and compact the remaining context."""

    lines = value.splitlines(keepends=True)
    markers = tuple(marker.lower() for marker in hard_lane_markers)
    hard_lines: list[str] = []
    soft_lines: list[str] = []
    in_hard_block = False
    for line in lines:
        lowered = line.lower()
        if any(marker in lowered for marker in markers):
            in_hard_block = True
        if in_hard_block:
            hard_lines.append(line)
        else:
            soft_lines.append(line)
        if in_hard_block and not line.strip():
            in_hard_block = False

    hard_text = "".join(hard_lines)
    hard_bytes = _utf8_size(hard_text)
    if hard_bytes > max_bytes:
        raise UnsafeCompactionError(
            "typed hard-lane content exceeds the context budget; "
            "expand the budget or decompose the context"
        )
    soft_text = "".join(soft_lines)
    if not soft_text:
        return hard_text
    separator = "\n[soft context compacted for typed hard lane]\n"
    separator_bytes = _utf8_size(separator)
    soft_budget = max_bytes - hard_bytes - separator_bytes
    if soft_budget <= 0:
        return hard_text
    return hard_text + separator + _compact_text(soft_text, soft_budget)


def _utf8_size(value: str) -> int:
    return len(value.encode("utf-8"))


def _compact_text(value: str, max_bytes: int) -> str:
    marker = "\n[context compacted for deterministic stress test]\n"
    marker_bytes = _utf8_size(marker)
    if marker_bytes >= max_bytes:
        return marker.encode("utf-8")[:max_bytes].decode("utf-8", errors="ignore")
    remaining = max_bytes - marker_bytes
    prefix_budget = remaining // 2
    suffix_budget = remaining - prefix_budget
    prefix = value.encode("utf-8")[:prefix_budget].decode("utf-8", errors="ignore")
    suffix = (
        value.encode("utf-8")[-suffix_budget:].decode("utf-8", errors="ignore")
        if suffix_budget
        else ""
    )
    return prefix + marker + suffix


__all__ = (
    "CONTEXT_MANAGEMENT_SCHEMA_VERSION",
    "CONTEXT_SIZE_UNIT",
    "ContextManager",
    "ContextOperation",
    "ContextTransformation",
    "DeterministicCompactionManager",
    "TypedCompactionManager",
    "UnsafeCompactionError",
    "NoCompactionManager",
    "build_context_event",
    "summarize_context_events",
)
