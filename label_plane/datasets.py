"""Validation metadata for the versioned benchmark, kept outside feature extraction."""

from __future__ import annotations

import json
import hashlib
import re
import unicodedata
from difflib import SequenceMatcher
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


def _canonical_intent_text(value: str) -> str:
    normalized = unicodedata.normalize("NFKC", str(value)).casefold()
    normalized = re.sub(r"[^\w\s]", " ", normalized, flags=re.UNICODE)
    return " ".join(normalized.split())


def _record_text(record: dict[str, Any]) -> str:
    for key in ("source_intent_text", "requirement_text", "clean_requirement", "text"):
        value = record.get(key)
        if isinstance(value, str) and value.strip():
            return value
    return ""


def _exception_key(left: str, right: str) -> str:
    return "::".join(sorted((left, right)))


def validate_design_metadata(
    metadata: dict[str, Any],
    *,
    expected_intents: int = 12,
    expected_variants: tuple[str, ...] = ("clean", "smelly"),
    expected_replications: int = 5,
    min_projects: int = 3,
    near_clone_threshold: float = 0.92,
) -> dict[str, int]:
    """Validate the confirmatory ``intent × variant × replication`` design.

    Unlike the legacy V4 provenance check, this helper is intentionally strict:
    it fails closed on incomplete rows, repeated design keys, duplicate or
    near-cloned source intents, and a missing project holdout.  It never pads a
    short dataset by renaming or copying records.
    """

    records = metadata.get("records")
    if not isinstance(records, list) or not records:
        raise ValueError("design metadata requires non-empty records")
    approved_raw = metadata.get("approved_paraphrases", ())
    approved: set[str] = set()
    if isinstance(approved_raw, (list, tuple, set)):
        for item in approved_raw:
            if isinstance(item, dict) and {"left", "right"} <= item.keys():
                approved.add(_exception_key(str(item["left"]), str(item["right"])))
            else:
                approved.add(str(item))
    required = {
        "source_intent_id",
        "project_id",
        "variant",
        "replication_id",
        "defect_family",
        "source",
    }
    design_keys: set[tuple[str, str, int, str, str]] = set()
    intent_text_candidates: dict[str, dict[str, str]] = {}
    projects: set[str] = set()
    intents: set[str] = set()
    variants_by_intent: dict[str, set[str]] = {}
    reps_by_variant: dict[tuple[str, str], set[int]] = {}

    for index, record in enumerate(records):
        if not isinstance(record, dict):
            raise ValueError(f"design record {index} must be an object")
        missing = required - record.keys()
        if missing:
            raise ValueError(f"design record {index} missing keys: {sorted(missing)}")
        intent = str(record["source_intent_id"])
        project = str(record["project_id"])
        variant = str(record["variant"])
        defect_family = str(record["defect_family"])
        try:
            replication = int(record["replication_id"])
        except (TypeError, ValueError) as exc:
            raise ValueError(f"design record {index} has invalid replication_id") from exc
        if variant not in expected_variants:
            raise ValueError(f"unexpected variant {variant!r}")
        if replication < 0 or replication >= expected_replications:
            raise ValueError(f"replication_id outside 0..{expected_replications - 1}: {replication}")
        if not str(record["source"]).strip() or not defect_family.strip():
            raise ValueError(f"design record {index} has incomplete provenance")
        key = (intent, variant, replication, project, defect_family)
        if key in design_keys:
            raise ValueError(f"duplicate design key: {key!r}")
        design_keys.add(key)
        intents.add(intent)
        projects.add(project)
        variants_by_intent.setdefault(intent, set()).add(variant)
        reps_by_variant.setdefault((intent, variant), set()).add(replication)
        text = _canonical_intent_text(_record_text(record))
        if text:
            intent_text_candidates.setdefault(intent, {})[variant] = text

    if len(intents) != expected_intents:
        raise ValueError(f"design requires {expected_intents} distinct source intents; got {len(intents)}")
    expected_variant_set = set(expected_variants)
    for intent in sorted(intents):
        if variants_by_intent.get(intent) != expected_variant_set:
            raise ValueError(f"source intent {intent!r} does not have exactly {expected_variants}")
        for variant in expected_variants:
            reps = reps_by_variant.get((intent, variant), set())
            if reps != set(range(expected_replications)):
                raise ValueError(f"source intent {intent!r}/{variant!r} does not have {expected_replications} replications")

    # A clean/smelly pair legitimately has different requirement text.  For
    # source-intent contamination checks, compare the clean source text when
    # available (or an explicit source_intent_text supplied in every row).
    intent_texts = {
        intent: texts.get("clean") or next(iter(texts.values()))
        for intent, texts in intent_text_candidates.items()
    }
    text_items = sorted(intent_texts.items())
    for left_index, (left_id, left_text) in enumerate(text_items):
        for right_id, right_text in text_items[left_index + 1 :]:
            pair_key = _exception_key(left_id, right_id)
            if pair_key in approved or left_id in approved or right_id in approved:
                continue
            if left_text == right_text:
                raise ValueError(f"duplicate source intent text for {left_id!r} and {right_id!r}")
            similarity = SequenceMatcher(None, left_text, right_text).ratio()
            if similarity >= near_clone_threshold:
                raise ValueError(
                    f"near-clone source intents {left_id!r} and {right_id!r} "
                    f"(similarity={similarity:.3f})"
                )

    if len(projects) < min_projects:
        raise ValueError(f"design requires at least {min_projects} projects for holdout; got {len(projects)}")

    expected_episode_count = expected_intents * len(expected_variants) * expected_replications
    if len(records) != expected_episode_count:
        raise ValueError(f"design requires exactly {expected_episode_count} episodes; got {len(records)}")
    return {
        "intent_count": len(intents),
        "project_count": len(projects),
        "episode_count": len(records),
        "replication_count": expected_replications,
        "variant_count": len(expected_variants),
    }


# Names used by experiment runners and external protocol checks.
validate_12x2x5_metadata = validate_design_metadata
validate_prepilot_metadata = validate_design_metadata
