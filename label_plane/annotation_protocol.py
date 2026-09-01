"""Blinded sampling contract for primary human annotation.

This module is intentionally provider-agnostic.  A task payload can be sent to
any annotation UI while the hidden experiment metadata remains in the source
manifest, not in the annotator-visible JSON.
"""

from __future__ import annotations

from dataclasses import dataclass
from hashlib import sha256
import json
import random
from pathlib import Path
from typing import Any, Iterable, Mapping


_FORBIDDEN_FIELDS = frozenset({"variant", "defect_family", "oracle_label", "model_id", "artifact"})


@dataclass(frozen=True, slots=True)
class BlindedAnnotationTask:
    item_id: str
    presented_text: str
    rubric_version: str
    duplicate_subset: bool = False

    def __post_init__(self) -> None:
        if not self.item_id or not self.presented_text.strip():
            raise ValueError("blinded task requires item_id and presented text")
        if not self.rubric_version:
            raise ValueError("blinded task requires rubric_version")

    @classmethod
    def from_record(
        cls,
        record: Mapping[str, Any],
        *,
        duplicate_subset: bool = False,
        rubric_version: str = "rubric-v2",
    ) -> "BlindedAnnotationTask":
        item_id = str(record.get("episode_id") or record.get("item_id") or "")
        text = str(record.get("requirement_text") or record.get("prompt") or "")
        return cls(item_id=item_id, presented_text=text, rubric_version=rubric_version,
                   duplicate_subset=duplicate_subset)

    def to_annotation_payload(self) -> dict[str, Any]:
        payload = {
            "item_id": self.item_id,
            "presented_text": self.presented_text,
            "rubric_version": self.rubric_version,
            "duplicate_subset": self.duplicate_subset,
        }
        assert not _FORBIDDEN_FIELDS.intersection(payload)
        return payload


@dataclass(frozen=True, slots=True)
class BlindedOutputSmellTask:
    """Secondary task that exposes only the generated acceptance criteria."""

    item_id: str
    generated_acceptance_criteria: str
    rubric_version: str = "rubric-v2"
    duplicate_subset: bool = False

    def __post_init__(self) -> None:
        if not self.item_id or not self.generated_acceptance_criteria.strip():
            raise ValueError(
                "output-smell task requires item_id and generated acceptance criteria"
            )
        if not self.rubric_version:
            raise ValueError("output-smell task requires rubric_version")

    @classmethod
    def from_record(
        cls,
        record: Mapping[str, Any],
        *,
        duplicate_subset: bool = False,
        rubric_version: str = "rubric-v2",
    ) -> "BlindedOutputSmellTask":
        item_id = str(record.get("episode_id") or record.get("item_id") or "")
        generated = record.get(
            "generated_acceptance_criteria", record.get("artifact_text", "")
        )
        if isinstance(generated, Mapping):
            generated = json.dumps(generated, sort_keys=True)
        return cls(
            item_id=item_id,
            generated_acceptance_criteria=str(generated),
            rubric_version=rubric_version,
            duplicate_subset=duplicate_subset,
        )

    def to_annotation_payload(self) -> dict[str, Any]:
        payload = {
            "item_id": self.item_id,
            "generated_acceptance_criteria": self.generated_acceptance_criteria,
            "rubric_version": self.rubric_version,
            "duplicate_subset": self.duplicate_subset,
        }
        assert not _FORBIDDEN_FIELDS.intersection(payload)
        return payload


def validate_blinded_payload(payload: Mapping[str, Any]) -> None:
    """Reject payloads that would leak condition or terminal evidence."""

    leaked = _FORBIDDEN_FIELDS.intersection(payload)
    if leaked:
        raise ValueError(f"blinded payload leaks experimental fields: {sorted(leaked)}")
    for required in ("item_id", "presented_text", "rubric_version", "duplicate_subset"):
        if required not in payload:
            raise ValueError(f"blinded payload missing {required}")


