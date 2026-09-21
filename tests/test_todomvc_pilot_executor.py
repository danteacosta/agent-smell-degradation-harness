from pathlib import Path
import os
import subprocess

import pytest

from eval.todomvc_pilot_executor import container_command


def test_generated_program_has_no_network_credentials_or_writable_source(tmp_path):
    inputs, output = tmp_path / "input", tmp_path / "output"
    inputs.mkdir()
    output.mkdir()
    command = container_command("sha256:" + "a" * 64, inputs, output, "pilot-test")
    assert command[command.index("--network") + 1] == "none"
    assert command[command.index("--user") + 1] == f"{os.getuid()}:{os.getgid()}"
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


def test_private_mount_uses_nonroot_collector_identity(tmp_path, monkeypatch):
    monkeypatch.setattr(os, "getuid", lambda: 2001)
    monkeypatch.setattr(os, "getgid", lambda: 2002)
    command = container_command("sha256:" + "a" * 64, tmp_path, tmp_path, "identity")
    assert command[command.index("--user") + 1] == "2001:2002"


def test_root_collector_is_rejected(tmp_path, monkeypatch):
    monkeypatch.setattr(os, "getuid", lambda: 0)
    with pytest.raises(ValueError, match="non-root"):
        container_command("sha256:" + "a" * 64, tmp_path, tmp_path, "root")


def test_runner_rejects_missing_inputs_before_preparing_runtime():
    # The real entrypoint must fail before touching /opt, /tmp or baked-in code.
    assert not Path("/input/response.json").exists()
    runner = Path("eval/fixtures/todomvc-pilot-run.sh")
    result = subprocess.run(["bash", str(runner)], capture_output=True, text=True)
    assert result.returncode == 78
    assert "required input is missing or unreadable" in result.stderr
    assert "cp:" not in result.stderr


@pytest.mark.skipif(not os.environ.get("TODOMVC_BOUNDARY_IMAGE"),
                    reason="requires the Docker custody probe image")
def test_real_container_reads_private_inputs_and_writes_private_output(tmp_path):
    inputs, output = tmp_path / "input", tmp_path / "output"
    inputs.mkdir(mode=0o700)
    output.mkdir(mode=0o700)
    for name in ("response.json", "TodoItem.vue"):
        path = inputs / name
        path.write_text("generated response sentinel")
        path.chmod(0o600)
    command = container_command(os.environ["TODOMVC_BOUNDARY_IMAGE"], inputs,
                                output, "custody-boundary-test")
    result = subprocess.run(command, capture_output=True, text=True, timeout=60)
    assert result.returncode == 0, result.stderr
    assert (output / "copied-response").read_text() == "generated response sentinel"
    assert (output / "copied-component").read_text() == "generated response sentinel"
    assert inputs.stat().st_mode & 0o777 == 0o700
    assert (inputs / "response.json").stat().st_mode & 0o777 == 0o600


@pytest.mark.skipif(not os.environ.get("TODOMVC_BOUNDARY_IMAGE"),
                    reason="requires the Docker custody probe image")
@pytest.mark.parametrize("invalid", ["response.json", "TodoItem.vue"])
def test_real_runner_rejects_either_missing_input(tmp_path, invalid):
    inputs, output = tmp_path / "input", tmp_path / "output"
    inputs.mkdir(mode=0o700)
    output.mkdir(mode=0o700)
    for name in ("response.json", "TodoItem.vue"):
        if name != invalid:
            (inputs / name).write_text("present")
    command = container_command(os.environ["TODOMVC_BOUNDARY_IMAGE"], inputs,
                                output, "custody-missing-test")
    command[-1:-1] = ["--entrypoint", "bash"]
    result = subprocess.run(command + ["/runner.sh"], capture_output=True,
                            text=True, timeout=60)
    assert result.returncode == 78, result.stderr
    assert f"required input is missing or unreadable: /input/{invalid}" in result.stderr
    assert not list(output.iterdir())
