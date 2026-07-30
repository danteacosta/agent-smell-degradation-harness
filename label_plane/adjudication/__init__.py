"""Deterministic adjudication over primary human annotations."""

from collections import Counter
from dataclasses import dataclass
from typing import Sequence

from label_plane.human_annotation import HumanAnnotation


@dataclass(frozen=True, slots=True)
class Adjudication:
    label: str
    vote_count: int


def adjudicate(annotations: Sequence[HumanAnnotation]) -> Adjudication:
    if not annotations:
        raise ValueError("adjudication requires at least one annotation")
    counts = Counter(annotation.label for annotation in annotations)
    label, vote_count = counts.most_common(1)[0]
    if list(counts.values()).count(vote_count) > 1:
        raise ValueError("adjudication requires a non-tied vote")
    return Adjudication(label=label, vote_count=vote_count)


__all__ = ["Adjudication", "adjudicate"]
