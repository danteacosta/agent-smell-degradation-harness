"""Freeze and run the reviewed RealWorld article-author collection once."""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import re
import runpy
import subprocess
import sys


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from agents.codex_cli import CodexCLIProvider
from agents.providers import ProviderRequest
from eval.realworld_author_ui_executor import execute
from scripts import realworld_author_admission as admission
from scripts.behavioral_expansion import summarize
from scripts.persistence_collection import (
    hash_inventory,
    html_bytes,
    now,
    put,
    sync_directory,
    validate_preflight,
    verify_inventory,
)


ADMISSION_DIRECTORY = (
    ROOT / "data/behavioral-expansion/realworld-author-ui-admission-20260925"
)
ADMISSION_RECEIPT_SHA256 = (
    "bd7a3a13a8f5c481df0908848846f6e4bb644bf52653c128ac532742357f1a0d"
)
INSTRUMENT_SHA256 = "526a2aee0264ac81e4c318ad6b9c58d968113bae7dc41d776d40b3500112434e"
CI_QUALIFICATION_SHA256 = (
    "cf5baf358bc64914f16e1023eb48f34d73c9034127d9b02079dcfe8f4006a820"
)
CI_IMAGE_ID = "sha256:bfa780d015f8549cd70f4ece4d48e2fa51a4d8399322661314001e564021f617"
LOCAL_IMAGE_ID = "sha256:ed4bc5071528d2340f1353d78adce12ba9a9993edffff97b1e89cbfb97ada441"
LOCAL_QUALIFICATION_SHA256 = (
    "98f4b6feec928291133187a2e9dfa4c83d08563d93671d584a30b139fb78f992"
)
FLAGS = {
    "confirmatory_eligible": False,
    "human_approvals": 0,
    "label_source": "independent_behavioral_oracle",
}
INTENT_ID = "realworld-article-author"
PROJECT_ID = "realworld"


def hash_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _runtime_paths() -> list[Path]:
    paths = set()
    for folder in ("agents", "protocol", "eval", "scripts"):
        paths.update((ROOT / folder).rglob("*.py"))
    paths.update(_instrument_paths())
    return sorted(paths)


def _instrument_paths() -> list[Path]:
    fixture = ROOT / "eval/fixtures/realworld-author-ui"
    paths = [path for path in fixture.iterdir() if path.is_file()]
    paths.extend([
        ROOT / "eval/focus_chain_executor.py",
        ROOT / "eval/realworld_author_ui_executor.py",
        ROOT / "tests/test_realworld_author_ui_executor.py",
    ])
    return sorted(paths, key=lambda path: path.relative_to(ROOT).as_posix())


def _instrument_digest(paths: list[Path]) -> str:
    combined = hashlib.sha256()
    for path in paths:
        relative = path.relative_to(ROOT).as_posix().encode()
        raw = path.read_bytes()
        combined.update(len(relative).to_bytes(8, "big"))
        combined.update(relative)
        combined.update(len(raw).to_bytes(8, "big"))
        combined.update(raw)
    return combined.hexdigest()


def runtime_hashes() -> dict[str, str]:
    return {
        str(path.relative_to(ROOT)): hash_file(path)
        for path in _runtime_paths()
    }


def _validate_parent(parent: Path) -> dict:
    manifest = admission.validate_materialized(parent)
    if hash_file(parent / "receipt.json") != ADMISSION_RECEIPT_SHA256:
        raise ValueError("canonical admission receipt drift")
    return manifest


def _canonical_request(row: dict) -> bytes:
    prompt = admission.build_prompt_bundle()["requests"][row["arm"]]
    return admission.json_bytes({"prompt": prompt})


def _qualification_contract() -> tuple[dict, dict]:
    namespace = runpy.run_path(
        str(ROOT / "eval/fixtures/realworld-author-ui/qualify.py")
    )
    regular = namespace["EXPECTED"]
    operational = {
        **namespace["OPERATIONAL_HTML_EXPECTED"],
        **namespace["OPERATIONAL_EXPECTED"],
    }
    return regular, operational


