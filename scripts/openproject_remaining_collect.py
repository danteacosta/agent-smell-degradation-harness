"""Single-attempt, generation-first OpenProject Remaining work E2E collection."""
from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
import runpy
import subprocess
import sys
import uuid

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from agents.codex_cli import CodexCLIProvider
from agents.providers import ProviderRequest
from scripts import openproject_remaining_freeze as freeze
from scripts.persistence_collection import (
    hash_file, hash_inventory, html_bytes, now, put, sync_directory,
    verify_inventory,
)

RUNTIME = (
    "agents/codex_cli.py", "agents/providers.py",
    "scripts/openproject_remaining_collect.py", "scripts/openproject_remaining_freeze.py",
    "scripts/persistence_collection.py", "eval/fixtures/openproject-remaining-pilot/qualify.py",
)
FLAGS = {"confirmatory_eligible": False, "human_approvals": 0,
         "label_source": "independent_browser_oracle"}


def admit(raw: str, limit: int = 200000) -> bytes:
    artifact = html_bytes(raw)
    if len(artifact) > limit:
        raise ValueError("artifact exceeds limit")
    scaffold = (ROOT / freeze.FIXTURE / "page.html").read_bytes()
    marker = freeze.MARKER.encode()
    if scaffold.count(marker) != 1:
        raise ValueError("scaffold marker drift")
    if scaffold.endswith(b"\n") and not artifact.endswith(b"\n"):
        artifact += b"\n"
    prefix, suffix = scaffold.split(marker)
    if not artifact.startswith(prefix) or not artifact.endswith(suffix):
        raise ValueError("generated output changed frozen scaffold")
    behavior = artifact[len(prefix):len(artifact) - len(suffix)]
    if not behavior.strip() or marker in behavior or b"</script" in behavior.lower():
        raise ValueError("invalid behavior insertion")
    if len(artifact) > limit:
        raise ValueError("artifact exceeds limit")
    return artifact


def prepare(parent: Path, destination: Path, executable: Path) -> dict:
    frozen = freeze.validate(parent)
    if not destination.is_absolute() or destination.exists() or destination.resolve().is_relative_to(ROOT):
        raise ValueError("fresh absolute private destination outside repository required")
    executable = executable.resolve(strict=True)
    auth = subprocess.run([str(executable), "login", "status"], capture_output=True,
                          text=True, timeout=15)
    if auth.returncode or "Logged in using ChatGPT" not in auth.stdout + auth.stderr:
        raise ValueError("saved ChatGPT Codex authentication required")
    version = subprocess.run([str(executable), "--version"], check=True, capture_output=True,
                             text=True, timeout=15).stdout.strip()
    image = subprocess.run(["docker", "image", "inspect", "--format", "{{.Id}}", freeze.IMAGE],
                           check=True, capture_output=True, text=True, timeout=30).stdout.strip()
    if image != freeze.IMAGE:
        raise ValueError("qualified image unavailable")
    destination.mkdir(mode=0o700, parents=True, exist_ok=False)
    os.chmod(destination, 0o700)
    sync_directory(destination.parent)
    source = destination / "frozen"
    put(source / "parent-manifest.json", (parent / "manifest.json").read_bytes())
    for row in frozen["schedule"]:
        name = row["slot_id"] + ".json"
        put(source / "requests" / name, (parent / "requests" / name).read_bytes())
    runtime = {name: hash_file(ROOT / name) for name in RUNTIME}
    for name in runtime:
        put(source / "runtime" / name, (ROOT / name).read_bytes())
    manifest = {
        **FLAGS, "schema_version": "openproject-remaining-collection/v1",
        "frozen_at_utc": now(), "parent": str(parent.resolve()),
        "parent_inventory": hash_inventory(parent),
        "executable": str(executable), "executable_sha256": hash_file(executable),
        "cli_version": version, "image_id": freeze.IMAGE, "runtime_sha256": runtime,
        "max_calls": 18, "concurrency": 1, "reasoning_effort": "low",
        "timeout_seconds": 240, "retry_policy": "no_retry_no_resume_no_repair",
        "billing_mode": "chatgpt_subscription", "api_key_fallback": False,
        "generation_before_browser": True, "artifact_limit_bytes": 200000,
        "claims": frozen["claims"],
    }
    put(source / "manifest.json", manifest)
    put(source / "receipt.json", {"files": hash_inventory(source)})
    return manifest


