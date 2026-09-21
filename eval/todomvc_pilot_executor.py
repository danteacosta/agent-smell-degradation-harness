"""Bounded offline container execution for the exploratory TodoMVC pilot."""
from __future__ import annotations

import json
from pathlib import Path
import re
import subprocess
import uuid


def container_command(image: str, inputs: Path, output: Path, name: str) -> list[str]:
    if not re.fullmatch(r"sha256:[0-9a-f]{64}", image):
        raise ValueError("immutable local Docker image ID required")
    for directory in (inputs, output):
        if not directory.is_dir() or directory.is_symlink():
            raise ValueError("real input/output directories required")
    return [
        "docker", "run", "--rm", "--name", name, "--network", "none",
        "--user", "1000:1000", "--read-only", "--cap-drop", "ALL",
        "--security-opt", "no-new-privileges", "--pids-limit", "1024",
        "--memory", "4g", "--cpus", "2", "--shm-size", "512m",
        "--tmpfs", "/tmp:rw,exec,nosuid,size=3g",
        "--mount", f"type=bind,src={inputs.resolve()},dst=/input,readonly",
        "--mount", f"type=bind,src={output.resolve()},dst=/output",
        image,
    ]


def execute(image: str, inputs: Path, output: Path, timeout: int = 240) -> dict:
    output.mkdir(parents=True, exist_ok=False)
    name = "todomvc-pilot-" + uuid.uuid4().hex
    command = container_command(image, inputs, output, name)
    (output / "container-command.json").write_text(json.dumps(command, indent=2))
    timed_out = False
    try:
        with (output / "container.log").open("wb") as log:
            try:
                result = subprocess.run(command, stdout=log, stderr=subprocess.STDOUT,
                                        timeout=timeout, check=False)
                returncode = result.returncode
            except subprocess.TimeoutExpired:
                timed_out = True
                returncode = 124
    finally:
        subprocess.run(["docker", "rm", "--force", name], capture_output=True,
                       timeout=30, check=False)
    receipt = {"returncode": returncode, "timed_out": timed_out, "image": image}
    (output / "executor.json").write_text(json.dumps(receipt, indent=2))
    return receipt
