"""Audit the private RealWorld collection and publish a bounded result bundle."""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import shutil
import struct
import sys

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from eval.realworld_author_ui_executor import classify_report
from scripts.behavioral_expansion import summarize
SOURCE_HASHES = {
    "receipt.json": "1bb56d83986f8d3ff6e50f2005da68382116ea8e6a5f2919a13f9f9e1552a625",
    "frozen/manifest.json": "28e659b7eb9424b3ca0dcc22fac5188dbce03f6f4ecd080e30547878cc11e046",
    "frozen/receipt.json": "1587ff4cc3e4c13b0f5035b2dd6b8aa402b5dee9f29b8fe1120a170e5ecb7f9e",
    "collection.json": "01d3f103474de4a04fb887fa9c74f64558d469539485cbfc5950380feb37dab1",
    "results.json": "fef7e9ec8a7102e85ef9938aff5355cddbe3c0ea55a10af5983c8442fcea6a8b",
    "analysis.json": "6090319e0bed99c6f20d2b435c961535ba7e7990304e5faa958e49a1633e5210",
}
SAMPLES = (
    ("luna-c-failure-nonauthor", "rw-f208b860b4a8581d093fe725", "article-alice-non-author.png"),
    ("sol-a-failure-nonauthor", "rw-228a72c565e30a6c89312d20", "article-alice-non-author.png"),
    ("sol-c-pass-nonauthor", "rw-269326a9008b406bcbc35921", "article-alice-non-author.png"),
    ("luna-b-unknown-author", "rw-1fcb4ac2a7f9d19e22d0dca0", "article-alice-author.png"),
)
FLAGS = {
    "confirmatory_eligible": False,
    "human_approvals": 0,
    "label_source": "independent_behavioral_oracle",
}
EXPECTED_USAGE = {
    "input_tokens": 392267,
    "cached_input_tokens": 150144,
    "cache_write_input_tokens": 0,
    "output_tokens": 25845,
    "reasoning_output_tokens": 3444,
}
APPROVED_PUBLIC_RECEIPT_SHA256 = (
    "2f20545d2119f660965db81ca838eb4c4c8c6563b918e627fd505f9db054a988"
)


def json_bytes(value: object) -> bytes:
    return (json.dumps(value, indent=2) + "\n").encode()


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def inventory(directory: Path, *, exclude: set[str] | None = None) -> dict[str, str]:
    excluded = exclude or set()
    result = {}
    for path in sorted(directory.rglob("*")):
        if path.is_symlink() or (not path.is_file() and not path.is_dir()):
            raise ValueError("only regular public evidence files and directories allowed")
        if path.is_file():
            relative = path.relative_to(directory).as_posix()
            if relative not in excluded:
                result[relative] = digest(path)
    return result


def _verify_receipt(directory: Path, receipt_name: str = "receipt.json") -> None:
    receipt = json.loads((directory / receipt_name).read_text())
    if set(receipt) != {"files"} or receipt["files"] != inventory(
        directory, exclude={receipt_name}
    ):
        raise ValueError("receipt inventory drift")


def _png_dimensions(path: Path) -> tuple[int, int]:
    raw = path.read_bytes()
    if len(raw) < 24 or raw[:16] != b"\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR":
        raise ValueError("invalid PNG evidence")
    return struct.unpack(">II", raw[16:24])


def _last_agent_message(path: Path) -> tuple[str, dict]:
    messages = []
    completed = []
    for line in path.read_text().splitlines():
        event = json.loads(line)
        if event.get("type") == "item.completed" and event.get("item", {}).get("type") == "agent_message":
            messages.append(event["item"].get("text"))
        if event.get("type") == "turn.completed":
            completed.append(event.get("usage"))
    if len(completed) != 1 or not messages or not isinstance(messages[-1], str):
        raise ValueError("incomplete captured provider event stream")
    return messages[-1], completed[0]