def verify(packet: Path) -> tuple[dict, list[dict]]:
    if packet.is_symlink() or not packet.is_dir() or packet.stat().st_mode & 0o077:
        raise ValueError("private packet required")
    source = packet / "frozen"
    verify_inventory(source)
    manifest = json.loads((source / "manifest.json").read_text())
    parent = Path(manifest["parent"])
    frozen = freeze.validate(parent)
    if (
        manifest.get("schema_version") != "openproject-remaining-collection/v1"
        or manifest.get("image_id") != freeze.IMAGE
        or manifest.get("max_calls") != 18 or manifest.get("concurrency") != 1
        or manifest.get("retry_policy") != "no_retry_no_resume_no_repair"
        or manifest.get("billing_mode") != "chatgpt_subscription"
        or manifest.get("api_key_fallback") is not False
        or manifest.get("generation_before_browser") is not True
        or manifest.get("parent_inventory") != hash_inventory(parent)
        or manifest.get("runtime_sha256") != {name: hash_file(ROOT / name) for name in RUNTIME}
        or manifest.get("executable_sha256") != hash_file(Path(manifest["executable"]))
        or (source / "parent-manifest.json").read_bytes() != (parent / "manifest.json").read_bytes()
    ):
        raise ValueError("frozen runtime or policy drift")
    for row in frozen["schedule"]:
        name = row["slot_id"] + ".json"
        if (source / "requests" / name).read_bytes() != (parent / "requests" / name).read_bytes():
            raise ValueError("frozen request drift")
    return manifest, frozen["schedule"]


def execute(image: str, inputs: Path, output: Path) -> dict:
    output.mkdir(mode=0o700, parents=True, exist_ok=False)
    command = [
        "docker", "run", "--rm", "--init", "--name", "openproject-generated-" + uuid.uuid4().hex,
        "--network", "none", "--user", f"{os.getuid()}:{os.getgid()}", "--read-only",
        "--cap-drop", "ALL", "--security-opt", "no-new-privileges",
        "--pids-limit", "256", "--memory", "1g", "--cpus", "2",
        "--shm-size", "256m", "--tmpfs", "/tmp:rw,nosuid,size=256m", "--env", "HOME=/tmp",
        "--mount", f"type=bind,src={inputs.resolve()},dst=/input,readonly",
        "--mount", f"type=bind,src={output.resolve()},dst=/output", image,
    ]
    result = subprocess.run(command, capture_output=True, timeout=90, check=False)
    put(output / "container-command.json", command)
    put(output / "container-stdout.bin", result.stdout)
    put(output / "container-stderr.bin", result.stderr)
    report_path = output / "report.json"
    if not report_path.is_file() or report_path.stat().st_size > 100000:
        return {"category": "browser_error", "returncode": result.returncode}
    try:
        report = json.loads(report_path.read_text())
    except (UnicodeError, json.JSONDecodeError):
        return {"category": "malformed_report", "returncode": result.returncode}
    classify = runpy.run_path(str(ROOT / freeze.FIXTURE / "qualify.py"))["classify"]
    category = classify(report)
    if (report.get("app_sha256") != hash_file(inputs / "app.html")
            or (report.get("status") == "complete") != (result.returncode == 0)):
        category = "malformed_report"
    if report.get("status") == "complete":
        for name in ("fixture-1.png", "fixture-2.png"):
            path = output / name
            if not path.is_file() or not path.read_bytes().startswith(b"\x89PNG\r\n\x1a\n"):
                category = "browser_error"
    return {"category": category, "returncode": result.returncode,
            "report_sha256": hash_file(report_path),
            "screenshots": {name: hash_file(output / name) for name in
                ("fixture-1.png", "fixture-2.png") if (output / name).is_file()}}


