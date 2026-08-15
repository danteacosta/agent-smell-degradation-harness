"""Native ARP 3.0 emission for confirmatory requirement-degradation runs."""

from __future__ import annotations

from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import platform
from typing import Any, Mapping

from agent_reliability_protocol import ExecutorIdentity, RunManifestV3, SourceIdentity, check_contract
from arp_profiles import AGENT_SMELL_PROFILE


def write_confirmatory_manifest(
    path: Path,
    *,
    identity: Mapping[str, Any],
    requirement_text: str,
    experiment_id: str,
    project_id: str,
    source_intent_id: str,
    variant: str,
    split: str,
    source_revision: str,
    configuration_hash: str,
    provider: str,
    model_version: str,
) -> dict[str, object]:
    if split not in {"train", "calibration", "test"}:
        raise ValueError("confirmatory ARP manifest split must be train, calibration, or test")
    if not source_revision.strip():
        raise ValueError("confirmatory ARP manifest requires an immutable source revision")
    input_digest = hashlib.sha256(requirement_text.encode("utf-8")).hexdigest()
    variant_digest = hashlib.sha256(
        f"{experiment_id}:{source_intent_id}:{variant}".encode("utf-8")
    ).hexdigest()
    manifest = RunManifestV3(
        run_id=str(identity["episode_id"]),
        created_at=datetime.now(timezone.utc).isoformat(),
        source=SourceIdentity(
            revision=source_revision,
            input_ref=f"urn:agent-smell:requirement:{source_intent_id}:{input_digest}",
            input_hash=f"sha256:{input_digest}",
        ),
        executor=ExecutorIdentity(name=provider, version=model_version),
        configuration_hash=configuration_hash,
        environment={"python": platform.python_version()},
        profile=AGENT_SMELL_PROFILE,
        capture_policy="metadata",
        extensions={
            AGENT_SMELL_PROFILE: {
                "experiment_id": experiment_id,
                "project_id": project_id,
                "source_intent_id": source_intent_id,
                "variant_ref": f"sha256:{variant_digest}",
                "split": split,
                "confirmatory": True,
                "checkpoint_provenance": "runtime_native",
            }
        },
    )
    payload = manifest.to_dict()
    errors = check_contract("manifest", payload)
    if errors:
        raise ValueError("invalid ARP 3.0 confirmatory manifest: " + "; ".join(errors))
    path.write_text(json.dumps(payload, sort_keys=True, indent=2) + "\n", encoding="utf-8")
    return payload


__all__ = ["write_confirmatory_manifest"]
