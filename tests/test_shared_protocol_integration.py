from __future__ import annotations
import pytest

from agent_reliability_protocol import __version__, check_contract, upgrade_manifest
from eval.prepilot import run_pre_pilot


def test_prepilot_protocol_manifest_validates_with_shared_protocol(tmp_path):
    with pytest.raises(ValueError, match="12 independent source intents"):
        run_pre_pilot(output_root=tmp_path, run_id="shared-protocol")


def test_shared_protocol_v2_accepts_legacy_protocol_next_manifest():
    legacy = {
        "schema_version": "protocol_next/v1",
        "run_id": "legacy-run",
        "started_at": "2026-07-30T00:00:00+00:00",
        "decision": {"outcome": "pass"},
        "identifiers": {"build": "legacy-build"},
        "hashes": {"input": "legacy-hash"},
    }

    assert __version__ == "2.0.5"
    assert check_contract("manifest", legacy) == []
    assert upgrade_manifest(legacy)["schema_version"] == "arp/v1"
