from __future__ import annotations

import copy
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
        oracle = copy.deepcopy(pair["oracle_spec"][task_family])

        if self.failure_mode == "oracle-mismatch":
            return self._weaken(oracle, pair["intent_id"], task_family)

        if self.failure_mode == "smell-blind" and variant == "smelly":
            return self._weaken(oracle, pair["intent_id"], task_family)

        return oracle

    def _weaken(
        self,
        oracle: dict[str, Any],
        intent_id: str,
        task_family: str,
    ) -> dict[str, Any]:
        overrides = _WEAKENINGS.get(intent_id, {}).get(task_family, {})
        weakened = copy.deepcopy(oracle)
        weakened.update(overrides)
        return weakened
