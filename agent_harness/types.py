from __future__ import annotations
from dataclasses import dataclass, field
from enum import Enum
from typing import Any


class Variant(str, Enum):
    CLEAN = "clean"
    SMELLY = "smelly"


class TaskFamily(str, Enum):
    CODEGEN = "codegen"
    TEST_GEN = "test_gen"


@dataclass(frozen=True)
class Smell:
    category: str
    type: str
    injection_rule: str


@dataclass
class OracleResult:
    passed: bool
    detail: str
    checks: dict[str, bool] = field(default_factory=dict)


@dataclass
class Episode:
    episode_id: str
    intent_id: str
    variant: Variant
    smell: Smell | None
    task_family: TaskFamily
    policy: str
    mode: str
    replication_id: int = 0
    requirement_text: str = ""
    artifact: dict[str, Any] | None = None
    oracle_result: OracleResult | None = None
    semantic_label: str | None = None  # ok | degraded | infra_error
    provenance_path: str | None = None
    cost: float = 0.0
    latency_ms: float = 0.0
    model: str | None = None
    provider: str | None = None
