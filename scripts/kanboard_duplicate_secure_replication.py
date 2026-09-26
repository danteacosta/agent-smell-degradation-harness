"""Prospective secure-origin replication of the Kanboard duplicate-title pilot."""
from __future__ import annotations

import argparse
from collections import Counter
import hashlib
import json
from pathlib import Path
import random
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from agents.codex_cli import CodexCLIProvider
from agents.providers import ProviderRequest
from scripts import kanboard_duplicate_freeze as original
from scripts.kanboard_duplicate_collect import admit, execute
from scripts.persistence_collection import hash_file, hash_inventory, put, verify_inventory

SEED = 2026092604
IMAGE = original.IMAGE
PARENT = ROOT / "data/e2e-kanboard-duplicate-title/freeze-20260926"
DIAGNOSTIC = ROOT / "data/e2e-kanboard-duplicate-title/secure-origin-diagnostic-20260926"
RUNNER = DIAGNOSTIC / "fixture/runner.cjs"
QUALIFIER = DIAGNOSTIC / "fixture/qualify.py"
QUALIFICATION = DIAGNOSTIC / "qualification/qualification.json"
QUALIFICATION_RECEIPT = DIAGNOSTIC / "receipt.json"
RUNTIME = (Path(__file__), ROOT / "agents/codex_cli.py", ROOT / "agents/providers.py",
           ROOT / "scripts/kanboard_duplicate_collect.py", ROOT / "scripts/kanboard_duplicate_freeze.py",
           ROOT / "scripts/persistence_collection.py", RUNNER, QUALIFIER)


def qualified_browser() -> None:
    proof = json.loads(QUALIFICATION.read_text())
    if (proof.get("qualified") is not True or proof.get("controls") != 9
            or proof.get("image_id") != IMAGE
            or proof.get("runner_sha256") != hash_file(RUNNER)
            or proof.get("qualifier_sha256") != hash_file(QUALIFIER)
            or {x["mode"]: x["observed"] for x in proof["cases"]} != {
                "reference": "pass", "alternative": "pass", "target-mutant": "target_only_failure",
                "non-target-mutant": "non_target_only_failure", "duplicate-identity": "interface_error",
                "precreated-duplicate": "interface_error", "missing-behavior": "interface_error",
                "script-error": "browser_error", "uuid-reference": "pass"}) :
        raise ValueError("secure-origin browser qualification drift")
    verify_inventory(QUALIFICATION_RECEIPT.parent)
    if "http://localhost/" not in RUNNER.read_text():
        raise ValueError("secure origin missing")


def schedule() -> list[dict]:
    rows = []
    for model in original.MODELS:
        for repetition in original.REPETITIONS:
            for arm in original.ARMS:
                key = json.dumps(["kanboard-duplicate-secure-replication", model, repetition, arm, SEED])
                rows.append({"slot_id": "secure-duplicate-" + hashlib.sha256(key.encode()).hexdigest()[:24],
                             "intent_id": "kanboard-duplicate-preserves-title", "project_id": "kanboard",
                             "model": model, "replication": repetition, "arm": arm})
    random.Random(SEED).shuffle(rows)
    return rows


def prepare(destination: Path, executable: Path) -> dict:
    if destination.exists() or not destination.is_absolute() or destination.resolve().is_relative_to(ROOT):
        raise ValueError("fresh private destination outside repository required")
    original.validate(PARENT)
    qualified_browser()
    executable = executable.resolve(strict=True)
    login = subprocess.run([str(executable), "login", "status"], capture_output=True, text=True, timeout=15)
    if login.returncode or "Logged in using ChatGPT" not in login.stdout + login.stderr:
        raise ValueError("saved ChatGPT authentication required")
    image = subprocess.run(["docker", "image", "inspect", "--format", "{{.Id}}", IMAGE],
                           capture_output=True, text=True, timeout=30, check=True)
    if image.stdout.strip() != IMAGE:
        raise ValueError("qualified image unavailable")
    destination.mkdir(mode=0o700, parents=True)
    rows = schedule()
    runtime_hashes = {str(p.relative_to(ROOT)): hash_file(p) for p in RUNTIME}
    for path in RUNTIME:
        put(destination / "frozen/runtime" / path.relative_to(ROOT), path.read_bytes())
    prompts = {}
    for row in rows:
        name = row["slot_id"] + ".json"
        prompt = original.prompt(row["arm"])
        put(destination / "frozen/requests" / name, {"prompt": prompt})
        prompts[row["slot_id"]] = hash_file(destination / "frozen/requests" / name)
    manifest = {
        "schema_version": "kanboard-duplicate-secure-replication/v1", "status": "pre_generation",
        "parent_manifest_sha256": hash_file(PARENT / "manifest.json"),
        "diagnostic_qualification_sha256": hash_file(QUALIFICATION),
        "diagnostic_receipt_sha256": hash_file(QUALIFICATION_RECEIPT),
        "runtime_sha256": runtime_hashes, "request_sha256": prompts, "schedule": rows,
        "seed": SEED, "planned_slots": 18, "arms": list(original.ARMS), "models": list(original.MODELS),
        "image_id": IMAGE, "executable": str(executable), "executable_sha256": hash_file(executable),
        "billing_mode": "chatgpt_subscription", "api_key_fallback": False,
        "retry_policy": "no_retry_no_resume_no_repair", "generation_before_browser": True,
        "confirmatory_eligible": False, "human_approvals": 0,
    }
    put(destination / "frozen/manifest.json", manifest)
    put(destination / "frozen/receipt.json", {"files": hash_inventory(destination / "frozen")})
    return manifest


