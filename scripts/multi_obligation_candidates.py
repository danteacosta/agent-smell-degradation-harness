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
REVISION_PANEL_PATH = (
    ROOT / "data/e2e-multi-obligation/deferred-candidate-revision-panel-20260925.json"
)
THIRD_PANEL_PATH = (
    ROOT / "data/e2e-multi-obligation/third-candidate-revision-panel-20260925.json"
)
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
    register_rows = json.loads(REGISTER_PATH.read_text())["candidates"]
    register_projects = {row["candidate_id"]: row["project_id"] for row in register_rows}
    register_ids = set(register_projects)
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
        if (
            set(indexed) != register_ids
            or set(indexed.values()) - {"ACCEPT", "DEFER"}
            or reviewer.get("accepted_count")
            != sum(verdict == "ACCEPT" for verdict in indexed.values())
            or reviewer.get("deferred_count")
            != sum(verdict == "DEFER" for verdict in indexed.values())
        ):
            raise ValueError("screening reviewer decision drift")
        decisions_by_model[reviewer["requested_model"]] = indexed

    accepted = []
    for row in consensus:
        candidate_id = row.get("candidate_id")
        expected = {
            model: decisions_by_model[model][candidate_id] for model in expected_models
        } if candidate_id in register_ids else None
        expected_verdict = "ACCEPT" if expected and set(expected.values()) == {"ACCEPT"} else "DEFER"
        if (
            row.get("decisions") != expected
            or row.get("verdict") != expected_verdict
            or row.get("project_id") != register_projects.get(candidate_id)
        ):
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


def validate_revision_panel(panel_path: Path) -> dict[str, int]:
    """Validate the prospective second-stage review of previously deferred cases."""
    payload = json.loads(panel_path.read_text())
    reviewers = payload.get("reviewers")
    revisions = payload.get("revisions")
    consensus = payload.get("consensus")
    expected_models = {"gpt-6-astra", "gpt-6-sol", "gpt-6-luna"}
    prior = json.loads(SCREENING_PATH.read_text())
    prior_eligible = prior["eligible_candidate_ids"]
    prior_deferred = {
        row["candidate_id"] for row in prior["consensus"] if row["verdict"] == "DEFER"
    }
    register_projects = {
        row["candidate_id"]: row["project_id"]
        for row in json.loads(REGISTER_PATH.read_text())["candidates"]
    }
    if (
        payload.get("schema_version") != "deferred-candidate-revision-panel/v1"
        or payload.get("stage") != "pre_oracle_pre_generation_revision_screening"
        or payload.get("collection_authorized") is not False
        or payload.get("provider_calls_for_generation") != 0
        or payload.get("prior_screening_path")
        != "data/e2e-multi-obligation/screening-panel-20260925.json"
        or payload.get("claims")
        != {"outcomes_observed": False, "h1_confirmed": False, "h2_evaluated": False}
        or not re.fullmatch(r"[0-9a-f]{64}", str(payload.get("revision_register_sha256", "")))
        or not re.fullmatch(r"[0-9a-f]{64}", str(payload.get("review_prompt_sha256", "")))
        or not isinstance(revisions, list)
        or len(revisions) != 9
        or not isinstance(reviewers, list)
        or len(reviewers) != 3
        or not isinstance(consensus, list)
        or len(consensus) != 9
    ):
        raise ValueError("revision panel contract drift")

    revision_ids = {row.get("candidate_id") for row in revisions}
    if revision_ids != prior_deferred:
        raise ValueError("revision candidate drift")
    for row in revisions:
        if row.get("revision_stage") != "before_oracle_and_generation" or not row.get(
            "revised_target"
        ):
            raise ValueError("revision target drift")
        if row.get("project_id") != register_projects.get(row.get("candidate_id")):
            raise ValueError("revision candidate drift")
        source = row.get("source", {})
        source_path = (ROOT / str(source.get("path", ""))).resolve()
        try:
            source_path.relative_to(ROOT)
        except ValueError as error:
            raise ValueError("revision source path escapes repository") from error
        if not source_path.is_file() or _digest(source_path) != source.get("sha256"):
            raise ValueError("revision source hash drift")
        context = source.get("exact_context")
        lines = source_path.read_text().splitlines()
        line_start, line_end = source.get("line_start"), source.get("line_end")
        if (
            not isinstance(context, str)
            or not context
            or not isinstance(line_start, int)
            or not isinstance(line_end, int)
            or line_start < 1
            or line_end < line_start
            or line_end > len(lines)
            or context not in "\n".join(lines[line_start - 1 : line_end])
        ):
            raise ValueError("revision source locator drift")

    if {row.get("requested_model") for row in reviewers} != expected_models:
        raise ValueError("revision reviewer drift")
    decisions_by_model: dict[str, dict[str, str]] = {}
    for reviewer in reviewers:
        decisions = reviewer.get("candidates")
        if (
            not re.fullmatch(r"[0-9a-f]{64}", str(reviewer.get("response_sha256", "")))
            or not isinstance(decisions, list)
            or len(decisions) != 9
        ):
            raise ValueError("revision reviewer evidence drift")
        indexed = {row.get("candidate_id"): row.get("verdict") for row in decisions}
        if (
            set(indexed) != revision_ids
            or set(indexed.values()) - {"ACCEPT", "DEFER"}
            or reviewer.get("accepted_count")
            != sum(verdict == "ACCEPT" for verdict in indexed.values())
            or reviewer.get("deferred_count")
            != sum(verdict == "DEFER" for verdict in indexed.values())
        ):
            raise ValueError("revision reviewer decision drift")
        decisions_by_model[reviewer["requested_model"]] = indexed

    newly_accepted: list[str] = []
    still_deferred: list[str] = []
    for row in consensus:
        candidate_id = row.get("candidate_id")
        expected = (
            {model: decisions_by_model[model][candidate_id] for model in expected_models}
            if candidate_id in revision_ids
            else None
        )
        expected_verdict = "ACCEPT" if expected and set(expected.values()) == {"ACCEPT"} else "DEFER"
        if (
            row.get("decisions") != expected
            or row.get("verdict") != expected_verdict
            or row.get("project_id") != register_projects.get(candidate_id)
        ):
            raise ValueError("revision consensus drift")
        (newly_accepted if expected_verdict == "ACCEPT" else still_deferred).append(candidate_id)

    total_eligible = prior_eligible + newly_accepted
    if (
        {row.get("candidate_id") for row in consensus} != revision_ids
        or payload.get("newly_eligible_candidate_ids") != newly_accepted
        or payload.get("still_deferred_candidate_ids") != still_deferred
        or payload.get("prior_eligible_candidate_ids") != prior_eligible
        or payload.get("total_eligible_candidate_ids") != total_eligible
        or payload.get("newly_accepted") != len(newly_accepted)
        or payload.get("still_deferred") != len(still_deferred)
        or payload.get("total_eligible") != len(total_eligible)
        or payload.get("eligible_positions") != len(total_eligible) * 18
    ):
        raise ValueError("revision panel summary drift")
    return {
        "reviewers": len(reviewers),
        "revised_candidates": len(revisions),
        "newly_accepted": len(newly_accepted),
        "still_deferred": len(still_deferred),
        "total_eligible": len(total_eligible),
        "eligible_positions": len(total_eligible) * 18,
    }


