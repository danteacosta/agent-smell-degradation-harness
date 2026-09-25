"""Validate the prospective six-project, multi-obligation candidate register."""
from __future__ import annotations

from collections import Counter
import argparse
import hashlib
import json
from pathlib import Path
import re


ROOT = Path(__file__).resolve().parents[1]
REGISTER_PATH = ROOT / "data/e2e-multi-obligation/candidates-20260925.json"
SCREENING_PATH = ROOT / "data/e2e-multi-obligation/screening-panel-20260925.json"
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


def validate_screening(screening_path: Path) -> dict[str, int]:
    payload = json.loads(screening_path.read_text())
    reviewers = payload.get("reviewers")
    consensus = payload.get("consensus")
    expected_models = {"gpt-6-astra", "gpt-6-sol", "gpt-6-luna"}
    register_ids = {
        row["candidate_id"] for row in json.loads(REGISTER_PATH.read_text())["candidates"]
    }
    if (
        payload.get("schema_version") != "multi-obligation-screening-panel/v1"
        or payload.get("stage") != "pre_oracle_pre_generation_screening"
        or payload.get("collection_authorized") is not False
        or payload.get("provider_calls_for_generation") != 0
        or payload.get("claims")
        != {"outcomes_observed": False, "h1_confirmed": False, "h2_evaluated": False}
        or not re.fullmatch(r"[0-9a-f]{64}", str(payload.get("review_prompt_sha256", "")))
        or not isinstance(reviewers, list)
        or len(reviewers) != 3
        or not isinstance(consensus, list)
        or len(consensus) != 12
    ):
        raise ValueError("screening contract drift")
    reviewer_models = {row.get("requested_model") for row in reviewers}
    if reviewer_models != expected_models:
        raise ValueError("screening reviewer drift")

    decisions_by_model: dict[str, dict[str, str]] = {}
    for reviewer in reviewers:
        decisions = reviewer.get("candidates")
        if (
            not re.fullmatch(r"[0-9a-f]{64}", str(reviewer.get("response_sha256", "")))
            or not isinstance(decisions, list)
            or len(decisions) != 12
        ):
            raise ValueError("screening reviewer evidence drift")
        indexed = {row.get("candidate_id"): row.get("verdict") for row in decisions}
        if set(indexed) != register_ids or set(indexed.values()) - {"ACCEPT", "DEFER"}:
            raise ValueError("screening reviewer decision drift")
        decisions_by_model[reviewer["requested_model"]] = indexed

    accepted = []
    for row in consensus:
        candidate_id = row.get("candidate_id")
        expected = {
            model: decisions_by_model[model][candidate_id] for model in expected_models
        } if candidate_id in register_ids else None
        expected_verdict = "ACCEPT" if expected and set(expected.values()) == {"ACCEPT"} else "DEFER"
        if row.get("decisions") != expected or row.get("verdict") != expected_verdict:
            raise ValueError("screening consensus drift")
        if expected_verdict == "ACCEPT":
            accepted.append(candidate_id)
    if (
        {row.get("candidate_id") for row in consensus} != register_ids
        or payload.get("eligible_candidate_ids") != accepted
        or payload.get("unanimously_accepted") != len(accepted)
        or payload.get("deferred") != 12 - len(accepted)
        or payload.get("eligible_positions") != len(accepted) * 18
    ):
        raise ValueError("screening summary drift")
    return {
        "reviewers": len(reviewers),
        "candidates": len(consensus),
        "unanimously_accepted": len(accepted),
        "deferred": 12 - len(accepted),
        "eligible_positions": len(accepted) * 18,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--register", type=Path, default=REGISTER_PATH)
    args = parser.parse_args()
    print(json.dumps(validate(args.register), indent=2))


if __name__ == "__main__":
    main()
