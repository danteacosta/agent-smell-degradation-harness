from pathlib import Path

import pytest

from eval.todomvc_pilot_executor import container_command


def test_generated_program_has_no_network_credentials_or_writable_source(tmp_path):
    inputs, output = tmp_path / "input", tmp_path / "output"
    inputs.mkdir()
    output.mkdir()
    command = container_command("sha256:" + "a" * 64, inputs, output, "pilot-test")
    assert command[command.index("--network") + 1] == "none"
    assert command[command.index("--user") + 1] == "1000:1000"
    assert "--read-only" in command
    assert command[command.index("--cap-drop") + 1] == "ALL"
    assert "no-new-privileges" in command
    mounts = [command[i + 1] for i, item in enumerate(command) if item == "--mount"]
    assert mounts == [f"type=bind,src={inputs},dst=/input,readonly",
                      f"type=bind,src={output},dst=/output"]
    assert "--env" not in command and "-e" not in command


def test_mutable_runtime_tag_is_rejected(tmp_path):
    with pytest.raises(ValueError, match="immutable"):
        container_command("image:latest", tmp_path, tmp_path, "pilot-test")
