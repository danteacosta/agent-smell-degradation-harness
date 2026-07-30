"""Validation metadata for the versioned benchmark, kept outside feature extraction."""

from __future__ import annotations

import json
import hashlib
from pathlib import Path
from typing import Any

V4_DATASET_ROOT = Path(__file__).resolve().parents[1] / "datasets" / "v4"
_REQUIRED_RECORD_KEYS = {
    "intent_id", "source", "license", "source_sha256", "preserved_intent",
    "manipulation", "single_defect", "natural_variant", "contamination_notes",
}


def load_v4_validation_metadata() -> dict[str, Any]:
    return json.loads((V4_DATASET_ROOT / "validation_metadata.json").read_text(encoding="utf-8"))


def validate_v4_metadata(metadata: dict[str, Any]) -> None:
    records = metadata.get("records")
    if not isinstance(records, list) or not records:
        raise ValueError("V4 validation metadata requires non-empty records")
    for record in records:
        missing = _REQUIRED_RECORD_KEYS - record.keys()
        if missing:
            raise ValueError(f"V4 record missing keys: {sorted(missing)}")
        if not record["preserved_intent"] or not record["single_defect"]:
            raise ValueError("V4 records must preserve intent and isolate one defect")
        source = V4_DATASET_ROOT.parents[1] / record["source"]
        if not source.exists():
            raise ValueError(f"V4 source does not exist: {record['source']}")
        source_hash = hashlib.sha256(source.read_bytes()).hexdigest()
        if source_hash != record["source_sha256"]:
            raise ValueError(f"V4 source hash mismatch: {record['intent_id']}")
