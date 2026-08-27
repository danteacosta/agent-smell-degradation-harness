"""Build a provenance-first candidate pool from the Unified Dataset.

The source dataset supplies requirement text and classification labels, but it
does not supply independent requirements-smell labels.  This module therefore
uses only text cues to create candidates for later blinded annotation.  The
source ``Class`` column is deliberately ignored so it cannot become a smell
oracle by accident.
"""

from __future__ import annotations

import csv
import hashlib
import json
import math
from collections import Counter
from pathlib import Path
from typing import Any, Iterable, Mapping

from baselines.contextual_smell import SUPPORTED_FAMILIES, analyze_family, extract_context_features

UNIFIED_DATASET_ID = "g4nh7vcfyb"
UNIFIED_DATASET_VERSION = 1
UNIFIED_DATASET_DOI = "10.17632/g4nh7vcfyb.1"
UNIFIED_DATASET_URL = "https://data.mendeley.com/datasets/g4nh7vcfyb/1"
UNIFIED_DOWNLOAD_URL = "https://data.mendeley.com/public-api/zip/g4nh7vcfyb/download/1"
UNIFIED_LICENSE = "CC BY 4.0"
POOL_SCHEMA_VERSION = "requirements-smell-candidate-pool/v1"
SELECTION_SCHEMA_VERSION = "requirements-smell-natural-selection/v2"
SOURCE_MANIFEST_SCHEMA_VERSION = "requirements-smell-source-manifest/v1"
PANEL_CANDIDATE_KINDS = ("cue_positive_candidate", "hard_clean_candidate")

REQUIRED_COLUMNS = (
    "Requirement ID",
    "Project ID",
    "Project Name",
    "Datasets",
    "Requirement Text (Original Requirement)",
)