def validate_third_panel(panel_path: Path) -> dict[str, int]:
    """Validate replacement candidates reviewed before any oracle or generation."""
    payload = json.loads(panel_path.read_text())
    revisions = payload.get("revisions")
    reviewers = payload.get("reviewers")
    consensus = payload.get("consensus")
    expected_models = {"gpt-6-astra", "gpt-6-sol", "gpt-6-luna"}
    prior = json.loads(REVISION_PANEL_PATH.read_text())
    prior_eligible = prior["total_eligible_candidate_ids"]
    prior_deferred = set(prior["still_deferred_candidate_ids"])
    prior_deferred_projects = {
        row["candidate_id"]: row["project_id"] for row in prior["revisions"]
    }
    if (
        payload.get("schema_version") != "third-candidate-revision-panel/v1"
        or payload.get("stage") != "pre_oracle_pre_generation_replacement_screening"
        or payload.get("collection_authorized") is not False
        or payload.get("provider_calls_for_generation") != 0
        or payload.get("prior_panel_path")
        != "data/e2e-multi-obligation/deferred-candidate-revision-panel-20260925.json"
        or payload.get("claims")
        != {"outcomes_observed": False, "h1_confirmed": False, "h2_evaluated": False}
        or not re.fullmatch(r"[0-9a-f]{64}", str(payload.get("revision_register_sha256", "")))
        or not re.fullmatch(r"[0-9a-f]{64}", str(payload.get("review_prompt_sha256", "")))
        or not isinstance(revisions, list)
        or len(revisions) != 7
        or not isinstance(reviewers, list)
        or len(reviewers) != 3
        or not isinstance(consensus, list)
        or len(consensus) != 7
    ):
        raise ValueError("third panel contract drift")

    revision_ids = {row.get("candidate_id") for row in revisions}
    replaced_ids = {row.get("replaces_candidate_id") for row in revisions}
    if (
        len(revision_ids) != 7
        or len(replaced_ids) != 7
        or replaced_ids != prior_deferred
    ):
        raise ValueError("third panel replacement drift")
    project_by_id: dict[str, str] = {}
    replacement_by_id: dict[str, str] = {}
    for row in revisions:
        if row.get("revision_stage") != "before_oracle_and_generation" or not row.get(
            "revised_target"
        ):
            raise ValueError("third panel target drift")
        candidate_id = row["candidate_id"]
        replaced_id = row.get("replaces_candidate_id")
        if row.get("project_id") != prior_deferred_projects.get(replaced_id):
            raise ValueError("third panel replacement drift")
        project_by_id[candidate_id] = row.get("project_id")
        replacement_by_id[candidate_id] = replaced_id
        source = row.get("source", {})
        source_path = (ROOT / str(source.get("path", ""))).resolve()
        try:
            source_path.relative_to(ROOT)
        except ValueError as error:
            raise ValueError("third panel source path escapes repository") from error
        if not source_path.is_file() or _digest(source_path) != source.get("sha256"):
            raise ValueError("third panel source hash drift")
        context = source.get("exact_context")
        lines = source_path.read_text().splitlines()
        line_start, line_end = source.get("line_start"), source.get("line_end")
        if (
            not isinstance(context, str)
            or not context
            or not isinstance(line_start, int)
            or not isinstance(line_end, int)
            or line_start < 1
            or line_end < line_start
            or line_end > len(lines)
            or context not in "\n".join(lines[line_start - 1 : line_end])
        ):
            raise ValueError("third panel source locator drift")

    if {row.get("requested_model") for row in reviewers} != expected_models:
        raise ValueError("third panel reviewer drift")
    decisions_by_model: dict[str, dict[str, str]] = {}
    for reviewer in reviewers:
        decisions = reviewer.get("candidates")
        if (
            not re.fullmatch(r"[0-9a-f]{64}", str(reviewer.get("response_sha256", "")))
            or not isinstance(decisions, list)
            or len(decisions) != 7
        ):
            raise ValueError("third panel reviewer evidence drift")
        indexed = {row.get("candidate_id"): row.get("verdict") for row in decisions}
        if (
            set(indexed) != revision_ids
            or set(indexed.values()) - {"ACCEPT", "DEFER"}
            or reviewer.get("accepted_count")
            != sum(verdict == "ACCEPT" for verdict in indexed.values())
            or reviewer.get("deferred_count")
            != sum(verdict == "DEFER" for verdict in indexed.values())
        ):
            raise ValueError("third panel reviewer decision drift")
        decisions_by_model[reviewer["requested_model"]] = indexed

    newly_accepted: list[str] = []
    still_deferred: list[str] = []
    for row in consensus:
        candidate_id = row.get("candidate_id")
        expected = (
            {model: decisions_by_model[model][candidate_id] for model in expected_models}
            if candidate_id in revision_ids
            else None
        )
        expected_verdict = "ACCEPT" if expected and set(expected.values()) == {"ACCEPT"} else "DEFER"
        if (
            row.get("decisions") != expected
            or row.get("verdict") != expected_verdict
            or row.get("project_id") != project_by_id.get(candidate_id)
            or row.get("replaces_candidate_id") != replacement_by_id.get(candidate_id)
        ):
            raise ValueError("third panel consensus drift")
        (newly_accepted if expected_verdict == "ACCEPT" else still_deferred).append(candidate_id)

    total_eligible = prior_eligible + newly_accepted
    represented_projects = payload.get("represented_projects")
    first_projects = {
        row["candidate_id"]: row["project_id"]
        for row in json.loads(SCREENING_PATH.read_text())["consensus"]
    }
    prior_projects = {
        **first_projects,
        **{row["candidate_id"]: row["project_id"] for row in prior["revisions"]},
    }
    eligible_project_counts = Counter(
        [prior_projects[candidate_id] for candidate_id in prior_eligible]
        + [project_by_id[candidate_id] for candidate_id in newly_accepted]
    )
    if (
        {row.get("candidate_id") for row in consensus} != revision_ids
        or payload.get("newly_eligible_candidate_ids") != newly_accepted
        or payload.get("still_deferred_candidate_ids") != still_deferred
        or payload.get("prior_eligible_candidate_ids") != prior_eligible
        or payload.get("total_eligible_candidate_ids") != total_eligible
        or payload.get("newly_accepted") != len(newly_accepted)
        or payload.get("still_deferred") != len(still_deferred)
        or payload.get("total_eligible") != len(total_eligible)
        or payload.get("eligible_positions") != len(total_eligible) * 18
        or len(set(total_eligible)) != len(total_eligible)
        or set(prior_eligible) & set(newly_accepted)
        or not isinstance(represented_projects, list)
        or len(represented_projects) != len(set(represented_projects))
        or set(represented_projects) != EXPECTED_PROJECTS
        or set(represented_projects) != set(eligible_project_counts)
        or payload.get("eligible_project_counts") != dict(eligible_project_counts)
    ):
        raise ValueError("third panel summary drift")
    return {
        "reviewers": len(reviewers),
        "replacement_candidates": len(revisions),
        "newly_accepted": len(newly_accepted),
        "still_deferred": len(still_deferred),
        "total_eligible": len(total_eligible),
        "represented_projects": len(represented_projects),
        "eligible_positions": len(total_eligible) * 18,
    }


def validate_chain() -> dict[str, int]:
    """Validate every prospective stage before reporting the final ceiling."""
    register = validate(REGISTER_PATH)
    validate_screening(SCREENING_PATH)
    validate_revision_panel(REVISION_PANEL_PATH)
    final = validate_third_panel(THIRD_PANEL_PATH)
    return {
        "projects": final["represented_projects"],
        "registered_candidates": register["candidates"],
        "eligible_obligations": final["total_eligible"],
        "eligible_positions": final["eligible_positions"],
        "still_deferred": final["still_deferred"],
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--register", type=Path)
    args = parser.parse_args()
    result = validate(args.register) if args.register else validate_chain()
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
