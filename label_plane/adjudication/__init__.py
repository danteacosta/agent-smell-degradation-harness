"""Deterministic adjudication over primary human annotations."""

from __future__ import annotations

from collections import Counter
import json
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Iterable, Sequence

from label_plane.human_annotation import HumanAnnotation


@dataclass(frozen=True, slots=True)
class Adjudication:
    label: str
    vote_count: int
    item_id: str = ""
    adjudicator_id: str = ""
    rationale: str = ""
    source: str = "human_adjudication"
    labels_considered: tuple[str, ...] = field(default_factory=tuple)

    def to_dict(self) -> dict[str, object]:
        return asdict(self)


@dataclass(frozen=True, slots=True)
class Disagreement:
    item_id: str
    labels: tuple[str, ...]
    annotator_ids: tuple[str, ...]

    def to_dict(self) -> dict[str, object]:
        return asdict(self)


def adjudicate(
    annotations: Sequence[HumanAnnotation],
    *,
    adjudicator_id: str = "",
    rationale: str = "",
) -> Adjudication:
    if not annotations:
        raise ValueError("adjudication requires at least one annotation")
    if any(annotation.source != "human_primary" for annotation in annotations):
        raise ValueError("secondary judgements cannot enter primary adjudication")
    if any(annotation.is_missing for annotation in annotations):
        raise ValueError("cannot adjudicate with missing primary labels")
    counts = Counter(annotation.label for annotation in annotations)
    label, vote_count = counts.most_common(1)[0]
    if list(counts.values()).count(vote_count) > 1:
        raise ValueError("adjudication requires a non-tied vote")
    item_ids = {annotation.item_id for annotation in annotations if annotation.item_id}
    if len(item_ids) > 1:
        raise ValueError("adjudication annotations must refer to one item")
    return Adjudication(
        label=str(label), vote_count=vote_count, item_id=next(iter(item_ids), ""),
        adjudicator_id=adjudicator_id, rationale=rationale,
        labels_considered=tuple(sorted(str(value) for value in counts)),
    )


def find_disagreements(annotations: Iterable[HumanAnnotation]) -> list[Disagreement]:
    grouped: dict[str, list[HumanAnnotation]] = {}
    for annotation in annotations:
        if not annotation.item_id or annotation.is_missing:
            continue
        grouped.setdefault(annotation.item_id, []).append(annotation)
    result = []
    for item_id in sorted(grouped):
        rows = grouped[item_id]
        labels = tuple(sorted({str(row.label) for row in rows}))
        if len(labels) > 1:
            result.append(Disagreement(item_id, labels, tuple(sorted(row.annotator_id for row in rows))))
    return result


def export_adjudications(path: Path | str, adjudications: Iterable[Adjudication]) -> None:
    rows = [record.to_dict() for record in adjudications]
    rows.sort(key=lambda row: (str(row.get("item_id", "")), str(row.get("adjudicator_id", ""))))
    Path(path).write_text(json.dumps(rows, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def export_disagreements(path: Path | str, disagreements: Iterable[Disagreement]) -> None:
    rows = [record.to_dict() for record in disagreements]
    rows.sort(key=lambda row: str(row.get("item_id", "")))
    Path(path).write_text(json.dumps(rows, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def missing_annotations(annotations: Iterable[HumanAnnotation]) -> list[HumanAnnotation]:
    """Return missing labels as a separate exportable evidence stream."""

    return sorted((row for row in annotations if row.is_missing), key=lambda row: (row.item_id, row.annotator_id))


__all__ = [
    "Adjudication", "Disagreement", "adjudicate", "find_disagreements",
    "export_adjudications", "export_disagreements", "missing_annotations",
]
