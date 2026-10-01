"""Outcome-aware replication of the frozen RealWorld comment Delete pilot."""
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
from scripts.kanboard_duplicate_collect import execute
from scripts.persistence_collection import hash_file, hash_inventory, html_bytes, put, verify_inventory

IMAGE = "sha256:00d1265095773b7f8a12aa73e81d0bab75563cbd672dd0b5d91783ea1b6d4400"
SEED = 2026100103
MODELS = ("gpt-5.6-luna", "gpt-5.6-sol")
ARMS = ("A", "B", "C")
REPETITIONS = (1, 2, 3)
FIXTURE = ROOT / "eval/fixtures/realworld-comment-delete"
QUALIFICATION = Path("/Users/dantecosta/Documents/GitHub/.private-research-evidence/realworld-comment-delete-qualification-20260927-v3")
REVIEW = Path("/Users/dantecosta/Documents/GitHub/.private-research-evidence/realworld-comment-delete-prompt-review-20260927-v4")
ADJUDICATION = Path("/Users/dantecosta/Documents/GitHub/.private-research-evidence/realworld-comment-delete-adjudication-20260927-v4")
SOURCE = ROOT / "data/criteria-expansion/sources/realworld/docs__src__content__docs__specifications__frontend__routing.md"
LICENSE = ROOT / "data/criteria-expansion/sources/realworld/LICENSE"
ARM_FILE = ROOT / "data/e2e-realworld-comment-delete/arms-20260927-v4.json"
MARKER = "/* MODEL_BEHAVIOR */"
PRIOR_PACKET = Path("/Users/dantecosta/Documents/GitHub/.private-research-evidence/realworld-comment-delete-pilot-20260927-v4")
SELECTION = ROOT / "data/prospective-h1-six-20261001/selection.json"
RUNTIME = (Path(__file__), ROOT / "agents/codex_cli.py", ROOT / "agents/providers.py",
           ROOT / "scripts/kanboard_duplicate_collect.py", ROOT / "scripts/persistence_collection.py",
           FIXTURE / "page.html", FIXTURE / "runner.cjs", FIXTURE / "qualify.py")


