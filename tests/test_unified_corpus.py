from __future__ import annotations

import csv
import json
from pathlib import Path

import pytest

from eval.unified_corpus import (
    SUPPORTED_FAMILIES,
    assign_project_splits,
    load_unified_rows,
    select_candidate_pool,
    write_candidate_pool,
    write_source_manifest,
    write_selection_manifest,
)


def _write_fixture(path: Path) -> None:
    fields = [
        "Requirement ID",
        "Project ID",
        "Project Name",
        "Datasets",
        "Requirement Text (Original Requirement)",
        "Class",
    ]
    rows: list[dict[str, str]] = []
    texts = {
        "subjective_language": "The system shall be easy to use within 2 seconds for workflow {index}.",
        "ambiguous_adjective_adverb": "The system shall respond appropriately within 2 seconds for workflow {index}.",
        "nonverifiable_term": "The system shall produce an acceptable response within 2 seconds for workflow {index}.",
        "vague_pronoun": "If the account is revoked, it shall be re-instantiated by the administrator for workflow {index}.",
        "uncertain_verb": "The system may send a notification when the threshold is exceeded for workflow {index}.",
        "polysemy": "The system shall process the request and return a response for workflow {index}.",
    }
    for family_index, family in enumerate(SUPPORTED_FAMILIES):
        for index in range(24):
            rows.append(
                {
                    "Requirement ID": f"R-{family_index:02d}-{index:02d}",
                    "Project ID": f"P-{family_index:02d}-{index:02d}",
                    "Project Name": f"Project {family_index}-{index}",
                    "Datasets": "D1",
                    "Requirement Text (Original Requirement)": texts[family].format(index=index),
                    "Class": "FR",
                }
            )
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)


def test_load_unified_rows_rejects_missing_contract_columns(tmp_path: Path) -> None:
    path = tmp_path / "bad.csv"
    path.write_text("Requirement ID\nR-1\n", encoding="utf-8")

    with pytest.raises(ValueError, match="required columns"):
        load_unified_rows(path)


def test_candidate_pool_has_positive_and_hard_clean_quota_without_source_class(tmp_path: Path) -> None:
    source = tmp_path / "unified.csv"
    _write_fixture(source)
    rows = load_unified_rows(source)

    selected, project_splits = select_candidate_pool(
        rows,
        per_kind=2,
        seed=17,
        split_quotas={"train": 1, "calibration": 1, "test": 1},
    )

    assert len(selected) == len(SUPPORTED_FAMILIES) * 6
    for family in SUPPORTED_FAMILIES:
        family_rows = [row for row in selected if row["target_family"] == family]
        assert {row["candidate_kind"] for row in family_rows} == {
            "cue_positive_candidate",
            "hard_clean_candidate",
        }
        assert len(family_rows) == 6
    assert all("Class" not in row for row in selected)
    assert set(project_splits.values()) == {"train", "calibration", "test"}
    assert all(row["project_id"] in project_splits for row in selected)


def test_project_splits_are_deterministic_and_disjoint() -> None:
    projects = [f"P-{index:02d}" for index in range(12)]
    first = assign_project_splits(projects, seed=9)
    second = assign_project_splits(projects, seed=9)

    assert first == second
    assert set(first.values()) == {"train", "calibration", "test"}
    assert len(set(first)) == 12


def test_candidate_outputs_keep_text_only_in_private_pool(tmp_path: Path) -> None:
    source = tmp_path / "unified.csv"
    _write_fixture(source)
    rows = load_unified_rows(source)
    selected, project_splits = select_candidate_pool(
        rows,
        per_kind=1,
        seed=2,
        split_quotas={"train": 1, "calibration": 1, "test": 1},
    )
    candidate_output = tmp_path / "candidates.jsonl"
    manifest_output = tmp_path / "selection.json"

    write_candidate_pool(candidate_output, selected, project_splits)
    write_selection_manifest(
        manifest_output,
        selected,
        project_splits,
        source_archive_sha256="archive-hash",
        source_member="requirements.csv",
        source_member_sha256="member-hash",
    )
    source_manifest_output = tmp_path / "source.json"
    write_source_manifest(
        source_manifest_output,
        rows,
        source_archive_sha256="archive-hash",
        source_archive_size_bytes=10,
        source_member="requirements.csv",
        source_member_sha256="member-hash",
        source_member_size_bytes=20,
    )

    private_rows = [json.loads(line) for line in candidate_output.read_text().splitlines()]
    manifest = json.loads(manifest_output.read_text())
    assert all(row["requirement_text"] for row in private_rows)
    assert all("requirement_text" not in row for row in manifest["records"])
    assert manifest["source"]["license"]["short_name"] == "CC BY 4.0"
    source_manifest = json.loads(source_manifest_output.read_text())
    assert source_manifest["processing"]["source_class_column_used"] is False
    assert source_manifest["license"]["short_name"] == "CC BY 4.0"
