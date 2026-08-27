from __future__ import annotations

import json

import pytest

from eval.validation_round import (
    build_validation_split,
    generate_paraphrase_probe,
    load_validation_cases,
    readiness_report,
    run_validation_round,
    validate_case_set,
)


def _case(case_id: str, project: str, label: str = "smelly") -> dict[str, object]:
    family = "subjective_language"
    return {
        "case_id": case_id,
        "source_dataset": "ARTA",
        "source_dataset_commit": "abc123",
        "source_file": "dataset.xlsx",
        "source_row": int(case_id.removeprefix("c")),
        "source_file_sha256": "f" * 64,
        "source_file_ref": "dataset.xlsx#row=1",
        "license_status": "redistributable",
        "redistribution_allowed": True,
        "derivative_use_allowed": True,
        "permission_record": "fixture-license.txt",
        "source_intent_id": f"intent-{case_id}",
        "source_file_id": f"file-{project}",
        "project_id": project,
        "requirement_text": "The system shall respond quickly." if label == "smelly" else "The system shall respond within 5 seconds.",
        "target_family": family,
        "source_label": label,
        "source_label_type": "arta_dataset_marker",
        "source_smell_markers": [family] if label == "smelly" else [],
        "expert_annotation_status": "pending",
        "paraphrase_status": "not_generated",
    }


def test_loader_rejects_duplicate_ids_and_missing_provenance(tmp_path) -> None:
    path = tmp_path / "cases.jsonl"
    rows = [_case("c1", "p1"), _case("c1", "p2")]
    path.write_text("\n".join(json.dumps(row) for row in rows), encoding="utf-8")

    with pytest.raises(ValueError, match="duplicate case_id"):
        load_validation_cases(path)

    rows = [_case("c1", "p1")]
    rows[0].pop("source_label_type")
    path.write_text(json.dumps(rows[0]), encoding="utf-8")
    with pytest.raises(ValueError, match="source_label_type"):
        load_validation_cases(path)


def test_loader_requires_permission_or_explicit_private_execution(tmp_path) -> None:
    path = tmp_path / "cases.jsonl"
    row = _case("c1", "p1")
    row["license_status"] = "private_use_only"
    row["redistribution_allowed"] = False
    row["derivative_use_allowed"] = False
    row["permission_record"] = ""
    path.write_text(json.dumps(row), encoding="utf-8")

    with pytest.raises(ValueError, match="lacks redistribution"):
        load_validation_cases(path)
    assert load_validation_cases(path, allow_private_source=True)[0]["license_status"] == "private_use_only"


def test_validation_requires_positive_and_clean_quota() -> None:
    cases = [_case("c1", "p1", "smelly"), _case("c2", "p2", "clean"), _case("c3", "p3", "clean")]

    with pytest.raises(ValueError, match="positive quota"):
        validate_case_set(cases, supported_families=("subjective_language",), minimum_per_family=2, minimum_clean_per_family=1)


def test_validation_rejects_marker_leak_into_clean_controls() -> None:
    cases = [_case("c1", "p1", "smelly"), _case("c2", "p2", "clean")]
    cases[1]["source_smell_markers"] = [{"column": "Polysemy", "value": "support"}]

    with pytest.raises(ValueError, match="not a clean control"):
        validate_case_set(cases, supported_families=("subjective_language",), minimum_per_family=1, minimum_clean_per_family=1)


def test_project_split_is_disjoint_and_has_three_partitions() -> None:
    cases = [_case(f"c{index}", project, "smelly" if index % 2 else "clean") for index, project in enumerate(("p1", "p2", "p3"), start=1)]

    manifest = build_validation_split(cases, seed=7)
    project_splits = {}
    for row in manifest["assignments"]:
        project_splits.setdefault(row["project_id"], set()).add(row["split"])

    assert set(project_splits) == {"p1", "p2", "p3"}
    assert all(len(splits) == 1 for splits in project_splits.values())
    assert {row["split"] for row in manifest["assignments"]} == {"train", "calibration", "test"}


def test_paraphrase_probe_is_not_primary_evidence() -> None:
    probe = generate_paraphrase_probe([_case("c1", "p1")])

    assert probe[0]["primary_metric_eligible"] is False
    assert probe[0]["paraphrase_status"] == "controlled_probe_unvalidated"


def test_readiness_blocks_without_experts_and_real_models() -> None:
    report = readiness_report([])

    assert report["confirmatory_ready"] is False
    assert "expert_annotation" in report["blocking_reasons"]
    assert "real_models" in report["blocking_reasons"]


def test_offline_round_writes_explicit_screening_artifacts(tmp_path) -> None:
    cases = []
    for index, project in enumerate(("p1", "p2", "p3"), start=1):
        cases.extend([_case(f"c{index * 2 - 1}", project, "smelly"), _case(f"c{index * 2}", project, "clean")])
    corpus = tmp_path / "cases.jsonl"
    corpus.write_text("\n".join(json.dumps(row) for row in cases), encoding="utf-8")

    result = run_validation_round(
        corpus,
        output_root=tmp_path / "artifacts",
        run_id="test-round",
        supported_families=("subjective_language",),
        minimum_per_family=1,
        minimum_clean_per_family=1,
    )

    assert result["status"] == "blocked_until_external_validation"
    assert (tmp_path / "artifacts" / "test-round" / "readiness.json").exists()
    assert (tmp_path / "artifacts" / "test-round" / "baseline_results.json").exists()
    assert (tmp_path / "artifacts" / "test-round" / "report.md").exists()
    assert (tmp_path / "artifacts" / "test-round" / "baseline-metrics.svg").exists()