def schedule() -> list[dict]:
    rows = []
    for model in MODELS:
        for repetition in REPETITIONS:
            for arm in ARMS:
                key = json.dumps(["realworld-comment-delete-replication-20261001", model, repetition, arm, SEED])
                rows.append({"slot_id": "realworld-comment-rep-20261001-" + hashlib.sha256(key.encode()).hexdigest()[:24],
                             "intent_id": "realworld-comment-delete", "project_id": "realworld",
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
            "app API. Data shapes: app.viewer() returns a string; "
            "comment.author.username is a string. Register app.onView. Do not change any "
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
    verify_inventory(PRIOR_PACKET / "frozen")
    verify_inventory(PRIOR_PACKET)
    prior = json.loads((PRIOR_PACKET / "frozen/manifest.json").read_text())
    if (prior.get("schema_version") != "realworld-comment-delete-pilot/v4"
            or prior.get("planned_slots") != 18
            or prior.get("arms_sha256") != hash_file(ARM_FILE)
            or prior.get("source_sha256") != hash_file(SOURCE)
            or prior.get("license_sha256") != hash_file(LICENSE)
            or any(prior["runtime_sha256"].get(str(path.relative_to(ROOT))) != hash_file(path)
                   for path in RUNTIME if path != Path(__file__))):
        raise ValueError("earlier v4 source or instrument drift")
    for row in prior["schedule"]:
        old_request = json.loads((PRIOR_PACKET / "frozen/requests" / (row["slot_id"] + ".json")).read_text())
        if old_request != {"prompt": prompt(row["arm"])}:
            raise ValueError("earlier v4 prompt drift")
    if not SELECTION.is_file():
        raise ValueError("prospective selection missing")
    verify_inventory(QUALIFICATION)
    verify_inventory(REVIEW)
    verify_inventory(ADJUDICATION)
    qualification = json.loads((QUALIFICATION / "qualification.json").read_text())
    if (qualification.get("qualified") is not True or qualification.get("controls") != 11
            or qualification.get("image_id") != IMAGE
            or qualification.get("source_scaffold_sha256") != hash_file(FIXTURE / "page.html")
            or qualification.get("runner_sha256") != hash_file(FIXTURE / "runner.cjs")
            or qualification.get("qualifier_sha256") != hash_file(FIXTURE / "qualify.py")
            or any(row["expected"] != row["observed"] for row in qualification["cases"])):
        raise ValueError("browser qualification drift")
    votes = []
    for model in ("gpt-6-astra", "gpt-6-sol", "gpt-6-luna"):
        vote = json.loads((REVIEW / model / "parsed.json").read_text())
        votes.append(vote.get("verdict"))
        adjudication = json.loads((ADJUDICATION / model / "parsed.json").read_text())
        if adjudication.get("verdict") != "NO_MATERIAL_BLOCKER":
            raise ValueError("material review concern unresolved")
    if sorted(votes) != ["ACCEPT", "ACCEPT", "DEFER"]:
        raise ValueError("split prompt review drift")
    if "Delete comment button (only shown to comment's author)" not in SOURCE.read_text():
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
    manifest = {"schema_version": "realworld-comment-delete-replication/20261001-v1", "status": "pre_generation",
                "planned_slots": 18, "schedule": rows, "seed": SEED, "models": MODELS, "arms": ARMS,
                "source_sha256": hash_file(SOURCE), "license_sha256": hash_file(LICENSE),
                "arms_sha256": hash_file(ARM_FILE),
                "qualification_receipt_sha256": hash_file(QUALIFICATION / "receipt.json"),
                "review_receipt_sha256": hash_file(REVIEW / "receipt.json"),
                "adjudication_receipt_sha256": hash_file(ADJUDICATION / "receipt.json"),
                "prior_packet_receipt_sha256": hash_file(PRIOR_PACKET / "receipt.json"),
                "selection_sha256": hash_file(SELECTION),
                "runtime_sha256": hashes, "request_sha256": requests,
                "image_id": IMAGE, "executable": str(executable), "executable_sha256": hash_file(executable),
                "billing_mode": "chatgpt_subscription", "api_key_fallback": False,
                "retry_policy": "no_retry; resume_only_unattempted_slots_at_batch_boundaries", "generation_before_browser": True,
                "confirmatory_eligible": False, "human_approvals": 0}
    put(destination / "frozen/manifest.json", manifest)
    put(destination / "frozen/receipt.json", {"files": hash_inventory(destination / "frozen")})
    return manifest


def verify(packet: Path) -> dict:
    verify_inventory(packet / "frozen")
    manifest = json.loads((packet / "frozen/manifest.json").read_text())
    if (manifest.get("schema_version") != "realworld-comment-delete-replication/20261001-v1"
            or manifest.get("schedule") != schedule() or manifest.get("planned_slots") != 18
            or manifest.get("source_sha256") != hash_file(SOURCE)
            or manifest.get("license_sha256") != hash_file(LICENSE)
            or manifest.get("arms_sha256") != hash_file(ARM_FILE)
            or manifest.get("qualification_receipt_sha256") != hash_file(QUALIFICATION / "receipt.json")
            or manifest.get("review_receipt_sha256") != hash_file(REVIEW / "receipt.json")
            or manifest.get("adjudication_receipt_sha256") != hash_file(ADJUDICATION / "receipt.json")
            or manifest.get("prior_packet_receipt_sha256") != hash_file(PRIOR_PACKET / "receipt.json")
            or manifest.get("selection_sha256") != hash_file(SELECTION)
            or manifest.get("runtime_sha256") != {str(path.relative_to(ROOT)): hash_file(path) for path in RUNTIME}
            or manifest.get("executable_sha256") != hash_file(Path(manifest["executable"]))):
        raise ValueError("frozen pilot drift")
    for row in manifest["schedule"]:
        path = packet / "frozen/requests" / (row["slot_id"] + ".json")
        if (manifest["request_sha256"][row["slot_id"]] != hash_file(path)
                or json.loads(path.read_text()) != {"prompt": prompt(row["arm"])}):
            raise ValueError("frozen request drift")
    return manifest


def generated_rows(packet: Path, slots: list[dict]) -> list[dict]:
    rows = []
    for slot in slots:
        call = packet / "calls" / slot["slot_id"]
        result_path = call / "generation-result.json"
        if result_path.is_file():
            result = json.loads(result_path.read_text())
            if any(result.get(key) != value for key, value in slot.items()):
                raise ValueError("generation result identity drift")
            rows.append(result)
        elif (call / "attempt.json").exists():
            rows.append({**slot, "category": "provider_error", "target_failed": None,
                         "error_type": "ambiguous_interrupted_attempt"})
        else:
            rows.append({**slot, "category": "not_attempted", "target_failed": None})
    return rows


def generate_batch(packet: Path, max_new_calls: int) -> dict:
    manifest = verify(packet)
    if not 1 <= max_new_calls <= 6 or (packet / "results.json").exists():
        raise ValueError("bounded batch and unfinished packet required")
    if not (packet / "run-started.json").exists():
        put(packet / "run-started.json", {"frozen_receipt_sha256": hash_file(packet / "frozen/receipt.json")})
    rows = generated_rows(packet, manifest["schedule"])
    if any(row["category"] == "provider_error" for row in rows):
        raise ValueError("provider failure or interrupted attempt; no additional calls")
    attempted = 0
    for row in rows:
        if (attempted == max_new_calls or row["category"] != "not_attempted"
                or (packet / "calls" / row["slot_id"] / "attempt.json").exists()):
            continue
        sid = row["slot_id"]
        request = packet / "frozen/requests" / (sid + ".json")
        call = packet / "calls" / sid
        put(call / "attempt.json", {"slot_id": sid, "request_sha256": hash_file(request)})
        attempted += 1
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
            row["category"] = "generated_pending_browser"
        put(call / "generation-result.json", row)
        print(json.dumps({"phase": "generation", "completed_calls": sum(
            (packet / "calls" / item["slot_id"] / "attempt.json").exists() for item in rows)}), flush=True)
    return {"batch_attempted": attempted, "planned": len(rows),
            "attempted_total": sum((packet / "calls" / item["slot_id"] / "attempt.json").exists() for item in rows)}


def execute_all_screenshots(image: str, inputs: Path, output: Path, runner: Path, qualifier: Path) -> dict:
    result = execute(image, inputs, output, runner, qualifier)
    report_path = output / "report.json"
    if report_path.is_file() and json.loads(report_path.read_text()).get("status") == "complete":
        for name in ("fixture-3.png", "fixture-4.png"):
            path = output / name
            if not path.is_file() or not path.read_bytes().startswith(b"\x89PNG\r\n\x1a\n"):
                result["category"] = "browser_error"
            else:
                result["screenshots"][name] = hash_file(path)
    return result


def finalize(packet: Path) -> dict:
    manifest = verify(packet)
    if (packet / "results.json").exists():
        raise FileExistsError("results already finalized")
    rows = generated_rows(packet, manifest["schedule"])
    put(packet / "collection.json", rows)
    runner = packet / "frozen/runtime" / (FIXTURE / "runner.cjs").relative_to(ROOT)
    qualifier = packet / "frozen/runtime" / (FIXTURE / "qualify.py").relative_to(ROOT)
    for row in rows:
        if not row.get("generation_valid"):
            continue
        sid = row["slot_id"]
        try:
            result = execute_all_screenshots(IMAGE, packet / "artifacts" / sid, packet / "execution" / sid,
                             runner, qualifier)
        except Exception as error:
            result = {"category": "browser_error", "error_type": type(error).__name__}
        row["category"] = result["category"]
        row["target_failed"] = (True if row["category"] in ("target_only_failure", "mixed_failure")
                                else False if row["category"] in ("pass", "non_target_only_failure") else None)
        row["execution"] = result
        print(json.dumps({"phase": "browser", "slot_id": sid, "category": row["category"]}), flush=True)
    result = {"schema_version": "realworld-comment-delete-replication-results/20261001-v1", "planned_slots": 18,
              "attempted_calls": sum((packet / "calls" / row["slot_id"] / "attempt.json").exists() for row in rows),
              "counts": {model: {arm: dict(Counter(row["category"] for row in rows if row["model"] == model
                                                   and row["arm"] == arm)) for arm in ARMS} for model in MODELS},
              "rows": rows, "confirmatory_eligible": False}
    put(packet / "results.json", result)
    put(packet / "receipt.json", {"files": hash_inventory(packet)})
    return result


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("mode", choices=("prepare", "generate-batch", "finalize"))
    parser.add_argument("--packet", required=True, type=Path)
    parser.add_argument("--executable", type=Path, default=Path("/opt/homebrew/bin/codex"))
    parser.add_argument("--max-new-calls", type=int, default=3)
    args = parser.parse_args()
    if args.mode == "prepare":
        result = prepare(args.packet, args.executable)
    elif args.mode == "generate-batch":
        result = generate_batch(args.packet, args.max_new_calls)
    else:
        result = finalize(args.packet)
    print(json.dumps(result))
