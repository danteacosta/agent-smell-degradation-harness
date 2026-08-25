"""Validation metadata for the versioned benchmark, kept outside feature extraction."""

from __future__ import annotations

import json
import hashlib
import re
import unicodedata
from difflib import SequenceMatcher
from pathlib import Path
from typing import Any
from urllib.parse import urlparse

from protocol.conditional_semantics import (
    CONDITIONAL_SEMANTICS_SCHEMA_VERSION,
    validate_conditional_semantics,
)

V4_DATASET_ROOT = Path(__file__).resolve().parents[1] / "datasets" / "v4"
REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
CONFIRMATORY_DATASET_ROOT = REPOSITORY_ROOT / "data" / "confirmatory"
CONFIRMATORY_MANIFEST_PATH = CONFIRMATORY_DATASET_ROOT / "manifest.json"
CONFIRMATORY_SCHEMA_VERSION = "confirmatory-v2"
PROJECT_DOMAIN_VALUES = frozenset({
    "ecommerce-order-management",
    "finance",
    "healthcare",
    "public-sector",
    "developer-tools",
})
LIFECYCLE_ROLE_VALUES = frozenset({
    "functional-requirement",
    "non-functional-requirement",
    "acceptance-criterion",
    "operational-policy",
})
LIFECYCLE_PHASE_VALUES = frozenset({
    "elicitation",
    "specification",
    "validation",
    "maintenance",
})
_REQUIRED_RECORD_KEYS = {
    "intent_id", "source", "license", "source_sha256", "preserved_intent",
    "manipulation", "single_defect", "natural_variant", "contamination_notes",
}
_REQUIRED_CONFIRMATORY_SOURCE_KEYS = {
    "source_intent_id",
    "source",
    "source_sha256",
    "provenance_url",
    "project_id",
    "defect_family",
    "clean_requirement",
    "smelly_requirement",
    "natural_variant",
    "contamination_notes",
    "project_domain",
    "lifecycle_role",
    "lifecycle_phase",
    "conditional_semantics",
    "conditional_semantics_schema",
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


def load_confirmatory_manifest(
    path: Path | str = CONFIRMATORY_MANIFEST_PATH,
) -> dict[str, Any]:
    """Load the checked-in source manifest for the confirmatory experiment.

    The source manifest is deliberately separate from the generated episode
    rows.  It contains one row per source intent; :func:`validate_confirmatory_manifest`
    expands each row into the two experimental variants and five repeated
    measurements.  Loading never makes an incomplete seed appear complete.
    """

    manifest_path = Path(path)
    try:
        value = json.loads(manifest_path.read_text(encoding="utf-8"))
    except OSError as exc:
        raise ValueError(f"confirmatory manifest is not readable: {manifest_path}") from exc
    except json.JSONDecodeError as exc:
        raise ValueError(f"confirmatory manifest is not valid JSON: {manifest_path}") from exc
    if not isinstance(value, dict):
        raise ValueError("confirmatory manifest must be a JSON object")
    return value


def _resolve_source(source: str, *, manifest_path: Path) -> Path:
    candidate = Path(source)
    if candidate.is_absolute():
        return candidate
    # Relative paths are repository-relative, not relative to the manifest's
    # directory.  This keeps manifests portable when copied to a run bundle.
    return REPOSITORY_ROOT / candidate


def _validate_source_record(
    record: dict[str, Any],
    *,
    index: int,
    manifest_path: Path,
) -> None:
    missing = _REQUIRED_CONFIRMATORY_SOURCE_KEYS - record.keys()
    if missing:
        raise ValueError(f"confirmatory source record {index} missing keys: {sorted(missing)}")
    source_intent = str(record["source_intent_id"]).strip()
    project = str(record["project_id"]).strip()
    defect_family = str(record["defect_family"]).strip()
    if not source_intent:
        raise ValueError(f"confirmatory source record {index} has empty source_intent_id")
    if not project:
        raise ValueError(f"confirmatory source record {index} requires non-empty project_id")
    if not defect_family:
        raise ValueError(f"confirmatory source record {index} requires non-empty defect_family")
    for field in ("project_domain", "lifecycle_role", "lifecycle_phase"):
        if not isinstance(record[field], str) or not record[field].strip():
            raise ValueError(f"confirmatory source record {index} requires non-empty {field}")
    controlled_values = {
        "project_domain": PROJECT_DOMAIN_VALUES,
        "lifecycle_role": LIFECYCLE_ROLE_VALUES,
        "lifecycle_phase": LIFECYCLE_PHASE_VALUES,
    }
    for field, allowed in controlled_values.items():
        if record[field] not in allowed:
            raise ValueError(f"confirmatory source record {index} has unsupported {field}: {record[field]!r}")
    if record["conditional_semantics_schema"] != CONDITIONAL_SEMANTICS_SCHEMA_VERSION:
        raise ValueError(
            f"confirmatory source record {index} conditional_semantics_schema must be "
            f"{CONDITIONAL_SEMANTICS_SCHEMA_VERSION}"
        )
    try:
        record["conditional_semantics"] = validate_conditional_semantics(record["conditional_semantics"])
    except ValueError as error:
        raise ValueError(f"confirmatory source record {index} has invalid conditional_semantics: {error}") from error
    for field in ("clean_requirement", "smelly_requirement", "contamination_notes"):
        if not str(record[field]).strip():
            raise ValueError(f"confirmatory source record {index} requires non-empty {field}")
    if not isinstance(record["natural_variant"], bool):
        raise ValueError(f"confirmatory source record {index} natural_variant must be boolean")
    provenance_url = str(record["provenance_url"]).strip()
    parsed = urlparse(provenance_url)
    if parsed.scheme not in {"http", "https"} or not parsed.netloc:
        raise ValueError(
            f"confirmatory source record {index} requires an http(s) provenance_url"
        )
    source = str(record["source"]).strip()
    if not source:
        raise ValueError(f"confirmatory source record {index} requires non-empty source")
    source_path = _resolve_source(source, manifest_path=manifest_path)
    if not source_path.exists() or not source_path.is_file():
        raise ValueError(f"confirmatory source does not exist: {source}")
    expected_hash = str(record["source_sha256"]).strip().lower()
    actual_hash = hashlib.sha256(source_path.read_bytes()).hexdigest()
    if expected_hash != actual_hash:
        raise ValueError(f"confirmatory source hash mismatch: {source_intent}")
    # Repository-local pair sources are JSON contracts.  Hash equality alone
    # is not enough: the manifest's canonical requirements must still refer
    # to the source intent being collected.  External URL-backed sources may
    # use another format and are covered by their immutable hash/provenance.
    if source_path.suffix.lower() == ".json":
        try:
            source_payload = json.loads(source_path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as exc:
            raise ValueError(f"confirmatory source is not readable JSON: {source}") from exc
        if isinstance(source_payload, dict):
            if str(source_payload.get("intent_id", source_intent)).strip() != source_intent:
                raise ValueError(f"confirmatory source intent mismatch: {source_intent}")
            for field in ("clean_requirement", "smelly_requirement"):
                source_text = source_payload.get(field)
                if isinstance(source_text, str) and source_text != str(record[field]):
                    raise ValueError(f"confirmatory requirement mismatch: {source_intent}/{field}")


def _expanded_confirmatory_records(
    manifest: dict[str, Any],
    *,
    manifest_path: Path,
    expected_intents: int,
    expected_variants: tuple[str, ...],
    expected_replications: int,
) -> list[dict[str, Any]]:
    source_records = manifest.get("records")
    if not isinstance(source_records, list) or not source_records:
        raise ValueError("confirmatory manifest requires non-empty source records")
    source_ids = [str(item.get("source_intent_id", "")).strip() if isinstance(item, dict) else "" for item in source_records]
    if len(set(source_ids)) != len(source_ids):
        raise ValueError("confirmatory manifest contains duplicate source_intent_id values")
    if len(source_ids) != expected_intents or not all(source_ids):
        raise ValueError(
            f"confirmatory design requires {expected_intents} distinct source intents; got {len(source_ids)}"
        )

    expanded: list[dict[str, Any]] = []
    for index, raw in enumerate(source_records):
        if not isinstance(raw, dict):
            raise ValueError(f"confirmatory source record {index} must be an object")
        _validate_source_record(raw, index=index, manifest_path=manifest_path)
        for variant, requirement_key in (("clean", "clean_requirement"), ("smelly", "smelly_requirement")):
            if variant not in expected_variants:
                raise ValueError(f"confirmatory expected_variants must include {variant!r}")
            for replication_id in range(expected_replications):
                expanded.append(
                    {
                        "source_intent_id": str(raw["source_intent_id"]),
                        "project_id": str(raw["project_id"]),
                        "variant": variant,
                        "replication_id": replication_id,
                        "defect_family": str(raw["defect_family"]),
                        "source": str(raw["source"]),
                        "source_sha256": str(raw["source_sha256"]),
                        "provenance_url": str(raw["provenance_url"]),
                        "natural_variant": bool(raw["natural_variant"]),
                        "contamination_notes": str(raw["contamination_notes"]),
                        "project_domain": str(raw["project_domain"]),
                        "lifecycle_role": str(raw["lifecycle_role"]),
                        "lifecycle_phase": str(raw["lifecycle_phase"]),
                        "conditional_semantics": list(raw["conditional_semantics"]),
                        "conditional_semantics_schema": str(raw["conditional_semantics_schema"]),
                        "requirement_text": str(raw[requirement_key]),
                        # The clean text is the stable source-intent identity
                        # used for near-clone checks across variants.
                        "source_intent_text": str(raw["clean_requirement"]),
                    }
                )
    return expanded


def validate_confirmatory_manifest(
    manifest: dict[str, Any],
    *,
    manifest_path: Path | str = CONFIRMATORY_MANIFEST_PATH,
) -> dict[str, Any]:
    """Validate and materialize the confirmatory 12×2×5 design.

    This is the single fail-closed boundary for the confirmatory dataset.  It
    requires independent, provenance-backed source intents; it does not infer
    missing projects, create synthetic intents, or pad a short seed.  The
    returned object is deterministic and suitable for writing into a run
    manifest or dissertation bundle.
    """

    if not isinstance(manifest, dict):
        raise ValueError("confirmatory manifest must be a JSON object")
    if manifest.get("schema_version") != CONFIRMATORY_SCHEMA_VERSION:
        raise ValueError(f"confirmatory manifest schema_version must be {CONFIRMATORY_SCHEMA_VERSION}")
    expected = manifest.get("expected", {})
    if not isinstance(expected, dict):
        raise ValueError("confirmatory manifest expected must be an object")
    expected_intents = int(expected.get("intents", 12))
    expected_replications = int(expected.get("replications", 5))
    raw_variants = expected.get("variants", ["clean", "smelly"])
    if not isinstance(raw_variants, list) or any(not isinstance(item, str) for item in raw_variants):
        raise ValueError("confirmatory manifest expected.variants must be a list of strings")
    expected_variants = tuple(raw_variants)
    if expected_intents != 12 or expected_replications != 5 or expected_variants != ("clean", "smelly"):
        raise ValueError("confirmatory design is frozen at 12 intents × 2 variants × 5 replications")
    threshold = float(manifest.get("near_clone_threshold", 0.92))
    if not 0.0 < threshold <= 1.0:
        raise ValueError("near_clone_threshold must be in (0, 1]")
    approved = manifest.get("approved_paraphrases", [])
    if not isinstance(approved, list):
        raise ValueError("approved_paraphrases must be a list")
    resolved_manifest_path = Path(manifest_path)
    expanded = _expanded_confirmatory_records(
        manifest,
        manifest_path=resolved_manifest_path,
        expected_intents=expected_intents,
        expected_variants=expected_variants,
        expected_replications=expected_replications,
    )
    counts = validate_design_metadata(
        {
            "records": expanded,
            "approved_paraphrases": approved,
        },
        expected_intents=expected_intents,
        expected_variants=expected_variants,
        expected_replications=expected_replications,
        min_projects=3,
        near_clone_threshold=threshold,
    )
    source_records = sorted(
        (dict(record) for record in manifest["records"]),
        key=lambda record: str(record["source_intent_id"]),
    )
    ordered_records = sorted(
        expanded,
        key=lambda record: (
            str(record["source_intent_id"]),
            expected_variants.index(str(record["variant"])),
            int(record["replication_id"]),
        ),
    )
    project_holdouts: dict[str, list[str]] = {}
    for record in source_records:
        project_holdouts.setdefault(str(record["project_id"]), []).append(str(record["source_intent_id"]))
    project_holdouts = {project: sorted(intent_ids) for project, intent_ids in sorted(project_holdouts.items())}
    canonical = {
        "schema_version": CONFIRMATORY_SCHEMA_VERSION,
        "expected": {
            "intents": expected_intents,
            "variants": list(expected_variants),
            "replications": expected_replications,
        },
        "near_clone_threshold": threshold,
        "approved_paraphrases": approved,
        "source_records": source_records,
        "records": ordered_records,
        "project_holdouts": project_holdouts,
        "counts": counts,
    }
    serialized = json.dumps(canonical, sort_keys=True, separators=(",", ":"), ensure_ascii=False)
    return {**canonical, "manifest_sha256": hashlib.sha256(serialized.encode("utf-8")).hexdigest()}


def build_confirmatory_manifest(
    manifest: dict[str, Any] | None = None,
    *,
    path: Path | str = CONFIRMATORY_MANIFEST_PATH,
) -> dict[str, Any]:
    """Load (or accept) and validate the deterministic confirmatory manifest."""

    manifest_path = Path(path)
    return validate_confirmatory_manifest(
        load_confirmatory_manifest(manifest_path) if manifest is None else manifest,
        manifest_path=manifest_path,
    )


# Names used by experiment runners and external protocol checks.
validate_12x2x5_metadata = validate_design_metadata
validate_prepilot_metadata = validate_design_metadata
