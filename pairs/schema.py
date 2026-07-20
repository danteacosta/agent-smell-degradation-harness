from __future__ import annotations

REQUIRED_TOP_LEVEL_KEYS = (
    "intent_id",
    "clean_requirement",
    "smelly_requirement",
    "smell",
    "oracle_spec",
)

REQUIRED_SMELL_KEYS = ("category", "type", "injection_rule")

REQUIRED_TASK_FAMILIES = ("codegen", "test_gen")
