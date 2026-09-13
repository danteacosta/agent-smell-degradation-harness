import subprocess
import sys
import time
import pytest

from eval.collection_limits import global_slot, supervise


def test_global_slots_cover_distinct_processes_and_preserve_policy(tmp_path):
    root = tmp_path / "global"
    with global_slot(root):
        command = [sys.executable, "-c", "from eval.collection_limits import global_slot; "
                   "import sys; c=global_slot(sys.argv[1]); c.__enter__()", str(root)]
        child = subprocess.run(command, capture_output=True, timeout=5)
        assert child.returncode != 0
        assert b"capacity exhausted" in child.stderr
    with global_slot(root):
        pass
    with pytest.raises(ValueError, match="policy mismatch"):
        with global_slot(root, max_runs=2):
            pass


def test_wall_deadline_terminates_worker_and_releases_global_slot(tmp_path):
    started = time.monotonic()
    assert supervise([sys.executable, "-c", "import time; time.sleep(60)"],
                     root=tmp_path / "global", wall_seconds=1) == 124
    assert time.monotonic() - started < 5
    with global_slot(tmp_path / "global"):
        pass


def test_resource_limits_are_installed_before_child_code(tmp_path):
    script = "import resource; assert resource.getrlimit(resource.RLIMIT_AS)==(268435456,268435456); assert resource.getrlimit(resource.RLIMIT_NOFILE)==(64,64); assert resource.getrlimit(resource.RLIMIT_FSIZE)==(4096,4096)"
    assert supervise([sys.executable, "-c", script], root=tmp_path / "global",
                     memory_bytes=268435456, open_files=64, file_bytes=4096) == 0


def test_file_growth_is_rejected_by_kernel(tmp_path):
    output = tmp_path / "oversize"
    script = "import sys; f=open(sys.argv[1],'wb'); f.write(b'x'*8192); f.flush()"
    assert supervise([sys.executable, "-c", script, str(output)],
                     root=tmp_path / "global", file_bytes=4096) != 0
    assert output.stat().st_size <= 4096


def test_symlink_global_root_is_rejected(tmp_path):
    target = tmp_path / "target"
    target.mkdir(mode=0o700)
    alias = tmp_path / "alias"
    alias.symlink_to(target, target_is_directory=True)
    with pytest.raises(OSError):
        with global_slot(alias):
            pass


def test_unqualified_cgroup_blocks_before_child_start(tmp_path):
    output = tmp_path / "started"
    with pytest.raises(ValueError, match="delegated cgroup"):
        supervise([sys.executable, "-c", f"open({str(output)!r},'w').close()"],
                  root=tmp_path / "global", cgroup=tmp_path / "fake")
    assert not output.exists()


def test_background_worker_cannot_outlive_completed_supervised_command(tmp_path):
    output = tmp_path / "escaped"
    child = f"import time; time.sleep(1); open({str(output)!r},'w').close()"
    parent = f"import subprocess,sys; subprocess.Popen([sys.executable,'-c',{child!r}])"
    assert supervise([sys.executable, "-c", parent], root=tmp_path / "global") == 0
    time.sleep(1.2)
    assert not output.exists()
