"""Single-host ownership and conservative recovery for private run directories."""
from contextlib import contextmanager
from pathlib import Path
import os
import stat


@contextmanager
def own_run(directory: Path, *, resume: bool):
    """Lock the directory inode; never unlink/recreate a lock while holders exist."""
    import fcntl
    # Include existing ancestors too: a preflight may be resumed after an
    # earlier mkdir/flush failure, so existence is not a durability receipt.
    parents_to_sync = list(directory.absolute().parents)
    if not resume:
        directory.parent.mkdir(parents=True, exist_ok=True)
        directory.mkdir(mode=0o700)  # Atomic claim; existing evidence is never reused.
    fd = os.open(directory, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW)
    try:
        info = os.fstat(fd)
        if info.st_uid != os.getuid() or stat.S_IMODE(info.st_mode) & 0o077:
            raise ValueError("run directory must be owned by this user with mode 0700")
        try:
            fcntl.flock(fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError:
            raise ValueError("run directory is already in use") from None
        if any(item.is_symlink() or not item.is_file() for item in directory.iterdir()):
            raise ValueError("run directory contains a symlink or unexpected entry")
        if resume and any((directory / name).exists() for name in (
            "live-started.json", "cost-ledger.jsonl", "raw-evidence.jsonl"
        )):
            raise ValueError("live recovery requires reconciliation; automatic replay is disabled")
        # Persist the path before handing control to the runner. flock alone
        # only excludes writers; all flush failures must prevent entry.
        os.fsync(fd)
        for parent in parents_to_sync:
            parent_fd = os.open(parent, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW)
            try:
                os.fsync(parent_fd)
            finally:
                os.close(parent_fd)
        yield
    finally:
        os.close(fd)
