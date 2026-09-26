"""Prospectively freeze one Kanboard duplicate-title browser pilot."""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import random
import sys

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts.persistence_collection import hash_file

SEED = 2026092602
MODELS = ("gpt-5.6-luna", "gpt-5.6-sol")
ARMS = ("A", "B", "C")
REPETITIONS = (1, 2, 3)
MARKER = "/* MODEL_BEHAVIOR */"
SOURCE = "data/e2e-six-projects/sources/kanboard/tasks.md"
LICENSE = "data/e2e-six-projects/sources/kanboard/LICENSE"
PANEL = "data/e2e-multi-obligation/third-candidate-revision-panel-20260925.json"
REVIEW = "data/e2e-kanboard-duplicate-title/prompt-review-20260926"
FIXTURE = "eval/fixtures/kanboard-duplicate-title-pilot"
IMAGE = "sha256:00d1265095773b7f8a12aa73e81d0bab75563cbd672dd0b5d91783ea1b6d4400"
QUALIFICATION = "data/e2e-kanboard-duplicate-title/oracle-qualification-20260926"

REQUIREMENTS = {
    "A": "In the task view, choosing Duplicate creates a distinct new task in the same project with the source task's visible title. Preserve the source and an unrelated task.",
    "B": "When a user duplicates a task within its project, the copied task must be a separate task and display the original task title. The original and an unrelated task remain unchanged.",
    "C": "In the task view, choosing Duplicate creates a distinct new task in the same project. Preserve the source and an unrelated task.",
}


def encoded(value: object) -> bytes:
    return (json.dumps(value, sort_keys=True, indent=2, ensure_ascii=False) + "\n").encode()


def prompt(arm: str) -> str:
    scaffold = (ROOT / FIXTURE / "page.html").read_text()
    if scaffold.count(MARKER) != 1:
        raise ValueError("one behavior marker required")
    return (
        "Implement only the requirement in the frozen browser page. Replace the single "
        "/* MODEL_BEHAVIOR */ marker with vanilla JavaScript statements using the provided "
        "app API. Do not change any other byte of the page. Return only the complete HTML page.\n\n"
        "Requirement:\n" + REQUIREMENTS[arm] + "\n\nFrozen page:\n" + scaffold
    )


def schedule() -> list[dict]:
    rows = []
    for model in MODELS:
        for repetition in REPETITIONS:
            for arm in ARMS:
                identity = encoded(["kanboard-duplicate-preserves-title", model, repetition, arm, SEED])
                rows.append({
                    "slot_id": "duplicate-title-" + hashlib.sha256(identity).hexdigest()[:24],
                    "intent_id": "kanboard-duplicate-preserves-title", "project_id": "kanboard",
                    "model": model, "replication": repetition, "arm": arm,
                })
    random.Random(SEED).shuffle(rows)
    return rows


def qualification() -> dict:
    root = ROOT / QUALIFICATION
    evidence = json.loads((root / "qualification.json").read_text())
    receipt = json.loads((root / "receipt.json").read_text())
    inventory = {
        p.relative_to(root).as_posix(): hash_file(p)
        for p in sorted(root.rglob("*")) if p.is_file() and p.name != "receipt.json"
    }
    expected = {
        "reference": "pass", "alternative": "pass",
        "target-mutant": "target_only_failure", "non-target-mutant": "non_target_only_failure",
        "duplicate-identity": "interface_error", "missing-behavior": "interface_error",
        "precreated-duplicate": "interface_error",
        "script-error": "browser_error",
    }
    if (
        evidence.get("schema_version") != "kanboard-duplicate-title-qualification/v1"
        or evidence.get("qualified") is not True or evidence.get("image_id") != IMAGE
        or evidence.get("controls") != 8
        or evidence.get("source_scaffold_sha256") != hash_file(ROOT / FIXTURE / "page.html")
        or evidence.get("runner_sha256") != hash_file(ROOT / FIXTURE / "runner.cjs")
        or evidence.get("qualifier_sha256") != hash_file(ROOT / FIXTURE / "qualify.py")
        or {r.get("mode"): (r.get("expected"), r.get("observed")) for r in evidence.get("cases", [])}
        != {key: (value, value) for key, value in expected.items()}
        or receipt.get("schema_version") != "kanboard-duplicate-title-public-receipt/v1"
        or receipt.get("files") != inventory
    ):
        raise ValueError("oracle qualification mismatch")
    return {"path": QUALIFICATION, "qualification_sha256": hash_file(root / "qualification.json"),
            "receipt_sha256": hash_file(root / "receipt.json"), "image_id": IMAGE}


