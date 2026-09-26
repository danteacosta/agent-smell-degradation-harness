"""Prospective TodoMVC edit-state persistence bridge with the qualified selector."""
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
from eval.persistence_executor import execute
from scripts.persistence_collection import hash_file, hash_inventory, html_bytes, put, verify_inventory

IMAGE = "sha256:7ec0ab7cde9cf5b84b0ee5d4c07e86a94f1a696c8a26c6ccdbd73569ae460d4a"
SEED = 2026092610
MODELS = ("gpt-5.6-luna", "gpt-5.6-sol")
ARMS = ("A", "B", "C")
REPETITIONS = (1, 2, 3)
QUALIFICATION = Path("/Users/dantecosta/Documents/GitHub/.private-research-evidence/persistence-selector-qualification-20260923-v1")
REVIEW = Path("/Users/dantecosta/Documents/GitHub/.private-research-evidence/todomvc-persistence-bridge-review-20260926-v2")
PROMPTS = ROOT / "data/behavioral-expansion/frozen-persistence-prompts-20260923.json"
SOURCE = ROOT / "data/criteria-expansion/sources/todomvc/app-spec.md"
LICENSE = ROOT / "data/criteria-expansion/sources/todomvc/license.md"
RUNTIME = (Path(__file__), ROOT / "agents/codex_cli.py", ROOT / "agents/providers.py",
           ROOT / "scripts/persistence_collection.py", ROOT / "eval/persistence_executor.py",
           ROOT / "eval/focus_chain_executor.py", ROOT / "eval/fixtures/persistence/runner.cjs",
           ROOT / "eval/fixtures/persistence/qualify.py")


def schedule() -> list[dict]:
    rows = []
    for model in MODELS:
        for repetition in REPETITIONS:
            for arm in ARMS:
                key = json.dumps(["todo-edit-state-not-persisted-bridge", model, repetition, arm, SEED])
                rows.append({"slot_id": "persistence-bridge-" + hashlib.sha256(key.encode()).hexdigest()[:24],
                             "intent_id": "todo-edit-state-not-persisted", "project_id": "todomvc",
                             "model": model, "replication": repetition, "arm": arm})
    random.Random(SEED).shuffle(rows)
    return rows


def prompt(arm: str) -> str:
    prompts = json.loads(PROMPTS.read_text())
    if set(prompts) != set(ARMS) or arm not in prompts:
        raise ValueError("frozen prompt arms drift")
    return prompts[arm]


def check_qualification() -> None:
    qualification = json.loads((QUALIFICATION / "qualification.json").read_text())
    if (qualification.get("qualified") is not True or qualification.get("image_id") != IMAGE
            or len(qualification.get("cases", [])) != 27
            or any(row["expected_category"] != row["observed_category"]
                   or row["expected_failures"] != row["observed_failures"]
                   for row in qualification["cases"])):
        raise ValueError("selector qualification invalid")
    for name, digest in qualification["files"].items():
        if hash_file(ROOT / name) != digest:
            raise ValueError("qualified endpoint runtime drift: " + name)
    checksums = (QUALIFICATION / "SHA256SUMS").read_text().splitlines()
    if len(checksums) != 193:
        raise ValueError("qualification inventory incomplete")
    for line in checksums:
        digest, name = line.split("  ", 1)
        if hash_file(QUALIFICATION / name) != digest:
            raise ValueError("qualification evidence drift")


def preflight() -> None:
    check_qualification()
    verify_inventory(REVIEW)
    for model in ("gpt-6-astra", "gpt-6-sol", "gpt-6-luna"):
        if json.loads((REVIEW / model / "response.txt").read_text()).get("verdict") != "ACCEPT":
            raise ValueError("instrument review not unanimous")
    if "Editing mode should not be persisted" not in SOURCE.read_text() or not LICENSE.is_file():
        raise ValueError("source or rights missing")
    if "Editing mode should not be persisted" not in prompt("A") or "Editing mode should not be persisted" in prompt("C"):
        raise ValueError("bridge manipulation drift")