def _validate_instrument_custody(commit: str, paths: list[Path]) -> None:
    relative_paths = [str(item.relative_to(ROOT)) for item in paths]
    head = subprocess.run(
        ["git", "rev-parse", "HEAD"], cwd=ROOT, check=True,
        capture_output=True, text=True, timeout=30,
    ).stdout.strip()
    exists = subprocess.run(
        ["git", "cat-file", "-e", f"{commit}^{{commit}}"], cwd=ROOT,
        capture_output=True, text=True, timeout=30,
    )
    if exists.returncode != 0:
        raise ValueError("local qualification custody commit does not exist")
    ancestor = subprocess.run(
        ["git", "merge-base", "--is-ancestor", commit, head], cwd=ROOT,
        capture_output=True, text=True, timeout=30,
    )
    if ancestor.returncode != 0:
        raise ValueError("local qualification custody commit is not ancestral")
    committed_diff = subprocess.run(
        ["git", "diff", "--quiet", commit, head, "--", *relative_paths],
        cwd=ROOT, capture_output=True, text=True, timeout=30,
    )
    if committed_diff.returncode != 0:
        raise ValueError("local qualification instrument changed after custody")
    dirty = subprocess.run(
        ["git", "status", "--porcelain", "--", *relative_paths],
        cwd=ROOT, check=True, capture_output=True, text=True, timeout=30,
    ).stdout
    if dirty:
        raise ValueError("local qualification instrument files changed")


def _validate_local_qualification(path: Path, image_id: str) -> tuple[dict, bytes, Path]:
    if re.fullmatch(r"sha256:[0-9a-f]{64}", image_id) is None:
        raise ValueError("explicit immutable local image id required")
    resolved = path.resolve(strict=True)
    manifest_path = resolved / "qualification.json" if resolved.is_dir() else resolved
    root = manifest_path.parent
    raw = manifest_path.read_bytes()
    try:
        value = json.loads(raw)
    except (UnicodeDecodeError, json.JSONDecodeError) as error:
        raise ValueError("local qualification evidence invalid") from error
    custody = value.get("custody") if isinstance(value, dict) else None
    if (
        not isinstance(value, dict)
        or set(value) != {
            "schema_version", "qualified", "matrix_matches", "custody",
            "image_id", "instrument_sha256", "source", "cases",
            "operational_cases", "files", "limitations",
        }
        or value.get("schema_version") != "realworld-author-ui-qualification/v1"
        or value.get("qualified") is not True
        or value.get("matrix_matches") is not True
        or value.get("image_id") != image_id
        or value.get("instrument_sha256") != INSTRUMENT_SHA256
        or not isinstance(custody, dict)
        or custody.get("mode") != "git-commit"
        or re.fullmatch(r"[0-9a-f]{40}", str(custody.get("git_commit", ""))) is None
    ):
        raise ValueError("local qualification evidence mismatch")
    paths = _instrument_paths()
    current_files = {
        item.relative_to(ROOT).as_posix(): hash_file(item) for item in paths
    }
    if (
        len(paths) != 34
        or value.get("files") != current_files
        or _instrument_digest(paths) != INSTRUMENT_SHA256
        or value.get("source") != {
            "revision": admission.SOURCE_REVISION,
            "sha256": admission.SOURCE_SHA256,
        }
    ):
        raise ValueError("local qualification instrument custody mismatch")
    _validate_instrument_custody(custody["git_commit"], paths)

    regular_expected, operational_expected = _qualification_contract()
    cases = value.get("cases")
    operational_cases = value.get("operational_cases")
    if (
        not isinstance(cases, list)
        or not isinstance(operational_cases, list)
        or not all(isinstance(row, dict) for row in cases)
        or not all(isinstance(row, dict) for row in operational_cases)
        or [row.get("id") for row in cases] != list(regular_expected)
        or [row.get("id") for row in operational_cases] != list(operational_expected)
        or len(cases) != 20
        or len(operational_cases) != 4
    ):
        raise ValueError("local qualification case matrix mismatch")

    expected_inventory = {"qualification.json"}
    for row, is_regular in [*((item, True) for item in cases), *((item, False) for item in operational_cases)]:
        case_id = row["id"]
        required_fields = (
            {"id", "expected", "observed", "matches", "receipt_fields_exact",
             "report_status", "receipt_sha256", "report_sha256", "screenshot_sha256"}
            if is_regular else
            {"id", "expected", "observed", "matches", "receipt_sha256",
             "report_sha256", "screenshot_sha256"}
        )
        if set(row) != required_fields:
            raise ValueError("local qualification row shape mismatch")
        expected = regular_expected[case_id] if is_regular else {
            key: item for key, item in operational_expected[case_id].items() if key != "flag"
        }
        if row.get("expected") != expected or row.get("observed") != expected or row.get("matches") is not True:
            raise ValueError("local qualification expected observation mismatch")
        if is_regular and (
            row.get("receipt_fields_exact") is not True
            or row.get("report_status") != "complete"
        ):
            raise ValueError("local qualification receipt contract mismatch")
        case_root = root / case_id
        input_path = case_root / "input/app.html"
        output = case_root / "output"
        base_files = {
            f"{case_id}/input/app.html",
            f"{case_id}/output/container-command.json",
            f"{case_id}/output/container.log",
            f"{case_id}/output/executor.json",
            f"{case_id}/output/report.json",
        }
        expected_inventory.update(base_files)
        report_path = output / "report.json"
        receipt_path = output / "executor.json"
        if (
            row.get("report_sha256") != hash_file(report_path)
            or row.get("receipt_sha256") != hash_file(receipt_path)
        ):
            raise ValueError("local qualification report or receipt hash mismatch")
        report = json.loads(report_path.read_text())
        receipt = json.loads(receipt_path.read_text())
        app_hash = hash_file(input_path)
        if report.get("app_sha256") != app_hash or receipt.get("app_sha256") != app_hash:
            raise ValueError("local qualification staged app hash mismatch")
        screenshots = row.get("screenshot_sha256")
        if not isinstance(screenshots, dict):
            raise ValueError("local qualification screenshot inventory invalid")
        actual_screenshots = {
            item.name: hash_file(item) for item in sorted(output.glob("*.png"))
        }
        if screenshots != actual_screenshots:
            raise ValueError("local qualification screenshot hash mismatch")
        for name in screenshots:
            screenshot = output / name
            if not screenshot.read_bytes().startswith(b"\x89PNG\r\n\x1a\n"):
                raise ValueError("local qualification screenshot invalid")
            expected_inventory.add(f"{case_id}/output/{name}")
    actual_inventory = {
        str(item.relative_to(root))
        for item in root.rglob("*")
        if item.is_file() and "__pycache__" not in item.parts and item.suffix != ".pyc"
    }
    if actual_inventory != expected_inventory or len(actual_inventory) != 201:
        raise ValueError("local qualification evidence inventory mismatch")
    return value, raw, root