def select_duplicate_subset(
    item_ids: Iterable[str], *, fraction: float = 0.20, seed: int = 0
) -> tuple[str, ...]:
    """Select a reproducible double-coded subset without looking at labels."""

    if not 0 < fraction <= 1:
        raise ValueError("duplicate subset fraction must be in (0, 1]")
    unique = sorted({str(item_id) for item_id in item_ids if str(item_id)})
    if not unique:
        return ()
    count = max(1, round(len(unique) * fraction))
    chooser = random.Random(seed)
    return tuple(sorted(chooser.sample(unique, min(count, len(unique)))))


def validate_duplicate_subset(annotations: Iterable[Any], duplicate_item_ids: Iterable[str]) -> None:
    """Require every prespecified duplicate item to have two primary coders."""

    expected = {str(item_id) for item_id in duplicate_item_ids}
    counts: dict[str, set[str]] = {}
    for annotation in annotations:
        if getattr(annotation, "source", "human_primary") != "human_primary":
            continue
        item_id = str(getattr(annotation, "item_id", ""))
        if item_id in expected:
            counts.setdefault(item_id, set()).add(str(annotation.annotator_id))
    missing = sorted(item_id for item_id in expected if len(counts.get(item_id, set())) < 2)
    if missing:
        raise ValueError(f"duplicate subset items must be double-coded: {missing}")



def freeze_blinded_tasks(
    records: Iterable[Mapping[str, Any]],
    *,
    fraction: float = 0.20,
    seed: int = 0,
    rubric_version: str = "rubric-v2",
) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    """Create annotator packets and freeze duplicates before any labels exist."""

    rows = [dict(record) for record in records]
    if not rows:
        raise ValueError("annotation packet preparation requires records")
    item_ids = [str(row.get("episode_id") or row.get("item_id") or "").strip() for row in rows]
    if any(not item_id for item_id in item_ids) or len(set(item_ids)) != len(item_ids):
        raise ValueError("annotation records require unique, non-empty item IDs")
    duplicate_ids = set(select_duplicate_subset(item_ids, fraction=fraction, seed=seed))
    tasks = [
        BlindedAnnotationTask.from_record(
            row,
            duplicate_subset=item_id in duplicate_ids,
            rubric_version=rubric_version,
        ).to_annotation_payload()
        for row, item_id in zip(rows, item_ids)
    ]
    for task in tasks:
        validate_blinded_payload(task)
    tasks.sort(key=lambda task: str(task["item_id"]))
    selection = {
        "schema_version": "annotation-selection/v1",
        "selection_method": "seeded_item_id_sampling_before_labels",
        "item_count": len(tasks),
        "duplicate_subset_fraction": fraction,
        "duplicate_subset_seed": seed,
        "duplicate_item_count": len(duplicate_ids),
        "duplicate_item_ids": sorted(duplicate_ids),
        "rubric_version": rubric_version,
    }
    selection["selection_sha256"] = sha256(
        json.dumps(selection, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")
    ).hexdigest()
    return tasks, selection


def load_annotation_rubric(path: Path | str | None = None) -> dict[str, Any]:
    """Load the frozen human-label policy used by collection tooling."""

    rubric_path = Path(path) if path else Path(__file__).resolve().parents[1] / "tasks" / "annotation_rubric.json"
    payload = json.loads(rubric_path.read_text(encoding="utf-8"))
    if payload.get("schema_version") != "human-annotation/v1":
        raise ValueError("unsupported annotation rubric")
    if not payload.get("labels") or not payload.get("missing_label_policy", {}).get("never_impute"):
        raise ValueError("annotation rubric must freeze labels and no-imputation policy")
    return payload


__all__ = [
    "BlindedAnnotationTask", "BlindedOutputSmellTask", "freeze_blinded_tasks",
    "load_annotation_rubric", "select_duplicate_subset", "validate_blinded_payload",
    "validate_duplicate_subset",
]
