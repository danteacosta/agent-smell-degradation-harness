"""Merge independent panel responses into consensus records."""

from __future__ import annotations

import argparse
import json
import sys
from collections import Counter
from pathlib import Path

REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
if str(REPOSITORY_ROOT) not in sys.path:
    sys.path.insert(0, str(REPOSITORY_ROOT))

from label_plane.llm_panel import (
    build_consensus_batch,
    select_human_audit_subset,
    summarize_panel_agreement,
)


def _assert_private_input(path: Path) -> None:
    try:
        path.resolve().relative_to(REPOSITORY_ROOT.resolve())
    except ValueError:
        return
    raise ValueError(
        f"raw panel responses must stay outside the repository: {path}; use /private/tmp or another private directory"
    )


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--responses", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument("--summary", required=True, type=Path)
    parser.add_argument("--audit-fraction", type=float, default=0.20)
    parser.add_argument("--seed", type=int, default=17)
    parser.add_argument(
        "--judges",
        nargs="+",
        help="configured judge IDs; omit only for the historical kimi/gpt/claude contract",
    )
    parser.add_argument("--consensus-required", type=int, default=2)
    parser.add_argument(
        "--human-labels",
        type=Path,
        help="optional private JSONL of explicitly adjudicated item_id/label rows",
    )
    parser.add_argument(
        "--metadata",
        type=Path,
        help="optional private JSONL joining item IDs to project/intent metadata",
    )
    args = parser.parse_args()
    _assert_private_input(args.responses)
    responses = [
        json.loads(line)
        for line in args.responses.read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]
    human_labels = _load_human_labels(args.human_labels) if args.human_labels else None
    item_metadata = _load_item_metadata(args.metadata) if args.metadata else None
    consensus = build_consensus_batch(
        responses,
        expected_providers=args.judges,
        consensus_required=args.consensus_required,
    )
    audit_ids = select_human_audit_subset(
        (row["item_id"] for row in consensus), fraction=args.audit_fraction, seed=args.seed
    )
    for row in consensus:
        row["human_audit_sample"] = row["item_id"] in audit_ids
    agreement = summarize_panel_agreement(
        consensus,
        annotations=responses,
        human_labels=human_labels,
        item_metadata=item_metadata,
    )
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.summary.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(
        "".join(json.dumps(row, ensure_ascii=False, sort_keys=True) + "\n" for row in consensus),
        encoding="utf-8",
    )
    summary = {
        "schema_version": "requirements-smell-panel-consensus/v1",
        "status": "panel_consensus_pending_human_review",
        "items": len(consensus),
        "status_counts": dict(sorted(Counter(row["status"] for row in consensus).items())),
        "human_review_count": sum(bool(row["human_review_required"]) for row in consensus),
        "human_audit_count": len(audit_ids),
        "human_audit_fraction": args.audit_fraction,
        "human_audit_seed": args.seed,
        "judges": args.judges,
        "consensus_required": args.consensus_required,
        "agreement": agreement,
    }
    args.summary.write_text(json.dumps(summary, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(summary, sort_keys=True))
    return 0


def _load_human_labels(path: Path) -> dict[str, str]:
    _assert_private_input(path)
    labels: dict[str, str] = {}
    for line_number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), start=1):
        if not line.strip():
            continue
        try:
            row = json.loads(line)
        except json.JSONDecodeError as exc:
            raise ValueError(f"invalid human label JSONL at line {line_number}") from exc
        if not isinstance(row, dict):
            raise ValueError(f"human label row {line_number} must be an object")
        if row.get("adjudicated") is not True:
            raise ValueError("human label rows must set adjudicated=true")
        item_id = str(row.get("item_id", "")).strip()
        label = str(row.get("label", "")).strip()
        if not item_id or not label or item_id in labels:
            raise ValueError(f"invalid or duplicate human label at line {line_number}")
        labels[item_id] = label
    if not labels:
        raise ValueError("human labels cannot be empty")
    return labels


def _load_item_metadata(path: Path) -> dict[str, dict[str, object]]:
    _assert_private_input(path)
    metadata: dict[str, dict[str, object]] = {}
    for line_number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), start=1):
        if not line.strip():
            continue
        try:
            row = json.loads(line)
        except json.JSONDecodeError as exc:
            raise ValueError(f"invalid metadata JSONL at line {line_number}") from exc
        if not isinstance(row, dict):
            raise ValueError(f"metadata row {line_number} must be an object")
        item_id = str(row.get("item_id") or row.get("candidate_id") or "").strip()
        if not item_id or item_id in metadata:
            raise ValueError(f"invalid or duplicate item metadata at line {line_number}")
        metadata[item_id] = row
    if not metadata:
        raise ValueError("item metadata cannot be empty")
    return metadata


if __name__ == "__main__":
    raise SystemExit(main())
