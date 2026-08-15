from __future__ import annotations

import json
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Literal, TextIO

Tier = Literal["A", "B"]


class ProvenanceRecorder:
    def __init__(
        self,
        path: Path | str,
        *,
        episode_identity: dict[str, Any] | None = None,
        arp_context: dict[str, Any] | None = None,
        wire_version: str = "2.0.5",
        profile: str | None = None,
    ) -> None:
        self._path = Path(path)
        self._episode_identity = episode_identity
        self._arp_context = arp_context or episode_identity or {}
        self._sequence = 0
        self._last_event_id: str | None = None
        self._last_ended_at: str | None = None
        self._wire_version = wire_version
        self._profile = profile
        if wire_version not in {"2.0.5", "3.0.0"}:
            raise ValueError("unsupported ARP wire version")
        if wire_version == "3.0.0" and not profile:
            raise ValueError("ARP 3.0 traces require a profile")
        self._path.parent.mkdir(parents=True, exist_ok=True)
        self._file: TextIO = self._path.open("a", encoding="utf-8")

    def operational(
        self,
        name: str,
        payload: dict[str, Any],
        *,
        tier: Tier = "A",
        started_at: str | None = None,
        ended_at: str | None = None,
    ) -> None:
        self._write("operational", name, payload, tier=tier, started_at=started_at, ended_at=ended_at)

    def semantic(
        self,
        name: str,
        payload: dict[str, Any],
        *,
        tier: Tier = "A",
        started_at: str | None = None,
        ended_at: str | None = None,
    ) -> None:
        self._write("semantic", name, payload, tier=tier, started_at=started_at, ended_at=ended_at)

    def oracle_verdict(
        self,
        payload: dict[str, Any],
        *,
        tier: Tier = "B",
    ) -> None:
        self._write("semantic", "oracle_verdict", payload, tier=tier)

    def _write(
        self,
        kind: str,
        name: str,
        payload: dict[str, Any],
        *,
        tier: Tier,
        started_at: str | None = None,
        ended_at: str | None = None,
    ) -> None:
        timestamp = datetime.now(timezone.utc).isoformat()
        started_at = started_at or timestamp
        ended_at = ended_at or started_at
        event_name = name
        if self._wire_version == "2.0.5":
            if name == "constraint_extract":
                event_name = "interpretation.completed"
            elif name in {"oracle_verdict", "evaluation.completed"}:
                event_name = "evaluation.completed"
            elif name in {"latency", "artifact.completed"}:
                event_name = "tool.completed"
        deployable_attributes = {
            key: value
            for key, value in payload.items()
            if key not in {"variant", "variant_id", "smell", "defect_family", "defect_type", "mutation"}
        }
        event_id = str(uuid.uuid4())
        sequence_number = self._sequence
        episode_id = str(self._arp_context.get("episode_id", "unknown"))
        source_refs = list(payload.get("source_refs", [])) or [
            {
                "kind": "episode",
                "identifier": episode_id,
                "event_id": event_id,
                "sequence_number": sequence_number,
            }
        ]
        if self._wire_version == "3.0.0":
            is_label_plane = event_name in {"artifact.completed", "evaluation.completed"}
            profile_payload = (
                {"plane": "label", "payload": deployable_attributes}
                if is_label_plane
                else {"checkpoint_source": "runtime_native"}
            )
            record = {
                "event_id": event_id,
                "schema_version": "3.0.0",
                "run_id": str(self._arp_context.get("run_id", "unknown")),
                "episode_id": episode_id,
                "sequence_number": sequence_number,
                "checkpoint": event_name,
                "event_type": event_name,
                "started_at": started_at,
                "ended_at": ended_at,
                "attributes": {} if is_label_plane else deployable_attributes,
                "content_reference": None,
                "parent_event_id": self._last_event_id,
                "extensions": {str(self._profile): profile_payload},
            }
        else:
            record = {
            "event_id": event_id,
            "schema_version": "2.0.5",
            "experiment_id": str(self._arp_context.get("experiment_id", "unknown")),
            "run_id": str(self._arp_context.get("run_id", "unknown")),
            "episode_id": episode_id,
            "replication_id": int(self._arp_context.get("replication_id", 0)),
            "sequence_number": sequence_number,
            "checkpoint": event_name,
            "event_type": event_name,
            "started_at": started_at,
            "ended_at": ended_at,
            "attributes": {**deployable_attributes, "source_event_name": name},
            "content_reference": None,
            "parent_event_id": self._last_event_id,
            "kind": kind,
            "name": name,
            "payload": payload,
            "tier": tier,
            "ts": timestamp,
            }
            if self._episode_identity is not None:
                record["episode_identity"] = self._episode_identity
            record["source_refs"] = source_refs
        self._file.write(json.dumps(record) + "\n")
        self._sequence += 1
        self._last_event_id = record["event_id"]
        self._last_ended_at = ended_at

    @property
    def last_ended_at(self) -> str | None:
        return self._last_ended_at

    def close(self) -> None:
        self._file.flush()
        self._file.close()
