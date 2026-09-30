"""Prospective browser pilot for Nextcloud restore-name conflict."""
from __future__ import annotations

import argparse
from collections import Counter
import hashlib
import json
from pathlib import Path
import random
import re
import runpy
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from agents.codex_cli import CodexCLIProvider
from agents.providers import ProviderRequest
from scripts.kanboard_duplicate_collect import execute as base_execute
from scripts.persistence_collection import hash_file, hash_inventory, html_bytes, put, verify_inventory

IMAGE = "sha256:00d1265095773b7f8a12aa73e81d0bab75563cbd672dd0b5d91783ea1b6d4400"
SEED = 2026092705
MODELS = ("gpt-5.6-luna", "gpt-5.6-sol")
ARMS = ("A", "B", "C")
REPETITIONS = (1, 2, 3)
FIXTURE = ROOT / "eval/fixtures/nextcloud-restore-conflict-v4"
QUALIFICATION = Path("/Users/dantecosta/Documents/GitHub/.private-research-evidence/nextcloud-restore-conflict-qualification-20260927-v4")
REVIEW = Path("/Users/dantecosta/Documents/GitHub/.private-research-evidence/nextcloud-restore-conflict-review-20260927-v4b")
SOURCE = ROOT / "data/e2e-six-projects/sources/nextcloud/deleted_file_management.rst"
LICENSE = ROOT / "data/e2e-six-projects/sources/nextcloud/COPYING"
ARM_FILE = ROOT / "data/e2e-nextcloud-restore-conflict/arms-20260926.json"
MARKER = "/* MODEL_BEHAVIOR */"
RUNTIME = (Path(__file__), ROOT / "agents/codex_cli.py", ROOT / "agents/providers.py",
           ROOT / "scripts/kanboard_duplicate_collect.py", ROOT / "scripts/persistence_collection.py",
           FIXTURE / "page.html", FIXTURE / "runner.cjs", FIXTURE / "qualify.py")


def corrected_category(base: dict, report: dict, output: Path, artifact: Path,
                       qualifier: Path) -> str:
    """Interpret this oracle's declared image names after the generic collector runs."""
    category = runpy.run_path(str(qualifier))["classify"](report)
    if (report.get("app_sha256") != hash_file(artifact)
            or (report.get("status") == "complete") != (base.get("returncode") == 0)):
        return "malformed_report"
    if report.get("status") == "complete":
        for name in ("files-1.png", "files-2.png"):
            image = output / name
            if not image.is_file() or not image.read_bytes().startswith(b"\x89PNG\r\n\x1a\n"):
                return "browser_error"
    return category


def execute_v4(image: str, inputs: Path, output: Path, runner: Path, qualifier: Path) -> dict:
    base = base_execute(image, inputs, output, runner, qualifier)
    report_path = output / "report.json"
    if not report_path.is_file():
        return base
    try:
        report = json.loads(report_path.read_text())
    except (UnicodeError, json.JSONDecodeError):
        return base
    category = corrected_category(base, report, output, inputs / "app.html", qualifier)
    return {**base, "category": category,
            "screenshots": {name: hash_file(output / name) for name in ("files-1.png", "files-2.png")
                            if (output / name).is_file()}}


def schedule() -> list[dict]:
    rows = []
    for model in MODELS:
        for repetition in REPETITIONS:
            for arm in ARMS:
                key = json.dumps(["nextcloud-restore-conflict-v4", model, repetition, arm, SEED])
                rows.append({"slot_id": "nextcloud-conflict-" + hashlib.sha256(key.encode()).hexdigest()[:24],
                             "intent_id": "nextcloud-restore-conflict-v4", "project_id": "nextcloud",
                             "model": model, "replication": repetition, "arm": arm})
    random.Random(SEED).shuffle(rows)
    return rows


def arms() -> dict:
    return json.loads(ARM_FILE.read_text())


def prompt(arm: str) -> str:
    page = (FIXTURE / "page.html").read_text()
    if page.count(MARKER) != 1:
        raise ValueError("one behavior marker required")
    return ("Implement only the requirement in the frozen browser page. Replace the single "
            "/* MODEL_BEHAVIOR */ marker with vanilla JavaScript statements using the provided "
            "app API. Register app.onRestore to handle the visible Restore button. Do not change any "
            "other byte of the page. Return only the complete HTML page.\n\nRequirement:\n"
            + arms()[arm] + "\n\nFrozen page:\n" + page)


def admit(raw: str) -> bytes:
    artifact = html_bytes(raw)
    page = (FIXTURE / "page.html").read_bytes()
    marker = MARKER.encode()
    if page.count(marker) != 1:
        raise ValueError("scaffold marker drift")
    prefix, suffix = page.split(marker)
    if suffix.endswith(b"\n") and not artifact.endswith(b"\n"):
        suffix = suffix[:-1]
    if not artifact.startswith(prefix) or not artifact.endswith(suffix):
        raise ValueError("generated output changed frozen scaffold")
    behavior = artifact[len(prefix):len(artifact) - len(suffix)]
    if not behavior.strip() or marker in behavior or b"</script" in behavior.lower():
        raise ValueError("invalid behavior insertion")
    return artifact


