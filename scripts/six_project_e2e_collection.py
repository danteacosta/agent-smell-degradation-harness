"""Collect the frozen four-project E2E expansion exactly once.

All 72 generations finish before any generated artifact is opened in a browser.
The private packet is immutable by receipt and cannot be resumed.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import re
import runpy
import subprocess
import sys
import uuid


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from agents.codex_cli import CodexCLIProvider
from agents.providers import ProviderRequest
from scripts import six_project_e2e_freeze as freeze
from scripts.behavioral_expansion import summarize
from scripts.persistence_collection import (
    hash_file, hash_inventory, html_bytes, now, put, sync_directory,
    validate_preflight, verify_inventory,
)


PARENT_DIRECTORY = ROOT / "data/e2e-six-projects/freeze-20260925"
QUALIFICATION_DIRECTORY = ROOT / "data/e2e-six-projects/oracle-qualification-20260925"
APPROVED_IMAGE_ID = "sha256:529bf59afccb0572970b728de7235f0f0130da00248fab232121cd2c3eef60df"
FLAGS = {
    "confirmatory_eligible": False,
    "human_approvals": 0,
    "label_source": "independent_behavioral_oracle",
}


def _runtime_paths() -> list[Path]:
    paths = {
        ROOT / "eval/fixtures/four-project-ui/runner.cjs",
        ROOT / "eval/fixtures/four-project-ui/Dockerfile",
        ROOT / "eval/fixtures/four-project-ui/package.json",
        ROOT / "eval/fixtures/four-project-ui/package-lock.json",
    }
    # Package initializers and helper imports can affect execution without being
    # named directly above. Bind every Python runtime module, as the earlier
    # admitted collectors do, instead of understating the executable surface.
    for package in ("agents", "protocol", "eval", "scripts"):
        paths.update((ROOT / package).rglob("*.py"))
    return sorted(paths)


def runtime_hashes() -> dict[str, str]:
    return {path.relative_to(ROOT).as_posix(): hash_file(path) for path in _runtime_paths()}


def _inventory_without_receipt(directory: Path) -> dict[str, str]:
    return {
        name: digest for name, digest in hash_inventory(directory).items()
        if name != "receipt.json"
    }


def _validate_qualification(directory: Path, image_id: str) -> dict:
    if directory.is_symlink() or not directory.is_dir():
        raise ValueError("real qualification directory required")
    evidence = json.loads((directory / "qualification.json").read_text())
    receipt = json.loads((directory / "receipt.json").read_text())
    if (
        image_id != APPROVED_IMAGE_ID
        or evidence.get("schema_version") != "four-project-ui-qualification/v1"
        or evidence.get("qualified") is not True
        or evidence.get("image_id") != image_id
        or evidence.get("controls") != 20
        or evidence.get("project_count") != 4
        or len(evidence.get("cases", [])) != 20
        or receipt.get("schema_version") != "four-project-ui-public-bundle/v1"
        or receipt.get("qualified") is not True
        or receipt.get("image_id") != image_id
        or receipt.get("files") != _inventory_without_receipt(directory)
    ):
        raise ValueError("qualification evidence mismatch")
    expected = {
        (project, mode)
        for project in freeze.PROJECTS
        for mode in ("reference", "alternative", "target-mutant", "non-target-mutant", "interface-ambiguous")
    }
    if (
        {(row.get("project_id"), row.get("mode")) for row in evidence["cases"]} != expected
        or any(row.get("expected") != row.get("observed") for row in evidence["cases"])
    ):
        raise ValueError("qualification control matrix mismatch")
    return evidence


def _normalized(schedule: list[dict]) -> list[dict]:
    return [
        {
            "slot_id": row["slot_id"],
            "intent_id": row["project_id"] + "-omitted-obligation",
            "project_id": row["project_id"],
            "model": row["model"],
            "replication": row["replication"],
            "variant": row["arm"],
        }
        for row in schedule
    ]


def _validate_parent(parent: Path) -> tuple[dict, dict[str, str]]:
    manifest = freeze.validate_materialized(parent)
    schedule = manifest.get("schedule")
    if not isinstance(schedule, list) or len(schedule) != 72:
        raise ValueError("canonical 72-slot schedule required")
    summarize(_normalized(schedule), [])
    return manifest, hash_inventory(parent)


def prepare(
    parent: Path,
    destination: Path,
    executable: Path,
    preflight: dict,
    *,
    image_id: str,
    qualification: Path,
) -> dict:
    validate_preflight(preflight)
    parent = parent.resolve(strict=True)
    qualification = qualification.resolve(strict=True)
    parent_manifest, parent_inventory = _validate_parent(parent)
    _validate_qualification(qualification, image_id)
    qualification_inventory = hash_inventory(qualification)
    if not destination.is_absolute() or destination.parent.is_symlink():
        raise ValueError("absolute private destination required")
    if destination.resolve().is_relative_to(ROOT):
        raise ValueError("private destination must be outside repository")
    executable = executable.resolve(strict=True)
    version = subprocess.run(
        [str(executable), "--version"], check=True, capture_output=True,
        text=True, timeout=15,
    ).stdout.strip()
    auth = subprocess.run(
        [str(executable), "login", "status"], capture_output=True,
        text=True, timeout=15,
    )
    if auth.returncode != 0 or "Logged in using ChatGPT" not in auth.stdout + auth.stderr:
        raise ValueError("Codex CLI ChatGPT authentication required")

    destination.mkdir(mode=0o700, parents=True, exist_ok=False)
    os.chmod(destination, 0o700)
    sync_directory(destination.parent)
    sync_directory(destination)
    frozen = destination / "frozen"
    put(frozen / "parent-manifest.json", (parent / "manifest.json").read_bytes())
    put(frozen / "schedule.json", parent_manifest["schedule"])
    for row in parent_manifest["schedule"]:
        name = f"{row['slot_id']}.json"
        put(frozen / "requests" / name, (parent / "requests" / name).read_bytes())
    put(frozen / "qualification.json", (qualification / "qualification.json").read_bytes())
    put(frozen / "qualification-receipt.json", (qualification / "receipt.json").read_bytes())
    hashes = runtime_hashes()
    for relative in hashes:
        put(frozen / "runtime" / relative, (ROOT / relative).read_bytes())
    manifest = {
        **FLAGS,
        "schema_version": "six-project-e2e-collection/v1",
        "frozen_at_utc": now(),
        "parent": str(parent),
        "parent_inventory": parent_inventory,
        "qualification": str(qualification),
        "qualification_inventory": qualification_inventory,
        "executable": str(executable),
        "executable_sha256": hash_file(executable),
        "cli_version": version,
        "runtime_hashes": hashes,
        "preflight": preflight,
        "image_id": image_id,
        "projects": list(freeze.PROJECTS),
        "max_calls": 72,
        "concurrency": 1,
        "reasoning_effort": "low",
        "timeout_seconds": 240,
        "retry_policy": "no_retry_no_resume_no_repair",
        "billing_mode": "chatgpt_subscription",
        "api_key_fallback": False,
        "generation_before_execution": True,
        "output_admission": "raw standalone HTML; no extraction, normalization or repair",
        "artifact_limit_bytes": 200000,
        "claims": {"pilot": True, "h1_confirmed": False, "h2_evaluated": False},
    }
    put(frozen / "manifest.json", manifest)
    put(frozen / "receipt.json", {"files": hash_inventory(frozen)})
    return manifest


def verify_execution(packet: Path) -> tuple[dict, list[dict]]:
    if packet.is_symlink() or not packet.is_dir() or packet.stat().st_mode & 0o077:
        raise ValueError("private collection packet required")
    frozen = packet / "frozen"
    verify_inventory(frozen)
    manifest = json.loads((frozen / "manifest.json").read_text())
    required_policy = {
        "schema_version": "six-project-e2e-collection/v1",
        "image_id": APPROVED_IMAGE_ID,
        "max_calls": 72,
        "concurrency": 1,
        "reasoning_effort": "low",
        "timeout_seconds": 240,
        "retry_policy": "no_retry_no_resume_no_repair",
        "billing_mode": "chatgpt_subscription",
        "api_key_fallback": False,
        "generation_before_execution": True,
    }
    if any(manifest.get(key) != value for key, value in required_policy.items()):
        raise ValueError("frozen execution policy drift")
    validate_preflight(manifest["preflight"])
    executable = Path(manifest["executable"])
    if hash_file(executable) != manifest["executable_sha256"]:
        raise ValueError("executable drift")
    if runtime_hashes() != manifest["runtime_hashes"]:
        raise ValueError("runtime drift")
    parent = Path(manifest["parent"])
    parent_manifest, inventory = _validate_parent(parent)
    if inventory != manifest["parent_inventory"]:
        raise ValueError("parent inventory drift")
    qualification = Path(manifest["qualification"])
    _validate_qualification(qualification, manifest["image_id"])
    if hash_inventory(qualification) != manifest["qualification_inventory"]:
        raise ValueError("qualification inventory drift")
    if (frozen / "parent-manifest.json").read_bytes() != (parent / "manifest.json").read_bytes():
        raise ValueError("frozen parent drift")
    schedule = json.loads((frozen / "schedule.json").read_text())
    if schedule != parent_manifest["schedule"]:
        raise ValueError("schedule drift")
    for row in schedule:
        name = f"{row['slot_id']}.json"
        if (frozen / "requests" / name).read_bytes() != (parent / "requests" / name).read_bytes():
            raise ValueError("request drift")
    summarize(_normalized(schedule), [])
    return manifest, schedule


def _docker_command(image: str, inputs: Path, output: Path) -> list[str]:
    if re.fullmatch(r"sha256:[0-9a-f]{64}", image) is None:
        raise ValueError("immutable Docker image ID required")
    return [
        "docker", "run", "--rm", "--init", "--name", "four-project-generated-" + uuid.uuid4().hex,
        "--network", "none", "--user", f"{os.getuid()}:{os.getgid()}", "--read-only",
        "--cap-drop", "ALL", "--security-opt", "no-new-privileges", "--pids-limit", "256",
        "--memory", "1g", "--cpus", "2", "--shm-size", "256m",
        "--tmpfs", "/tmp:rw,nosuid,size=256m", "--env", "HOME=/tmp",
        "--mount", f"type=bind,src={inputs.resolve()},dst=/input,readonly",
        "--mount", f"type=bind,src={output.resolve()},dst=/output", image,
    ]


def execute_generated(*, image: str, inputs: Path, output: Path, project_id: str) -> dict:
    output.mkdir(mode=0o700, parents=True, exist_ok=False)
    found = subprocess.run(
        ["docker", "image", "inspect", "--format", "{{.Id}}", image],
        check=True, capture_output=True, text=True, timeout=30,
    ).stdout.strip()
    if found != image:
        raise ValueError("Docker image identity mismatch")
    command = _docker_command(image, inputs, output)
    result = subprocess.run(
        command, capture_output=True,
        timeout=90, check=False,
    )
    put(output / "container-command.json", command)
    put(output / "container-stdout.bin", result.stdout)
    put(output / "container-stderr.bin", result.stderr)
    report_path = output / "report.json"
    if not report_path.is_file() or report_path.stat().st_size > 100000:
        return {"category": "browser_error", "target_failed": [], "returncode": result.returncode}
    try:
        report = json.loads(report_path.read_text())
    except (UnicodeError, json.JSONDecodeError):
        return {"category": "browser_error", "target_failed": [], "returncode": result.returncode}
    namespace = runpy.run_path(str(ROOT / "eval/fixtures/four-project-ui/qualify.py"))
    category = namespace["classify"](report)
    if (
        report.get("project_id") != project_id
        or report.get("app_sha256") != hash_file(inputs / "app.html")
        or (report.get("status") == "complete" and result.returncode != 0)
        or (report.get("status") != "complete" and result.returncode == 0)
    ):
        category = "malformed_report"
    contract = namespace["PROJECT_ASSERTIONS"].get(project_id, {})
    assertions = report.get("assertions", {}) if isinstance(report, dict) else {}
    target_failed = sorted(
        key for key in contract.get("target", set()) if assertions.get(key) is False
    )
    screenshot = output / "final.png"
    if report.get("status") == "complete" and (
        not screenshot.is_file() or not screenshot.read_bytes().startswith(b"\x89PNG\r\n\x1a\n")
    ):
        category = "browser_error"
        target_failed = []
    return {
        "category": category,
        "target_failed": target_failed,
        "returncode": result.returncode,
        "report_sha256": hash_file(report_path),
        "screenshot_sha256": hash_file(screenshot) if screenshot.is_file() else None,
    }


def _analysis_category(outcome: dict) -> tuple[str, bool | None]:
    category = outcome.get("category")
    if category in {"target_only_failure", "mixed_failure"}:
        return category, True
    if category in {"pass", "non_target_only_failure"}:
        return category, False
    if category in {"interface_error", "browser_error", "malformed_report"}:
        return "browser_error" if category == "malformed_report" else category, None
    return "browser_error", None


def run(packet: Path, provider_factory=CodexCLIProvider, executor=execute_generated) -> dict:
    manifest, schedule = verify_execution(packet)
    if (packet / "run-started.json").exists():
        raise FileExistsError("collection packet cannot be resumed")
    put(packet / "run-started.json", {"started_at_utc": now(), "policy": "no_resume", **FLAGS})
    normalized = _normalized(schedule)
    rows = [{**slot, "category": "not_attempted", "target_failed": None} for slot in normalized]
    put(packet / "initial-observations.json", rows)
    state = {**FLAGS, "calls_attempted": 0, "stop_reason": None, "rows": rows}
    for source, row in zip(schedule, rows):
        if state["stop_reason"]:
            break
        slot_id = row["slot_id"]
        request_path = packet / "frozen/requests" / f"{slot_id}.json"
        request = json.loads(request_path.read_text())
        call = packet / "calls" / slot_id
        put(call / "attempt.json", {
            "slot_id": slot_id, "started_at_utc": now(), "model": source["model"],
            "request_sha256": hash_file(request_path),
        })
        state["calls_attempted"] += 1
        try:
            provider = provider_factory(
                executable=manifest["executable"], model=source["model"],
                timeout_seconds=manifest["timeout_seconds"], evidence_directory=call / "capture",
            )
            raw = provider.complete(ProviderRequest(request["prompt"], {}, "opaque", "code"))
        except Exception as error:
            row.update(category="provider_error", error_type=type(error).__name__)
            state["stop_reason"] = "provider_infrastructure_error"
        else:
            put(call / "response.txt", raw.encode("utf-8", errors="backslashreplace"))
            put(call / "provider-metadata.json", provider.last_call_metadata)
            try:
                artifact = html_bytes(raw)
            except (UnicodeError, ValueError):
                row["category"] = "invalid_output"
            else:
                inputs = packet / "artifacts" / slot_id
                put(inputs / "app.html", artifact)
                put(inputs / "case.json", {"project_id": source["project_id"], "mode": "generated"})
                row["generation_valid"] = True
        put(call / "generation-result.json", row)
        print(json.dumps({"completed_calls": state["calls_attempted"], "phase": "generation"}), flush=True)

    put(packet / "collection.json", state)
    for source, row in zip(schedule, rows):
        if not row.get("generation_valid"):
            continue
        try:
            outcome = executor(
                image=manifest["image_id"], inputs=packet / "artifacts" / row["slot_id"],
                output=packet / "execution" / row["slot_id"], project_id=source["project_id"],
            )
        except Exception as error:
            outcome = {"category": "browser_error", "error_type": type(error).__name__}
        category, failed = _analysis_category(outcome)
        row.update(category=category, target_failed=failed, execution=outcome)
        print(json.dumps({"slot_id": row["slot_id"], "phase": "browser", "category": category}), flush=True)

    put(packet / "results.json", state)
    analysis = summarize(normalized, rows)
    analysis.update(
        **FLAGS, calls_attempted=state["calls_attempted"], stop_reason=state["stop_reason"],
        projects=list(freeze.PROJECTS), claims=manifest["claims"],
    )
    put(packet / "analysis.json", analysis)
    put(packet / "receipt.json", {"files": hash_inventory(packet)})
    return analysis


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest="command", required=True)
    prepare_parser = commands.add_parser("prepare")
    for name in ("parent", "destination", "executable", "preflight", "qualification"):
        prepare_parser.add_argument("--" + name, type=Path, required=True)
    prepare_parser.add_argument("--image-id", required=True)
    commands.add_parser("run").add_argument("--packet", type=Path, required=True)
    args = parser.parse_args()
    result = prepare(
        args.parent, args.destination, args.executable,
        json.loads(args.preflight.read_text()), image_id=args.image_id,
        qualification=args.qualification,
    ) if args.command == "prepare" else run(args.packet)
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