def _normalized_slots(rows: list[dict]) -> list[dict]:
    return [
        {
            "slot_id": row["slot_id"],
            "intent_id": INTENT_ID,
            "project_id": PROJECT_ID,
            "model": row["model"],
            "replication": row["replication"],
            "variant": row["arm"],
        }
        for row in rows
    ]


def _validate_schedule(rows: object) -> list[dict]:
    if rows != admission.build_schedule() or not isinstance(rows, list) or len(rows) != 18:
        raise ValueError("canonical 18-slot schedule drift")
    normalized = _normalized_slots(rows)
    summarize(normalized, [])
    if any(re.fullmatch(r"rw-[0-9a-f]{24}", row["slot_id"]) is None for row in rows):
        raise ValueError("opaque slot identifier drift")
    return rows


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
    _, qualification_bytes, qualification_root = _validate_local_qualification(
        qualification, image_id
    )
    if (
        image_id != LOCAL_IMAGE_ID
        or hashlib.sha256(qualification_bytes).hexdigest()
        != LOCAL_QUALIFICATION_SHA256
    ):
        raise ValueError("approved local qualification binding mismatch")
    parent = parent.resolve(strict=True)
    parent_manifest = _validate_parent(parent)
    schedule_bytes = (parent / "schedule.json").read_bytes()
    if schedule_bytes != admission.json_bytes(admission.build_schedule()):
        raise ValueError("canonical admission schedule drift")
    rows = _validate_schedule(json.loads(schedule_bytes))
    for row in rows:
        request = parent / "requests" / f"{row['slot_id']}.json"
        if request.read_bytes() != _canonical_request(row):
            raise ValueError("canonical admission request drift")

    if not destination.is_absolute() or destination.parent.is_symlink():
        raise ValueError("absolute private destination required")
    if destination.resolve().is_relative_to(ROOT):
        raise ValueError("private destination must be outside repository")
    executable = executable.resolve(strict=True)
    version = subprocess.run(
        [str(executable), "--version"],
        capture_output=True,
        text=True,
        check=True,
        timeout=15,
    ).stdout.strip()
    auth = subprocess.run(
        [str(executable), "login", "status"],
        capture_output=True,
        text=True,
        timeout=15,
    )
    if auth.returncode != 0 or "Logged in using ChatGPT" not in (
        auth.stdout + auth.stderr
    ):
        raise ValueError("Codex CLI ChatGPT authentication required")

    destination.mkdir(mode=0o700, parents=True, exist_ok=False)
    sync_directory(destination.parent)
    sync_directory(destination)
    frozen = destination / "frozen"
    put(frozen / "admission-receipt.json", (parent / "receipt.json").read_bytes())
    put(frozen / "admission-manifest.json", (parent / "manifest.json").read_bytes())
    put(frozen / "independent-review.json", (parent / "independent-review.json").read_bytes())
    put(frozen / "local-qualification.json", qualification_bytes)
    put(frozen / "schedule.json", schedule_bytes)
    for row in rows:
        relative = Path("requests") / f"{row['slot_id']}.json"
        put(frozen / relative, (parent / relative).read_bytes())

    hashes = runtime_hashes()
    for relative in hashes:
        put(frozen / "runtime" / relative, (ROOT / relative).read_bytes())

    manifest = {
        **FLAGS,
        "schema_version": "realworld-author-collection/v1",
        "frozen_at_utc": now(),
        "parent": str(parent),
        "parent_receipt_sha256": ADMISSION_RECEIPT_SHA256,
        "parent_review_sha256": parent_manifest["review"]["evidence_sha256"],
        "executable": str(executable),
        "executable_sha256": hash_file(executable),
        "cli_version": version,
        "runtime_hashes": hashes,
        "preflight": preflight,
        "image_id": LOCAL_IMAGE_ID,
        "instrument_sha256": parent_manifest["instrument"]["instrument_sha256"],
        "local_qualification": str(qualification_root),
        "local_qualification_sha256": LOCAL_QUALIFICATION_SHA256,
        "ci_qualification_sha256": CI_QUALIFICATION_SHA256,
        "ci_image_id": CI_IMAGE_ID,
        "scope": parent_manifest["scope"],
        "max_calls": 18,
        "concurrency": 1,
        "reasoning_effort": "low",
        "timeout_seconds": 180,
        "retry_policy": "no_retry_no_resume_no_repair",
        "billing_mode": "chatgpt_subscription",
        "api_key_fallback": False,
        "output_admission": "raw HTML document; no fence removal, extraction, normalization or repair",
        "artifact_limit_bytes": 200000,
        "capture_limit_bytes_per_stream": 2000000,
        "provider_calls": 0,
        "experimental_results": False,
        "h1_supported": False,
        "h2_supported": False,
    }
    put(frozen / "manifest.json", manifest)
    put(frozen / "receipt.json", {"files": hash_inventory(frozen)})
    return manifest


