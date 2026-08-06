"""Auditable episode handoffs kept separate from experiment labels."""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Literal

Plane = Literal["pre_final", "post_eval"]
_LABEL_KEYS = {"oracle", "oracle_verdict", "label", "ground_truth", "outcome", "adjudication"}
_RESERVED_FIELDS = {
    "experiment_id",
    "run_id",
    "episode_id",
    "plane",
    "decision",
    "next_step",
    "risks",
    "new_facts",
    "source_refs",
}


@dataclass(frozen=True)
class SourceRef:
    kind: str
    identifier: str
    content_hash: str | None = None
    event_id: str | None = None
    sequence_number: int | None = None

    def __post_init__(self) -> None:
        if not self.kind.strip() or not self.identifier.strip():
            raise ValueError("source reference kind and identifier are required")
        if any(part in self.identifier.lower() for part in ("api_key", "token", "password", "secret")):
            raise ValueError("source reference identifier cannot contain secret-like values")
        if self.sequence_number is not None and self.sequence_number < 0:
            raise ValueError("source reference sequence_number must be non-negative")

    def to_dict(self) -> dict[str, Any]:
        value = {"kind": self.kind, "identifier": self.identifier}
        if self.content_hash is not None:
            value["content_hash"] = self.content_hash
        if self.event_id is not None:
            value["event_id"] = self.event_id
        if self.sequence_number is not None:
            value["sequence_number"] = self.sequence_number
        return value


@dataclass(frozen=True)
class EpisodeHandoff:
    experiment_id: str
    run_id: str
    episode_id: str
    plane: Plane
    decision: str
    next_step: str
    risks: tuple[str, ...]
    new_facts: tuple[str, ...]
    source_refs: tuple[SourceRef, ...]
    extra: dict[str, Any]

    def to_dict(self) -> dict[str, Any]:
        return {
            "experiment_id": self.experiment_id,
            "run_id": self.run_id,
            "episode_id": self.episode_id,
            "plane": self.plane,
            "decision": self.decision,
            "next_step": self.next_step,
            "risks": list(self.risks),
            "new_facts": list(self.new_facts),
            "source_refs": [ref.to_dict() for ref in self.source_refs],
            **self.extra,
        }


def build_handoff(
    *,
    experiment_id: str,
    run_id: str,
    episode_id: str,
    plane: Plane,
    decision: str,
    next_step: str,
    risks: list[str],
    new_facts: list[str],
    source_refs: list[SourceRef],
    extra: dict[str, Any] | None = None,
) -> EpisodeHandoff:
    if plane not in {"pre_final", "post_eval"}:
        raise ValueError("plane must be pre_final or post_eval")
    extra = dict(extra or {})
    reserved = sorted(_RESERVED_FIELDS.intersection(extra))
    if reserved:
        raise ValueError(f"handoff extra cannot override reserved fields: {', '.join(reserved)}")
    if plane == "pre_final":
        leaked = sorted(_LABEL_KEYS.intersection(extra) | _nested_label_keys(extra))
        if leaked:
            raise ValueError(f"pre_final handoff cannot contain label fields: {', '.join(leaked)}")
    return EpisodeHandoff(
        experiment_id=experiment_id,
        run_id=run_id,
        episode_id=episode_id,
        plane=plane,
        decision=decision,
        next_step=next_step,
        risks=tuple(risks),
        new_facts=tuple(new_facts),
        source_refs=tuple(source_refs),
        extra=extra,
    )


def _nested_label_keys(value: Any) -> set[str]:
    found: set[str] = set()
    if isinstance(value, dict):
        for key, item in value.items():
            normalized = str(key).lower().replace("-", "_")
            if normalized in _LABEL_KEYS or any(token in normalized for token in ("groundtruth", "outcome", "adjudicat")):
                found.add(str(key))
            found.update(_nested_label_keys(item))
    elif isinstance(value, list):
        for item in value:
            found.update(_nested_label_keys(item))
    return found


def write_handoff(path: Path | str, handoff: EpisodeHandoff) -> Path:
    destination = Path(path)
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_text(
        json.dumps(handoff.to_dict(), ensure_ascii=True, sort_keys=True, indent=2) + "\n",
        encoding="utf-8",
    )
    return destination
