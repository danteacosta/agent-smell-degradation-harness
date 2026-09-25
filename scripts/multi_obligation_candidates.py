"""Validate the prospective six-project, multi-obligation candidate register."""
from __future__ import annotations

from collections import Counter
import argparse
import hashlib
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
REGISTER_PATH = ROOT / "data/e2e-multi-obligation/candidates-20260925.json"
EXPECTED_PROJECTS = {
    "todomvc",
    "realworld",
    "kanboard",
    "paperless-ngx",
    "nextcloud",
    "openproject",
}


def _digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def validate(register_path: Path) -> dict[str, int]:
    payload = json.loads(register_path.read_text())
    design = payload.get("design", {})
    claims = payload.get("claims", {})
    rows = payload.get("candidates")
    if (
        payload.get("schema_version") != "multi-obligation-e2e-candidates/v1"
        or payload.get("stage") != "screened_candidates_before_oracle_implementation"
        or payload.get("collection_authorized") is not False
        or payload.get("provider_calls") != 0
        or claims
        != {
            "outcomes_observed": False,
            "h1_confirmed": False,
            "h2_evaluated": False,
        }
        or design.get("arms") != ["A", "B", "C"]
        or design.get("models") != ["gpt-5.6-luna", "gpt-5.6-sol"]
        or design.get("repetitions") != 3
        or design.get("planned_positions_if_all_admitted") != 216
        or not isinstance(rows, list)
        or len(rows) != 12
    ):
        raise ValueError("candidate register contract drift")

    identifiers = [row.get("candidate_id") for row in rows]
    if len(set(identifiers)) != len(rows) or any(not value for value in identifiers):
        raise ValueError("candidate identity drift")

    project_counts = Counter(row.get("project_id") for row in rows)
    if set(project_counts) != EXPECTED_PROJECTS or set(project_counts.values()) != {2}:
        raise ValueError("project balance drift")

    for row in rows:
        if row.get("status") != "screened_not_admitted" or not row.get("target"):
            raise ValueError("candidate status drift")
        source = row.get("source", {})
        source_path = (ROOT / str(source.get("path", ""))).resolve()
        try:
            source_path.relative_to(ROOT)
        except ValueError as error:
            raise ValueError("source path escapes repository") from error
        if not source_path.is_file() or _digest(source_path) != source.get("sha256"):
            raise ValueError("source hash drift")
        excerpt = source.get("exact_excerpt")
        source_text = source_path.read_text()
        if not isinstance(excerpt, str) or not excerpt or excerpt not in source_text:
            raise ValueError("source excerpt drift")
        line_start = source.get("line_start")
        line_end = source.get("line_end")
        source_lines = source_text.splitlines()
        if (
            not isinstance(line_start, int)
            or not isinstance(line_end, int)
            or line_start < 1
            or line_end < line_start
            or line_end > len(source_lines)
            or excerpt not in "\n".join(source_lines[line_start - 1 : line_end])
        ):
            raise ValueError("source locator drift")

    planned = len(rows) * len(design["arms"]) * len(design["models"]) * design["repetitions"]
    if planned != design["planned_positions_if_all_admitted"]:
        raise ValueError("planned position drift")
    return {
        "projects": len(project_counts),
        "candidates": len(rows),
        "planned_positions": planned,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--register", type=Path, default=REGISTER_PATH)
    args = parser.parse_args()
    print(json.dumps(validate(args.register), indent=2))


if __name__ == "__main__":
    main()
