"""Freeze the post-outcome fixed-scaffold successor without provider calls."""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import random
import re
import sys

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts import six_project_e2e_freeze as predecessor
ARMS = predecessor.ARMS
PROJECTS = ("paperless-ngx", "nextcloud", "openproject")
MODELS = predecessor.MODELS
REPETITIONS = predecessor.REPETITIONS
PLACEHOLDER = "/* MODEL_BEHAVIOR */"
SEED = 20260926
OPAQUE_SLOT = re.compile(r"successor-[0-9a-f]{24}")


def _sha256(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def _json_bytes(value: object) -> bytes:
    return (json.dumps(value, indent=2, sort_keys=True) + "\n").encode()


def case_definitions() -> dict[str, dict]:
    previous = predecessor.case_definitions()
    cases = {}
    for project in PROJECTS:
        base = previous[project]
        path = f"eval/fixtures/three-project-scaffold/{project}.html"
        raw = (ROOT / path).read_bytes()
        if raw.decode().count(PLACEHOLDER) != 1:
            raise ValueError(f"{project}: scaffold must contain one placeholder")
        cases[project] = {
            "project_id": project,
            "variants": base["variants"],
            "omission": base["omission"],
            "source": base["source"],
            "rights": base["rights"],
            "endpoint": base["endpoint"],
            "scaffold": {"path": path, "sha256": _sha256(raw)},
        }
    return cases


def requests_for(case: dict) -> dict[str, str]:
    scaffold = (ROOT / case["scaffold"]["path"]).read_text()
    instruction = (
        "Implement only the behavior required below in the frozen browser page. "
        "Replace the single /* MODEL_BEHAVIOR */ marker with vanilla JavaScript statements. "
        "Use the provided app API and do not change any other byte of the page. "
        "Return only the complete HTML page.\n\nRequirement:\n"
    )
    return {arm: instruction + case["variants"][arm] + "\n\nFrozen page:\n" + scaffold for arm in ARMS}


def build_schedule(seed: int = SEED) -> list[dict]:
    rows = []
    for project in PROJECTS:
        for model in MODELS:
            for repetition in REPETITIONS:
                for arm in ARMS:
                    identity = json.dumps([project, model, repetition, arm, seed], separators=(",", ":"))
                    rows.append({
                        "slot_id": "successor-" + hashlib.sha256(identity.encode()).hexdigest()[:24],
                        "project_id": project,
                        "model": model,
                        "replication": repetition,
                        "arm": arm,
                    })
    random.Random(seed).shuffle(rows)
    return rows


def build_manifest() -> dict:
    return {
        "schema_version": "three-project-fixed-scaffold-freeze/v1",
        "stage": "post_outcome_successor_pre_generation",
        "predecessor": "data/e2e-six-projects/results-20260925/manifest.json",
        "replaces_original_collection": False,
        "outcomes_observed_in_predecessor": True,
        "new_provider_calls": 0,
        "automatic_dispatch_allowed": False,
        "seed": SEED,
        "models": list(MODELS),
        "repetitions": list(REPETITIONS),
        "projects": list(PROJECTS),
        "planned_slots": 54,
        "oracle_qualification": {
            "qualified": True,
            "controls": 18,
            "image_id": "sha256:274868c475888f4228e376a2596e99dd7daebacccde04df5b678f7a31212e7a5",
            "qualification_path": "data/e2e-three-project-successor/oracle-qualification-20260925/qualification.json",
            "qualification_sha256": "a426cb4fa49568dc872270268b0a85e099cdce184819e81fbc39099637f1d46c",
            "receipt_path": "data/e2e-three-project-successor/oracle-qualification-20260925/receipt.json",
            "receipt_sha256": "5a002d2cacedd046458f19dc1a8c360a12f67d02efd2a27177f0a6b5781c3070",
        },
        "cases": case_definitions(),
        "schedule": build_schedule(),
        "claims": {"pilot": True, "confirmatory": False, "h1_confirmed": False, "h2_evaluated": False},
    }


def validate_manifest(manifest: dict) -> dict:
    expected = build_manifest()
    if manifest.get("schedule") != expected["schedule"]:
        raise ValueError("schedule drift")
    if manifest != expected:
        raise ValueError("canonical freeze drift")
    for case in manifest["cases"].values():
        for key in ("source", "rights"):
            path = ROOT / case[key]["path"]
            if not path.is_file() or _sha256(path.read_bytes()) != case[key]["sha256"]:
                raise ValueError(f"{key} custody mismatch")
        scaffold = ROOT / case["scaffold"]["path"]
        if not scaffold.is_file() or _sha256(scaffold.read_bytes()) != case["scaffold"]["sha256"]:
            raise ValueError("scaffold custody mismatch")
    qualification = manifest["oracle_qualification"]
    for path_key, hash_key in (("qualification_path", "qualification_sha256"), ("receipt_path", "receipt_sha256")):
        evidence = ROOT / qualification[path_key]
        if not evidence.is_file() or _sha256(evidence.read_bytes()) != qualification[hash_key]:
            raise ValueError("oracle qualification custody mismatch")
    evidence_root = (ROOT / qualification["receipt_path"]).parent
    receipt = json.loads((ROOT / qualification["receipt_path"]).read_text())
    observed = json.loads((ROOT / qualification["qualification_path"]).read_text())
    expected_pairs = {(project, mode) for project in PROJECTS for mode in (
        "reference", "alternative", "target-mutant", "non-target-mutant", "interface-ambiguous", "missing-behavior"
    )}
    if (
        receipt.get("schema_version") != "three-project-fixed-scaffold-public-bundle/v1"
        or receipt.get("qualified") is not True
        or receipt.get("image_id") != qualification["image_id"]
        or observed.get("schema_version") != "three-project-fixed-scaffold-qualification/v1"
        or observed.get("qualified") is not True
        or observed.get("controls") != 18
        or observed.get("project_count") != 3
        or observed.get("image_id") != qualification["image_id"]
        or {(row.get("project_id"), row.get("mode")) for row in observed.get("cases", [])} != expected_pairs
        or any(row.get("expected") != row.get("observed") for row in observed.get("cases", []))
    ):
        raise ValueError("oracle qualification semantics mismatch")
    actual_files = {
        path.relative_to(evidence_root).as_posix(): _sha256(path.read_bytes())
        for path in sorted(evidence_root.rglob("*"))
        if path.is_file() and path.name != "receipt.json"
    }
    if receipt.get("files") != actual_files:
        raise ValueError("oracle qualification inventory mismatch")
    return manifest


def materialize(output: Path) -> dict:
    if output.exists():
        raise FileExistsError(output)
    output.mkdir(parents=True)
    requests = output / "requests"
    requests.mkdir()
    manifest = validate_manifest(build_manifest())
    hashes = {}
    prompts = {project: requests_for(case) for project, case in manifest["cases"].items()}
    for row in manifest["schedule"]:
        path = requests / f"{row['slot_id']}.json"
        path.write_bytes(_json_bytes({"prompt": prompts[row["project_id"]][row["arm"]]}))
        hashes[row["slot_id"]] = _sha256(path.read_bytes())
    materialized = dict(manifest, request_sha256=hashes)
    (output / "manifest.json").write_bytes(_json_bytes(materialized))
    return materialized


def validate_materialized(output: Path) -> dict:
    manifest = json.loads((output / "manifest.json").read_text())
    canonical = dict(manifest)
    hashes = canonical.pop("request_sha256", None)
    validate_manifest(canonical)
    if not isinstance(hashes, dict) or len(hashes) != 54:
        raise ValueError("request inventory invalid")
    prompts = {project: requests_for(case) for project, case in canonical["cases"].items()}
    for row in canonical["schedule"]:
        path = output / "requests" / f"{row['slot_id']}.json"
        if not path.is_file() or _sha256(path.read_bytes()) != hashes.get(row["slot_id"]):
            raise ValueError("request custody mismatch")
        if json.loads(path.read_text()) != {"prompt": prompts[row["project_id"]][row["arm"]]}:
            raise ValueError("request content drift")
    return manifest


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()
    materialize(args.output)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
