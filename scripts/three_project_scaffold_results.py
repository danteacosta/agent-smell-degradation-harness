"""Validate the aggregate-only fixed-scaffold successor result bundle."""
from __future__ import annotations

from collections import Counter
import argparse
import hashlib
import json
from pathlib import Path
import runpy


ROOT = Path(__file__).resolve().parents[1]
RESULTS_DIRECTORY = ROOT / "data/e2e-three-project-successor/results-20260925"
PUBLIC_RECEIPT_SHA256 = "28bbd2e7d3c9637c16fae77500e460b4e5e17852472a4d983c49994bd9412786"
PRIVATE_RECEIPT_SHA256 = "560c3b68f0d9c6ee3cc275b0f64f83440f19f0e7b6f6ada5640adbc0f17b7d22"


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
        receipt.get("schema_version")
        != "three-project-fixed-scaffold-public-results-receipt/v1"
        or receipt.get("files") != inventory
        or len(inventory) != 110
    ):
        raise ValueError("receipt inventory drift")
    manifest = json.loads((directory / "manifest.json").read_text())
    if (
        manifest.get("schema_version") != "three-project-fixed-scaffold-public-results/v1"
        or manifest.get("private_receipt_sha256") != PRIVATE_RECEIPT_SHA256
        or manifest.get("provider_calls") != 54
        or manifest.get("planned") != 54
        or manifest.get("executable") != 53
        or manifest.get("unknown") != 1
        or manifest.get("terminal_lf_canonicalization_declared_before_v4") is not True
        or manifest.get("published_provider_captures") is not False
        or manifest.get("published_raw_generations") is not False
        or manifest.get("claims")
        != {"pilot": True, "h1_confirmed": False, "h2_evaluated": False}
    ):
        raise ValueError("canonical public manifest drift")
    rows = json.loads((directory / "rows.json").read_text())
    if not isinstance(rows, list) or len(rows) != 54 or len({row.get("slot_id") for row in rows}) != 54:
        raise ValueError("public row inventory drift")
    classify = runpy.run_path(
        str(ROOT / "eval/fixtures/three-project-scaffold/qualify.py")
    )["classify"]
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
        if row["category"] == "invalid_output":
            if row.get("target_failed") is not None or any(
                (directory / folder / f"{slot}.{extension}").exists()
                for folder, extension in (("reports", "json"), ("screenshots", "png"))
            ):
                raise ValueError("invalid output has execution evidence")
            continue
        report_path = directory / "reports" / f"{slot}.json"
        screenshot = directory / "screenshots" / f"{slot}.png"
        report = json.loads(report_path.read_text())
        observed = classify(report)
        if (
            observed == "malformed_report"
            or row.get("category") != observed
            or row.get("target_failed") is not expected_target.get(observed)
            or row.get("report_sha256") != _digest(report_path)
            or report.get("project_id") != row.get("project_id")
            or row.get("screenshot_sha256") != _digest(screenshot)
            or not screenshot.read_bytes().startswith(b"\x89PNG\r\n\x1a\n")
        ):
            raise ValueError("report classification drift")
    categories = Counter(row["category"] for row in rows)
    summary = {
        "planned": len(rows),
        "executable": categories["pass"] + categories["target_only_failure"],
        "unknown": categories["invalid_output"],
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