def _text_hash(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def load_unified_rows(path: Path | str) -> list[dict[str, Any]]:
    """Load the preprocessing CSV while dropping the source class label."""

    source = Path(path)
    with source.open(encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle)
        fieldnames = tuple(reader.fieldnames or ())
        missing = set(REQUIRED_COLUMNS) - set(fieldnames)
        if missing:
            raise ValueError(f"Unified Dataset is missing required columns: {sorted(missing)}")
        rows: list[dict[str, Any]] = []
        seen_ids: set[str] = set()
        seen_texts: set[str] = set()
        for source_row, raw in enumerate(reader, start=2):
            requirement_id = str(raw.get("Requirement ID", "")).strip()
            project_id = str(raw.get("Project ID", "")).strip()
            text = str(raw.get("Requirement Text (Original Requirement)", "")).strip()
            if not requirement_id or not project_id or not text:
                continue
            if requirement_id in seen_ids:
                raise ValueError(f"duplicate Requirement ID in Unified Dataset: {requirement_id}")
            text_hash = _text_hash(text)
            if text_hash in seen_texts:
                # Exact duplicates are not independent candidate units. Keep
                # the first row so they cannot cross project/split boundaries.
                continue
            seen_ids.add(requirement_id)
            seen_texts.add(text_hash)
            rows.append(
                {
                    "source_record_id": requirement_id,
                    "source_row": source_row,
                    "project_id": project_id,
                    "project_name": str(raw.get("Project Name", "")).strip(),
                    "source_partition": str(raw.get("Datasets", "")).strip(),
                    "requirement_text": text,
                    "requirement_text_sha256": text_hash,
                }
            )
    if not rows:
        raise ValueError("Unified Dataset contains no usable requirement rows")
    return rows


def _stable_project_order(projects: Iterable[str], seed: int) -> list[str]:
    return sorted(
        {str(project).strip() for project in projects if str(project).strip()},
        key=lambda project: hashlib.sha256(f"unified-v1:{seed}:{project}".encode("utf-8")).hexdigest(),
    )


def assign_project_splits(
    projects: Iterable[str],
    *,
    seed: int = 0,
    train_fraction: float = 0.5,
    calibration_fraction: float = 0.2,
    test_fraction: float = 0.3,
) -> dict[str, str]:
    """Assign whole projects to disjoint splits deterministically."""

    fractions = (train_fraction, calibration_fraction, test_fraction)
    if any(fraction <= 0 for fraction in fractions) or abs(sum(fractions) - 1.0) > 1e-9:
        raise ValueError("project split fractions must be positive and sum to 1")
    ordered = _stable_project_order(projects, seed)
    if len(ordered) < 3:
        raise ValueError("project split requires at least three distinct projects")
    raw = [len(ordered) * fraction for fraction in fractions]
    counts = [max(1, int(math.floor(value))) for value in raw]
    while sum(counts) < len(ordered):
        index = max(range(3), key=lambda item: (raw[item] - math.floor(raw[item]), -item))
        counts[index] += 1
    while sum(counts) > len(ordered):
        index = max(range(3), key=lambda item: (counts[item], -item))
        if counts[index] == 1:
            raise ValueError("could not allocate project split quotas")
        counts[index] -= 1
    labels = ("train", "calibration", "test")
    assignments: dict[str, str] = {}
    cursor = 0
    for label, count in zip(labels, counts):
        for project in ordered[cursor : cursor + count]:
            assignments[project] = label
        cursor += count
    return assignments


def _hard_clean_support(features: Mapping[str, Any], family: str) -> int:
    support = 0
    if features.get("has_measurement"):
        support += 1
    if features.get("has_comparator"):
        support += 1
    if features.get("has_explicit_response") and features.get("has_actor"):
        support += 1
    if features.get("has_condition") and features.get("has_actor"):
        support += 1
    if family == "vague_pronoun" and features.get("local_antecedent") is True:
        support += 2
    if family == "uncertain_verb" and features.get("has_normative_modal"):
        support += 1
    return support


def _candidate_row(
    row: Mapping[str, Any],
    *,
    family: str,
    kind: str,
    score: float,
    features: Mapping[str, Any],
) -> dict[str, Any]:
    # The target family is a legitimate annotation input, but the sampling
    # kind must remain hidden.  An opaque ID prevents ``cue_positive`` or
    # ``hard_clean`` from leaking through the item identifier.
    opaque_key = f"{UNIFIED_DATASET_ID}:{family}:{row['source_record_id']}"
    candidate_id = f"unified-v1-item-{_text_hash(opaque_key)[:20]}"
    return {
        "candidate_id": candidate_id,
        "source_dataset": UNIFIED_DATASET_ID,
        "source_dataset_version": UNIFIED_DATASET_VERSION,
        "source_record_id": row["source_record_id"],
        "source_row": row["source_row"],
        "project_id": row["project_id"],
        "project_name": row["project_name"],
        "source_partition": row["source_partition"],
        "target_family": family,
        "candidate_kind": kind,
        "requirement_text": row["requirement_text"],
        "requirement_text_sha256": row["requirement_text_sha256"],
        "cue_terms": list(features.get("cue_hits", ())),
        "structural_support": _hard_clean_support(features, family),
        "selection_score": round(float(score), 6),
        "selection_basis": "text_cues_and_structure_only",
        "source_class_used_for_selection": False,
    }


def _select_diverse(
    candidates: list[dict[str, Any]],
    *,
    count: int,
    used_record_ids: set[str],
    seed: int,
) -> list[dict[str, Any]]:
    available = [candidate for candidate in candidates if candidate["source_record_id"] not in used_record_ids]
    available.sort(
        key=lambda candidate: (
            -float(candidate["selection_score"]),
            hashlib.sha256(f"{seed}:{candidate['candidate_id']}".encode("utf-8")).hexdigest(),
        )
    )
    selected: list[dict[str, Any]] = []
    projects: set[str] = set()
    while available and len(selected) < count:
        index = next(
            (position for position, candidate in enumerate(available) if candidate["project_id"] not in projects),
            0,
        )
        candidate = available.pop(index)
        selected.append(candidate)
        projects.add(str(candidate["project_id"]))
        used_record_ids.add(str(candidate["source_record_id"]))
    if len(selected) < count:
        raise ValueError(
            f"candidate pool has only {len(selected)} unused rows; requires {count}"
        )
    return selected


def select_candidate_pool(
    rows: list[dict[str, Any]],
    *,
    per_kind: int = 20,
    seed: int = 0,
    families: Iterable[str] = SUPPORTED_FAMILIES,
    split_quotas: Mapping[str, int] | None = None,
) -> tuple[list[dict[str, Any]], dict[str, str]]:
    """Select a balanced, project-disjoint candidate pool.

    ``per_kind`` is the default test quota.  Callers can provide explicit
    train/calibration/test quotas when the test set must retain enough
    candidates to reach its confirmed-case target.
    """

    if per_kind < 1:
        raise ValueError("per_kind must be positive")
    requested = tuple(families)
    unknown = set(requested) - set(SUPPORTED_FAMILIES)
    if unknown:
        raise ValueError(f"unsupported smell families: {sorted(unknown)}")
    quotas = {"test": per_kind} if split_quotas is None else {
        str(split): int(quota) for split, quota in split_quotas.items()
    }
    unknown_splits = set(quotas) - {"train", "calibration", "test"}
    if unknown_splits:
        raise ValueError(f"unsupported project splits: {sorted(unknown_splits)}")
    if any(quota < 0 for quota in quotas.values()) or not any(quotas.values()):
        raise ValueError("split quotas must contain at least one non-negative quota")
    project_splits = assign_project_splits((row["project_id"] for row in rows), seed=seed)
    used_record_ids: set[str] = set()
    selected: list[dict[str, Any]] = []
    # Rare families are selected first to avoid common cues consuming all
    # rows that could serve as candidates for a less frequent family.
    family_order = sorted(
        requested,
        key=lambda family: sum(
            bool(extract_context_features(str(row["requirement_text"]), family).get("cue_hits"))
            for row in rows
        ),
    )
    for family in family_order:
        positive: list[dict[str, Any]] = []
        hard_clean: list[dict[str, Any]] = []
        for row in rows:
            features = extract_context_features(str(row["requirement_text"]), family)
            if not features.get("cue_hits"):
                continue
            analysis = analyze_family(str(row["requirement_text"]), family)
            positive_score = float(analysis["score"]) + 0.05 * len(features["cue_hits"])
            positive.append(
                _candidate_row(
                    row,
                    family=family,
                    kind="cue_positive_candidate",
                    score=positive_score,
                    features=features,
                )
            )
            support = _hard_clean_support(features, family)
            if support > 0:
                clean_score = float(support) + (1.0 - float(analysis["score"]))
                hard_clean.append(
                    _candidate_row(
                        row,
                        family=family,
                        kind="hard_clean_candidate",
                        score=clean_score,
                        features=features,
                    )
                )
        for kind_offset, candidates in enumerate((positive, hard_clean)):
            for split_offset, (split, quota) in enumerate(sorted(quotas.items())):
                if quota == 0:
                    continue
                split_candidates = [
                    candidate
                    for candidate in candidates
                    if project_splits[str(candidate["project_id"])] == split
                ]
                selected.extend(
                    _select_diverse(
                        split_candidates,
                        count=quota,
                        used_record_ids=used_record_ids,
                        seed=seed + (kind_offset * 100) + split_offset,
                    )
                )
    selected.sort(key=lambda row: str(row["candidate_id"]))
    return selected, project_splits


def _ensure_private_text_output(path: Path) -> None:
    repository_root = Path(__file__).resolve().parents[1]
    try:
        path.resolve().relative_to(repository_root)
    except ValueError:
        return
    raise ValueError("candidate text output must be outside the repository")


def write_candidate_pool(
    path: Path | str,
    candidates: Iterable[Mapping[str, Any]],
    project_splits: Mapping[str, str],
) -> None:
    """Write text-bearing candidates outside the repository."""

    destination = Path(path)
    _ensure_private_text_output(destination)
    destination.parent.mkdir(parents=True, exist_ok=True)
    rows = []
    for candidate in candidates:
        row = dict(candidate)
        row["project_split"] = project_splits[str(row["project_id"])]
        rows.append(row)
    rows.sort(key=lambda row: str(row["candidate_id"]))
    destination.write_text(
        "".join(json.dumps(row, ensure_ascii=False, sort_keys=True) + "\n" for row in rows),
        encoding="utf-8",
    )


def write_selection_manifest(
    path: Path | str,
    candidates: Iterable[Mapping[str, Any]],
    project_splits: Mapping[str, str],
    *,
    source_archive_sha256: str,
    source_member: str,
    source_member_sha256: str,
    seed: int = 0,
    per_kind: int | None = None,
    split_quotas: Mapping[str, int] | None = None,
) -> None:
    """Write metadata-only selection output suitable for version control."""

    destination = Path(path)
    rows = []
    for candidate in candidates:
        row = {
            key: value
            for key, value in dict(candidate).items()
            if key not in {"requirement_text"}
        }
        row["project_split"] = project_splits[str(row["project_id"])]
        rows.append(row)
    rows.sort(key=lambda row: str(row["candidate_id"]))
    counts = Counter(
        (str(row["target_family"]), str(row["candidate_kind"])) for row in rows
    )
    manifest = {
        "schema_version": SELECTION_SCHEMA_VERSION,
        "status": "candidate_pool_pending_panel_annotation",
        "source": {
            "dataset_id": UNIFIED_DATASET_ID,
            "version": UNIFIED_DATASET_VERSION,
            "doi": UNIFIED_DATASET_DOI,
            "url": UNIFIED_DATASET_URL,
            "download_url": UNIFIED_DOWNLOAD_URL,
            "license": {
                "short_name": UNIFIED_LICENSE,
                "url": "https://creativecommons.org/licenses/by/4.0/",
                "source_rights_note": "CC BY applies to the deposited dataset; third-party content remains subject to its own rights.",
            },
            "archive_sha256": source_archive_sha256,
            "member": source_member,
            "member_sha256": source_member_sha256,
        },
        "selection": {
            "seed": seed,
            "families": list(SUPPORTED_FAMILIES),
            "candidate_kinds": list(PANEL_CANDIDATE_KINDS),
            "per_kind_target": per_kind,
            "split_quotas": dict(sorted((split_quotas or {"test": per_kind or 0}).items())),
            "selection_basis": "text_cues_and_structure_only",
            "source_class_used": False,
            "duplicate_policy": "exact_requirement_text_deduplicated_before_selection",
            "split_policy": "project_disjoint_train_calibration_test",
        },
        "project_splits": dict(sorted(project_splits.items())),
        "counts": {
            f"{family}:{kind}": counts.get((family, kind), 0)
            for family in SUPPORTED_FAMILIES
            for kind in PANEL_CANDIDATE_KINDS
        },
        "records": rows,
    }
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_text(json.dumps(manifest, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def write_source_manifest(
    path: Path | str,
    rows: Iterable[Mapping[str, Any]],
    *,
    source_archive_sha256: str,
    source_archive_size_bytes: int,
    source_member: str,
    source_member_sha256: str,
    source_member_size_bytes: int,
) -> None:
    """Write provenance and rights metadata without redistributing source text."""

    destination = Path(path)
    materialized = list(rows)
    partitions = Counter(str(row["source_partition"]) for row in materialized)
    manifest = {
        "schema_version": SOURCE_MANIFEST_SCHEMA_VERSION,
        "status": "source_acquired_candidate_generation_only",
        "dataset": {
            "dataset_id": UNIFIED_DATASET_ID,
            "version": UNIFIED_DATASET_VERSION,
            "doi": UNIFIED_DATASET_DOI,
            "landing_page": UNIFIED_DATASET_URL,
            "download_url": UNIFIED_DOWNLOAD_URL,
        },
        "license": {
            "short_name": UNIFIED_LICENSE,
            "url": "https://creativecommons.org/licenses/by/4.0/",
            "evidence_url": UNIFIED_DATASET_URL,
            "rights_note": "The deposited dataset declares CC BY 4.0; third-party content remains subject to its own rights.",
        },
        "archive": {
            "sha256": source_archive_sha256,
            "size_bytes": source_archive_size_bytes,
        },
        "source_member": {
            "path_in_archive": source_member,
            "sha256": source_member_sha256,
            "size_bytes": source_member_size_bytes,
        },
        "observed_counts": {
            "usable_rows_after_exact_text_deduplication": len(materialized),
            "unique_project_ids": len({str(row["project_id"]) for row in materialized}),
            "unique_project_names": len({str(row["project_name"]) for row in materialized}),
            "source_partitions": len(partitions),
        },
        "source_partition_counts": dict(sorted(partitions.items())),
        "processing": {
            "source_class_column_used": False,
            "exact_text_duplicates_removed": True,
            "project_disjoint_split": True,
            "candidate_text_storage": "private_external_path",
            "conditional_sources_not_used": ["ARTA", "PURE", "Paska"],
        },
    }
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )


__all__ = [
    "PANEL_CANDIDATE_KINDS",
    "POOL_SCHEMA_VERSION",
    "SELECTION_SCHEMA_VERSION",
    "SOURCE_MANIFEST_SCHEMA_VERSION",
    "SUPPORTED_FAMILIES",
    "UNIFIED_DATASET_DOI",
    "UNIFIED_DATASET_ID",
    "UNIFIED_DATASET_URL",
    "UNIFIED_DOWNLOAD_URL",
    "UNIFIED_LICENSE",
    "UNIFIED_DATASET_VERSION",
    "assign_project_splits",
    "load_unified_rows",
    "select_candidate_pool",
    "write_candidate_pool",
    "write_source_manifest",
    "write_selection_manifest",
]
