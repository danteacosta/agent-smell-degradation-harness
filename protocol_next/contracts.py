from __future__ import annotations
from dataclasses import asdict, dataclass, field
from enum import StrEnum
from typing import Any, Mapping

class EvidenceStage(StrEnum):
    INPUT = "input"; INTERMEDIATE = "intermediate"; OUTPUT = "output"

@dataclass(frozen=True)
class EpisodeIdentity:
    experiment_id: str; run_id: str; episode_id: str; replication_id: int; workload_id: str; variant_id: str; task_id: str; configuration_id: str
    def to_dict(self) -> dict[str, Any]: return asdict(self)

@dataclass(frozen=True)
class RunManifest:
    run_id: str; experiment_id: str; configuration: Mapping[str, Any]; input_hashes: Mapping[str, str] = field(default_factory=dict); metadata: Mapping[str, Any] = field(default_factory=dict)
    def to_dict(self) -> dict[str, Any]: return {"run_id": self.run_id, "experiment_id": self.experiment_id, "configuration": dict(self.configuration), "input_hashes": dict(self.input_hashes), "metadata": dict(self.metadata)}

@dataclass(frozen=True)
class EvidenceReference:
    uri: str; sha256: str | None = None
    def to_dict(self) -> dict[str, Any]: return {k:v for k,v in asdict(self).items() if v is not None}

@dataclass(frozen=True)
class Evidence:
    kind: str; subject: str; stage: EvidenceStage = EvidenceStage.OUTPUT; observed: Any = None; expected: Any = None; reference: EvidenceReference | None = None
    def to_dict(self) -> dict[str, Any]:
        data = asdict(self); data["stage"] = self.stage.value
        if self.reference: data["reference"] = self.reference.to_dict()
        return {k:v for k,v in data.items() if v is not None}

@dataclass(frozen=True)
class DecisionReason:
    code: str; message: str; evidence: tuple[Evidence, ...] = ()
    def to_dict(self) -> dict[str, Any]: return {"code": self.code, "message": self.message, "evidence": [item.to_dict() for item in self.evidence]}

@dataclass(frozen=True)
class GateDecision:
    outcome: str; reasons: tuple[DecisionReason, ...] = ()
    def __post_init__(self) -> None:
        if self.outcome not in ("pass", "fail"): raise ValueError("outcome must be 'pass' or 'fail'")
        if (self.outcome == "pass") != (not self.reasons): raise ValueError("pass has no reasons; fail requires reasons")
    def to_dict(self) -> dict[str, Any]: return {"outcome": self.outcome, "reasons": [r.to_dict() for r in self.reasons]}
