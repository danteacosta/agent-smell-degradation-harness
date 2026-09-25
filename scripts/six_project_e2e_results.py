"""Validate the public, aggregate-only four-project E2E result bundle."""
from __future__ import annotations

from collections import Counter
import argparse
import hashlib
import json
from pathlib import Path
import runpy


ROOT = Path(__file__).resolve().parents[1]
RESULTS_DIRECTORY = ROOT / "data/e2e-six-projects/results-20260925"
PUBLIC_RECEIPT_SHA256 = "b6f7067dae5faf67fd33372f2de868fb89054532ee9198e04ec0fce16b208017"
PRIVATE_RECEIPT_SHA256 = "6039b4bb2fba7d32e0ab6a4ee41e2ab002d96df3e8b26985a70fe1405805212a"


def _digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _inventory(directory: Path) -> dict[str, str]:
    return {
        path.relative_to(directory).as_posix(): _digest(path)
        for path in sorted(directory.rglob("*"))
        if path.is_file() and path.name != "receipt.json"
    }


def validate(directory: Path) -> dict[str, int]:
    directory = directory.resolve(strict=True)
    receipt_path = directory / "receipt.json"
    if _digest(receipt_path) != PUBLIC_RECEIPT_SHA256:
        raise ValueError("canonical public receipt drift")
    receipt = json.loads(receipt_path.read_text())
    inventory = _inventory(directory)
    if (
        receipt.get("schema_version") != "six-project-e2e-public-results-receipt/v1"
        or receipt.get("files") != inventory
        or len(inventory) != 85
    ):
        raise ValueError("receipt inventory drift")
    manifest = json.loads((directory / "manifest.json").read_text())
    if manifest != {
        "claims": {"h1_confirmed": False, "h2_evaluated": False, "pilot": True},
        "collected_at": "2026-09-25",
        "executable": 8,
        "planned": 72,
        "posthoc_visualization": {
            "A_slot_id": "e2e-cc870c03b74f9929d0aa417c",
            "C_slot_id": "e2e-900818b6205deabcdf294d4f",
            "classification_unchanged": True,
            "model": "gpt-5.6-luna",
            "project_id": "kanboard",
            "purpose": "show the already-classified Closed tasks state; not used to assign labels",
            "replication": 1,
        },
        "private_file_count": 1164,
        "private_receipt_sha256": PRIVATE_RECEIPT_SHA256,
        "projects": ["paperless-ngx", "kanboard", "nextcloud", "openproject"],
        "provider_calls": 72,
        "published_provider_captures": False,
        "published_raw_generations": False,
        "schema_version": "six-project-e2e-public-results/v1",
        "unknown": 64,
    }:
        raise ValueError("canonical public manifest drift")
    rows = json.loads((directory / "rows.json").read_text())
    if not isinstance(rows, list) or len(rows) != 72 or len({row.get("slot_id") for row in rows}) != 72:
        raise ValueError("public row inventory drift")
    namespace = runpy.run_path(str(ROOT / "eval/fixtures/four-project-ui/qualify.py"))
    classify = namespace["classify"]
    expected_target = {
        "pass": False,
        "non_target_only_failure": False,
        "target_only_failure": True,
        "mixed_failure": True,
        "interface_error": None,
        "browser_error": None,
    }
    for row in rows:
        slot = row["slot_id"]
        report_path = directory / "reports" / f"{slot}.json"
        report = json.loads(report_path.read_text())
        observed = classify(report)
        if observed == "malformed_report":
            observed = "browser_error"
        if (
            row.get("category") != observed
            or row.get("target_failed") is not expected_target.get(observed)
            or row.get("report_sha256") != _digest(report_path)
            or report.get("project_id") != row.get("project_id")
        ):
            raise ValueError("report classification drift")
        screenshot_hash = row.get("screenshot_sha256")
        screenshot = directory / "screenshots" / f"{slot}.png"
        if screenshot_hash is None:
            if screenshot.exists():
                raise ValueError("unexpected screenshot")
        elif (
            not screenshot.is_file()
            or _digest(screenshot) != screenshot_hash
            or not screenshot.read_bytes().startswith(b"\x89PNG\r\n\x1a\n")
        ):
            raise ValueError("screenshot drift")
    for path in sorted((directory / "posthoc-kanboard-proof").glob("*.png")):
        if not path.read_bytes().startswith(b"\x89PNG\r\n\x1a\n"):
            raise ValueError("post-hoc proof image invalid")
    categories = Counter(row["category"] for row in rows)
    summary = {
        "planned": len(rows),
        "executable": sum(categories[key] for key in ("pass", "non_target_only_failure", "target_only_failure", "mixed_failure")),
        "unknown": sum(categories[key] for key in ("interface_error", "browser_error")),
        "pass": categories["pass"],
        "target_only_failure": categories["target_only_failure"],
    }
    analysis = json.loads((directory / "analysis.json").read_text())
    if any(analysis.get(key) != summary[key] for key in ("planned", "executable", "unknown")):
        raise ValueError("analysis summary drift")
    return summary


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--directory", type=Path, default=RESULTS_DIRECTORY)
    args = parser.parse_args()
    print(json.dumps(validate(args.directory), indent=2))


if __name__ == "__main__":
    main()
