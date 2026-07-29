from __future__ import annotations

from dataclasses import dataclass
from types import MappingProxyType
from typing import Any, Mapping


def _freeze(value: Any) -> Any:
    if isinstance(value, Mapping):
        return MappingProxyType({key: _freeze(item) for key, item in value.items()})
    if isinstance(value, list):
        return tuple(_freeze(item) for item in value)
    if isinstance(value, set):
        return frozenset(_freeze(item) for item in value)
    return value


@dataclass(frozen=True, slots=True)
class FeatureEpisodeInput:
    """The episode data available before final evaluation."""

    intent_id: str
    task_family: str
    variant: str
    smell: Mapping[str, Any] | None
    requirement_text: str
    @classmethod
    def from_episode(cls, episode: Mapping[str, Any]) -> FeatureEpisodeInput:
        smell = episode.get("smell")
        return cls(
            intent_id=str(episode["intent_id"]),
            task_family=str(episode["task_family"]),
            variant=str(episode["variant"]),
            smell=_freeze(smell) if isinstance(smell, Mapping) else None,
            requirement_text=str(episode.get("requirement_text", "")),
        )