def _normalized(schedule: list[dict]) -> list[dict]:
    return [{
        "slot_id": row["slot_id"],
        "intent_id": "realworld-article-author",
        "project_id": "realworld",
        "model": row["model"],
        "replication": row["replication"],
        "variant": row["arm"],
    } for row in schedule]


def _validate_claims(ledger: dict, analysis: dict) -> None:
    rows = ledger.get("rows")
    if not isinstance(rows, list) or len(rows) != 18:
        raise ValueError("fixed denominator must contain 18 rows")
    counts = {model: sum(row.get("model") == model for row in rows) for model in (
        "gpt-5.6-luna", "gpt-5.6-sol")}
    if counts != {"gpt-5.6-luna": 9, "gpt-5.6-sol": 9}:
        raise ValueError("model allocation drift")
    if analysis.get("planned") != 18 or analysis.get("recorded_rows") != 18:
        raise ValueError("analysis denominator drift")
    if analysis.get("executable") != 17 or analysis.get("unknown") != 1:
        raise ValueError("analysis missingness drift")
    contrasts = {
        (row["model"], row["comparison"]): row["difference_bounds"]
        for row in analysis.get("contrasts", [])
    }
    expected = {
        ("gpt-5.6-luna", "C-A"): [1.0, 1.0],
        ("gpt-5.6-sol", "C-A"): [-1 / 3, -1 / 3],
        ("gpt-5.6-luna", "B-A"): [1 / 3, 2 / 3],
        ("gpt-5.6-sol", "B-A"): [-1 / 3, -1 / 3],
    }
    if contrasts != expected:
        raise ValueError("heterogeneous contrast claim drift")
    unknown = [row for row in rows if row.get("target_failed") is None]
    if len(unknown) != 1 or unknown[0].get("slot_id") != "rw-1fcb4ac2a7f9d19e22d0dca0":
        raise ValueError("unknown outcome drift")


