import os
from pathlib import Path
import subprocess
import sys
import pytest
from eval.run_ownership import own_run


@pytest.mark.parametrize("nested", [False, True])
def test_creation_flushes_path_before_entering_runner(tmp_path, monkeypatch, nested):
    directory = tmp_path / "a" / "b" / "run" if nested else tmp_path / "run"
    flushed = []
    real_fsync = os.fsync

    def record(fd):
        flushed.append(os.fstat(fd).st_ino)
        real_fsync(fd)

    monkeypatch.setattr(os, "fsync", record)
    with own_run(directory, resume=False):
        expected = [directory, *directory.absolute().parents]
        assert flushed == [path.stat().st_ino for path in expected]


@pytest.mark.parametrize("fail_at", [1, 2, 3, 4])
def test_creation_flush_error_blocks_runner_and_releases_lock(tmp_path, monkeypatch, fail_at):
    directory = tmp_path / "a" / "b" / "run"
    real_fsync = os.fsync
    calls = 0

    def fail(fd):
        nonlocal calls
        calls += 1
        if calls == fail_at:
            raise OSError("injected persistence failure")
        real_fsync(fd)

    monkeypatch.setattr(os, "fsync", fail)
    with pytest.raises(OSError, match="persistence failure"):
        with own_run(directory, resume=False):
            pytest.fail("runner must not start after a persistence failure")
    assert directory.is_dir()  # No cleanup that could destroy evidence.
    monkeypatch.setattr(os, "fsync", real_fsync)
    with own_run(directory, resume=True):
        pass  # Failed entry released its descriptor and lock.


def test_preflight_resume_must_retry_persistence_barrier(tmp_path, monkeypatch):
    directory = tmp_path / "run"
    with own_run(directory, resume=False):
        pass

    def fail(fd):
        raise OSError("injected persistence failure")

    monkeypatch.setattr(os, "fsync", fail)
    with pytest.raises(OSError, match="persistence failure"):
        with own_run(directory, resume=True):
            pytest.fail("resume must not bypass persistence")


def test_exclusive_claim_and_lock_released_after_process_death(tmp_path):
    directory = tmp_path / "run"
    with own_run(directory, resume=False):
        child = subprocess.run([sys.executable, "-c",
            "from pathlib import Path; from eval.run_ownership import own_run; "
            "c=own_run(Path(__import__('sys').argv[1]),resume=True); c.__enter__()",
            str(directory)], capture_output=True, timeout=5)
        assert child.returncode != 0
        assert b"already in use" in child.stderr
    child = subprocess.run([sys.executable, "-c",
        "from pathlib import Path; from eval.run_ownership import own_run; import os,sys; "
        "c=own_run(Path(sys.argv[1]),resume=True); c.__enter__(); os._exit(0)",
        str(directory)], capture_output=True, timeout=5)
    assert child.returncode == 0, child.stderr
    with own_run(directory, resume=True):
        pass


@pytest.mark.parametrize("marker", ["live-started.json", "cost-ledger.jsonl", "raw-evidence.jsonl"])
def test_live_or_ambiguous_evidence_never_replayed(tmp_path, marker):
    directory = tmp_path / "run"
    with own_run(directory, resume=False):
        (directory / marker).write_text("preserve")
    with pytest.raises(ValueError, match="reconciliation"):
        with own_run(directory, resume=True):
            pytest.fail("must not call provider")
    assert (directory / marker).read_text() == "preserve"


def test_duplicate_launch_preserves_existing_evidence(tmp_path):
    directory = tmp_path / "run"
    with own_run(directory, resume=False):
        (directory / "checkpoint.json").write_text("keep")
    with pytest.raises(FileExistsError):
        with own_run(directory, resume=False):
            pass
    assert (directory / "checkpoint.json").read_text() == "keep"


@pytest.mark.parametrize("attack", ["directory_symlink", "file_symlink", "public_permissions"])
def test_local_filesystem_attacks_rejected(tmp_path, attack):
    directory = tmp_path / "run"
    directory.mkdir(mode=0o700)
    target = tmp_path / "target"
    target.write_text("untouched")
    if attack == "directory_symlink":
        link = tmp_path / "alias"
        link.symlink_to(directory, target_is_directory=True)
        directory = link
    elif attack == "file_symlink":
        (directory / "report.json").symlink_to(target)
    else:
        directory.chmod(0o755)
    with pytest.raises((ValueError, OSError)):
        with own_run(directory, resume=True):
            pytest.fail("attack accepted")
    assert target.read_text() == "untouched"
