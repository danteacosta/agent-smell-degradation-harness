from __future__ import annotations

import hashlib
import hmac
import json
from dataclasses import asdict, astuple
from pathlib import Path

import pytest

from eval.exploratory_call_plan import (
    ExploratoryCallPlan,
    PublicArtifact,
    PublicBaseTask,
    PublicEpisode,
    PublicOccurrence,
    ReferenceConstraint,
    _PrivateJoin,
    _PrivateProviderConfiguration,
    _opaque_id,
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


def _direct_plan(
    *, nonce: object = b"a" * 32, private_join: object = (), private_configurations: object = (), **public_fields: object
):  # type: ignore[no-untyped-def]
    fields: dict[str, object] = {
        "episodes": (),
        "artifacts": (),
        "base_tasks": (),
        "occurrences": (),
        "duplicate_occurrences": (),
        "reference_constraints": (),
    }
    fields.update(public_fields)
    return ExploratoryCallPlan(
        **fields,  # type: ignore[arg-type]
        _run_nonce=nonce,  # type: ignore[arg-type]
        _private_join=private_join,  # type: ignore[arg-type]
        _private_configurations=private_configurations,  # type: ignore[arg-type]
    )


@pytest.mark.parametrize("nonce", ["a" * 32, bytearray(b"a" * 32), b"a" * 31, b"a" * 33])
def test_direct_plan_construction_rejects_invalid_nonce(nonce: object):
    with pytest.raises(ValueError, match="run_nonce must be bytes"):
        _direct_plan(nonce=nonce)


def test_direct_plan_construction_freezes_mutable_private_inputs():
    private_join = [_PrivateJoin("episode", "artifact", "task", "intent", 0, 0, "slot")]
    private_configurations = [_PrivateProviderConfiguration("slot", "provider", "model", "version")]

    plan = _direct_plan(private_join=private_join, private_configurations=private_configurations)
    private_join.clear()
    private_configurations.clear()

    assert isinstance(plan._private_join, tuple)
    assert isinstance(plan._private_configurations, tuple)
    assert len(plan._private_join) == len(plan._private_configurations) == 1


@pytest.mark.parametrize(
    "private_input",
    [
        ("join", (_PrivateJoin([], "artifact", "task", "intent", 0, 0, "slot"),)),
        ("configuration", (_PrivateProviderConfiguration("slot", [], "model", "version"),)),
        ("join", [{}]),
    ],
)
def test_direct_plan_construction_rejects_mutable_or_untyped_private_inputs(private_input: tuple[str, object]):
    field, value = private_input
    argument = "private_configurations" if field == "configuration" else f"private_{field}"
    with pytest.raises(ValueError, match="private"):
        _direct_plan(**{argument: value})


@pytest.mark.parametrize(
    ("field", "record", "expected"),
    [
        ("episodes", {"episode_id": "episode"}, (PublicEpisode("episode"),)),
        ("artifacts", {"artifact_id": "artifact"}, (PublicArtifact("artifact"),)),
        (
            "base_tasks",
            {"base_task_id": "task", "artifact_id": "artifact"},
            (PublicBaseTask("task", "artifact"),),
        ),
        (
            "occurrences",
            {"occurrence_id": "occurrence", "base_task_id": "task", "duplicate": False},
            (PublicOccurrence("occurrence", "task", False),),
        ),
        (
            "duplicate_occurrences",
            {"occurrence_id": "duplicate", "base_task_id": "task", "duplicate": True},
            (PublicOccurrence("duplicate", "task", True),),
        ),
        (
            "reference_constraints",
            {"constraint_id": "constraint", "text": "constraint text"},
            (ReferenceConstraint("constraint", "constraint text"),),
        ),
    ],
)
def test_direct_plan_canonicalizes_mutable_public_field_inputs(
    field: str, record: dict[str, object], expected: tuple[object, ...]
):
    records = [record]
    plan = _direct_plan(**{field: records})
    record.clear()
    records.clear()

    assert getattr(plan, field) == expected
    assert isinstance(getattr(plan, field), tuple)


@pytest.mark.parametrize(
    "field",
    ["episodes", "artifacts", "base_tasks", "occurrences", "duplicate_occurrences", "reference_constraints"],
)
def test_direct_plan_rejects_mapping_instead_of_retaining_mutable_public_field(field: str):
    with pytest.raises(ValueError, match="public"):
        _direct_plan(**{field: {"mutable": []}})


@pytest.mark.parametrize("attempts", [None, True, 0, 3, 2.0, "2", [2], {"attempts": 2}])
def test_direct_plan_rejects_invalid_max_attempts_values(attempts: object):
    with pytest.raises(ValueError, match="max_attempts_per_api_call"):
        _direct_plan(max_attempts_per_api_call=attempts)


@pytest.mark.parametrize("attempts", [1, 2])
def test_direct_plan_canonicalizes_max_attempts_and_public_serialization(attempts: int):
    plan = _direct_plan(max_attempts_per_api_call=attempts)

    assert type(plan.max_attempts_per_api_call) is int
    assert plan.max_attempts_per_api_call == attempts
    assert type(plan.to_public_dict()["max_attempts_per_api_call"]) is int
    assert plan.to_public_dict()["max_attempts_per_api_call"] == attempts


def test_provider_identity_must_differ_even_when_models_differ(tmp_path: Path):
    path = tmp_path / "constraints.json"
    write_constraints(path)
    same_provider_slots = [
        {"slot_id": "slot-a", "provider": "provider", "model": "model-a", "model_version": "version-a"},
        {"slot_id": "slot-b", "provider": "provider", "model": "model-b", "model_version": "version-b"},
    ]

    with pytest.raises(ValueError, match="provider identity"):
        build_exploratory_call_plan(
            records(), same_provider_slots, load_reference_constraints(path), run_nonce=b"a" * 32
        )


@pytest.mark.parametrize("nonce", ["a" * 32, bytearray(b"a" * 32), b"a" * 31, b"a" * 33])
def test_plan_rejects_non_bytes_nonce_before_hmac(tmp_path: Path, nonce: object):
    path = tmp_path / "constraints.json"
    write_constraints(path)

    with pytest.raises(ValueError, match="run_nonce must be bytes"):
        build_exploratory_call_plan(records(), slots(), load_reference_constraints(path), run_nonce=nonce)  # type: ignore[arg-type]


def test_provider_configuration_is_trimmed_before_distinctness_and_preserved(tmp_path: Path):
    path = tmp_path / "constraints.json"
    write_constraints(path)
    configured_slots = [
        {
            "slot_id": " slot-a ",
            "provider": " provider ",
            "model": " model ",
            "model_version": " version ",
        },
        {
            "slot_id": " slot-b ",
            "provider": "provider-2",
            "model": "model-2",
            "model_version": "version-2",
        },
    ]

    plan = build_exploratory_call_plan(
        records(), configured_slots, load_reference_constraints(path), run_nonce=b"a" * 32
    )

    assert [(item.slot_id, item.provider, item.model, item.model_version) for item in plan._private_configurations] == [
        ("slot-a", "provider", "model", "version"),
        ("slot-b", "provider-2", "model-2", "version-2"),
    ]


def test_provider_configuration_distinctness_uses_trimmed_values(tmp_path: Path):
    path = tmp_path / "constraints.json"
    write_constraints(path)
    equivalent_slots = [
        {"slot_id": "slot-a", "provider": " provider ", "model": " model ", "model_version": " version "},
        {"slot_id": "slot-b", "provider": "provider", "model": "model", "model_version": "version"},
    ]

    with pytest.raises(ValueError, match="provider/model/model_version"):
        build_exploratory_call_plan(
            records(), equivalent_slots, load_reference_constraints(path), run_nonce=b"a" * 32
        )


def test_opaque_id_matches_independent_length_prefixed_hmac_vector():
    nonce = bytes(range(32))
    message = b"\x00\x00\x00\x07episode\x00\x00\x00\x010"
    expected_digest = hmac.new(nonce, message, hashlib.sha256).digest()[:16]

    assert expected_digest.hex() == "8ad15c43e313a1f6a54aa6fae0b14769"
    assert _opaque_id(nonce, "episode", 0) == "rlivyq7dcoq7njkku35obmkhne"
