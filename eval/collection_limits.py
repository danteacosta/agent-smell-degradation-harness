"""Single-host collection admission and bounded subprocess supervision.

All cooperating launchers must share one root/policy. This is not a distributed
scheduler, cgroup replacement, or protection against another same-UID program.
"""
from contextlib import contextmanager
import argparse
import fcntl
import json
import os
from pathlib import Path
import resource
import signal
import stat
import subprocess
import sys
import tempfile
import threading


@contextmanager
def global_slot(root=None, *, max_runs=1):
    if type(max_runs) is not int or not 1 <= max_runs <= 64:
        raise ValueError("max_runs must be an integer between 1 and 64")
    root = Path(root) if root is not None else Path(tempfile.gettempdir()) / f"asd-collections-{os.getuid()}"
    root.mkdir(mode=0o700, parents=True, exist_ok=True)
    fd = os.open(root, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW)
    selected = None
    try:
        info = os.fstat(fd)
        if info.st_uid != os.getuid() or stat.S_IMODE(info.st_mode) != 0o700:
            raise ValueError("global resource directory must be private and owned")
        fcntl.flock(fd, fcntl.LOCK_EX)
        policy = root / "policy.json"
        expected = json.dumps({"schema": "collection-slots/v1", "max_runs": max_runs})
        pfd = os.open(policy, os.O_RDWR | os.O_CREAT | os.O_NOFOLLOW, 0o600)
        try:
            if not stat.S_ISREG(os.fstat(pfd).st_mode):
                raise ValueError("invalid global policy")
            if os.fstat(pfd).st_size == 0:
                os.write(pfd, expected.encode())
                os.fsync(pfd)
                os.fsync(fd)
            elif os.read(pfd, 1024).decode() != expected:
                raise ValueError("global policy mismatch; do not change capacity during collection")
        finally:
            os.close(pfd)
        for index in range(max_runs):
            slot = os.open(root / f"slot-{index}", os.O_RDWR | os.O_CREAT | os.O_NOFOLLOW, 0o600)
            try:
                if not stat.S_ISREG(os.fstat(slot).st_mode):
                    raise ValueError("invalid global slot")
                fcntl.flock(slot, fcntl.LOCK_EX | fcntl.LOCK_NB)
                selected = slot
                break
            except BlockingIOError:
                os.close(slot)
            except BaseException:
                os.close(slot)
                raise
        if selected is None:
            raise BlockingIOError("global collection capacity exhausted")
        fcntl.flock(fd, fcntl.LOCK_UN)
        yield
    finally:
        if selected is not None:
            os.close(selected)
        os.close(fd)


def verify_cgroup(path, *, memory_bytes, max_tasks, cpu_quota_us):
    """Require a preconfigured delegated cgroup; never loosen a live policy."""
    group = Path(path)
    root = Path("/sys/fs/cgroup")
    if group.is_symlink() or not group.resolve().is_relative_to(root) or group.resolve() == root:
        raise ValueError("a delegated cgroup v2 below /sys/fs/cgroup is required")
    if not (root / "cgroup.controllers").is_file():
        raise ValueError("cgroup v2 is unavailable")
    expected = {"memory.max": str(memory_bytes), "memory.swap.max": "0", "pids.max": str(max_tasks),
                "cpu.max": f"{cpu_quota_us} 100000"}
    for name, value in expected.items():
        if (group / name).read_text().strip() != value:
            raise ValueError(f"cgroup {name} differs from required shared policy")
    return group


def supervise(command, *, root=None, max_runs=1, wall_seconds=3600,
              memory_bytes=2_147_483_648, file_bytes=268_435_456, open_files=128,
              cgroup=None, max_tasks=64, cpu_quota_us=100000):
    for value in (wall_seconds, memory_bytes, file_bytes, open_files, max_tasks, cpu_quota_us):
        if type(value) is not int or value <= 0:
            raise ValueError("limits must be positive integers")
    if not command:
        raise ValueError("command is required")
    if threading.active_count() != 1:
        raise ValueError("supervisor must be launched from a single-threaded process")
    group = verify_cgroup(cgroup, memory_bytes=memory_bytes, max_tasks=max_tasks,
                          cpu_quota_us=cpu_quota_us) if cgroup else None
    if sys.platform == "darwin":
        # Darwin advertises RLIMIT_AS but refuses finite values. Never launch a
        # worker with a missing memory boundary.
        raise RuntimeError("finite RLIMIT_AS is unavailable on macOS; run supervised collection on Linux")

    def child_limits():
        # CLI is single-threaded. Do not call this launcher from multithreaded
        # application servers: preexec_fn is intentionally limited to this CLI.
        resource.setrlimit(resource.RLIMIT_AS, (memory_bytes, memory_bytes))
        resource.setrlimit(resource.RLIMIT_FSIZE, (file_bytes, file_bytes))
        resource.setrlimit(resource.RLIMIT_NOFILE, (open_files, open_files))
        resource.setrlimit(resource.RLIMIT_CPU, (wall_seconds, wall_seconds))
        if group is not None:
            # Membership is inherited by descendants. A failed join prevents exec.
            (group / "cgroup.procs").write_text(str(os.getpid()))

    with global_slot(root, max_runs=max_runs):
        process = subprocess.Popen(command, start_new_session=True, preexec_fn=child_limits)
        try:
            try:
                return process.wait(timeout=wall_seconds)
            except subprocess.TimeoutExpired:
                return 124
        finally:
            # Kill the whole group even if its leader exited early; otherwise
            # a surviving worker would escape the slot's resource accounting.
            try:
                os.killpg(process.pid, signal.SIGKILL)
            except ProcessLookupError:
                pass
            process.wait()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root")
    parser.add_argument("--max-runs", type=int, default=1)
    parser.add_argument("--wall-seconds", type=int, default=3600)
    parser.add_argument("--memory-bytes", type=int, default=2_147_483_648)
    parser.add_argument("--file-bytes", type=int, default=268_435_456)
    parser.add_argument("--open-files", type=int, default=128)
    parser.add_argument("--cgroup", help="preconfigured shared cgroup for aggregate memory/task limits")
    parser.add_argument("--max-tasks", type=int, default=64)
    parser.add_argument("--cpu-quota-us", type=int, default=100000)
    parser.add_argument("command", nargs=argparse.REMAINDER)
    args = vars(parser.parse_args())
    if args["command"][:1] == ["--"]:
        args["command"] = args["command"][1:]
    raise SystemExit(supervise(**args))


if __name__ == "__main__":
    main()