def audit_private(source: Path) -> tuple[dict, dict, dict]:
    source = source.resolve(strict=True)
    for relative, expected in SOURCE_HASHES.items():
        if digest(source / relative) != expected:
            raise ValueError(f"private source hash drift: {relative}")
    _verify_receipt(source)
    _verify_receipt(source / "frozen")

    schedule = json.loads((source / "frozen/schedule.json").read_text())
    results = json.loads((source / "results.json").read_text())
    collection = json.loads((source / "collection.json").read_text())
    analysis = json.loads((source / "analysis.json").read_text())
    normalized = _normalized(schedule)
    if len(schedule) != 18 or len(results.get("rows", [])) != 18:
        raise ValueError("private fixed denominator drift")
    slot_ids = [row["slot_id"] for row in schedule]
    if len(set(slot_ids)) != 18:
        raise ValueError("private slot identity drift")
    expected_set = set(slot_ids)
    for name in ("calls", "artifacts", "execution"):
        found = {path.name for path in (source / name).iterdir() if path.is_dir()}
        if found != expected_set:
            raise ValueError(f"private {name} inventory drift")

    result_by_id = {row["slot_id"]: row for row in results["rows"]}
    ledger_rows = []
    usage_totals: dict[str, int] = {}
    png_count = 0
    generation_mtimes = []
    execution_mtimes = []
    for planned, normal in zip(schedule, normalized):
        slot_id = planned["slot_id"]
        call = source / "calls" / slot_id
        artifact = source / "artifacts" / slot_id / "app.html"
        execution = source / "execution" / slot_id
        attempt = json.loads((call / "attempt.json").read_text())
        generation = json.loads((call / "generation-result.json").read_text())
        metadata = json.loads((call / "provider-metadata.json").read_text())
        capture = json.loads((call / "capture/capture.json").read_text())
        response = (call / "response.txt").read_bytes()
        message, captured_usage = _last_agent_message(call / "capture/stdout.jsonl")
        if (
            attempt.get("slot_id") != slot_id
            or attempt.get("model") != planned["model"]
            or attempt.get("request_sha256") != digest(source / "frozen/requests" / f"{slot_id}.json")
            or generation != {**normal, "category": "not_attempted", "target_failed": None, "generation_valid": True}
            or response != message.encode()
            or response != artifact.read_bytes()
            or capture.get("returncode") != 0
            or capture.get("stdout", {}).get("truncated") is not False
            or capture.get("stderr", {}).get("truncated") is not False
            or metadata.get("billing_mode") != "chatgpt_subscription"
            or metadata.get("usage") != captured_usage
        ):
            raise ValueError(f"generation custody drift: {slot_id}")
        usage = metadata["usage"]
        if not isinstance(usage, dict) or any(type(value) is not int or value < 0 for value in usage.values()):
            raise ValueError("invalid provider usage")
        for key, value in usage.items():
            usage_totals[key] = usage_totals.get(key, 0) + value

        receipt = json.loads((execution / "executor.json").read_text())
        report_path = execution / "report.json"
        classified = classify_report(report_path.read_bytes(), receipt.get("returncode"))
        expected_classification = {
            key: receipt[key] for key in (
                "category", "target_failed", "target_not_evaluable", "not_evaluable_reasons")
        }
        if classified != expected_classification or receipt.get("app_sha256") != digest(artifact):
            raise ValueError(f"browser classification drift: {slot_id}")
        row = result_by_id.get(slot_id)
        failed = True if classified["category"] == "target_only_failure" else (
            False if classified["category"] == "pass" else None)
        if row != {**normal, "category": classified["category"], "target_failed": failed, "generation_valid": True, "execution": receipt}:
            raise ValueError(f"result row drift: {slot_id}")
        screenshots = sorted(execution.glob("*.png"))
        if len(screenshots) != 4 or any(_png_dimensions(path) != (1000, 720) for path in screenshots):
            raise ValueError(f"browser screenshot drift: {slot_id}")
        png_count += len(screenshots)
        generation_mtimes.append((call / "generation-result.json").stat().st_mtime_ns)
        execution_mtimes.append(report_path.stat().st_mtime_ns)
        ledger_rows.append({
            **normal,
            "category": classified["category"],
            "target_failed": failed,
            "target_assertions_failed": classified.get("target_failed", []),
            "target_assertions_not_evaluable": classified.get("target_not_evaluable", []),
            "artifact_sha256": digest(artifact),
            "report_sha256": digest(report_path),
            "executor_sha256": digest(execution / "executor.json"),
            "usage": usage,
        })

    if png_count != 72:
        raise ValueError("expected exactly 72 browser screenshots")
    collection_mtime = (source / "collection.json").stat().st_mtime_ns
    if not max(generation_mtimes) <= collection_mtime < min(execution_mtimes):
        raise ValueError("generation/browser phase ordering drift")
    if collection.get("calls_attempted") != 18 or collection.get("stop_reason") is not None:
        raise ValueError("collection completion drift")
    recomputed = summarize(normalized, results["rows"])
    recomputed.update(
        **FLAGS, calls_attempted=18, stop_reason=None,
        scope={
            "excluded": ["button click behavior", "backend authorization", "article deletion"],
            "included": "visibility of the Delete Article button",
        },
    )
    if recomputed != analysis:
        raise ValueError("analysis recomputation drift")
    ledger = {
        "schema_version": "realworld-author-ui-public-ledger/v1",
        "planned": 18,
        "recorded_rows": 18,
        "rows": ledger_rows,
    }
    _validate_claims(ledger, analysis)
    audit = {
        "models": {model: sum(row["model"] == model for row in normalized) for model in (
            "gpt-5.6-luna", "gpt-5.6-sol")},
        "usage": usage_totals,
        "screenshots": 72,
        "classifications_recomputed": 18,
        "generation_before_browser": True,
    }
    return ledger, analysis, audit


