"""Build the reviewed pre-generation RealWorld article-author admission packet.

This module is deliberately provider-free. It freezes source-relative prompt
bytes and a balanced schedule, but it does not freeze or invoke a collector.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import random
import re


ROOT = Path(__file__).resolve().parents[1]
ARMS = ("A", "B", "C")
MODELS = ("gpt-5.6-luna", "gpt-5.6-sol")
REPETITIONS = (1, 2, 3)
SEED = 20260925
OPAQUE_SLOT = re.compile(r"rw-[0-9a-f]{24}")

SOURCE_REVISION = "ebbcdeb8d55b42a3a613c787560498b8ef10003f"
SOURCE_PATH = (
    "data/criteria-expansion/sources/realworld/"
    "docs__src__content__docs__specifications__frontend__routing.md"
)
SOURCE_SHA256 = "65fbd975a3ab2021057b1c1944cf66418aa846039e51b166d2a98eb29e7169fb"
SOURCE_URL = (
    "https://raw.githubusercontent.com/realworld-apps/realworld/"
    f"{SOURCE_REVISION}/docs/src/content/docs/specifications/frontend/routing.md"
)
SOURCE_LINE = "  - Delete article button (only shown to article's author)"
OMITTED_SPAN = " (only shown to article's author)"

INSTRUMENT_SHA256 = "526a2aee0264ac81e4c318ad6b9c58d968113bae7dc41d776d40b3500112434e"
QUALIFICATION_MANIFEST_SHA256 = (
    "cf5baf358bc64914f16e1023eb48f34d73c9034127d9b02079dcfe8f4006a820"
)
CI_ARTIFACT_ARCHIVE_SHA256 = (
    "2b2b301f21838d515e2ea56636425d0c50f81ae14d73b7f0ba607b9890b368d8"
)
LICENSE_PATH = "data/criteria-expansion/sources/realworld/LICENSE"
LICENSE_SHA256 = "a999311c4ccfecf18b7c7beb7a7a31682bb009839ab3827164fa2f8c333fc9dd"
LICENSE_URL = (
    "https://raw.githubusercontent.com/realworld-apps/realworld/"
    f"{SOURCE_REVISION}/LICENSE"
)
REVIEWER_ID = "codex-agent-independent-admission-review-20260925"
REVIEW_DECISION = "approved_for_execution-freeze_preparation"

COMMON_INTERFACE = """Implementation interface:
Implement one self-contained HTML page using vanilla JavaScript with no external resources. Consume window.initialState exactly as supplied with this shape: window.initialState = { viewer: { username: string }, article: { slug: string, title: string, body: string, author: { username: string } } }. Render the supplied article at the fixed route /article/bounded-ui-case using the supplied title and body. Render the article author's username as visible text in an element matching [rel~="author"]. If you implement Delete Article, expose it as an accessible button with the exact accessible name Delete Article. Choose the layout, styling, and internal data representation. Return only the raw HTML artifact.
"""


def sha256_text(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def json_bytes(value: object) -> bytes:
    return (json.dumps(value, indent=2, sort_keys=True) + "\n").encode("utf-8")


def variants() -> dict[str, str]:
    return {
        "A": "Delete article button (only shown to article's author)",
        "B": "Display the Delete article button only to the article's author.",
        "C": "Delete article button",
    }


def compose_request(requirement: str, common_interface: str = COMMON_INTERFACE) -> str:
    return (
        "Build the browser application described below.\n\n"
        f"Requirement:\n{requirement}\n\n{common_interface}"
    )


def build_prompt_bundle() -> dict:
    values = variants()
    requests = {arm: compose_request(values[arm]) for arm in ARMS}
    return {
        "schema_version": "realworld-author-ui-prompts/v1",
        "status": REVIEW_DECISION,
        "variants": values,
        "omission": {
            "text": OMITTED_SPAN,
            "start": values["A"].index(OMITTED_SPAN),
            "end": values["A"].index(OMITTED_SPAN) + len(OMITTED_SPAN),
            "coordinate_system": "zero-based Unicode code points; end exclusive",
        },
        "common_interface": COMMON_INTERFACE,
        "common_interface_sha256": sha256_text(COMMON_INTERFACE),
        "requests": requests,
        "request_text_sha256": {
            arm: sha256_text(requests[arm]) for arm in ARMS
        },
    }


def build_schedule(seed: int = SEED) -> list[dict]:
    if type(seed) is not int:
        raise ValueError("integer seed required")
    rows = []
    for model in MODELS:
        for replication in REPETITIONS:
            for arm in ARMS:
                identity = json.dumps(
                    ["realworld-article-author", model, replication, arm, seed],
                    separators=(",", ":"),
                )
                slot_id = "rw-" + hashlib.sha256(identity.encode("utf-8")).hexdigest()[:24]
                rows.append(
                    {
                        "slot_id": slot_id,
                        "model": model,
                        "replication": replication,
                        "arm": arm,
                    }
                )
    random.Random(seed).shuffle(rows)
    return rows


def build_review_record() -> dict:
    bundle = build_prompt_bundle()
    return {
        "schema_version": "realworld-author-ui-admission-review/v1",
        "decision": REVIEW_DECISION,
        "reviewer_id": REVIEWER_ID,
        "review_date": "2026-09-25",
        "human_approvals": 0,
        "reviewed": {
            "source_manipulation": "approved",
            "common_interface": "approved",
            "schedule": "approved",
        },
        "reviewed_evidence": {
            "source_sha256": SOURCE_SHA256,
            "license_sha256": LICENSE_SHA256,
            "instrument_sha256": INSTRUMENT_SHA256,
            "qualification_manifest_sha256": QUALIFICATION_MANIFEST_SHA256,
            "ci_artifact_archive_sha256": CI_ARTIFACT_ARCHIVE_SHA256,
            "common_interface_sha256": bundle["common_interface_sha256"],
            "request_text_sha256": bundle["request_text_sha256"],
            "schedule_sha256": sha256_bytes(json_bytes(build_schedule())),
        },
        "scope": "visibility of the Delete Article button",
        "limits": [
            "button click behavior is not evaluated",
            "backend authorization is not evaluated",
            "article deletion is not evaluated",
            "collector executable and runtime are not frozen",
            "provider dispatch is not authorized",
            "no experimental result or H1/H2 inference exists",
        ],
        "leakage_risk": {
            "status": "accepted_bounded_residual_risk",
            "shared_across_arms": True,
            "description": (
                "The common interface reveals viewer and article-author identities, "
                "the author relation, and Delete Article accessibility. These feasibility "
                "cues are byte-identical across arms and disclose no expected ownership verdict."
            ),
        },
    }


def build_admission_package() -> dict:
    review = build_review_record()
    return {
        "schema_version": "realworld-author-ui-admission/v1",
        "stage": "approved_pre_execution_freeze",
        "endpoint_admission": "admitted_bounded_exploratory_endpoint",
        "freeze_status": "prompts_and_bounded_endpoint_frozen_not_execution_ready",
        "review": {
            "decision": review["decision"],
            "reviewer_id": review["reviewer_id"],
            "evidence_path": "independent-review.json",
            "evidence_sha256": sha256_bytes(json_bytes(review)),
        },
        "human_approvals": 0,
        "model_calls": 0,
        "automatic_dispatch_allowed": False,
        "execution_configuration_frozen": False,
        "source": {
            "repository": "realworld-apps/realworld",
            "revision": SOURCE_REVISION,
            "upstream_path": "docs/src/content/docs/specifications/frontend/routing.md",
            "preserved_path": SOURCE_PATH,
            "url": SOURCE_URL,
            "sha256": SOURCE_SHA256,
            "exact_line": SOURCE_LINE,
            "slice": variants()["A"],
        },
        "rights": {
            "license": "MIT",
            "path": LICENSE_PATH,
            "sha256": LICENSE_SHA256,
            "url": LICENSE_URL,
            "revision": SOURCE_REVISION,
        },
        "instrument": {
            "instrument_sha256": INSTRUMENT_SHA256,
            "qualification_manifest_sha256": QUALIFICATION_MANIFEST_SHA256,
            "ci_artifact_archive_sha256": CI_ARTIFACT_ARCHIVE_SHA256,
            "qualification_scope": "authorship-conditioned perceptibility in four crossed browser contexts",
        },
        "scope": {
            "included": "visibility of the Delete Article button",
            "excluded": [
                "button click behavior",
                "backend authorization",
                "article deletion",
            ],
        },
        "claims": {
            "h1_supported": False,
            "h2_supported": False,
            "experimental_outcome": False,
        },
        "seed": SEED,
        "models": list(MODELS),
        "repetitions": list(REPETITIONS),
        "planned_slots": 18,
        "prompt_bundle": build_prompt_bundle(),
        "schedule": build_schedule(),
        "remaining_execution_requirements": [
            "freeze collector executable, configuration, runtime, and per-request isolation",
            "verify capacity and custody before any provider dispatch",
        ],
    }


def validate_admission_package(package: dict) -> dict:
    if not isinstance(package, dict):
        raise ValueError("admission object required")
    expected = build_admission_package()
    if (
        package.get("endpoint_admission")
        != "admitted_bounded_exploratory_endpoint"
        or package.get("freeze_status")
        != "prompts_and_bounded_endpoint_frozen_not_execution_ready"
    ):
        raise ValueError("admission status drift")
    expected_review = expected["review"]
    if package.get("review") != expected_review:
        raise ValueError("independent review state drift")
    review_hash = package.get("review", {}).get("evidence_sha256")
    if (
        not isinstance(review_hash, str)
        or not re.fullmatch(r"[0-9a-f]{64}", review_hash)
        or review_hash != sha256_bytes(json_bytes(build_review_record()))
    ):
        raise ValueError("approved review evidence hash invalid")
    if package.get("human_approvals") != 0:
        raise ValueError("human approval count drift")
    source = package.get("source", {})
    if (
        source.get("sha256") != SOURCE_SHA256
        or source.get("revision") != SOURCE_REVISION
        or source.get("preserved_path") != SOURCE_PATH
        or source.get("slice") != variants()["A"]
    ):
        raise ValueError("source custody drift")
    instrument = package.get("instrument", {})
    if instrument != expected["instrument"]:
        raise ValueError("instrument custody drift")
    if package.get("rights") != expected["rights"]:
        raise ValueError("rights custody drift")
    bundle = package.get("prompt_bundle", {})
    expected_bundle = build_prompt_bundle()
    if bundle != expected_bundle:
        raise ValueError("request or prompt bundle drift")
    schedule = package.get("schedule")
    if schedule != build_schedule(package.get("seed", SEED)) or len(schedule or []) != 18:
        raise ValueError("exact 18-position schedule required")
    if package.get("planned_slots") != 18:
        raise ValueError("exact 18 planned slots required")
    if (
        package.get("model_calls") != 0
        or package.get("automatic_dispatch_allowed") is not False
        or package.get("execution_configuration_frozen") is not False
    ):
        raise ValueError("admission package must remain non-executable")
    if package != expected:
        raise ValueError("admission package metadata drift")
    return package


def inventory(directory: Path, exclude: set[str] | None = None) -> dict[str, str]:
    excluded = exclude or set()
    files = {}
    for path in sorted(directory.rglob("*")):
        if path.is_file():
            relative = str(path.relative_to(directory))
            if relative not in excluded:
                files[relative] = hashlib.sha256(path.read_bytes()).hexdigest()
    return files


def verify_preserved_source() -> Path:
    source = ROOT / SOURCE_PATH
    license_path = ROOT / LICENSE_PATH
    if (
        not source.is_file()
        or hashlib.sha256(source.read_bytes()).hexdigest() != SOURCE_SHA256
        or source.read_text(encoding="utf-8").splitlines().count(SOURCE_LINE) != 1
    ):
        raise ValueError("preserved source missing or changed")
    if (
        not license_path.is_file()
        or hashlib.sha256(license_path.read_bytes()).hexdigest() != LICENSE_SHA256
    ):
        raise ValueError("preserved license missing or changed")
    return source


def materialize(destination: Path) -> dict:
    verify_preserved_source()
    destination.mkdir(parents=True, exist_ok=False)
    package = validate_admission_package(build_admission_package())
    (destination / "independent-review.json").write_bytes(
        json_bytes(build_review_record())
    )
    request_hashes = {}
    for row in package["schedule"]:
        request = {"prompt": package["prompt_bundle"]["requests"][row["arm"]]}
        request_path = destination / "requests" / f"{row['slot_id']}.json"
        request_path.parent.mkdir(parents=True, exist_ok=True)
        request_path.write_bytes(json_bytes(request))
        request_hashes[row["slot_id"]] = hashlib.sha256(request_path.read_bytes()).hexdigest()
    manifest = {
        **package,
        "provider_calls": 0,
        "request_sha256": request_hashes,
    }
    (destination / "manifest.json").write_bytes(json_bytes(manifest))
    (destination / "prompt-bundle.json").write_bytes(json_bytes(package["prompt_bundle"]))
    (destination / "schedule.json").write_bytes(json_bytes(package["schedule"]))
    (destination / "receipt.json").write_bytes(
        json_bytes(inventory(destination, exclude={"receipt.json"}))
    )
    return manifest


def validate_materialized(directory: Path) -> dict:
    manifest = json.loads((directory / "manifest.json").read_text(encoding="utf-8"))
    review_path = directory / manifest.get("review", {}).get("evidence_path", "")
    if (
        not review_path.is_file()
        or sha256_bytes(review_path.read_bytes())
        != manifest.get("review", {}).get("evidence_sha256")
        or review_path.read_bytes() != json_bytes(build_review_record())
    ):
        raise ValueError("approved review evidence drift")
    canonical_bundle = build_prompt_bundle()
    if (directory / "prompt-bundle.json").read_bytes() != json_bytes(canonical_bundle):
        raise ValueError("canonical prompt bundle drift")
    canonical_schedule = build_schedule()
    if (directory / "schedule.json").read_bytes() != json_bytes(canonical_schedule):
        raise ValueError("canonical schedule drift")
    core = {
        key: value
        for key, value in manifest.items()
        if key not in {"provider_calls", "request_sha256"}
    }
    validate_admission_package(core)
    if manifest.get("provider_calls") != 0:
        raise ValueError("provider call count drift")
    schedule = manifest["schedule"]
    expected_names = {row["slot_id"] + ".json" for row in schedule}
    requests = directory / "requests"
    if {path.name for path in requests.iterdir() if path.is_file()} != expected_names:
        raise ValueError("request inventory drift")
    for row in schedule:
        request_path = requests / f"{row['slot_id']}.json"
        expected_request = json_bytes(
            {"prompt": canonical_bundle["requests"][row["arm"]]}
        )
        if request_path.read_bytes() != expected_request:
            raise ValueError("canonical request drift")
        if (
            sha256_bytes(request_path.read_bytes())
            != manifest.get("request_sha256", {}).get(row["slot_id"])
        ):
            raise ValueError("request hash drift")
    receipt = json.loads((directory / "receipt.json").read_text(encoding="utf-8"))
    if receipt != inventory(directory, exclude={"receipt.json"}):
        raise ValueError("receipt inventory drift")
    return manifest


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    manifest = materialize(args.output)
    print(json.dumps({"output": str(args.output), "planned_slots": manifest["planned_slots"]}))


if __name__ == "__main__":
    main()
