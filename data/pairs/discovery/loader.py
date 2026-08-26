"""Strict loader and validator for the twelve-case discovery corpus.

This module is intentionally local to the discovery corpus. It does not change
the historical pair loader or the production experiment code.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parent
MANIFEST_PATH = ROOT / "manifest.json"
EXPECTED_CASE_IDS = {
    "ARTA-NFR-001",
    "ARTA-NFR-002",
    "ARTA-CCTNS-001",
    "ARTA-CCTNS-002",
    "ARTA-ERTMS-001",
    "ARTA-ERTMS-002",
    "ARTA-FUN-001",
    "ARTA-FUN-002",
    "ARTA-GAMMA-001",
    "ARTA-GAMMA-002",
    "ARTA-PEERING-001",
    "ARTA-PEERING-002",
}
EXPECTED_FAMILIES = {"codegen", "test_gen", "behavior_codegen"}
FORBIDDEN_HISTORICAL_KEYS = {
    "_execution",
    "hidden_tests",
    "reference_implementations",
    "input_schema",
}


def _read(path: Path) -> dict[str, Any]:
    with path.open(encoding="utf-8") as handle:
        value = json.load(handle)
    if not isinstance(value, dict):
        raise ValueError(f"{path.name}: expected a JSON object")
    return value


def _assert(condition: bool, message: str) -> None:
    if not condition:
        raise ValueError(message)


def _validate_case(path: Path, case: dict[str, Any], manifest_entry: dict[str, Any]) -> None:
    prefix = path.name
    required = {
        "intent_id",
        "source_intent_id",
        "source",
        "source_excerpt",
        "source_sha256",
        "provenance_url",
        "project_id",
        "clean_requirement",
        "smelly_requirement",
        "removed_condition",
        "natural_variant",
        "contamination_notes",
        "licensing_notes",
        "smell",
        "generation_contract",
        "oracle_spec",
    }
    _assert(required <= set(case), f"{prefix}: missing required case fields")
    _assert(case["intent_id"] == manifest_entry["intent_id"], f"{prefix}: manifest intent_id mismatch")
    _assert(case["source_intent_id"] == manifest_entry["source_intent_id"], f"{prefix}: manifest source_intent_id mismatch")
    _assert(case["project_id"] == manifest_entry["project_id"], f"{prefix}: manifest project_id mismatch")
    _assert(case["smell"]["type"] == manifest_entry["smell_type"], f"{prefix}: manifest smell_type mismatch")
    _assert(case["source"]["source_file_sha256"] == case["source_sha256"], f"{prefix}: source hash mismatch")
    _assert(case["natural_variant"] is False, f"{prefix}: discovery pairs must be controlled variants")

    generation = case["generation_contract"]
    oracle = case["oracle_spec"]
    _assert(set(generation) == EXPECTED_FAMILIES, f"{prefix}: unexpected generation families")
    _assert(set(oracle) == EXPECTED_FAMILIES, f"{prefix}: unexpected oracle families")

    for family in ("codegen", "test_gen"):
        contract = generation[family]
        expected_keys = contract.get("output_keys")
        _assert(isinstance(expected_keys, list) and expected_keys, f"{prefix}: {family} needs output_keys")
        _assert(set(oracle[family]) == set(expected_keys), f"{prefix}: {family} contract/oracle mismatch")
        _assert(not (FORBIDDEN_HISTORICAL_KEYS & set(oracle[family])), f"{prefix}: executable metadata leaked into historical {family}")

    behavior_contract = generation["behavior_codegen"]
    _assert(behavior_contract["output_keys"] == ["source_code"], f"{prefix}: behavior_codegen must emit source_code only")
    behavior_oracle = oracle["behavior_codegen"]
    _assert(set(behavior_oracle) == {"_execution"}, f"{prefix}: behavior_codegen oracle must contain private evaluator metadata only")
    execution = behavior_oracle["_execution"]
    _assert(execution["language"] == "python", f"{prefix}: behavior evaluator must use Python")
    _assert(execution["entry_point"] == "evaluate", f"{prefix}: behavior evaluator entry point must be evaluate")
    tests = execution["hidden_tests"]
    _assert(isinstance(tests, list) and tests, f"{prefix}: hidden tests are required")
    _assert(all({"id", "input", "expected_output"} <= set(test) for test in tests), f"{prefix}: malformed hidden test")
    removed = set(execution["removed_condition_test_ids"])
    _assert(removed and removed <= {test["id"] for test in tests}, f"{prefix}: removed-condition tests must be hidden-test IDs")
    refs = execution["reference_implementations"]
    _assert(set(refs) == {"clean", "smelly_plausible"}, f"{prefix}: both reference implementations are required")


def load_discovery_cases() -> list[dict[str, Any]]:
    manifest = _read(MANIFEST_PATH)
    entries = manifest.get("records")
    _assert(manifest.get("case_count") == 12, "manifest: case_count must be 12")
    _assert(isinstance(entries, list) and len(entries) == 12, "manifest: exactly twelve record entries are required")
    by_id = {entry["intent_id"]: entry for entry in entries}
    _assert(set(by_id) == EXPECTED_CASE_IDS, "manifest: case IDs do not match the approved twelve-case set")

    paths = sorted(ROOT.glob("arta-*.json"))
    _assert(len(paths) == 12, "discovery directory must contain exactly twelve case JSON files")
    cases = []
    for path in paths:
        case = _read(path)
        entry = next((item for item in entries if item.get("filename") == path.name), None)
        _assert(entry is not None, f"manifest: missing entry for {path.name}")
        _validate_case(path, case, entry)
        cases.append(case)
    _assert({case["intent_id"] for case in cases} == EXPECTED_CASE_IDS, "case IDs do not match the approved set")
    _assert({case["project_id"] for case in cases} == set(manifest["required_projects"]), "all six projects are required")
    return cases


if __name__ == "__main__":
    cases = load_discovery_cases()
    print(f"validated {len(cases)} discovery cases across {len({case['project_id'] for case in cases})} projects")
