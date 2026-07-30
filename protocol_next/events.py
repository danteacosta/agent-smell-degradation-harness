from __future__ import annotations
import json
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any, Iterable, Mapping

@dataclass(frozen=True)
class LifecycleEvent:
    name: str; episode_id: str; stage: str; payload: Mapping[str, Any]
    def to_dict(self) -> dict[str, Any]: return asdict(self)

def redact(value: Any, keys: frozenset[str] = frozenset({"api_key", "authorization", "secret", "token"})) -> Any:
    if isinstance(value, Mapping): return {k: "[REDACTED]" if k.lower() in keys else redact(v, keys) for k,v in value.items()}
    if isinstance(value, list): return [redact(item, keys) for item in value]
    return value

def export_jsonl(path: Path, rows: Iterable[Mapping[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(json.dumps(redact(dict(row)), sort_keys=True) for row in rows) + "\n", encoding="utf-8")