def _validate_manifest_policy(manifest: dict) -> None:
    expected_fields = {
        *FLAGS,
        "schema_version", "frozen_at_utc", "parent", "parent_receipt_sha256",
        "parent_review_sha256", "executable", "executable_sha256", "cli_version",
        "runtime_hashes", "preflight", "image_id", "instrument_sha256",
        "local_qualification", "local_qualification_sha256",
        "ci_qualification_sha256", "ci_image_id", "scope", "max_calls",
        "concurrency", "reasoning_effort", "timeout_seconds", "retry_policy",
        "billing_mode", "api_key_fallback", "output_admission",
        "artifact_limit_bytes", "capture_limit_bytes_per_stream", "provider_calls",
        "experimental_results", "h1_supported", "h2_supported",
    }
    if set(manifest) != expected_fields:
        raise ValueError("frozen manifest shape drift")
    expected = {
        **FLAGS,
        "schema_version": "realworld-author-collection/v1",
        "parent_receipt_sha256": ADMISSION_RECEIPT_SHA256,
        "instrument_sha256": INSTRUMENT_SHA256,
        "ci_qualification_sha256": CI_QUALIFICATION_SHA256,
        "ci_image_id": CI_IMAGE_ID,
        "image_id": LOCAL_IMAGE_ID,
        "local_qualification_sha256": LOCAL_QUALIFICATION_SHA256,
        "max_calls": 18,
        "concurrency": 1,
        "reasoning_effort": "low",
        "timeout_seconds": 180,
        "retry_policy": "no_retry_no_resume_no_repair",
        "billing_mode": "chatgpt_subscription",
        "api_key_fallback": False,
        "output_admission": "raw HTML document; no fence removal, extraction, normalization or repair",
        "artifact_limit_bytes": 200000,
        "capture_limit_bytes_per_stream": 2000000,
        "provider_calls": 0,
        "experimental_results": False,
        "h1_supported": False,
        "h2_supported": False,
    }
    if any(manifest.get(key) != value for key, value in expected.items()):
        raise ValueError("frozen execution policy drift")
    string_hashes = ("parent_review_sha256", "executable_sha256", "local_qualification_sha256")
    if any(re.fullmatch(r"[0-9a-f]{64}", str(manifest.get(key, ""))) is None for key in string_hashes):
        raise ValueError("frozen manifest hash binding invalid")
    if not isinstance(manifest.get("cli_version"), str) or not manifest["cli_version"]:
        raise ValueError("frozen CLI version invalid")


