from __future__ import annotations

from copy import deepcopy

import pytest

from label_plane.calibration_queues import freeze_calibration_queues


SOURCE_HASH = "a" * 64


def test_manifest_binds_population_and_selected_packet_contents() -> None:
    tasks = _tasks()
    kwargs = dict(calibration_count=6, triage_count=3, seed=17,
                  source_selection_sha256=SOURCE_HASH)
    first = freeze_calibration_queues(tasks, _signals(), **kwargs)
    changed = deepcopy(tasks)
    changed[0]["generated_acceptance_criteria"] = "Different obligation"
    second = freeze_calibration_queues(changed, _signals(), **kwargs)
    assert first[2]["selection_sha256"] != second[2]["selection_sha256"]
    for field in ("population_sha256", "calibration_tasks_sha256", "triage_tasks_sha256"):
        assert len(first[2][field]) == 64
    reordered = freeze_calibration_queues(list(reversed(tasks)), _signals(), **kwargs)
    assert first[2] == reordered[2]


def _tasks() -> list[dict]:
    return [
        {
            "item_id": f"item-{index}",
            "generated_acceptance_criteria": f"Criterion {index}",
            "reference_constraints": [f"Constraint {index}"],
            "rubric_version": "rubric-v2",
            "duplicate_subset": index % 5 == 0,
        }
        for index in range(12)
    ]


def _signals() -> list[dict]:
    rows = []
    for index in range(12):
        rows.append(
            {
                "item_id": f"item-{index}",
                "stratum_id": f"project-{index % 3}",
                "machine_disagreement": index in {0, 1, 2, 3},
                "machine_abstention": index in {0, 3, 6},
                "invalid_evidence": index in {3, 7},
                "metamorphic_violation": index in {3, 8},
                "incomplete_trace": index == 3,
            }
        )
    return rows


def test_probability_sample_is_stratified_reproducible_and_signal_invariant() -> None:
    first = freeze_calibration_queues(
        _tasks(), _signals(), calibration_count=6, triage_count=3, seed=17,
        source_selection_sha256=SOURCE_HASH,
    )
    changed_signals = deepcopy(_signals())
    for row in changed_signals:
        for field in set(row) - {"item_id", "stratum_id"}:
            row[field] = not row[field]
    second = freeze_calibration_queues(
        list(reversed(_tasks())), changed_signals, calibration_count=6,
        triage_count=3, seed=17, source_selection_sha256=SOURCE_HASH,
    )

    calibration, triage, manifest = first
    assert calibration == second[0]
    assert {row["stratum_id"] for row in manifest["calibration_sample"]} == {
        "project-0", "project-1", "project-2"
    }
    assert all(row["inclusion_probability"] == 0.5 for row in manifest["calibration_sample"])
    assert not ({task["item_id"] for task in calibration} & {task["item_id"] for task in triage})
    assert len(manifest["selection_sha256"]) == 64


def test_triage_signals_stay_private_and_queue_is_project_balanced() -> None:
    calibration, triage, manifest = freeze_calibration_queues(
        _tasks(), _signals(), calibration_count=3, triage_count=3, seed=2,
        source_selection_sha256=SOURCE_HASH,
    )

    visible_fields = {field for task in calibration + triage for field in task}
    assert not visible_fields.intersection(
        {"stratum_id", "machine_disagreement", "machine_abstention", "reasons", "priority_score"}
    )
    assert len({row["stratum_id"] for row in manifest["triage_queue"]}) == 3
    assert manifest["interpretation"]["triage"].startswith("outcome-enriched")


def test_queue_freeze_fails_closed_on_invalid_scope() -> None:
    with pytest.raises(ValueError, match="at least one item per stratum"):
        freeze_calibration_queues(
            _tasks(), _signals(), calibration_count=2, triage_count=1, seed=0,
            source_selection_sha256=SOURCE_HASH,
        )

    leaking = _signals()
    leaking[0]["human_label"] = "clean"
    with pytest.raises(ValueError, match="unsupported fields"):
        freeze_calibration_queues(
            _tasks(), leaking, calibration_count=3, triage_count=1, seed=0,
            source_selection_sha256=SOURCE_HASH,
        )

    requirement_tasks = [
        {
            "item_id": f"item-{index}",
            "presented_text": f"Requirement {index}",
            "rubric_version": "rubric-v2",
            "duplicate_subset": False,
            "machine_disagreement": True,
        }
        for index in range(12)
    ]
    with pytest.raises(ValueError, match="invalid field set"):
        freeze_calibration_queues(
            requirement_tasks, _signals(), calibration_count=3, triage_count=1,
            seed=0, source_selection_sha256=SOURCE_HASH,
        )
