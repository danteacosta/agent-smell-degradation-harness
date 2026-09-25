import hashlib
import json
from pathlib import Path

import pytest

from scripts import realworld_author_admission as admission


ROOT = Path(__file__).resolve().parents[1]
SOURCE_RELATIVE = (
    "data/criteria-expansion/sources/realworld/"
    "docs__src__content__docs__specifications__frontend__routing.md"
)


def test_source_and_single_span_omission_are_exact() -> None:
    source = ROOT / SOURCE_RELATIVE
    assert hashlib.sha256(source.read_bytes()).hexdigest() == admission.SOURCE_SHA256
    assert admission.SOURCE_REVISION == "ebbcdeb8d55b42a3a613c787560498b8ef10003f"
    assert admission.SOURCE_PATH == SOURCE_RELATIVE
    assert source.read_text(encoding="utf-8").splitlines().count(
        "  - Delete article button (only shown to article's author)"
    ) == 1
    assert hashlib.sha256(
        (ROOT / "data/criteria-expansion/sources/realworld/LICENSE").read_bytes()
    ).hexdigest() == "a999311c4ccfecf18b7c7beb7a7a31682bb009839ab3827164fa2f8c333fc9dd"

    variants = admission.variants()
    assert variants["A"] == "Delete article button (only shown to article's author)"
    assert variants["B"] == "Display the Delete article button only to the article's author."
    assert variants["C"] == "Delete article button"
    assert admission.OMITTED_SPAN == " (only shown to article's author)"
    assert variants["A"].replace(admission.OMITTED_SPAN, "", 1) == variants["C"]
    assert variants["A"].count(admission.OMITTED_SPAN) == 1


def test_requests_share_exact_interface_and_do_not_leak_study_metadata() -> None:
    bundle = admission.build_prompt_bundle()
    assert bundle["common_interface_sha256"] == admission.sha256_text(
        bundle["common_interface"]
    )
    for arm in admission.ARMS:
        expected = admission.compose_request(
            bundle["variants"][arm], bundle["common_interface"]
        )
        assert bundle["requests"][arm] == expected
        assert expected.endswith(bundle["common_interface"])
        lower = expected.casefold()
        for forbidden in (
            "expected verdict",
            "target label",
            "variant a",
            "variant b",
            "variant c",
            "source url",
            "omitted span",
            "oracle",
            "github.com/realworld-apps",
        ):
            assert forbidden not in lower
    assert len({bundle["requests"][arm] for arm in admission.ARMS}) == 3
    assert "window.initialState" in bundle["common_interface"]
    assert (
        'window.initialState = { viewer: { username: string }, article: { slug: string, '
        'title: string, body: string, author: { username: string } } }'
        in bundle["common_interface"]
    )
    assert "/article/bounded-ui-case" in bundle["common_interface"]
    assert '[rel~="author"]' in bundle["common_interface"]
    assert "accessible button" in bundle["common_interface"]
    assert "raw HTML" in bundle["common_interface"]


def test_schedule_is_deterministic_balanced_and_opaque() -> None:
    first = admission.build_schedule(seed=20260925)
    second = admission.build_schedule(seed=20260925)
    assert first == second
    assert len(first) == 18
    assert len({row["slot_id"] for row in first}) == 18
    assert all(admission.OPAQUE_SLOT.fullmatch(row["slot_id"]) for row in first)
    assert all(set(row) == {"slot_id", "model", "replication", "arm"} for row in first)
    assert {
        (row["model"], row["replication"], row["arm"]) for row in first
    } == {
        (model, replication, arm)
        for model in admission.MODELS
        for replication in admission.REPETITIONS
        for arm in admission.ARMS
    }
    assert [row["slot_id"] for row in first] != [
        row["slot_id"] for row in admission.build_schedule(seed=20260926)
    ]