def _manifest(source: Path, ledger: dict, analysis: dict, audit: dict) -> dict:
    samples = []
    lookup = {row["slot_id"]: row for row in ledger["rows"]}
    for sample_id, slot_id, screenshot in SAMPLES:
        source_image = source / "execution" / slot_id / screenshot
        row = lookup[slot_id]
        samples.append({
            "id": sample_id,
            "slot_id": slot_id,
            "model": row["model"],
            "variant": row["variant"],
            "category": row["category"],
            "context": "non-author" if "nonauthor" in sample_id else "author",
            "file": f"screenshots/{sample_id}.png",
            "sha256": digest(source_image),
            "dimensions": [1000, 720],
        })
    return {
        "schema_version": "realworld-author-ui-results/v1",
        "status": "bounded_exploratory_second_project_e2e",
        "source_sha256": SOURCE_HASHES,
        "audit": audit,
        "claims": {
            "finding": "heterogeneous_effect",
            "luna_c_minus_a": [1.0, 1.0],
            "sol_c_minus_a": [-1 / 3, -1 / 3],
            "unknown": {"count": 1, "slot_id": "rw-1fcb4ac2a7f9d19e22d0dca0", "variant": "B"},
            "b_is_sensitivity_control": True,
            "h1_supported": False,
            "h2_supported": False,
        },
        "samples": samples,
        "privacy": {
            "included": ["manifest", "ledger", "analysis", "four preselected screenshots"],
            "excluded": ["prompts", "generated HTML", "raw provider captures", "private filesystem paths"],
        },
        "ledger_sha256": hashlib.sha256(json_bytes(ledger)).hexdigest(),
        "analysis_sha256": hashlib.sha256(json_bytes(analysis)).hexdigest(),
    }


def materialize(source: Path, destination: Path) -> dict:
    if destination.exists():
        raise FileExistsError(destination)
    ledger, analysis, audit = audit_private(source)
    manifest = _manifest(source, ledger, analysis, audit)
    destination.mkdir(parents=True)
    (destination / "screenshots").mkdir()
    (destination / "manifest.json").write_bytes(json_bytes(manifest))
    (destination / "ledger.json").write_bytes(json_bytes(ledger))
    (destination / "analysis.json").write_bytes(json_bytes(analysis))
    for sample, (_, slot_id, screenshot) in zip(manifest["samples"], SAMPLES):
        shutil.copyfile(
            source / "execution" / slot_id / screenshot,
            destination / sample["file"],
        )
    (destination / "receipt.json").write_bytes(json_bytes({
        "files": inventory(destination, exclude={"receipt.json"})
    }))
    validate_materialized(destination, source)
    return manifest


