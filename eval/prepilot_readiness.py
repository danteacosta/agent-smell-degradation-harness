"""Fail-closed readiness gate for the empirical pre-pilot.

This module deliberately governs only the 120-episode pre-pilot.  Passing it
does not confirm the sample plan, preregistration, H1, H2, or external validity.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any, Mapping


SCHEMA_VERSION = "prepilot-launch/v1"
ALLOWED_STATUSES = {"draft", "blocked", "pilot_ready"}
FORBIDDEN_KEY_MARKERS = (
    "api_key",
    "apikey",
    "authorization",
    "password",
    "secret",
    "token",
)


def _require_mapping(value: Any, name: str) -> Mapping[str, Any]:
    if not isinstance(value, Mapping):
        raise ValueError(f"{name} must be an object")
    return value


def _assert_no_secret_fields(value: Any, *, path: str = "plan") -> None:
    if isinstance(value, Mapping):
        for key, item in value.items():
            lowered = str(key).lower()
            if any(marker in lowered for marker in FORBIDDEN_KEY_MARKERS):
                raise ValueError(f"secret-like field is prohibited: {path}.{key}")
            _assert_no_secret_fields(item, path=f"{path}.{key}")
    elif isinstance(value, list):
        for index, item in enumerate(value):
            _assert_no_secret_fields(item, path=f"{path}[{index}]")


def load_launch_plan(path: Path | str) -> dict[str, Any]:
    plan = json.loads(Path(path).read_text(encoding="utf-8"))
    if not isinstance(plan, dict):
        raise ValueError("launch plan must be a JSON object")
    _assert_no_secret_fields(plan)
    return plan


def evaluate_launch_plan(plan: Mapping[str, Any]) -> dict[str, Any]:
    """Return an auditable pre-pilot decision without inspecting outcomes."""

    _assert_no_secret_fields(plan)
    if plan.get("schema_version") != SCHEMA_VERSION:
        raise ValueError(f"schema_version must be {SCHEMA_VERSION}")
    status = str(plan.get("status", ""))
    if status not in ALLOWED_STATUSES:
        raise ValueError(
            "status must be draft, blocked, or pilot_ready; confirmatory status is prohibited"
        )
    if plan.get("claim_level") != "non_confirmatory_pre_pilot":
        raise ValueError("claim_level must remain non_confirmatory_pre_pilot")

    blockers: list[str] = []
    warnings: list[str] = []

    design = _require_mapping(plan.get("design"), "design")
    if design.get("primary_task") != "acceptance_criteria_generation":
        blockers.append("primary task is not frozen to acceptance-criteria generation")
    if design.get("primary_defect_family") != "incompleteness_missing_condition":
        blockers.append("primary defect family is not frozen to missing-condition")
    if design.get("independent_intents") != 12:
        blockers.append("pre-pilot requires exactly 12 independent intents")
    if design.get("variants_per_intent") != 2 or design.get("replications") != 5:
        blockers.append("pre-pilot must use 2 variants and 5 replications per intent")
    if design.get("episode_count") != 120:
        blockers.append("pre-pilot episode count must be 120")

    context_management = _require_mapping(
        plan.get("context_management"), "context_management"
    )
    context_checks = {
        "context-management schema is missing": context_management.get("schema_version")
        == "context-management/v1",
        "primary pre-pilot condition must disable compaction": (
            context_management.get("primary_condition") == "no_compaction"
            and context_management.get("primary_compaction_enabled") is False
        ),
        "secondary context condition must be compaction_stress_test": (
            context_management.get("secondary_condition") == "compaction_stress_test"
        ),
        "secondary matrix must preserve clean/smelly variants": (
            context_management.get("secondary_variant_factor") == ["clean", "smelly"]
        ),
        "secondary context protocol test is missing": (
            context_management.get("secondary_protocol_tested") is True
        ),
        "context-management event field list is incomplete": (
            context_management.get("event_fields")
            == [
                "schema_version",
                "event_id",
                "stage",
                "operation",
                "trigger",
                "started_at",
                "ended_at",
                "context_size_before",
                "context_size_after",
                "context_size_unit",
                "checkpoint_id",
                "checkpoint_sha256",
            ]
        ),
        "atomic-obligation schema is missing": (
            context_management.get("atomic_obligation_schema")
            == "atomic-obligations/v1"
        ),
        "atomic-obligation observation fields are incomplete": (
            context_management.get("atomic_obligation_observation_fields")
            == [
                "schema_version",
                "obligation_id",
                "constraint_id",
                "constraint_sha256",
                "constraint_index",
                "atom_type",
                "status",
                "source_checkpoint",
                "observation_id",
                "preservation_class",
                "available_at",
            ]
        ),
        "article-inspired secondary mechanism is missing": (
            context_management.get("mechanism_secondary")
            == "typed_compaction_stress_test"
            and context_management.get("mechanism_secondary_confirmatory") is False
        ),
        "2x2 context interaction estimand is missing": (
            context_management.get("interaction_analysis")
            == "difference_in_differences"
        ),
    }
    blockers.extend(message for message, passed in context_checks.items() if not passed)

    corpus = _require_mapping(plan.get("corpus"), "corpus")
    corpus_checks = {
        "corpus manifest path is missing": bool(str(corpus.get("manifest_path", "")).strip()),
        "corpus manifest is not frozen": corpus.get("manifest_frozen") is True,
        "corpus does not contain 12 unique intents": corpus.get("unique_intents") == 12,
        "source licenses/provenance are incomplete": corpus.get("all_sources_licensed") is True,
        "project identifiers are incomplete": corpus.get("all_project_ids_present") is True,
        "near-clone screening is incomplete": corpus.get("near_clone_screening_complete") is True,
        "manipulation checks are incomplete": corpus.get("manipulation_checks_complete") is True,
        "development seed has not been replaced": corpus.get("development_seed_replaced") is True,
    }
    blockers.extend(message for message, passed in corpus_checks.items() if not passed)

    configurations = plan.get("provider_configurations")
    if not isinstance(configurations, list) or len(configurations) < 2:
        blockers.append("two real provider/model configurations are required")
        configurations = []
    identities: set[tuple[str, str, str]] = set()
    for index, raw in enumerate(configurations):
        config = _require_mapping(raw, f"provider_configurations[{index}]")
        identity = tuple(str(config.get(key, "")).strip() for key in ("provider", "model", "model_version"))
        if not all(identity):
            blockers.append(f"provider configuration {index + 1} lacks provider/model/version")
        elif identity in identities:
            blockers.append("provider/model configurations must be distinct")
        identities.add(identity)
        if config.get("mode") != "runtime" or config.get("checkpoint_source") != "runtime_native":
            blockers.append(f"provider configuration {index + 1} is not runtime-native")
        if config.get("qualification_passed") is not True:
            blockers.append(f"provider configuration {index + 1} has not passed qualification")
        if not str(config.get("qualification_report_path", "")).strip():
            blockers.append(f"provider configuration {index + 1} lacks a qualification report")
        if config.get("t1_t3_before_t4") is not True:
            blockers.append(f"provider configuration {index + 1} lacks a verified pre-final boundary")
        if config.get("prompted_snapshot") is not False:
            blockers.append(f"provider configuration {index + 1} permits prompted snapshots")
        if not str(config.get("configuration_hash", "")).strip():
            blockers.append(f"provider configuration {index + 1} lacks a configuration hash")

    annotation = _require_mapping(plan.get("annotation"), "annotation")
    annotation_checks = {
        "annotation rubric path is missing": bool(str(annotation.get("rubric_path", "")).strip()),
        "annotation rubric is not frozen": annotation.get("rubric_frozen") is True,
        "at least two trained annotators are required": int(annotation.get("trained_annotators", 0)) >= 2,
        "20% double coding is not reserved": annotation.get("duplicate_subset_fraction") == 0.2,
        "duplicate subset is not selected outcome-blind": annotation.get("duplicate_subset_selected_outcome_blind") is True,
        "annotation blinding has not been verified": annotation.get("blinding_verified") is True,
        "adjudication owner is missing": bool(str(annotation.get("adjudication_owner", "")).strip()),
    }
    blockers.extend(message for message, passed in annotation_checks.items() if not passed)

    budget = _require_mapping(plan.get("budget"), "budget")
    estimated_cost = float(budget.get("estimated_provider_cost_usd", 0.0))
    contingency = float(budget.get("contingency_fraction", 0.0))
    cap = float(budget.get("approved_cap_usd", 0.0))
    estimated_hours = float(budget.get("estimated_annotation_hours", 0.0))
    projected_cost = estimated_cost * (1.0 + contingency)
    if estimated_cost <= 0 or contingency < 0 or cap <= 0:
        blockers.append("provider budget and contingency must be estimated and approved")
    elif projected_cost > cap:
        blockers.append("provider cost plus contingency exceeds the approved cap")
    if estimated_hours <= 0:
        blockers.append("annotation effort has not been estimated")

    gates = _require_mapping(plan.get("go_no_go"), "go_no_go")
    required_gates = (
        "advisor_authorized_pre_pilot",
        "corpus_gate",
        "provider_gate",
        "annotation_gate",
        "leakage_gate",
        "budget_gate",
        "reproducibility_gate",
    )
    blockers.extend(
        f"go/no-go gate is not approved: {gate}"
        for gate in required_gates
        if gates.get(gate) is not True
    )

    if plan.get("confirmatory_precision_plan_status") != "candidate":
        warnings.append(
            "pre-pilot launch must not silently promote the confirmatory precision plan"
        )

    decision = "go" if not blockers else "no_go"
    declared = status == "pilot_ready"
    if declared != (decision == "go"):
        blockers.append(
            "declared status disagrees with computed readiness; set pilot_ready only after every gate passes"
        )
        decision = "no_go"

    return {
        "schema_version": SCHEMA_VERSION,
        "decision": decision,
        "claim_level": "non_confirmatory_pre_pilot",
        "blockers": blockers,
        "warnings": warnings,
        "provider_configuration_count": len(configurations),
        "episode_count": design.get("episode_count"),
        "projected_provider_cost_usd": round(projected_cost, 2),
        "approved_cap_usd": round(cap, 2),
        "estimated_annotation_hours": round(estimated_hours, 2),
        "confirmatory_authorized": False,
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--plan",
        type=Path,
        default=Path("data/prepilot/launch-plan.candidate.json"),
    )
    parser.add_argument("--output", type=Path)
    parser.add_argument("--allow-blocked", action="store_true")
    args = parser.parse_args(argv)

    report = evaluate_launch_plan(load_launch_plan(args.plan))
    rendered = json.dumps(report, indent=2, sort_keys=True) + "\n"
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(rendered, encoding="utf-8")
    print(rendered, end="")
    return 0 if report["decision"] == "go" or args.allow_blocked else 2


if __name__ == "__main__":
    raise SystemExit(main())