def test_approved_package_binds_review_rights_and_stays_non_executable() -> None:
    package = admission.build_admission_package()
    assert package["endpoint_admission"] == "admitted_bounded_exploratory_endpoint"
    assert package["freeze_status"] == (
        "prompts_and_bounded_endpoint_frozen_not_execution_ready"
    )
    assert package["review"]["decision"] == (
        "approved_for_execution-freeze_preparation"
    )
    assert package["review"]["reviewer_id"] == (
        "codex-agent-independent-admission-review-20260925"
    )
    assert package["review"]["evidence_path"] == "independent-review.json"
    assert package["review"]["evidence_sha256"] == admission.sha256_bytes(
        admission.json_bytes(admission.build_review_record())
    )
    assert package["rights"] == {
        "license": "MIT",
        "path": "data/criteria-expansion/sources/realworld/LICENSE",
        "sha256": "a999311c4ccfecf18b7c7beb7a7a31682bb009839ab3827164fa2f8c333fc9dd",
        "url": (
            "https://raw.githubusercontent.com/realworld-apps/realworld/"
            "ebbcdeb8d55b42a3a613c787560498b8ef10003f/LICENSE"
        ),
        "revision": "ebbcdeb8d55b42a3a613c787560498b8ef10003f",
    }
    assert package["human_approvals"] == 0
    assert package["model_calls"] == 0
    assert package["automatic_dispatch_allowed"] is False
    assert package["execution_configuration_frozen"] is False
    assert package["instrument"]["instrument_sha256"] == (
        "526a2aee0264ac81e4c318ad6b9c58d968113bae7dc41d776d40b3500112434e"
    )
    assert package["instrument"]["qualification_manifest_sha256"] == (
        "cf5baf358bc64914f16e1023eb48f34d73c9034127d9b02079dcfe8f4006a820"
    )
    assert package["instrument"]["ci_artifact_archive_sha256"] == (
        "2b2b301f21838d515e2ea56636425d0c50f81ae14d73b7f0ba607b9890b368d8"
    )
    assert package["source"]["sha256"] == admission.SOURCE_SHA256
    assert package["scope"]["included"] == "visibility of the Delete Article button"
    assert package["scope"]["excluded"] == [
        "button click behavior",
        "backend authorization",
        "article deletion",
    ]
    assert package["claims"] == {
        "h1_supported": False,
        "h2_supported": False,
        "experimental_outcome": False,
    }


def test_canonical_review_records_scope_limits_and_leakage_risk() -> None:
    review = admission.build_review_record()
    assert review["schema_version"] == "realworld-author-ui-admission-review/v1"
    assert review["decision"] == "approved_for_execution-freeze_preparation"
    assert review["reviewer_id"] == "codex-agent-independent-admission-review-20260925"
    assert review["human_approvals"] == 0
    assert review["reviewed"] == {
        "source_manipulation": "approved",
        "common_interface": "approved",
        "schedule": "approved",
    }
    assert review["scope"] == "visibility of the Delete Article button"
    assert review["limits"] == [
        "button click behavior is not evaluated",
        "backend authorization is not evaluated",
        "article deletion is not evaluated",
        "collector executable and runtime are not frozen",
        "provider dispatch is not authorized",
        "no experimental result or H1/H2 inference exists",
    ]
    assert review["leakage_risk"]["status"] == "accepted_bounded_residual_risk"
    assert review["leakage_risk"]["shared_across_arms"] is True


