import json
from hashlib import sha256
import subprocess
import sys
from pathlib import Path

import pytest


SCRIPT = Path(__file__).resolve().parents[1] / "scripts/prepare_calibration_queues.py"


def run_freezer(tmp_path, mode="valid"):
    tasks = tmp_path / "tasks.json"
    signals = tmp_path / "signals.json"
    tasks.write_text(json.dumps([dict(item_id="x", presented_text="An obligation",
                                    rubric_version="v2", duplicate_subset=False)]))
    signals.write_text(json.dumps([dict(item_id="x", stratum_id="p")]))
    outputs = [tmp_path / name for name in ("audit.jsonl", "triage.jsonl", "manifest.json")]
    if mode == "existing":
        outputs[2].write_text("preserve me")
    elif mode == "input_alias":
        outputs[0] = tasks
    elif mode == "output_alias":
        outputs[1] = outputs[0]
    elif mode == "symlink":
        outputs[0].symlink_to(tasks)
    elif mode == "dangling":
        outputs[0].symlink_to(tmp_path / "missing")
    elif mode == "write_failure":
        parent = tmp_path / "not_a_directory"
        parent.write_text("preserve parent")
        outputs[1] = parent / "triage.jsonl"
    before = tasks.read_bytes()
    result = subprocess.run([sys.executable, str(SCRIPT), "--tasks", str(tasks),
        "--signals", str(signals), "--calibration-tasks", str(outputs[0]),
        "--triage-tasks", str(outputs[1]), "--manifest", str(outputs[2]),
        "--calibration-count", "1", "--triage-count", "0", "--seed", "1",
        "--source-selection-sha256", "a" * 64], capture_output=True, text=True)
    return result, outputs, tasks, before


@pytest.mark.parametrize("mode", ["existing", "input_alias", "output_alias", "symlink", "dangling", "write_failure"])
def test_rejects_unsafe_targets_without_writing_any_packet(tmp_path, mode):
    result, outputs, tasks, before = run_freezer(tmp_path, mode)
    assert result.returncode != 0
    assert tasks.read_bytes() == before
    if mode == "existing":
        assert outputs[2].read_text() == "preserve me"
        assert not outputs[0].exists()
        assert not outputs[1].exists()
    else:
        assert not outputs[2].exists()
    if mode == "write_failure":
        assert not outputs[0].exists()
        assert outputs[1].parent.read_text() == "preserve parent"


def test_cli_publishes_private_content_bound_packets(tmp_path):
    result, outputs, _, _ = run_freezer(tmp_path)
    assert result.returncode == 0, result.stderr
    manifest = json.loads(outputs[2].read_text())
    assert len(manifest["calibration_tasks_sha256"]) == 64
    assert all(path.stat().st_mode & 0o777 == 0o600 for path in outputs)
    for path, field in zip(outputs[:2], ["calibration_tasks_sha256", "triage_tasks_sha256"]):
        rows = [json.loads(line) for line in path.read_text().splitlines()]
        digest = sha256(json.dumps(rows, ensure_ascii=False, sort_keys=True,
                                  separators=(",", ":")).encode()).hexdigest()
        assert manifest[field] == digest
