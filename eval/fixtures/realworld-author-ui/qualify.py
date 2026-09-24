"""Qualify authored RealWorld article-author UI controls in a pinned browser."""
from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys
import uuid

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT))

from eval.realworld_author_ui_executor import (  # noqa: E402
    classify_report,
    container_command,
    execute,
)


AUTHOR = "author_sees_delete_article"
NON_AUTHOR = "non_author_does_not_see_delete_article"
SOURCE_REVISION = "ebbcdeb8d55b42a3a613c787560498b8ef10003f"
SOURCE_SHA256 = "65fbd975a3ab2021057b1c1944cf66418aa846039e51b166d2a98eb29e7169fb"
INSTRUMENT_LABEL = "org.opencontainers.image.realworld-instrument-sha256"
SCREENSHOTS = [
    "article-alice-author.png",
    "article-alice-non-author.png",
    "article-bob-author.png",
    "article-bob-non-author.png",
]


def _expected(category="pass", failed=None, not_evaluable=None, reasons=None):
    return {
        "category": category,
        "target_failed": failed or [],
        "target_not_evaluable": not_evaluable or [],
        "not_evaluable_reasons": reasons or [],
    }


def _reason(assertion_id, fixture_id, context_id, reason):
    return {
        "assertion_id": assertion_id,
        "fixture_id": fixture_id,
        "context_id": context_id,
        "reason": reason,
    }


def _four_reasons(reason):
    return [
        _reason(AUTHOR, "article-alice", "author", reason),
        _reason(AUTHOR, "article-bob", "author", reason),
        _reason(NON_AUTHOR, "article-alice", "non-author", reason),
        _reason(NON_AUTHOR, "article-bob", "non-author", reason),
    ]


EXPECTED = {
    name: _expected()
    for name in (
        "reference-explicit",
        "reference-derived-hidden",
        "reference-two-buttons",
        "reference-transparent-nonauthor",
        "reference-partial-occlusion",
        "reference-pointer-events-button",
        "reference-pointer-events-prerequisites",
        "reference-fresh-context",
    )
}
EXPECTED.update({
    "mutant-always-visible": _expected("target_only_failure", [NON_AUTHOR]),
    "mutant-never-visible": _expected("target_only_failure", [AUTHOR]),
    "mutant-wrong-identity": _expected(
        "target_only_failure", sorted([AUTHOR, NON_AUTHOR])),
    "mutant-hardcoded-alice": _expected(
        "target_only_failure", sorted([AUTHOR, NON_AUTHOR])),
    "mutant-transparent-author": _expected("target_only_failure", [AUTHOR]),
    "mutant-visible-and-transparent-nonauthor": _expected(
        "target_only_failure", [NON_AUTHOR]),
    "mutant-fully-occluded-author": _expected("target_only_failure", [AUTHOR]),
    "control-broken-article": _expected(
        "target_not_evaluable", not_evaluable=sorted([AUTHOR, NON_AUTHOR]),
        reasons=_four_reasons("body_missing")),
    "control-mixed-evaluability": _expected(
        "target_not_evaluable", failed=[NON_AUTHOR], not_evaluable=[AUTHOR],
        reasons=[_reason(AUTHOR, "article-bob", "author", "body_missing")]),
    "control-viewer-only-author-text": _expected(
        "target_not_evaluable", not_evaluable=sorted([AUTHOR, NON_AUTHOR]),
        reasons=_four_reasons("article_author_missing")),
    "control-hidden-author-text": _expected(
        "target_not_evaluable", not_evaluable=sorted([AUTHOR, NON_AUTHOR]),
        reasons=_four_reasons("article_author_missing")),
})

OPERATIONAL_EXPECTED = {
    "operational-invalid-interface": {
        "flag": "--qualify-invalid-interface",
        "status": "interface_failure",
        "browser_started": False,
        "returncode": 20,
        "category": "interface_failure",
    },
    "operational-browser-failure": {
        "flag": "--qualify-browser-failure",
        "status": "browser_failure",
        "browser_started": True,
        "returncode": 21,
        "category": "browser_failure",
    },
}


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--image", required=True)
    parser.add_argument("--output", required=True, type=Path)
    custody = parser.add_mutually_exclusive_group(required=True)
    custody.add_argument("--provisional", action="store_true")
    custody.add_argument("--git-commit")
    return parser


def instrument_paths() -> list[Path]:
    fixture_dir = Path(__file__).resolve().parent
    paths = sorted(path for path in fixture_dir.iterdir() if path.is_file())
    paths.extend([
        ROOT / "eval/focus_chain_executor.py",
        ROOT / "eval/realworld_author_ui_executor.py",
        ROOT / "tests/test_realworld_author_ui_executor.py",
    ])
    return sorted(paths, key=lambda path: path.relative_to(ROOT).as_posix())