def test_materialize_writes_hash_bound_requests_without_provider_calls(tmp_path: Path) -> None:
    output = tmp_path / "candidate"
    manifest = admission.materialize(output)

    assert manifest["planned_slots"] == 18
    assert manifest["provider_calls"] == 0
    assert set(path.name for path in (output / "requests").iterdir()) == {
        row["slot_id"] + ".json" for row in manifest["schedule"]
    }
    review_path = output / "independent-review.json"
    assert json.loads(review_path.read_text(encoding="utf-8")) == (
        admission.build_review_record()
    )
    assert manifest["review"]["evidence_sha256"] == hashlib.sha256(
        review_path.read_bytes()
    ).hexdigest()
    for row in manifest["schedule"]:
        request_path = output / "requests" / f"{row['slot_id']}.json"
        request = json.loads(request_path.read_text(encoding="utf-8"))
        assert set(request) == {"prompt"}
        assert request["prompt"] == manifest["prompt_bundle"]["requests"][row["arm"]]
        assert manifest["request_sha256"][row["slot_id"]] == hashlib.sha256(
            request_path.read_bytes()
        ).hexdigest()
    receipt = json.loads((output / "receipt.json").read_text(encoding="utf-8"))
    assert receipt == admission.inventory(output, exclude={"receipt.json"})
    assert admission.validate_materialized(output)["review"]["decision"] == (
        "approved_for_execution-freeze_preparation"
    )

    with pytest.raises(FileExistsError):
        admission.materialize(output)

    review_path.write_text("{}\n", encoding="utf-8")
    with pytest.raises(ValueError, match="review evidence"):
        admission.validate_materialized(output)


def test_materialize_rejects_missing_or_changed_preserved_source(
    tmp_path: Path, monkeypatch
) -> None:
    monkeypatch.setattr(admission, "ROOT", tmp_path)
    with pytest.raises(ValueError, match="preserved source"):
        admission.materialize(tmp_path / "missing-source")

    source = tmp_path / admission.SOURCE_PATH
    source.parent.mkdir(parents=True)
    source.write_text(admission.SOURCE_LINE + "\nchanged\n", encoding="utf-8")
    with pytest.raises(ValueError, match="preserved source"):
        admission.materialize(tmp_path / "changed-source")


@pytest.mark.parametrize(
    "target,error",
    [
        ("prompt_bundle", "canonical prompt bundle"),
        ("schedule", "canonical schedule"),
        ("request", "canonical request"),
    ],
)
def test_materialized_validation_rejects_self_consistent_tampering(
    tmp_path: Path, target: str, error: str
) -> None:
    output = tmp_path / target
    manifest = admission.materialize(output)

    if target == "prompt_bundle":
        altered = admission.build_prompt_bundle()
        altered["common_interface"] += "altered"
        (output / "prompt-bundle.json").write_bytes(admission.json_bytes(altered))
    elif target == "schedule":
        altered = list(reversed(admission.build_schedule()))
        (output / "schedule.json").write_bytes(admission.json_bytes(altered))
    else:
        row = manifest["schedule"][0]
        request_path = output / "requests" / f"{row['slot_id']}.json"
        request_path.write_bytes(admission.json_bytes({"prompt": "altered"}))
        manifest["request_sha256"][row["slot_id"]] = hashlib.sha256(
            request_path.read_bytes()
        ).hexdigest()
        (output / "manifest.json").write_bytes(admission.json_bytes(manifest))

    (output / "receipt.json").write_bytes(
        admission.json_bytes(admission.inventory(output, exclude={"receipt.json"}))
    )
    with pytest.raises(ValueError, match=error):
        admission.validate_materialized(output)


@pytest.mark.parametrize(
    "mutation,error",
    [
        (lambda package: package["schedule"].pop(), "18"),
        (
            lambda package: package["prompt_bundle"]["requests"].__setitem__(
                "C", package["prompt_bundle"]["requests"]["A"]
            ),
            "request",
        ),
        (
            lambda package: package["instrument"].__setitem__(
                "instrument_sha256", "0" * 64
            ),
            "instrument",
        ),
        (
            lambda package: package.__setitem__("endpoint_admission", "qualified"),
            "status",
        ),
        (
            lambda package: package["review"].__setitem__(
                "evidence_sha256", "0" * 64
            ),
            "review",
        ),
        (
            lambda package: package.__setitem__("human_approvals", 1),
            "approval",
        ),
        (
            lambda package: package["claims"].__setitem__("h1_supported", True),
            "metadata",
        ),
    ],
)
def test_validation_fails_closed_on_admission_drift(mutation, error: str) -> None:
    package = admission.build_admission_package()
    mutation(package)
    with pytest.raises(ValueError, match=error):
        admission.validate_admission_package(package)
