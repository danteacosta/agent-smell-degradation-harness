from __future__ import annotations

import json
from dataclasses import asdict, astuple
from pathlib import Path

import pytest

from eval.exploratory_call_plan import (
    build_exploratory_call_plan,
    load_reference_constraints,
)


def records():
    return [{"source_intent_id": f"intent-{index:02d}"} for index in range(12)]


def slots():
    return [
        {
            "slot_id": "slot-a",
            "provider": "provider-a",
            "model": "model-a",
            "model_version": "version-a",
        },
        {
            "slot_id": "slot-b",
            "provider": "provider-b",
            "model": "model-b",
            "model_version": "version-b",
        },
    ]


def constraint_records(count: int = 12) -> list[dict[str, str]]:
    return [
        {
            "source_intent_id": f"intent-{index:02d}",
            "constraint_id": f"opaque-{index:02d}",
            "text": f"Constraint text {index}.",
        }
        for index in range(count)
    ]


def write_constraints(path: Path, count: int = 12) -> None:
    path.write_text(
        json.dumps(
            {
                "schema_version": "prepilot-reference-constraints/v1",
                "records": constraint_records(count),
            }
        ),
        encoding="utf-8",
    )


def _representation_exposes_private_metadata(value: object, run_nonce: bytes) -> bool:
    rendered = repr(value)
    private_markers = (
        "_private_join",
        "_run_nonce",
        "source_intent_id",
        "provider_slot_id",
        "variant_index",
        "replication_index",
        "intent-",
        "provider-a",
        "provider-b",
        "slot-a",
        "slot-b",
        run_nonce.decode("ascii"),
    )
    return any(marker in rendered for marker in private_markers)


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
    first = build_exploratory_call_plan(records(), slots(), constraints, run_nonce=b"a" * 32)
    second = build_exploratory_call_plan(records(), slots(), constraints, run_nonce=b"a" * 32)

    assert [x.occurrence_id for x in first.occurrences] == [x.occurrence_id for x in second.occurrences]
    assert [x.base_task_id for x in first.duplicate_occurrences] == [x.base_task_id for x in second.duplicate_occurrences]


def test_duplicate_fraction_cannot_be_overridden(tmp_path: Path):
    path = tmp_path / "constraints.json"
    write_constraints(path)

    with pytest.raises(TypeError):
        build_exploratory_call_plan(
            records(),
            slots(),
            load_reference_constraints(path),
            duplicate_fraction=0.1,
            run_nonce=b"a" * 32,
        )


def test_public_serialization_has_no_hidden_metadata_and_nonce_is_fresh(tmp_path: Path):
    path = tmp_path / "constraints.json"
    write_constraints(path)
    constraints = load_reference_constraints(path)
    first = build_exploratory_call_plan(records(), slots(), constraints)
    second = build_exploratory_call_plan(records(), slots(), constraints)
    serialized = json.dumps(first.to_public_dict())

    assert first.episodes[0].episode_id != second.episodes[0].episode_id
    public = first.to_public_dict()
    assert public["duplicate_fraction"] == 0.2
    assert public["duplicate_seed"] == 0
    assert all(token not in serialized for token in ("intent-", "slot-a", "slot-b", "variant", "provider", "replication"))
    assert all(set(item) == {"constraint_id", "text"} for item in public["reference_constraints"])


def test_generic_plan_representations_do_not_expose_private_metadata(tmp_path: Path):
    path = tmp_path / "constraints.json"
    write_constraints(path)
    run_nonce = b"0123456789abcdef0123456789abcdef"
    plan = build_exploratory_call_plan(records(), slots(), load_reference_constraints(path), run_nonce=run_nonce)

    assert not _representation_exposes_private_metadata(plan, run_nonce), (
        "plan representation exposed private exploratory metadata"
    )
    assert not _representation_exposes_private_metadata(asdict(plan), run_nonce), (
        "plan asdict exposed private exploratory metadata"
    )
    assert not _representation_exposes_private_metadata(astuple(plan), run_nonce), (
        "plan astuple exposed private exploratory metadata"
    )
    assert not _representation_exposes_private_metadata(plan.to_public_dict(), run_nonce), (
        "plan public dict exposed private exploratory metadata"
    )

    assert plan._private_join
    assert plan._run_nonce == run_nonce