def manifest() -> dict:
    source = (ROOT / SOURCE).read_text()
    if "A new task will be created with the same properties as the original." not in source or "- `title`" not in source:
        raise ValueError("source obligation missing")
    panel = json.loads((ROOT / PANEL).read_text())
    candidates = [row for row in panel.get("revisions", [])
                  if row.get("candidate_id") == "kanboard-duplicate-preserves-title"]
    if (
        len(candidates) != 1
        or candidates[0].get("project_id") != "kanboard"
        or candidates[0].get("source", {}).get("path") != SOURCE
        or candidates[0].get("source", {}).get("sha256") != hash_file(ROOT / SOURCE)
        or "kanboard-duplicate-preserves-title" not in panel.get("newly_eligible_candidate_ids", [])
    ):
        raise ValueError("prior panel mapping missing")
    review = json.loads((ROOT / REVIEW / "review.json").read_text())
    if (
        review.get("schema_version") != "kanboard-duplicate-title-prompt-review/v1"
        or review.get("stage") != "pre_generation" or review.get("unanimous") is not True
        or review.get("human_approvals") != 0
        or review.get("arms_sha256") != hashlib.sha256(encoded(REQUIREMENTS)).hexdigest()
        or review.get("scaffold_sha256") != hash_file(ROOT / FIXTURE / "page.html")
        or len(review.get("reviewers", [])) != 3
        or {row.get("model") for row in review["reviewers"]} != {"gpt-6-astra", "gpt-6-sol", "gpt-6-luna"}
        or any(row.get("verdict") != "ACCEPT" or row.get("response_sha256") != hash_file(ROOT / REVIEW / (row["model"] + ".txt")) for row in review["reviewers"])
    ):
        raise ValueError("prompt review mismatch")
    paths = [SOURCE, LICENSE, PANEL, f"{REVIEW}/review.json",
        *(f"{REVIEW}/{model}.txt" for model in ("gpt-6-astra", "gpt-6-sol", "gpt-6-luna")),
        *(f"{FIXTURE}/{name}" for name in ("page.html", "runner.cjs", "qualify.py"))]
    return {
        "schema_version": "kanboard-duplicate-title-freeze/v1", "status": "pre_generation_exploratory",
        "case_id": "kanboard-duplicate-preserves-title", "project_id": "kanboard",
        "source_revision": "4455fd04fb48ed42817fc99402d4c1fb3bde1c0d",
        "source_obligation": "A new task will be created with the same properties as the original; title is a listed duplicated property.",
        "source_and_runtime_sha256": {path: hash_file(ROOT / path) for path in paths},
        "reconstruction": True, "removed_in_C": "duplicate's visible title equals the source task's visible title",
        "requirements": REQUIREMENTS, "seed": SEED, "models": MODELS,
        "repetitions": REPETITIONS, "arms": ARMS, "schedule": schedule(),
        "planned_slots": 18, "image_id": IMAGE, "qualification": qualification(),
        "provider": "Codex CLI saved ChatGPT subscription; no API key fallback",
        "reasoning_effort": "low", "timeout_seconds": 240,
        "concurrency": 1, "retry_policy": "no_retry_no_resume_no_repair",
        "generation_before_browser": True, "artifact_limit_bytes": 200000,
        "endpoint": "browser target failure after Duplicate with distinct same-project task and source/control preserved",
        "claims": {"confirmatory": False, "h1_confirmed": False, "h2_evaluated": False},
    }


def materialize(output: Path) -> dict:
    if output.exists():
        raise FileExistsError(output)
    result = manifest()
    output.mkdir(parents=True)
    requests = output / "requests"
    requests.mkdir()
    hashes = {}
    for row in result["schedule"]:
        name = row["slot_id"] + ".json"
        data = encoded({"prompt": prompt(row["arm"])})
        (requests / name).write_bytes(data)
        hashes[row["slot_id"]] = hashlib.sha256(data).hexdigest()
    result["request_sha256"] = hashes
    (output / "manifest.json").write_bytes(encoded(result))
    return result


def validate(output: Path) -> dict:
    observed = json.loads((output / "manifest.json").read_text())
    expected = manifest()
    hashes = observed.pop("request_sha256", None)
    if observed != json.loads(encoded(expected)):
        raise ValueError("frozen manifest drift")
    if not isinstance(hashes, dict) or len(hashes) != 18:
        raise ValueError("request inventory invalid")
    for row in expected["schedule"]:
        data = encoded({"prompt": prompt(row["arm"])})
        path = output / "requests" / (row["slot_id"] + ".json")
        if path.read_bytes() != data or hashlib.sha256(data).hexdigest() != hashes[row["slot_id"]]:
            raise ValueError("request drift")
    return {**observed, "request_sha256": hashes}


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()
    materialize(args.output)