def verify_execution(packet: Path) -> tuple[dict, list[dict]]:
    if packet.is_symlink() or not packet.is_dir() or packet.stat().st_mode & 0o077:
        raise ValueError("private real packet required")
    frozen = packet / "frozen"
    verify_inventory(frozen)
    manifest = json.loads((frozen / "manifest.json").read_text())
    _validate_manifest_policy(manifest)
    validate_preflight(manifest["preflight"])
    if manifest.get("max_calls") != 18:
        raise ValueError("call bound drift")
    if (
        manifest.get("concurrency") != 1
        or manifest.get("reasoning_effort") != "low"
        or manifest.get("retry_policy") != "no_retry_no_resume_no_repair"
        or manifest.get("api_key_fallback") is not False
    ):
        raise ValueError("execution policy drift")
    if hash_file(Path(manifest["executable"])) != manifest["executable_sha256"]:
        raise ValueError("executable drift")
    _, qualification_bytes, _ = _validate_local_qualification(
        Path(manifest["local_qualification"]), manifest["image_id"]
    )
    if (
        hashlib.sha256(qualification_bytes).hexdigest()
        != manifest["local_qualification_sha256"]
        or (frozen / "local-qualification.json").read_bytes() != qualification_bytes
    ):
        raise ValueError("local qualification drift")
    if (
        manifest.get("ci_qualification_sha256") != CI_QUALIFICATION_SHA256
        or manifest.get("ci_image_id") != CI_IMAGE_ID
        or manifest.get("instrument_sha256") != INSTRUMENT_SHA256
    ):
        raise ValueError("qualification provenance drift")
    hashes = runtime_hashes()
    if hashes != manifest["runtime_hashes"]:
        raise ValueError("runtime drift")
    for relative, expected in hashes.items():
        frozen_path = frozen / "runtime" / relative
        if not frozen_path.is_file() or hash_file(frozen_path) != expected:
            raise ValueError("frozen runtime drift")

    parent = Path(manifest["parent"])
    parent_manifest = _validate_parent(parent)
    if parent_manifest["review"]["evidence_sha256"] != manifest["parent_review_sha256"]:
        raise ValueError("parent review drift")
    if (frozen / "admission-receipt.json").read_bytes() != (parent / "receipt.json").read_bytes():
        raise ValueError("frozen admission receipt drift")
    if (frozen / "admission-manifest.json").read_bytes() != (parent / "manifest.json").read_bytes():
        raise ValueError("frozen admission manifest drift")
    if (frozen / "independent-review.json").read_bytes() != (parent / "independent-review.json").read_bytes():
        raise ValueError("frozen independent review drift")

    schedule_bytes = frozen.joinpath("schedule.json").read_bytes()
    if schedule_bytes != admission.json_bytes(admission.build_schedule()):
        raise ValueError("canonical frozen schedule drift")
    rows = _validate_schedule(json.loads(schedule_bytes))
    if schedule_bytes != (parent / "schedule.json").read_bytes():
        raise ValueError("parent schedule drift")
    for row in rows:
        relative = Path("requests") / f"{row['slot_id']}.json"
        raw = (frozen / relative).read_bytes()
        if raw != _canonical_request(row) or raw != (parent / relative).read_bytes():
            raise ValueError("canonical frozen request drift")
    return manifest, rows


