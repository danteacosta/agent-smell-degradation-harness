from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Mapping


@dataclass(frozen=True, slots=True)
class FeatureEpisodeInput:
    """The episode data available before final evaluation."""

    intent_id: str
    task_family: str
    variant: str
    smell: Mapping[str, Any] | None
    requirement_text: str
    provenance_jsonl: str

    @classmethod
    def from_episode(
        cls, episode: Mapping[str, Any], provenance_jsonl: str
    ) -> FeatureEpisodeInput:
        return cls(
            intent_id=str(episode["intent_id"]),
            task_family=str(episode["task_family"]),
            variant=str(episode["variant"]),
            smell=episode.get("smell"),
            requirement_text=str(episode.get("requirement_text", "")),
            provenance_jsonl=provenance_jsonl,
        )