def file_hashes(paths: list[Path]) -> dict[str, str]:
    return {
        path.relative_to(ROOT).as_posix(): digest(path)
        for path in sorted(paths, key=lambda item: item.relative_to(ROOT).as_posix())
    }


def instrument_digest(paths: list[Path]) -> str:
    combined = hashlib.sha256()
    for path in sorted(paths, key=lambda item: item.relative_to(ROOT).as_posix()):
        relative = path.relative_to(ROOT).as_posix().encode("utf-8")
        raw = path.read_bytes()
        combined.update(len(relative).to_bytes(8, "big"))
        combined.update(relative)
        combined.update(len(raw).to_bytes(8, "big"))
        combined.update(raw)
    return combined.hexdigest()


def validate_commit_custody(commit: str, paths: list[Path]) -> None:
    if re.fullmatch(r"[0-9a-f]{40}", commit) is None:
        raise ValueError("git commit must be 40 lowercase hex characters")
    head = subprocess.run(
        ["git", "rev-parse", "HEAD"], cwd=ROOT, check=True,
        capture_output=True, text=True, timeout=30,
    ).stdout.strip()
    if commit != head:
        raise ValueError("git commit must equal HEAD")
    relative = [str(path.resolve().relative_to(ROOT.resolve())) for path in paths]
    dirty = subprocess.run(
        ["git", "status", "--porcelain", "--", *relative], cwd=ROOT,
        check=True, capture_output=True, text=True, timeout=30,
    ).stdout
    if dirty:
        raise ValueError("hashed instrument paths must be clean")


def is_qualified(*, matrix_matches: bool, custody_mode: str) -> bool:
    return matrix_matches and custody_mode == "git-commit"


def matrix_matches(html_rows: list[dict], operational_rows: list[dict]) -> bool:
    return (
        all(
            row["matches"]
            and row["receipt_fields_exact"]
            and row["report_status"] == "complete"
            and set(row["screenshot_sha256"]) == set(SCREENSHOTS)
            for row in html_rows
        )
        and all(
            row["matches"] and row["screenshot_sha256"] == {}
            for row in operational_rows
        )
    )


def validate_image(image: str, *, expected_instrument_digest: str | None = None) -> None:
    if re.fullmatch(r"sha256:[0-9a-f]{64}", image) is None:
        raise ValueError("immutable Docker image ID required")
    found = subprocess.run(
        ["docker", "image", "inspect", "--format", "{{.Id}}", image],
        check=True, capture_output=True, text=True, timeout=30,
    ).stdout.strip()
    if found != image:
        raise ValueError("image identity mismatch")
    if expected_instrument_digest is not None:
        if re.fullmatch(r"[0-9a-f]{64}", expected_instrument_digest) is None:
            raise ValueError("invalid instrument digest")
        label = subprocess.run(
            [
                "docker", "image", "inspect", "--format",
                f'{{{{index .Config.Labels "{INSTRUMENT_LABEL}"}}}}', image,
            ],
            check=True, capture_output=True, text=True, timeout=30,
        ).stdout.strip()
        if label != expected_instrument_digest:
            raise ValueError("image instrument label mismatch")


def _copy_input(fixture_dir: Path, output_root: Path, run_id: str, source: str) -> Path:
    inputs = output_root / run_id / "input"
    inputs.mkdir(parents=True)
    shutil.copyfile(fixture_dir / source, inputs / "app.html")
    os.chmod(inputs / "app.html", 0o400)
    return inputs


def _regular_row(control_id: str, expected: dict, image: str,
                 fixture_dir: Path, output_root: Path) -> dict:
    inputs = _copy_input(fixture_dir, output_root, control_id, f"{control_id}.html")
    output = output_root / control_id / "output"
    receipt = execute(image, inputs, output)
    raw = json.loads((output / "report.json").read_text())
    observed = {
        "category": receipt.get("category"),
        "target_failed": receipt.get("target_failed", []),
        "target_not_evaluable": receipt.get("target_not_evaluable", []),
        "not_evaluable_reasons": receipt.get("not_evaluable_reasons", []),
    }
    return {
        "id": control_id,
        "expected": expected,
        "observed": observed,
        "matches": observed == expected,
        "receipt_fields_exact": set(receipt) == {
            "image", "app_sha256", "returncode", "category", "target_failed",
            "target_not_evaluable", "not_evaluable_reasons",
        },
        "report_status": raw.get("status"),
        "receipt_sha256": digest(output / "executor.json"),
        "report_sha256": digest(output / "report.json"),
        "screenshot_sha256": {
            name: digest(output / name) for name in SCREENSHOTS
            if (output / name).is_file()
        },
    }