def preflight() -> None:
    verify_inventory(QUALIFICATION)
    verify_inventory(REVIEW)
    qualification = json.loads((QUALIFICATION / "qualification.json").read_text())
    if (qualification.get("qualified") is not True or qualification.get("controls") != 10
            or qualification.get("image_id") != IMAGE
            or qualification.get("source_scaffold_sha256") != hash_file(FIXTURE / "page.html")
            or qualification.get("runner_sha256") != hash_file(FIXTURE / "runner.cjs")
            or qualification.get("qualifier_sha256") != hash_file(FIXTURE / "qualify.py")
            or any(row["expected"] != row["observed"] for row in qualification["cases"])):
        raise ValueError("browser qualification drift")
    for model in ("gpt-6-astra", "gpt-6-sol", "gpt-6-luna"):
        vote = json.loads((REVIEW / model / "parsed.json").read_text())
        if vote.get("verdict") != "ACCEPT":
            raise ValueError("instrument review not unanimous")
    source_text = re.sub(r"\s+", " ", SOURCE.read_text())
    if "If an item with the same name already exists, Nextcloud gives the restored item a unique name." not in source_text:
        raise ValueError("source obligation missing")
    if not LICENSE.is_file() or set(arms()) != set(ARMS):
        raise ValueError("license/arms missing")


def prepare(destination: Path, executable: Path) -> dict:
    if destination.exists() or not destination.is_absolute() or destination.resolve().is_relative_to(ROOT):
        raise ValueError("fresh private destination outside repository required")
    preflight()
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
    hashes = {str(path.relative_to(ROOT)): hash_file(path) for path in RUNTIME}
    for path in RUNTIME:
        put(destination / "frozen/runtime" / path.relative_to(ROOT), path.read_bytes())
    requests = {}
    for row in rows:
        path = destination / "frozen/requests" / (row["slot_id"] + ".json")
        put(path, {"prompt": prompt(row["arm"])})
        requests[row["slot_id"]] = hash_file(path)
    manifest = {"schema_version": "nextcloud-restore-conflict-v4-pilot/v2", "status": "pre_generation",
                "planned_slots": 18, "schedule": rows, "seed": SEED, "models": MODELS, "arms": ARMS,
                "source_sha256": hash_file(SOURCE), "license_sha256": hash_file(LICENSE),
                "arms_sha256": hash_file(ARM_FILE),
                "qualification_receipt_sha256": hash_file(QUALIFICATION / "receipt.json"),
                "review_receipt_sha256": hash_file(REVIEW / "receipt.json"),
                "runtime_sha256": hashes, "request_sha256": requests,
                "image_id": IMAGE, "executable": str(executable), "executable_sha256": hash_file(executable),
                "billing_mode": "chatgpt_subscription", "api_key_fallback": False,
                "retry_policy": "no_retry_no_resume_no_repair", "generation_before_browser": True,
                "confirmatory_eligible": False, "human_approvals": 0}
    put(destination / "frozen/manifest.json", manifest)
    put(destination / "frozen/receipt.json", {"files": hash_inventory(destination / "frozen")})
    return manifest


def verify(packet: Path) -> dict:
    verify_inventory(packet / "frozen")
    manifest = json.loads((packet / "frozen/manifest.json").read_text())
    if (manifest.get("schema_version") != "nextcloud-restore-conflict-v4-pilot/v2"
            or manifest.get("schedule") != schedule() or manifest.get("planned_slots") != 18
            or manifest.get("source_sha256") != hash_file(SOURCE)
            or manifest.get("license_sha256") != hash_file(LICENSE)
            or manifest.get("arms_sha256") != hash_file(ARM_FILE)
            or manifest.get("qualification_receipt_sha256") != hash_file(QUALIFICATION / "receipt.json")
            or manifest.get("review_receipt_sha256") != hash_file(REVIEW / "receipt.json")
            or manifest.get("runtime_sha256") != {str(path.relative_to(ROOT)): hash_file(path) for path in RUNTIME}
            or manifest.get("executable_sha256") != hash_file(Path(manifest["executable"]))):
        raise ValueError("frozen pilot drift")
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
    runner = packet / "frozen/runtime" / (FIXTURE / "runner.cjs").relative_to(ROOT)
    qualifier = packet / "frozen/runtime" / (FIXTURE / "qualify.py").relative_to(ROOT)
    for row in rows:
        if not row.get("generation_valid"):
            continue
        sid = row["slot_id"]
        try:
            result = execute_v4(IMAGE, packet / "artifacts" / sid, packet / "execution" / sid,
                             runner, qualifier)
        except Exception as error:
            result = {"category": "browser_error", "error_type": type(error).__name__}
        row["category"] = result["category"]
        row["target_failed"] = (True if row["category"] in ("target_only_failure", "mixed_failure")
                                else False if row["category"] in ("pass", "non_target_failure") else None)
        row["execution"] = result
        print(json.dumps({"phase": "browser", "slot_id": sid, "category": row["category"]}), flush=True)
    result = {"schema_version": "nextcloud-restore-conflict-v4-results/v2", "planned_slots": 18,
              "attempted_calls": sum((packet / "calls" / row["slot_id"] / "attempt.json").exists() for row in rows),
              "counts": {model: {arm: dict(Counter(row["category"] for row in rows if row["model"] == model
                                                   and row["arm"] == arm)) for arm in ARMS} for model in MODELS},
              "rows": rows, "confirmatory_eligible": False}
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
