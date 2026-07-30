from __future__ import annotations
import json
from pathlib import Path

from agent_reliability_protocol import check_contract
from eval.prepilot import run_pre_pilot


def test_prepilot_protocol_manifest_validates_with_shared_protocol(tmp_path):
    run_dir = Path(run_pre_pilot(output_root=tmp_path, run_id="shared-protocol")["run_dir"])
    manifest = json.loads((run_dir / "protocol_manifest.json").read_text())
    assert check_contract("manifest", manifest) == []
