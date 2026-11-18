"""Offline audit of a frozen duplicate-coding selection manifest.

Checks that an ``annotation-selection/v1`` manifest (see
``label_plane.annotation_protocol``) is internally consistent and reproducible
from the item-id list and seed alone, i.e. that the selection could not have
used labels. It does NOT set ``duplicate_subset_selected_outcome_blind`` in any
plan, approve anything, or prove that the item ids are free of outcome
information beyond a token heuristic. Setting the flag stays a human decision.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from hashlib import sha256
from pathlib import Path
from typing import Any, Iterable, Mapping

from label_plane.annotation_protocol import select_duplicate_subset

_OUTCOME_TOKENS = re.compile(r"(clean|defect|degrad|label|oracle|loss|lost|positive|negative)", re.I)


def audit_selection(manifest: Mapping[str, Any], item_ids: Iterable[str]) -> dict[str, list[str]]:
    errors: list[str] = []
    warnings: list[str] = []
    ids = sorted({str(i) for i in item_ids if str(i)})
    if manifest.get("schema_version") != "annotation-selection/v1":
        errors.append("unsupported schema_version")
    if manifest.get("selection_method") != "seeded_item_id_sampling_before_labels":
        errors.append("selection_method is not seeded_item_id_sampling_before_labels")
    fraction, seed = manifest.get("duplicate_subset_fraction"), manifest.get("duplicate_subset_seed")
    if not isinstance(seed, int) or isinstance(seed, bool):
        errors.append("duplicate_subset_seed must be an integer")
    if fraction != 0.2:
        errors.append("duplicate_subset_fraction must be 0.2")
    if manifest.get("item_count") != len(ids):
        errors.append("item_count does not match supplied item ids")
    chosen = manifest.get("duplicate_item_ids")
    if not isinstance(chosen, list):
        errors.append("duplicate_item_ids must be a list")
        chosen = []
    if len(set(chosen)) != len(chosen):
        errors.append("duplicate_item_ids contains repeats")
    if not set(chosen) <= set(ids):
        errors.append("duplicate_item_ids contains ids outside the item list")
    if manifest.get("duplicate_item_count") != len(chosen):
        errors.append("duplicate_item_count does not match duplicate_item_ids")
    if not errors:
        if list(select_duplicate_subset(ids, fraction=0.2, seed=seed)) != sorted(chosen):
            errors.append("selection is not reproducible from item ids and seed")
    body = {k: v for k, v in manifest.items() if k != "selection_sha256"}
    digest = sha256(
        json.dumps(body, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")
    ).hexdigest()
    if manifest.get("selection_sha256") != digest:
        errors.append("selection_sha256 does not match manifest content")
    flagged = [i for i in ids if _OUTCOME_TOKENS.search(i)]
    if flagged:
        warnings.append(f"{len(flagged)} item ids contain outcome-like tokens (e.g. {flagged[0]!r}); confirm ids are opaque")
    return {"errors": errors, "warnings": warnings}


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    p.add_argument("--manifest", type=Path, required=True)
    p.add_argument("--item-ids", type=Path, required=True, help="JSON list of item ids")
    args = p.parse_args(argv)
    report = audit_selection(
        json.loads(args.manifest.read_text(encoding="utf-8")),
        json.loads(args.item_ids.read_text(encoding="utf-8")),
    )
    print(json.dumps(report, indent=2))
    return 1 if report["errors"] else 0


if __name__ == "__main__":
    sys.exit(main())
