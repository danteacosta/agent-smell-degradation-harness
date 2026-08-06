"""Primary human annotation records and deterministic export helpers.

The annotation layer deliberately stores only what a primary annotator could
see.  Experimental condition, oracle output, model identity and terminal
artifacts belong to the experiment manifest and are never copied into a
blinded annotation record.
"""

from __future__ import annotations

import csv
import json
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any, Iterable


@dataclass(frozen=True, slots=True)
class HumanAnnotation:
    annotator_id: str
    label: str | None
    item_id: str = ""
    rubric_version: str = ""
    duplicate_subset: bool = False
    missing_reason: str | None = None
    source: str = "human_primary"

    def __post_init__(self) -> None:
        if not self.annotator_id:
            raise ValueError("human annotations require annotator_id")
        if self.label is None or not str(self.label).strip():
            if not self.missing_reason or not str(self.missing_reason).strip():
                raise ValueError("missing labels require missing_reason")
        elif self.missing_reason:
            raise ValueError("missing_reason is only valid for missing labels")
        if not self.source:
            raise ValueError("human annotations require source")

    @property
    def is_missing(self) -> bool:
        return self.label is None or not str(self.label).strip()

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def export_annotations(path: Path | str, annotations: Iterable[HumanAnnotation]) -> None:
    """Export raw labels, including missing-label reasons, deterministically."""

    rows = [annotation.to_dict() for annotation in annotations]
    rows.sort(key=lambda row: (str(row.get("item_id", "")), str(row["annotator_id"])))
    destination = Path(path)
    if destination.suffix.lower() == ".csv":
        fields = [
            "item_id", "annotator_id", "label", "rubric_version",
            "duplicate_subset", "missing_reason", "source",
        ]
        with destination.open("w", encoding="utf-8", newline="") as handle:
            writer = csv.DictWriter(handle, fieldnames=fields)
            writer.writeheader()
            writer.writerows({key: row.get(key) for key in fields} for row in rows)
    else:
        destination.write_text(json.dumps(rows, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def load_primary_label_manifest(
    manifest: dict[str, Any], expected_episode_ids: Iterable[str]
) -> dict[str, int]:
    """Load the frozen human/adjudicated binary label view used by H2."""

    if manifest.get("schema_version") != "human-labels/v1":
        raise ValueError("primary label manifest schema_version must be human-labels/v1")
    if float(manifest.get("duplicate_subset_fraction", 0.0)) < 0.20:
        raise ValueError("primary label manifest requires a 20% duplicate subset")
    rows = manifest.get("labels")
    if not isinstance(rows, list):
        raise ValueError("primary label manifest labels are required")
    expected = {str(item) for item in expected_episode_ids}
    labels: dict[str, int] = {}
    for row in rows:
        if not isinstance(row, dict):
            raise ValueError("primary label rows must be objects")
        episode_id = str(row.get("episode_id", "")).strip()
        if not episode_id or episode_id in labels:
            raise ValueError("primary label rows require unique episode_id")
        if row.get("missing") or row.get("adjudicated") is not True:
            raise ValueError(f"primary label for {episode_id} is missing adjudication")
        label = row.get("label")
        if isinstance(label, bool):
            raise ValueError(f"primary label for {episode_id} must be binary")
        if isinstance(label, str):
            label = {"clean": 0, "ok": 0, "degraded": 1, "material_failure": 1}.get(label)
        if label not in (0, 1):
            raise ValueError(f"primary label for {episode_id} must be binary")
        labels[episode_id] = int(label)
    if expected - set(labels):
        raise ValueError("primary label manifest is missing episode labels")
    return labels


__all__ = ["HumanAnnotation", "export_annotations", "load_primary_label_manifest"]