def test_reference_constraints_require_exact_unique_intent_coverage(tmp_path: Path):
    path = tmp_path / "constraints.json"
    write_constraints(path, count=11)
    with pytest.raises(ValueError, match="exactly one.*source intent"):
        build_exploratory_call_plan(records(), slots(), load_reference_constraints(path), run_nonce=b"a" * 32)


def test_provider_configurations_must_be_distinct_beyond_slot_ids(tmp_path: Path):
    path = tmp_path / "constraints.json"
    write_constraints(path)
    duplicate_configuration_slots = [
        {
            "slot_id": "slot-a",
            "provider": "provider",
            "model": "model",
            "model_version": "version",
        },
        {
            "slot_id": "slot-b",
            "provider": "provider",
            "model": "model",
            "model_version": "version",
        },
    ]

    with pytest.raises(ValueError, match="provider/model/model_version"):
        build_exploratory_call_plan(
            records(),
            duplicate_configuration_slots,
            load_reference_constraints(path),
            run_nonce=b"a" * 32,
        )


def test_direct_reference_constraint_mappings_use_the_loaded_validation_path():
    direct = constraint_records()

    plan = build_exploratory_call_plan(records(), slots(), direct, run_nonce=b"a" * 32)

    assert len(plan.reference_constraints) == 12


@pytest.mark.parametrize(
    ("field", "value"),
    [
        ("source_intent_id", 7),
        ("constraint_id", 7),
        ("text", 7),
    ],
)
def test_loaded_reference_constraints_reject_non_string_values(
    tmp_path: Path, field: str, value: object
):
    payload = {"schema_version": "prepilot-reference-constraints/v1", "records": constraint_records()}
    payload["records"][0][field] = value  # type: ignore[index]
    path = tmp_path / "constraints.json"
    path.write_text(json.dumps(payload), encoding="utf-8")

    with pytest.raises(ValueError):
        load_reference_constraints(path)


@pytest.mark.parametrize(
    "mutate",
    [
        lambda item: item.pop("text"),
        lambda item: item.update(extra="not allowed"),
        lambda item: item.update(source_intent_id=7),
        lambda item: item.update(constraint_id=7),
        lambda item: item.update(text=7),
        lambda item: item.update(text="incompleteness_missing_condition is private"),
        lambda item: item.update(oracle_result="must not cross the judge boundary"),
        lambda item: item.update(text="x" * 4001),
        lambda item: item.update(constraint_id="x" * 129),
        lambda item: item.update(text="   "),
    ],
)
def test_direct_reference_constraints_reject_malformed_or_forbidden_records(mutate):
    direct = constraint_records()
    mutate(direct[0])

    with pytest.raises(ValueError):
        build_exploratory_call_plan(records(), slots(), direct, run_nonce=b"a" * 32)


@pytest.mark.parametrize(
    "mutate",
    [
        lambda item: item.pop("text"),
        lambda item: item.update(extra="not allowed"),
        lambda item: item.update(text="incompleteness_missing_condition is private"),
        lambda item: item.update(t4="must not cross the judge boundary"),
        lambda item: item.update(text="x" * 4001),
        lambda item: item.update(constraint_id="x" * 129),
        lambda item: item.update(text="   "),
    ],
)
def test_loaded_reference_constraints_reject_malformed_or_forbidden_records(tmp_path: Path, mutate):
    payload = {"schema_version": "prepilot-reference-constraints/v1", "records": constraint_records()}
    mutate(payload["records"][0])
    path = tmp_path / "constraints.json"
    path.write_text(json.dumps(payload), encoding="utf-8")

    with pytest.raises(ValueError):
        load_reference_constraints(path)


def test_loaded_reference_constraints_reject_duplicate_ids(tmp_path: Path):
    payload = {"schema_version": "prepilot-reference-constraints/v1", "records": constraint_records()}
    payload["records"][1]["constraint_id"] = payload["records"][0]["constraint_id"]
    path = tmp_path / "constraints.json"
    path.write_text(json.dumps(payload), encoding="utf-8")

    with pytest.raises(ValueError, match="unique.*constraint IDs"):
        load_reference_constraints(path)


def test_direct_reference_constraints_reject_duplicate_ids():
    direct = constraint_records()
    direct[1]["constraint_id"] = direct[0]["constraint_id"]

    with pytest.raises(ValueError, match="unique.*constraint IDs"):
        build_exploratory_call_plan(records(), slots(), direct, run_nonce=b"a" * 32)