def _analysis_category(outcome: dict) -> tuple[str, bool | None]:
    category = outcome.get("category")
    failed_assertions = outcome.get("target_failed")
    if isinstance(failed_assertions, list) and failed_assertions:
        return "target_only_failure", True
    if category == "pass":
        return "pass", False
    if category == "target_only_failure":
        return "target_only_failure", True
    if category == "target_not_evaluable":
        return "target_not_evaluable", None
    return "browser_error", None


def run(
    packet: Path,
    provider_factory=CodexCLIProvider,
    executor=execute,
) -> dict:
    manifest, schedule = verify_execution(packet)
    put(packet / "run-started.json", {"started_at_utc": now(), "policy": "no_resume", **FLAGS})
    normalized = _normalized_slots(schedule)
    rows = [
        {**slot, "category": "not_attempted", "target_failed": None}
        for slot in normalized
    ]
    put(packet / "initial-observations.json", rows)
    state = {**FLAGS, "calls_attempted": 0, "stop_reason": None, "rows": rows}

    for source, row in zip(schedule, rows):
        if state["stop_reason"]:
            break
        slot_id = row["slot_id"]
        request_path = packet / "frozen/requests" / f"{slot_id}.json"
        request = json.loads(request_path.read_text())
        call = packet / "calls" / slot_id
        put(
            call / "attempt.json",
            {
                "slot_id": slot_id,
                "started_at_utc": now(),
                "model": source["model"],
                "request_sha256": hash_file(request_path),
            },
        )
        state["calls_attempted"] += 1
        try:
            provider = provider_factory(
                executable=manifest["executable"],
                model=source["model"],
                timeout_seconds=manifest["timeout_seconds"],
                evidence_directory=call / "capture",
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
                put(packet / "artifacts" / slot_id / "app.html", artifact)
                row["generation_valid"] = True
        put(call / "generation-result.json", row)
        print(json.dumps({"completed_calls": state["calls_attempted"], "phase": "generation"}), flush=True)

    put(packet / "collection.json", state)
    for row in rows:
        if not row.get("generation_valid"):
            continue
        try:
            outcome = executor(
                image=manifest["image_id"],
                inputs=packet / "artifacts" / row["slot_id"],
                output=packet / "execution" / row["slot_id"],
            )
        except Exception as error:
            outcome = {"category": "browser_error", "error_type": type(error).__name__}
        category, failed = _analysis_category(outcome)
        row.update(category=category, target_failed=failed, execution=outcome)

    put(packet / "results.json", state)
    analysis = summarize(normalized, rows)
    analysis.update(
        **FLAGS,
        calls_attempted=state["calls_attempted"],
        stop_reason=state["stop_reason"],
        scope=manifest["scope"],
    )
    put(packet / "analysis.json", analysis)
    put(packet / "receipt.json", {"files": hash_inventory(packet)})
    return analysis


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest="command", required=True)
    prepare_command = commands.add_parser("prepare")
    for name in ("parent", "destination", "executable", "preflight"):
        prepare_command.add_argument("--" + name, type=Path, required=True)
    prepare_command.add_argument("--image-id", required=True)
    prepare_command.add_argument("--qualification", type=Path, required=True)
    commands.add_parser("run").add_argument("--packet", type=Path, required=True)
    args = parser.parse_args()
    result = (
        prepare(
            args.parent,
            args.destination,
            args.executable,
            json.loads(args.preflight.read_text()),
            image_id=args.image_id,
            qualification=args.qualification,
        )
        if args.command == "prepare"
        else run(args.packet)
    )
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
