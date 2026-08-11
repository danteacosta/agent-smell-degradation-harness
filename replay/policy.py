from __future__ import annotations

import json
import hashlib
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from .schema import ContractError, canonical_json_bytes

POLICY_SCHEMA_VERSION = "constraint-policy/v1"
_RULES = {
    "missing_constraints",
    "contradiction",
    "execution_error",
    "missing_validation",
    "unresolved_reference",
    "missing_coverage",
}
_FACTS = {
    "constraint_count",
    "validation_check_count",
    "coverage_target_count",
    "unresolved_reference_count",
    "contradiction_count",
    "error_count",
}
_RULE_TO_FACT = {
    "missing_constraints": ("constraint_count", "zero"),
    "contradiction": ("contradiction_count", "positive"),
    "execution_error": ("error_count", "positive"),
    "missing_validation": ("validation_check_count", "zero"),
    "unresolved_reference": ("unresolved_reference_count", "positive"),
    "missing_coverage": ("coverage_target_count", "zero"),
}
_EVIDENCE = {
    "missing_constraints": ("requirement constraints", "interpretation.completed", 0.95, "block"),
    "contradiction": ("requirement constraints", "interpretation.completed", 0.95, "block"),
    "execution_error": ("execution evidence", "tool.completed", 0.95, "block"),
    "missing_validation": ("validation checks", "plan.completed", 0.95, "block"),
    "unresolved_reference": ("requirement constraints", "interpretation.completed", 0.55, "clarify"),
    "missing_coverage": ("coverage targets", "plan.completed", 0.55, "clarify"),
}


@dataclass(frozen=True)
class GatePolicy:
    version: str
    block_when: tuple[str, ...]
    warn_when: tuple[str, ...]

    @classmethod
    def from_mapping(cls, value: Any) -> "GatePolicy":
        if not isinstance(value, dict):
            raise ContractError("policy must be an object")
        if set(value) != {"schema_version", "version", "block_when", "warn_when"}:
            raise ContractError("policy has unknown or missing fields")
        if value["schema_version"] != POLICY_SCHEMA_VERSION:
            raise ContractError(f"policy schema_version must be {POLICY_SCHEMA_VERSION}")
        version = value["version"]
        if not isinstance(version, str) or not version.strip():
            raise ContractError("policy version must be a non-empty string")
        rules: list[tuple[str, ...]] = []
        for field in ("block_when", "warn_when"):
            entries = value[field]
            if not isinstance(entries, list) or not all(isinstance(item, str) and item.strip() for item in entries):
                raise ContractError(f"policy {field} must be an array of non-empty strings")
            if len(set(entries)) != len(entries):
                raise ContractError(f"policy {field} contains duplicate rules")
            if not set(entries).issubset(_RULES):
                raise ContractError(f"policy {field} contains an unknown rule")
            rules.append(tuple(entries))
        return cls(version.strip(), rules[0], rules[1])

    def to_mapping(self) -> dict[str, Any]:
        return {
            "schema_version": POLICY_SCHEMA_VERSION,
            "version": self.version,
            "block_when": list(self.block_when),
            "warn_when": list(self.warn_when),
        }

    @property
    def sha256(self) -> str:
        return hashlib.sha256(canonical_json_bytes(self.to_mapping())).hexdigest()

    def evaluate(self, facts: dict[str, Any]) -> tuple[str, list[dict[str, Any]]]:
        if not isinstance(facts, dict) or set(facts) != _FACTS:
            raise ContractError("policy facts have unknown or missing fields")
        for name, value in facts.items():
            if isinstance(value, bool) or not isinstance(value, int) or value < 0:
                raise ContractError(f"policy fact {name} must be a non-negative integer")
        for decision, rules in (("block", self.block_when), ("warn", self.warn_when)):
            triggered = [rule for rule in rules if self._triggered(rule, facts)]
            if triggered:
                return decision, [self._evidence(rule, decision) for rule in triggered]
        return "approve", []

    @staticmethod
    def _triggered(rule: str, facts: dict[str, int]) -> bool:
        fact_name, predicate = _RULE_TO_FACT[rule]
        return facts[fact_name] == 0 if predicate == "zero" else facts[fact_name] > 0

    @staticmethod
    def _evidence(rule: str, decision: str) -> dict[str, Any]:
        constraint, checkpoint, confidence, action = _EVIDENCE[rule]
        return {
            "constraint": constraint,
            "checkpoint": checkpoint,
            "confidence": confidence,
            "recommended_action": "block" if decision == "block" else action,
            "rule_id": rule,
        }


DEFAULT_POLICY = GatePolicy(
    version="constraint-gate/v1",
    block_when=("missing_constraints", "contradiction", "execution_error", "missing_validation"),
    warn_when=("unresolved_reference", "missing_coverage"),
)


def load_policy(path: str | Path) -> GatePolicy:
    target = Path(path)
    try:
        value = json.loads(target.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise ContractError(f"cannot read policy {target}: {exc}") from exc
    return GatePolicy.from_mapping(value)


def load_failure_cases(path: str | Path | None = None) -> list[dict[str, Any]]:
    target = Path(path) if path else Path(__file__).with_name("failure_cases.json")
    value = json.loads(target.read_text(encoding="utf-8"))
    if not isinstance(value, list):
        raise ValueError("failure case registry must be an array")
    for case in value:
        if not isinstance(case, dict) or not case.get("case_id") or case.get("confirmatory") is not False:
            raise ValueError("failure case registry entries must be explicit non-confirmatory cases")
    return value
