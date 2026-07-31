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

    def __post_init__(self) -> None:
        if isinstance(self.smell, Mapping):
            object.__setattr__(self, "smell", _freeze(self.smell))

    @classmethod
    def from_episode(cls, episode: Mapping[str, Any]) -> FeatureEpisodeInput:
        smell = episode.get("smell")
        return cls(
            intent_id=str(episode["intent_id"]),
            task_family=str(episode["task_family"]),
            variant=str(episode["variant"]),
            smell=smell if isinstance(smell, Mapping) else None,
            requirement_text=str(episode.get("requirement_text", "")),
        )


@dataclass(frozen=True, slots=True)
class DeployableFeatureInput:
    """The strict, deployable pre-final input contract.

    This model deliberately contains only information available before the
    terminal label is produced.  ``variant`` and ``smell`` remain on the
    legacy :class:`FeatureEpisodeInput` for backwards-compatible retrospective
    analyses, but are not part of this contract.
    """

    intent_id: str
    task_family: str
    requirement_text: str

    @classmethod
    def from_episode(cls, episode: Mapping[str, Any]) -> "DeployableFeatureInput":
        """Copy only the allowlisted fields from an episode mapping.

        Reading explicit keys (rather than copying a mapping and filtering it
        later) makes terminal fields impossible to smuggle into the feature
        plane, including nested ``artifact``/oracle/label values.
        """

        return cls(
            intent_id=str(episode["intent_id"]),
            task_family=str(episode["task_family"]),
            requirement_text=str(episode.get("requirement_text", "")),
        )