def prepare(destination: Path, executable: Path) -> dict:
    if destination.exists() or not destination.is_absolute() or destination.resolve().is_relative_to(ROOT):
        raise ValueError("fresh private destination outside repository required")
    preflight()
    executable = executable.resolve(strict=True)
    auth = subprocess.run([str(executable), "login", "status"], capture_output=True, text=True, timeout=15)
    if auth.returncode or "Logged in using ChatGPT" not in auth.stdout + auth.stderr:
        raise ValueError("saved ChatGPT authentication required")
    image = subprocess.run(["docker", "image", "inspect", "--format", "{{.Id}}", IMAGE],
                           capture_output=True, text=True, timeout=30, check=True)
    if image.stdout.strip() != IMAGE:
        raise ValueError("qualified image unavailable")
    destination.mkdir(mode=0o700, parents=True)
    rows = schedule()
    hashes = {str(path.relative_to(ROOT)): hash_file(path) for path in RUNTIME}
    for path in RUNTIME:
        put(destination / "frozen/runtime" / path.relative_to(ROOT), path.read_bytes())
    requests = {}
    for row in rows:
        path = destination / "frozen/requests" / (row["slot_id"] + ".json")
        put(path, {"prompt": prompt(row["arm"])})
        requests[row["slot_id"]] = hash_file(path)
    manifest = {"schema_version": "todomvc-persistence-bridge/v1", "status": "pre_generation",
                "planned_slots": 18, "schedule": rows, "seed": SEED, "models": MODELS, "arms": ARMS,
                "source_sha256": hash_file(SOURCE), "license_sha256": hash_file(LICENSE),
                "prompts_sha256": hash_file(PROMPTS),
                "qualification_receipt_sha256": hash_file(QUALIFICATION / "receipt.json"),
                "review_receipt_sha256": hash_file(REVIEW / "receipt.json"),
                "runtime_sha256": hashes, "request_sha256": requests,
                "image_id": IMAGE, "executable": str(executable), "executable_sha256": hash_file(executable),
                "billing_mode": "chatgpt_subscription", "api_key_fallback": False,
                "retry_policy": "no_retry_no_resume_no_repair", "generation_before_browser": True,
                "confirmatory_eligible": False, "human_approvals": 0, "bridge_replication": True}
    put(destination / "frozen/manifest.json", manifest)
    put(destination / "frozen/receipt.json", {"files": hash_inventory(destination / "frozen")})
    return manifest


def verify(packet: Path) -> dict:
    verify_inventory(packet / "frozen")
    manifest = json.loads((packet / "frozen/manifest.json").read_text())
    if (manifest.get("schema_version") != "todomvc-persistence-bridge/v1"
            or manifest.get("schedule") != schedule() or manifest.get("planned_slots") != 18
            or manifest.get("source_sha256") != hash_file(SOURCE)
            or manifest.get("license_sha256") != hash_file(LICENSE)
            or manifest.get("prompts_sha256") != hash_file(PROMPTS)
            or manifest.get("qualification_receipt_sha256") != hash_file(QUALIFICATION / "receipt.json")
            or manifest.get("review_receipt_sha256") != hash_file(REVIEW / "receipt.json")
            or manifest.get("runtime_sha256") != {str(path.relative_to(ROOT)): hash_file(path) for path in RUNTIME}
            or manifest.get("executable_sha256") != hash_file(Path(manifest["executable"]))):
        raise ValueError("frozen bridge drift")
    for row in manifest["schedule"]:
        path = packet / "frozen/requests" / (row["slot_id"] + ".json")
        if (manifest["request_sha256"][row["slot_id"]] != hash_file(path)
                or json.loads(path.read_text()) != {"prompt": prompt(row["arm"])}):
            raise ValueError("frozen request drift")
    return manifest


def run(packet: Path) -> dict:
    manifest = verify(packet)
    if (packet / "run-started.json").exists():
        raise FileExistsError("no resume or retry")
    put(packet / "run-started.json", {"frozen_receipt_sha256": hash_file(packet / "frozen/receipt.json")})
    rows = [{**row, "category": "not_attempted", "target_failed": None} for row in manifest["schedule"]]
    for row in rows:
        sid = row["slot_id"]
        request = packet / "frozen/requests" / (sid + ".json")
        call = packet / "calls" / sid
        put(call / "attempt.json", {"slot_id": sid, "request_sha256": hash_file(request)})
        try:
            provider = CodexCLIProvider(executable=manifest["executable"], model=row["model"],
                                        timeout_seconds=240, evidence_directory=call / "capture")
            raw = provider.complete(ProviderRequest(json.loads(request.read_text())["prompt"], {}, "opaque", "code"))
        except Exception as error:
            row.update(category="provider_error", error_type=type(error).__name__)
            put(call / "generation-result.json", row)
            break
        put(call / "response.txt", raw.encode())
        put(call / "provider-metadata.json", provider.last_call_metadata)
        try:
            artifact = html_bytes(raw)
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
    for row in rows:
        if not row.get("generation_valid"):
            continue
        sid = row["slot_id"]
        try:
            outcome = execute(IMAGE, packet / "artifacts" / sid, packet / "execution" / sid)
        except Exception as error:
            outcome = {"category": "browser_error", "error_type": type(error).__name__}
        row["category"] = outcome["category"]
        row["target_failed"] = outcome.get("target_failed")
        row["execution"] = outcome
        print(json.dumps({"phase": "browser", "slot_id": sid, "category": row["category"]}), flush=True)
    result = {"schema_version": "todomvc-persistence-bridge-results/v1", "planned_slots": 18,
              "attempted_calls": sum((packet / "calls" / row["slot_id"] / "attempt.json").exists() for row in rows),
              "counts": {model: {arm: dict(Counter(row["category"] for row in rows if row["model"] == model
                                                   and row["arm"] == arm)) for arm in ARMS} for model in MODELS},
              "rows": rows, "confirmatory_eligible": False, "bridge_replication": True}
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
