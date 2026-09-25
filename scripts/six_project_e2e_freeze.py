"""Freeze four source-grounded browser cases that extend the pilot to six projects.

This module performs no provider calls and observes no experimental outcomes.
It binds exact sources, A/B/C prompts, and a balanced 72-slot schedule before
the browser instruments or generated artifacts are inspected.
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
PROJECTS = ("paperless-ngx", "kanboard", "nextcloud", "openproject")
MODELS = ("gpt-5.6-luna", "gpt-5.6-sol")
REPETITIONS = (1, 2, 3)
SEED = 20260925
OPAQUE_SLOT = re.compile(r"e2e-[0-9a-f]{24}")


def _sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def _json_bytes(value: object) -> bytes:
    return (json.dumps(value, indent=2, sort_keys=True) + "\n").encode("utf-8")


def _case(
    *,
    project_id: str,
    requirement: str,
    rewrite: str,
    omission: str,
    source: dict,
    rights: dict,
    common_interface: str,
    target: str,
    non_targets: list[str],
) -> dict:
    if requirement.count(omission) != 1:
        raise ValueError(f"{project_id}: omission must occur exactly once")
    return {
        "project_id": project_id,
        "variants": {
            "A": requirement,
            "B": rewrite,
            "C": requirement.replace(omission, "", 1),
        },
        "omission": {
            "text": omission,
            "start": requirement.index(omission),
            "end": requirement.index(omission) + len(omission),
            "coordinate_system": "zero-based Unicode code points; end exclusive",
        },
        "source": source,
        "rights": rights,
        "common_interface": common_interface,
        "endpoint": {
            "layer": "browser_e2e",
            "target": target,
            "non_targets": non_targets,
            "invalid_if": "the required interface cannot be exercised",
            "unknown_if": "the rendered state cannot be classified without guessing",
        },
    }


def case_definitions() -> dict[str, dict]:
    paperless_a = (
        "The dashboard has a button to upload documents to paperless or you\n"
        "can simply drag a file anywhere into the app to initiate the consumption\n"
        "process."
    )
    paperless_omission = " or you\ncan simply drag a file anywhere into the app"
    kanboard_a = (
        "When a task is closed, it is hidden from the board.\n\n"
        "However, you can always access the list of closed tasks by using the query "
        "status:closed in any search form or by choosing Closed tasks from the filter "
        "dropdown.\n\n"
        "Note: When you close a task, all incomplete subtasks will be changed to the status \"Done.\""
    )
    kanboard_omission = (
        "\n\nNote: When you close a task, all incomplete subtasks will be changed to the status \"Done.\""
    )
    nextcloud_a = (
        "When you delete a file or folder in Nextcloud, it is normally moved to the\n"
        "trash bin instead of being deleted immediately. This allows you to restore it\n"
        "later."
    )
    nextcloud_omission = (
        " This allows you to restore it\nlater."
    )
    openproject_a = (
        "When none of the three fields (% Complete, Work, or Remaining Work) have values "
        "set, the field you fill in first will determine how the others are calculated:\n\n"
        "- If you enter Work only, Remaining Work will automatically match the Work value, "
        "and % Complete will be set to 0%."
    )
    openproject_omission = "Remaining Work will automatically match the Work value, and "

    return {
        "paperless-ngx": _case(
            project_id="paperless-ngx",
            requirement=paperless_a,
            rewrite=(
                "The Paperless-ngx dashboard lets users start document consumption either "
                "with its upload button or by dragging a file anywhere over the app."
            ),
            omission=paperless_omission,
            source={
                "repository": "paperless-ngx/paperless-ngx",
                "revision": "4f777d7438378fe0b6dcc9f140a7eb469f9f0b0b",
                "upstream_path": "docs/usage.md",
                "blob_sha": "12cdaa921cc4fad9edbad5e9bf6c4ea9279d9c6f",
                "path": "data/e2e-six-projects/sources/paperless-ngx/usage.md",
                "sha256": "78fc960ff99fb102d11e9db2830f9e879f4894822ff8f18684e972ffe04bd9dd",
                "exact_excerpt": paperless_a,
                "locator": "Web UI Upload",
            },
            rights={
                "license": "GPL-3.0",
                "upstream_path": "LICENSE",
                "blob_sha": "733c072369ca77331f392c40da7404c85c36542c",
                "path": "data/e2e-six-projects/sources/paperless-ngx/LICENSE",
                "sha256": "d62f065830aa3739cc031156b9690805c7b2e811b4a178c8b4acd8725d561c94",
            },
            common_interface=(
                "Implementation interface:\nImplement one self-contained HTML page using vanilla "
                "JavaScript with no external resources. Render a document dashboard. Consume "
                "window.initialState.documents, whose entries have id and title. Render document rows "
                "with data-document-id and an accessible Upload document button. When a new document "
                "is accepted, render its supplied title as a document row. Return only raw HTML.\n"
            ),
            target="Dropping a file over the rendered app creates a visible document row.",
            non_targets=["existing document remains visible", "upload button remains usable"],
        ),
        "kanboard": _case(
            project_id="kanboard",
            requirement=kanboard_a,
            rewrite=(
                "Closing a task removes it from the board but keeps it available in the Closed tasks "
                "view. Closing also changes every unfinished subtask to Done."
            ),
            omission=kanboard_omission,
            source={
                "repository": "kanboard/documentation",
                "revision": "4455fd04fb48ed42817fc99402d4c1fb3bde1c0d",
                "upstream_path": "content/en/v1/user/tasks.md",
                "blob_sha": "4f1eb3c75fb8cddb433851afbe4afa3b008930c8",
                "path": "data/e2e-six-projects/sources/kanboard/tasks.md",
                "sha256": "281c39c6e4c5a9c071d28bf01d08d2544929942977eeff4ae53ce0716510f081",
                "exact_excerpt": "Note: When you close a task, all incomplete subtasks will be changed to the status \"Done.\"",
                "locator": "Closing Tasks",
            },
            rights={
                "license": "MIT",
                "upstream_path": "LICENSE",
                "blob_sha": "1f7e971d90c79129a19992dc197f0a49bf322aae",
                "path": "data/e2e-six-projects/sources/kanboard/LICENSE",
                "sha256": "b14398501e47b08042d57b3ef7994cb2aab8d353a87d928a2395b7aea7c8ca2a",
            },
            common_interface=(
                "Implementation interface:\nImplement one self-contained HTML page using vanilla "
                "JavaScript with no external resources. Consume window.initialState.tasks; each task "
                "has id, title, closed, and subtasks with id, title, and status strings. "
                "Provide accessible Board and Closed tasks view buttons, a Close task button in each open "
                "task, task containers with data-task-id, and subtask rows with data-subtask-id and a "
                "visible status. Return only raw HTML.\n"
            ),
            target="After closing, each formerly unfinished subtask is visibly Done in Closed tasks.",
            non_targets=["closed task leaves Board", "closed task appears in Closed tasks", "unrelated task is unchanged"],
        ),
        "nextcloud": _case(
            project_id="nextcloud",
            requirement=nextcloud_a,
            rewrite=(
                "Deleting a Nextcloud file moves it to the trash rather than erasing it immediately, "
                "so it can be restored later."
            ),
            omission=nextcloud_omission,
            source={
                "repository": "nextcloud/documentation",
                "revision": "121cb83001db7722870050b7980aea35fab82141",
                "upstream_path": "user_manual/files/deleted_file_management.rst",
                "blob_sha": "2dd0da71dc2a848d6000579e329cd135d0691bea",
                "path": "data/e2e-six-projects/sources/nextcloud/deleted_file_management.rst",
                "sha256": "9e8218c16b5f8e558cb535834271e9a02fd27ac733c7f45bba0126f62e67106f",
                "exact_excerpt": "When you delete a file or folder in Nextcloud, it is normally moved to the\ntrash bin instead of being deleted immediately. This allows you to restore it\nlater.",
                "locator": "Deleted files",
            },
            rights={
                "license": "CC-BY-3.0",
                "upstream_path": "COPYING",
                "blob_sha": "1d658d6d37633decaec4382fcc8a2c05ac21bdf9",
                "path": "data/e2e-six-projects/sources/nextcloud/COPYING",
                "sha256": "5138a74ac20f2965d97b2a9c35219ca74e24f4a93618b33f0e36e4b3c7873197",
            },
            common_interface=(
                "Implementation interface:\nImplement one self-contained HTML page using vanilla "
                "JavaScript with no external resources. Consume window.initialState.files with id and "
                "name. Provide accessible All files and Deleted files view buttons, file rows with "
                "data-file-id, and an accessible Delete button for each active file. The two views must "
                "be operable without page reload. Return only raw HTML.\n"
            ),
            target="A file in Deleted files can be restored and becomes visible in All files again.",
            non_targets=["deleted file leaves All files", "deleted file appears in Deleted files", "unrelated active file remains"],
        ),
        "openproject": _case(
            project_id="openproject",
            requirement=openproject_a,
            rewrite=(
                "With Work, Remaining Work, and % Complete initially empty, entering only Work sets "
                "Remaining Work to the same value and sets % Complete to 0%."
            ),
            omission=openproject_omission,
            source={
                "repository": "opf/openproject",
                "revision": "de051918ba8771d5415c172cc81bcd49f7d10472",
                "upstream_path": "docs/user-guide/time-and-costs/progress-tracking/README.md",
                "blob_sha": "1da0385336c3c2601ad76941a3969c20b1ef9ce8",
                "path": "data/e2e-six-projects/sources/openproject/progress-tracking.md",
                "sha256": "9aec062470806acf90d8dec1eab6f90d61377ec1ef20f7217fe5c3ed89ee27f9",
                "exact_excerpt": "If you enter Work only, Remaining Work will automatically match the Work value, and % Complete will be set to 0%.",
                "locator": "Calculation logic / When no field is set",
            },
            rights={
                "license": "GPL-3.0",
                "upstream_path": "LICENSE",
                "blob_sha": "94a9ed024d3859793618152ea559a168bbcbb5e2",
                "path": "data/e2e-six-projects/sources/openproject/LICENSE",
                "sha256": "8ceb4b9ee5adedde47b31e975c1d90c73ad27b6b165a1dcd80c7c545eb65b903",
            },
            common_interface=(
                "Implementation interface:\nImplement one self-contained HTML page using vanilla "
                "JavaScript with no external resources. Render an editable work package with accessible "
                "fields named Work, Remaining Work, and % Complete plus an accessible Save button. All "
                "three fields start empty. Values must remain visible after Save. Return only raw HTML.\n"
            ),
            target="Entering only Work and saving visibly makes Remaining Work equal Work.",
            non_targets=["% Complete becomes 0%", "entered Work remains visible"],
        ),
    }


def requests_for(case: dict) -> dict[str, str]:
    return {
        arm: (
            "Build the browser application described below.\n\nRequirement:\n"
            + case["variants"][arm]
            + "\n\n"
            + case["common_interface"]
        )
        for arm in ARMS
    }


def build_schedule(seed: int = SEED) -> list[dict]:
    rows = []
    for project in PROJECTS:
        for model in MODELS:
            for repetition in REPETITIONS:
                for arm in ARMS:
                    identity = json.dumps(
                        [project, model, repetition, arm, seed], separators=(",", ":")
                    )
                    rows.append(
                        {
                            "slot_id": "e2e-" + hashlib.sha256(identity.encode()).hexdigest()[:24],
                            "project_id": project,
                            "model": model,
                            "replication": repetition,
                            "arm": arm,
                        }
                    )
    random.Random(seed).shuffle(rows)
    return rows


def build_manifest() -> dict:
    cases = case_definitions()
    return {
        "schema_version": "six-project-e2e-freeze/v1",
        "stage": "pre_generation_pre_outcome",
        "selected_before_outcomes": True,
        "outcomes_observed": False,
        "provider_calls": 0,
        "automatic_dispatch_allowed": False,
        "seed": SEED,
        "models": list(MODELS),
        "repetitions": list(REPETITIONS),
        "new_projects": list(PROJECTS),
        "projects_after_completion": 6,
        "planned_slots": 72,
        "oracle_qualification": {
            "qualified": True,
            "controls": 20,
            "image_id": "sha256:529bf59afccb0572970b728de7235f0f0130da00248fab232121cd2c3eef60df",
            "qualification_path": "data/e2e-six-projects/oracle-qualification-20260925/qualification.json",
            "qualification_sha256": "328cb5b05e293466895e871d41cb3074dc56a274aae91337ca06a21ea6c14b94",
            "receipt_path": "data/e2e-six-projects/oracle-qualification-20260925/receipt.json",
            "receipt_sha256": "d1c1e6ec7b2e5044c4beb3aee1f07d3acb32ce4b7da731fd854944801f698348",
        },
        "cases": cases,
        "schedule": build_schedule(),
        "claims": {
            "pilot": True,
            "confirmatory": False,
            "h1_confirmed": False,
            "h2_evaluated": False,
        },
    }


def validate_manifest(manifest: dict) -> dict:
    expected = build_manifest()
    if manifest.get("schedule") != expected["schedule"]:
        raise ValueError("schedule drift")
    if manifest != expected:
        raise ValueError("canonical freeze drift")
    for case in manifest["cases"].values():
        source = ROOT / case["source"]["path"]
        license_path = ROOT / case["rights"]["path"]
        if not source.is_file() or _sha256_bytes(source.read_bytes()) != case["source"]["sha256"]:
            raise ValueError("source custody mismatch")
        if not license_path.is_file() or _sha256_bytes(license_path.read_bytes()) != case["rights"]["sha256"]:
            raise ValueError("rights custody mismatch")
    qualification = manifest["oracle_qualification"]
    for path_key, hash_key in (
        ("qualification_path", "qualification_sha256"),
        ("receipt_path", "receipt_sha256"),
    ):
        evidence = ROOT / qualification[path_key]
        if not evidence.is_file() or _sha256_bytes(evidence.read_bytes()) != qualification[hash_key]:
            raise ValueError("oracle qualification custody mismatch")
    evidence_root = (ROOT / qualification["receipt_path"]).parent
    receipt = json.loads((ROOT / qualification["receipt_path"]).read_text(encoding="utf-8"))
    observed = json.loads((ROOT / qualification["qualification_path"]).read_text(encoding="utf-8"))
    expected_pairs = {(project, mode) for project in PROJECTS for mode in (
        "reference", "alternative", "target-mutant", "non-target-mutant", "interface-ambiguous"
    )}
    if (
        receipt.get("schema_version") != "four-project-ui-public-bundle/v1"
        or receipt.get("qualified") is not True
        or receipt.get("image_id") != qualification["image_id"]
        or not isinstance(receipt.get("files"), dict)
        or observed.get("schema_version") != "four-project-ui-qualification/v1"
        or observed.get("qualified") is not True
        or observed.get("controls") != 20
        or observed.get("project_count") != 4
        or observed.get("image_id") != qualification["image_id"]
        or not isinstance(observed.get("cases"), list)
        or len(observed["cases"]) != 20
        or {(row.get("project_id"), row.get("mode")) for row in observed["cases"]} != expected_pairs
        or any(row.get("expected") != row.get("observed") for row in observed["cases"])
    ):
        raise ValueError("oracle qualification semantics mismatch")
    actual_files = {
        path.relative_to(evidence_root).as_posix(): _sha256_bytes(path.read_bytes())
        for path in sorted(evidence_root.rglob("*"))
        if path.is_file() and path.name != "receipt.json"
    }
    if receipt["files"] != actual_files:
        raise ValueError("oracle qualification inventory mismatch")
    return manifest


def materialize(output: Path) -> dict:
    if output.exists():
        raise FileExistsError(output)
    output.mkdir(parents=True)
    request_dir = output / "requests"
    request_dir.mkdir()
    manifest = validate_manifest(build_manifest())
    request_hashes = {}
    for row in manifest["schedule"]:
        case = manifest["cases"][row["project_id"]]
        payload = {"prompt": requests_for(case)[row["arm"]]}
        path = request_dir / f"{row['slot_id']}.json"
        path.write_bytes(_json_bytes(payload))
        request_hashes[row["slot_id"]] = _sha256_bytes(path.read_bytes())
    manifest = dict(manifest)
    manifest["request_sha256"] = request_hashes
    (output / "manifest.json").write_bytes(_json_bytes(manifest))
    return manifest


def validate_materialized(output: Path) -> dict:
    manifest = json.loads((output / "manifest.json").read_text(encoding="utf-8"))
    canonical = dict(manifest)
    request_hashes = canonical.pop("request_sha256", None)
    validate_manifest(canonical)
    if not isinstance(request_hashes, dict) or len(request_hashes) != 72:
        raise ValueError("request inventory invalid")
    for row in canonical["schedule"]:
        path = output / "requests" / f"{row['slot_id']}.json"
        if not path.is_file() or _sha256_bytes(path.read_bytes()) != request_hashes.get(row["slot_id"]):
            raise ValueError("request custody mismatch")
        expected = {"prompt": requests_for(canonical["cases"][row["project_id"]])[row["arm"]]}
        if json.loads(path.read_text(encoding="utf-8")) != expected:
            raise ValueError("request content drift")
    return manifest


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    materialize(args.output)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