def validate_public(directory: Path) -> dict:
    if (
        APPROVED_PUBLIC_RECEIPT_SHA256 is not None
        and digest(directory / "receipt.json") != APPROVED_PUBLIC_RECEIPT_SHA256
    ):
        raise ValueError("approved public receipt drift")
    _verify_receipt(directory)
    allowed = {"manifest.json", "ledger.json", "analysis.json", "receipt.json", *(
        f"screenshots/{sample_id}.png" for sample_id, _, _ in SAMPLES)}
    if set(inventory(directory)) != allowed:
        raise ValueError("public result surface drift")
    manifest = json.loads((directory / "manifest.json").read_text())
    ledger = json.loads((directory / "ledger.json").read_text())
    analysis = json.loads((directory / "analysis.json").read_text())
    if (
        set(manifest) != {
            "schema_version", "status", "source_sha256", "audit", "claims",
            "samples", "privacy", "ledger_sha256", "analysis_sha256",
        }
        or manifest.get("schema_version") != "realworld-author-ui-results/v1"
        or manifest.get("status") != "bounded_exploratory_second_project_e2e"
        or manifest.get("source_sha256") != SOURCE_HASHES
        or manifest.get("audit") != {
            "models": {"gpt-5.6-luna": 9, "gpt-5.6-sol": 9},
            "usage": EXPECTED_USAGE,
            "screenshots": 72,
            "classifications_recomputed": 18,
            "generation_before_browser": True,
        }
        or manifest.get("claims") != {
            "finding": "heterogeneous_effect",
            "luna_c_minus_a": [1.0, 1.0],
            "sol_c_minus_a": [-1 / 3, -1 / 3],
            "unknown": {"count": 1, "slot_id": "rw-1fcb4ac2a7f9d19e22d0dca0", "variant": "B"},
            "b_is_sensitivity_control": True,
            "h1_supported": False,
            "h2_supported": False,
        }
        or manifest.get("privacy") != {
            "included": ["manifest", "ledger", "analysis", "four preselected screenshots"],
            "excluded": ["prompts", "generated HTML", "raw provider captures", "private filesystem paths"],
        }
        or manifest.get("ledger_sha256") != digest(directory / "ledger.json")
        or manifest.get("analysis_sha256") != digest(directory / "analysis.json")
    ):
        raise ValueError("public manifest claim drift")
    _validate_claims(ledger, analysis)
    if not isinstance(manifest.get("samples"), list) or len(manifest["samples"]) != 4:
        raise ValueError("public sample inventory drift")
    ledger_by_id = {row["slot_id"]: row for row in ledger["rows"]}
    for sample, (sample_id, slot_id, _) in zip(manifest["samples"], SAMPLES):
        expected_context = "non-author" if "nonauthor" in sample_id else "author"
        row = ledger_by_id[slot_id]
        public = directory / f"screenshots/{sample_id}.png"
        if sample != {
            "id": sample_id,
            "slot_id": slot_id,
            "model": row["model"],
            "variant": row["variant"],
            "category": row["category"],
            "context": expected_context,
            "file": f"screenshots/{sample_id}.png",
            "sha256": digest(public),
            "dimensions": [1000, 720],
        } or _png_dimensions(public) != (1000, 720):
            raise ValueError("public sample drift")
    if any(
        isinstance(value, str) and (value.startswith("/") or "private-research-evidence" in value)
        for value in _walk_values((manifest, ledger, analysis))
    ):
        raise ValueError("private path leaked into public bundle")
    return manifest


def _walk_values(values):
    for value in values:
        if isinstance(value, dict):
            yield from _walk_values(value.values())
        elif isinstance(value, list):
            yield from _walk_values(value)
        else:
            yield value


def validate_materialized(directory: Path, source: Path) -> dict:
    validate_public(directory)
    ledger, analysis, audit = audit_private(source)
    manifest = json.loads((directory / "manifest.json").read_text())
    if (directory / "ledger.json").read_bytes() != json_bytes(ledger):
        raise ValueError("public ledger drift")
    if (directory / "analysis.json").read_bytes() != json_bytes(analysis):
        raise ValueError("public analysis drift")
    if manifest != _manifest(source, ledger, analysis, audit):
        raise ValueError("public manifest drift")
    for sample, (_, slot_id, screenshot) in zip(manifest["samples"], SAMPLES):
        public = directory / sample["file"]
        private = source / "execution" / slot_id / screenshot
        if public.read_bytes() != private.read_bytes() or digest(public) != sample["sha256"]:
            raise ValueError("public screenshot drift")
    _validate_claims(ledger, analysis)
    return manifest


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("command", choices=("audit", "materialize", "validate"))
    parser.add_argument("--source", required=True, type=Path)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    if args.command == "audit":
        _, _, result = audit_private(args.source)
    elif args.command == "materialize":
        if args.output is None:
            parser.error("materialize requires --output")
        result = materialize(args.source, args.output)
    else:
        if args.output is None:
            parser.error("validate requires --output")
        result = validate_materialized(args.output, args.source)
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
