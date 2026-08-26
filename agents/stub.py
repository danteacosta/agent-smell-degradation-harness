from __future__ import annotations

import copy
import re
from typing import Any

from agents.policies import Policy

# Plausible-but-wrong overrides per intent and task family.
_WEAKENINGS: dict[str, dict[str, dict[str, Any]]] = {
    "RF-04": {
        "codegen": {"order_id_pattern": r"^P-\d+$"},
        "test_gen": {
            "must_reject_ids": [],
            "criterion": "starts with P- followed by digits",
        },
    },
    "RF-07": {
        "codegen": {"sort_key": "order_code"},
        "test_gen": {
            "required_sort_key": "order_code",
            "criterion": "cards ordered by order antiquity",
        },
    },
    "RF-09": {
        "codegen": {"comparator": ">="},
        "test_gen": {
            "must_reject_minutes": [],
            "criterion": "after significant time",
        },
    },
    "RF-13": {
        "codegen": {"cardinality": 10},
        "test_gen": {
            "exact_cardinality": 10,
            "criterion": "display old active orders in sufficient quantity",
        },
    },
    "RF-11": {
        "codegen": {"refund_window_minutes": 15},
        "test_gen": {
            "must_reject_minutes": [],
            "must_accept_minutes": [15],
            "criterion": "refund within reasonable time",
        },
    },
}


_INTENT_SMELL_TYPES = {
    "RF-04": "identifier_format",
    "RF-07": "ordering_ambiguity",
    "RF-09": "vague_threshold",
    "RF-13": "cardinality_ambiguity",
    "RF-11": "numerical_inconsistency",
}


class StubAgent:
    def __init__(
        self,
        failure_mode: str | None = None,
        policy: Policy = Policy.DIRECT,
    ) -> None:
        self.failure_mode = failure_mode
        self.policy = policy

    def generate(self, pair: dict, variant: str, task_family: str) -> dict[str, Any]:
        controlled = pair.get("controlled_artifacts", {})
        if isinstance(controlled, dict):
            selected = controlled.get(variant, {})
            if isinstance(selected, dict) and isinstance(selected.get(task_family), dict):
                return copy.deepcopy(selected[task_family])

        if task_family == "behavior_codegen":
            execution = pair.get("oracle_spec", {}).get(task_family, {}).get("_execution", {})
            references = execution.get("reference_implementations", {})
            reference_name = "smelly_plausible" if self.failure_mode == "smell-blind" and variant == "smelly" else "clean"
            source_code = references.get(reference_name)
            if isinstance(source_code, str):
                return {"source_code": source_code}

        oracle = copy.deepcopy(pair["oracle_spec"][task_family])
        if isinstance(oracle, dict):
            oracle = {key: value for key, value in oracle.items() if not str(key).startswith("_")}

        if self.failure_mode == "oracle-mismatch":
            return self._weaken(
                oracle,
                pair["intent_id"],
                task_family,
                pair.get("smell", {}).get("type", ""),
            )

        if self.failure_mode == "smell-blind" and variant == "smelly":
            return self._weaken(
                oracle,
                pair["intent_id"],
                task_family,
                pair.get("smell", {}).get("type", ""),
            )

        return oracle

    def observe_checkpoints(
        self, pair: dict[str, Any], *, variant: str, task_family: str
    ) -> dict[str, dict[str, Any]]:
        """Emit an explicitly stub-labelled checkpoint for offline schema tests."""

        requirement = str(
            pair["clean_requirement"] if variant == "clean" else pair["smelly_requirement"]
        )
        quantities = [
            {"value": int(value), "unit": unit.lower()}
            for value, unit in re.findall(r"\b(\d+)\s*([A-Za-z]+)", requirement)
        ]
        vague_terms = {
            "old", "some", "significant", "reasonable", "sufficient", "several", "while"
        }
        unresolved = sorted(
            {word.lower() for word in re.findall(r"[A-Za-z]+", requirement) if word.lower() in vague_terms}
        )
        return {
            "interpretation": {
                "constraints": [requirement],
                "quantities": quantities,
                "unresolved_references": unresolved,
                "assumptions": [],
                "contradictions": [],
            },
            "plan": {
                "validation_checks": [task_family],
                "planned_tools": [],
                "coverage_targets": ["requirement constraints"],
            },
            "execution": {
                "revisions": 0,
                "validation_attempts": 1,
                "errors": [],
                "retrieval_events": 0,
            },
        }

    def _weaken(
        self,
        oracle: dict[str, Any],
        intent_id: str,
        task_family: str,
        smell_type: str = "",
    ) -> dict[str, Any]:
        overrides = _WEAKENINGS.get(intent_id, {}).get(task_family, {})
        if not overrides and smell_type:
            for source_intent, source_smell in _INTENT_SMELL_TYPES.items():
                if source_smell == smell_type:
                    overrides = _WEAKENINGS.get(source_intent, {}).get(task_family, {})
                    if overrides:
                        break
        weakened = copy.deepcopy(oracle)
        weakened.update(overrides)
        return weakened
