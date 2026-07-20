from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, TextIO


class ProvenanceRecorder:
    def __init__(self, path: Path | str) -> None:
        self._path = Path(path)
        self._path.parent.mkdir(parents=True, exist_ok=True)
        self._file: TextIO = self._path.open("a", encoding="utf-8")

    def operational(self, name: str, payload: dict[str, Any]) -> None:
        self._write("operational", name, payload)

    def semantic(self, name: str, payload: dict[str, Any]) -> None:
        self._write("semantic", name, payload)

    def _write(self, kind: str, name: str, payload: dict[str, Any]) -> None:
        record = {
            "kind": kind,
            "name": name,
            "payload": payload,
            "ts": datetime.now(timezone.utc).isoformat(),
        }
        self._file.write(json.dumps(record) + "\n")

    def close(self) -> None:
        self._file.flush()
        self._file.close()