def _operational_row(control_id: str, expected: dict, image: str,
                     fixture_dir: Path, output_root: Path) -> dict:
    inputs = _copy_input(
        fixture_dir, output_root, control_id, "reference-explicit.html")
    output = output_root / control_id / "output"
    output.mkdir()
    name = "realworld-author-ui-qualify-" + uuid.uuid4().hex
    command = [*container_command(image, inputs, output, name), expected["flag"]]
    (output / "container-command.json").write_text(json.dumps(command, indent=2))
    try:
        with (output / "container.log").open("wb") as log:
            result = subprocess.run(
                command, stdout=log, stderr=subprocess.STDOUT, timeout=90,
                check=False,
            )
    finally:
        subprocess.run(
            ["docker", "rm", "--force", name], capture_output=True,
            timeout=30, check=False,
        )
    report_path = output / "report.json"
    raw_bytes = report_path.read_bytes() if report_path.is_file() else b""
    raw = json.loads(raw_bytes) if raw_bytes else {}
    classified = classify_report(raw_bytes, result.returncode)
    exact_fields = {
        "schema_version", "status", "app_sha256", "runner_version",
        "browser_sandbox", "isolation", "error", "browser_started",
    }
    screenshot_names = sorted(path.name for path in output.glob("*.png"))
    matches = (
        set(raw) == exact_fields
        and raw.get("status") == expected["status"]
        and raw.get("browser_started") is expected["browser_started"]
        and result.returncode == expected["returncode"]
        and classified.get("category") == expected["category"]
        and screenshot_names == []
    )
    receipt = {
        "image": image,
        "app_sha256": raw.get("app_sha256"),
        "returncode": result.returncode,
        **classified,
    }
    (output / "executor.json").write_text(json.dumps(receipt, indent=2) + "\n")
    return {
        "id": control_id,
        "expected": {key: value for key, value in expected.items() if key != "flag"},
        "observed": {
            "status": raw.get("status"),
            "browser_started": raw.get("browser_started"),
            "returncode": result.returncode,
            "category": classified.get("category"),
        },
        "matches": matches,
        "receipt_sha256": digest(output / "executor.json"),
        "report_sha256": digest(report_path) if report_path.is_file() else None,
        "screenshot_sha256": {},
    }


def main(argv=None) -> int:
    effective_argv = list(sys.argv[1:] if argv is None else argv)
    if effective_argv == ["--print-instrument-digest"]:
        print(instrument_digest(instrument_paths()))
        return 0
    args = build_parser().parse_args(argv)
    paths = instrument_paths()
    current_instrument_digest = instrument_digest(paths)
    custody_mode = "provisional" if args.provisional else "git-commit"
    if args.git_commit:
        validate_commit_custody(args.git_commit, paths)
    validate_image(
        args.image,
        expected_instrument_digest=(
            current_instrument_digest if args.git_commit else None),
    )
    args.output.mkdir(parents=True, exist_ok=False, mode=0o700)
    os.chmod(args.output, 0o700)
    fixture_dir = Path(__file__).resolve().parent

    rows = [
        _regular_row(control_id, expected, args.image, fixture_dir, args.output)
        for control_id, expected in EXPECTED.items()
    ]
    operational = [
        _operational_row(control_id, expected, args.image, fixture_dir, args.output)
        for control_id, expected in OPERATIONAL_EXPECTED.items()
    ]
    matrix_ok = matrix_matches(rows, operational)
    report = {
        "schema_version": "realworld-author-ui-qualification/v1",
        "qualified": is_qualified(
            matrix_matches=matrix_ok, custody_mode=custody_mode),
        "matrix_matches": matrix_ok,
        "custody": {"mode": custody_mode, "git_commit": args.git_commit},
        "image_id": args.image,
        "instrument_sha256": current_instrument_digest,
        "source": {
            "revision": SOURCE_REVISION,
            "sha256": SOURCE_SHA256,
        },
        "cases": rows,
        "operational_cases": operational,
        "files": file_hashes(paths),
        "limitations": (
            "Authored controls qualify this bounded oracle only; they do not "
            "admit a study case, establish H1 or H2, establish general "
            "sensitivity, or prove universal browser escape safety."
        ),
    }
    destination = args.output / "qualification.json"
    destination.write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps({
        "qualified": report["qualified"],
        "matrix_matches": matrix_ok,
        "path": str(destination),
    }))
    return 0 if report["qualified"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