def run(packet: Path, provider_factory=CodexCLIProvider, executor=execute) -> dict:
    manifest, slots = verify(packet)
    if (packet / "run-started.json").exists():
        raise FileExistsError("no resume allowed")
    put(packet / "run-started.json", {"started_at_utc": now(), "policy": "no_resume"})
    rows = [{**slot, "category": "not_attempted", "target_failed": None} for slot in slots]
    put(packet / "initial-observations.json", rows)
    stop_reason = None
    calls = 0
    for row in rows:
        if stop_reason:
            break
        slot_id = row["slot_id"]
        request_path = packet / "frozen/requests" / (slot_id + ".json")
        request = json.loads(request_path.read_text())["prompt"]
        call = packet / "calls" / slot_id
        put(call / "attempt.json", {"slot_id": slot_id, "started_at_utc": now(),
                                   "request_sha256": hash_file(request_path)})
        calls += 1
        try:
            provider = provider_factory(executable=manifest["executable"], model=row["model"],
                timeout_seconds=manifest["timeout_seconds"], evidence_directory=call / "capture")
            raw = provider.complete(ProviderRequest(request, {}, "opaque", "code"))
        except Exception as error:
            row.update(category="provider_error", error_type=type(error).__name__)
            stop_reason = "provider_infrastructure_error"
        else:
            put(call / "response.txt", raw.encode(errors="backslashreplace"))
            put(call / "provider-metadata.json", provider.last_call_metadata)
            try:
                artifact = admit(raw, manifest["artifact_limit_bytes"])
            except (UnicodeError, ValueError) as error:
                row.update(category="invalid_output", invalid_reason=str(error))
            else:
                put(packet / "artifacts" / slot_id / "app.html", artifact)
                row["generation_valid"] = True
        put(call / "generation-result.json", row)
        print(json.dumps({"phase": "generation", "completed_calls": calls}), flush=True)
    put(packet / "collection.json", {"calls_attempted": calls, "stop_reason": stop_reason, "rows": rows})
    for row in rows:
        if not row.get("generation_valid"):
            continue
        slot_id = row["slot_id"]
        try:
            result = executor(manifest["image_id"], packet / "artifacts" / slot_id,
                              packet / "execution" / slot_id)
        except Exception as error:
            result = {"category": "browser_error", "error_type": type(error).__name__}
        row.update(category=result["category"], execution=result)
        row["target_failed"] = True if row["category"] in ("target_only_failure", "mixed_failure") else (
            False if row["category"] in ("pass", "non_target_only_failure") else None)
        print(json.dumps({"phase": "browser", "slot_id": slot_id,
                          "category": row["category"]}), flush=True)
    analysis = {**FLAGS, "schema_version": "openproject-remaining-analysis/v1",
        "case_id": "openproject-derive-remaining-hours", "planned_slots": 18,
        "calls_attempted": calls, "stop_reason": stop_reason,
        "counts": {model: {arm: {category: sum(1 for row in rows if row["model"] == model
            and row["arm"] == arm and row["category"] == category)
            for category in sorted({row["category"] for row in rows})} for arm in freeze.ARMS}
            for model in freeze.MODELS},
        "rows": rows, "claims": manifest["claims"]}
    put(packet / "results.json", rows)
    put(packet / "analysis.json", analysis)
    put(packet / "receipt.json", {"files": hash_inventory(packet)})
    return analysis


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)
    setup = sub.add_parser("prepare")
    setup.add_argument("--parent", required=True, type=Path)
    setup.add_argument("--destination", required=True, type=Path)
    setup.add_argument("--executable", required=True, type=Path)
    execute_cmd = sub.add_parser("run")
    execute_cmd.add_argument("--packet", required=True, type=Path)
    args = parser.parse_args()
    result = prepare(args.parent, args.destination, args.executable) if args.command == "prepare" else run(args.packet)
    print(json.dumps(result, indent=2))
