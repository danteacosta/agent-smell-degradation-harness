"""Prepare a metadata-audited candidate pool from the Unified Dataset."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

from eval.unified_corpus import (
    UNIFIED_DATASET_ID,
    UNIFIED_DATASET_VERSION,
    load_unified_rows,
    select_candidate_pool,
    write_candidate_pool,
    write_source_manifest,
    write_selection_manifest,
)


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--csv", required=True, type=Path)
    parser.add_argument("--archive", required=True, type=Path)
    parser.add_argument("--candidate-output", required=True, type=Path)
    parser.add_argument("--selection-manifest", required=True, type=Path)
    parser.add_argument("--source-manifest", required=True, type=Path)
    parser.add_argument("--source-member", required=True)
    parser.add_argument("--seed", type=int, default=17)
    parser.add_argument("--per-kind", type=int, default=20)
    parser.add_argument("--train-per-kind", type=int, default=0)
    parser.add_argument("--calibration-per-kind", type=int, default=0)
    args = parser.parse_args()
    rows = load_unified_rows(args.csv)
    split_quotas = {
        "train": args.train_per_kind,
        "calibration": args.calibration_per_kind,
        "test": args.per_kind,
    }
    candidates, project_splits = select_candidate_pool(
        rows,
        per_kind=args.per_kind,
        seed=args.seed,
        split_quotas=split_quotas,
    )
    write_candidate_pool(args.candidate_output, candidates, project_splits)
    write_source_manifest(
        args.source_manifest,
        rows,
        source_archive_sha256=_sha256(args.archive),
        source_archive_size_bytes=args.archive.stat().st_size,
        source_member=args.source_member,
        source_member_sha256=_sha256(args.csv),
        source_member_size_bytes=args.csv.stat().st_size,
    )
    write_selection_manifest(
        args.selection_manifest,
        candidates,
        project_splits,
        source_archive_sha256=_sha256(args.archive),
        source_member=args.source_member,
        source_member_sha256=_sha256(args.csv),
        seed=args.seed,
        per_kind=args.per_kind,
        split_quotas=split_quotas,
    )
    print(json.dumps({
        "source_dataset": f"{UNIFIED_DATASET_ID}:{UNIFIED_DATASET_VERSION}",
        "source_rows": len(rows),
        "candidate_rows": len(candidates),
        "candidate_output": str(args.candidate_output),
        "selection_manifest": str(args.selection_manifest),
        "projects": len(project_splits),
        "split_quotas": split_quotas,
    }, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