def verify(packet: Path) -> dict:
    verify_inventory(packet / "frozen")
    manifest = json.loads((packet / "frozen/manifest.json").read_text())
    if (manifest.get("schema_version") != "kanboard-duplicate-secure-replication/v1"
            or manifest.get("schedule") != schedule() or manifest.get("planned_slots") != 18
            or manifest.get("parent_manifest_sha256") != hash_file(PARENT / "manifest.json")
            or manifest.get("diagnostic_qualification_sha256") != hash_file(QUALIFICATION)
            or manifest.get("diagnostic_receipt_sha256") != hash_file(QUALIFICATION_RECEIPT)
            or manifest.get("runtime_sha256") != {str(p.relative_to(ROOT)): hash_file(p) for p in RUNTIME}
            or manifest.get("executable_sha256") != hash_file(Path(manifest["executable"]))):
        raise ValueError("frozen replication drift")
    for row in manifest["schedule"]:
        path = packet / "frozen/requests" / (row["slot_id"] + ".json")
        if (manifest["request_sha256"][row["slot_id"]] != hash_file(path)
                or json.loads(path.read_text()) != {"prompt": original.prompt(row["arm"])}):
            raise ValueError("frozen request drift")
    return manifest


def run(packet: Path) -> dict:
    manifest = verify(packet)
    if (packet / "run-started.json").exists():
        raise FileExistsError("replication cannot resume")
    put(packet / "run-started.json", {"frozen_receipt_sha256": hash_file(packet / "frozen/receipt.json")})
    rows = [{**row, "category": "not_attempted", "target_failed": None}
            for row in manifest["schedule"]]
    for row in rows:
        sid = row["slot_id"]
        prompt_path = packet / "frozen/requests" / (sid + ".json")
        call = packet / "calls" / sid
        put(call / "attempt.json", {"request_sha256": hash_file(prompt_path), "slot_id": sid})
        try:
            provider = CodexCLIProvider(executable=manifest["executable"], model=row["model"],
                                        timeout_seconds=240, evidence_directory=call / "capture")
            raw = provider.complete(ProviderRequest(json.loads(prompt_path.read_text())["prompt"], {},
                                                    "opaque", "code"))
        except Exception as error:
            row.update(category="provider_error", error_type=type(error).__name__)
            put(call / "generation-result.json", row)
            break
        put(call / "response.txt", raw.encode())
        put(call / "provider-metadata.json", provider.last_call_metadata)
        try:
            artifact = admit(raw)
        except (UnicodeError, ValueError) as error:
            row.update(category="invalid_output", invalid_reason=str(error))
        else:
            put(packet / "artifacts" / sid / "app.html", artifact)
            row["generation_valid"] = True
        put(call / "generation-result.json", row)
        print(json.dumps({"phase": "generation", "completed_calls": sum(
            (packet / "calls" / item["slot_id"] / "attempt.json").exists() for item in rows)}), flush=True)
    put(packet / "collection.json", rows)
    verify(packet)
    frozen_runner = packet / "frozen/runtime" / RUNNER.relative_to(ROOT)
    frozen_qualifier = packet / "frozen/runtime" / QUALIFIER.relative_to(ROOT)
    for row in rows:
        if not row.get("generation_valid"):
            continue
        sid = row["slot_id"]
        try:
            result = execute(IMAGE, packet / "artifacts" / sid, packet / "execution" / sid,
                             frozen_runner, frozen_qualifier)
        except Exception as error:
            result = {"category": "browser_error", "error_type": type(error).__name__}
        row["category"] = result["category"]
        row["target_failed"] = (True if row["category"] in ("target_only_failure", "mixed_failure")
                                else False if row["category"] in ("pass", "non_target_only_failure") else None)
        row["execution"] = result
        print(json.dumps({"phase": "browser", "slot_id": sid, "category": row["category"]}), flush=True)
    counts = {model: {arm: dict(Counter(row["category"] for row in rows if row["model"] == model
                                      and row["arm"] == arm)) for arm in original.ARMS} for model in original.MODELS}
    result = {"schema_version": "kanboard-duplicate-secure-replication-results/v1",
              "confirmatory_eligible": False, "planned_slots": 18,
              "attempted_calls": sum((packet / "calls" / row["slot_id"] / "attempt.json").exists() for row in rows),
              "counts": counts, "rows": rows}
    put(packet / "results.json", result)
    put(packet / "receipt.json", {"files": hash_inventory(packet)})
    return result


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("mode", choices=("prepare", "run"))
    parser.add_argument("--packet", required=True, type=Path)
    parser.add_argument("--executable", type=Path, default=Path("/opt/homebrew/bin/codex"))
    args = parser.parse_args()
    print(json.dumps(prepare(args.packet, args.executable) if args.mode == "prepare" else run(args.packet)))
