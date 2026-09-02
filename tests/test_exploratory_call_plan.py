from __future__ import annotations

import json
from pathlib import Path

import pytest

from eval.exploratory_call_plan import (
    build_exploratory_call_plan,
    load_reference_constraints,
)


def records():
    return [{"source_intent_id": f"intent-{index:02d}"} for index in range(12)]


def slots():
    return [{"slot_id": "slot-a"}, {"slot_id": "slot-b"}]


def write_constraints(path: Path, count: int = 12) -> None:
    path.write_text(
        json.dumps(
            {
                "schema_version": "prepilot-reference-constraints/v1",
                "records": [
                    {
                        "source_intent_id": f"intent-{index:02d}",
                        "constraint_id": f"opaque-{index:02d}",
                        "text": f"Constraint text {index}.",
                    }
                    for index in range(count)
                ],
            }
        ),
        encoding="utf-8",
    )


def test_plan_has_exact_episode_artifact_task_and_operation_counts(tmp_path: Path):
    constraints_path = tmp_path / "constraints.json"
    write_constraints(constraints_path)

    plan = build_exploratory_call_plan(
        records(), slots(), load_reference_constraints(constraints_path), run_nonce=b"n" * 32
    )

    assert len(plan.episodes) == 120
    assert len(plan.artifacts) == 240
    assert len(plan.base_tasks) == 240
    assert plan.duplicate_base_task_count == 48
    assert plan.judging_occurrence_count_per_judge == 288
    assert plan.logical_judging_calls == 576
    assert plan.logical_operations == 816
    assert plan.provider_api_calls == 1296
    assert plan.max_attempts_per_api_call == 2


def test_ids_are_opaque_unique_and_duplicate_occurrences_share_private_task_id(tmp_path: Path):
    path = tmp_path / "constraints.json"
    write_constraints(path)
    plan = build_exploratory_call_plan(records(), slots(), load_reference_constraints(path), run_nonce=b"a" * 32)

    ids = [item.episode_id for item in plan.episodes]
    ids += [item.artifact_id for item in plan.artifacts]
    ids += [item.base_task_id for item in plan.base_tasks]
    ids += [item.occurrence_id for item in plan.occurrences]
    assert len(ids) == len(set(ids))
    assert all(len(value) == 26 and value == value.lower() for value in ids)
    assert all(not value.startswith(("episode", "artifact", "task", "occ")) for value in ids)
    assert len(plan.duplicate_occurrences) == 48
    assert all(item.base_task_id in {task.base_task_id for task in plan.base_tasks} for item in plan.occurrences)
    assert len({item.occurrence_id for item in plan.occurrences}) == 288


def test_duplicate_selection_is_seed_reproducible_and_frozen_before_outcomes(tmp_path: Path):
    path = tmp_path / "constraints.json"
    write_constraints(path)
    constraints = load_reference_constraints(path)
    first = build_exploratory_call_plan(records(), slots(), constraints, duplicate_seed=0, run_nonce=b"a" * 32)
    second = build_exploratory_call_plan(records(), slots(), constraints, duplicate_seed=0, run_nonce=b"a" * 32)
    third = build_exploratory_call_plan(records(), slots(), constraints, duplicate_seed=1, run_nonce=b"a" * 32)

    assert [x.occurrence_id for x in first.occurrences] == [x.occurrence_id for x in second.occurrences]
    assert [x.base_task_id for x in first.duplicate_occurrences] == [x.base_task_id for x in second.duplicate_occurrences]
    assert [x.base_task_id for x in first.duplicate_occurrences] != [x.base_task_id for x in third.duplicate_occurrences]


def test_public_serialization_has_no_hidden_metadata_and_nonce_is_fresh(tmp_path: Path):
    path = tmp_path / "constraints.json"
    write_constraints(path)
    constraints = load_reference_constraints(path)
    first = build_exploratory_call_plan(records(), slots(), constraints)
    second = build_exploratory_call_plan(records(), slots(), constraints)
    serialized = json.dumps(first.to_public_dict())

    assert first.episodes[0].episode_id != second.episodes[0].episode_id
    assert all(token not in serialized for token in ("intent-", "slot-a", "slot-b", "variant", "provider", "replication"))


def test_reference_constraints_require_exact_unique_intent_coverage(tmp_path: Path):
    path = tmp_path / "constraints.json"
    write_constraints(path, count=11)
    with pytest.raises(ValueError, match="exactly one.*source intent"):
        build_exploratory_call_plan(records(), slots(), load_reference_constraints(path), run_nonce=b"a" * 32)

