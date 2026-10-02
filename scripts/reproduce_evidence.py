"""Regenerate the proposal's exploratory evidence table from public packets.

Each row is either recomputed from files in this repository and compared with
the number stated in the proposal, or marked as having no public
machine-readable source. A mismatch exits with status 1, so `make reproduce`
fails loudly when the text and the data drift apart.
"""
from __future__ import annotations

import argparse
from collections import Counter
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]


def _load(path: str) -> dict:
    return json.loads((ROOT / path).read_text())


def october_replications() -> list[dict]:
    rows = []
    expected = {  # case: stated C target failures out of 6, and A/B all passing
        "openproject-invalid-remaining": 6,
        "paperless-duplicate-consumption": 5,
        "realworld-favorites": 0,
    }
    for case, stated_c_failures in expected.items():
        summary = _load(f"data/e2e-replications-20261001/{case}/summary.json")
        arm = Counter()
        for model_counts in summary["counts"].values():
            for variant, categories in model_counts.items():
                arm.update({(variant, cat): n for cat, n in categories.items()})
        c_fail = arm[("C", "target_only_failure")]
        ab_pass = arm[("A", "pass")] + arm[("B", "pass")]
        rows.append({
            "row": f"October replication, {case}",
            "stated": f"C failed {stated_c_failures}/6; A and B passed 12/12",
            "recomputed": f"C failed {c_fail}/6; A and B passed {ab_pass}/12",
            "status": "reproduced" if (c_fail, ab_pass) == (stated_c_failures, 12) else "mismatch",
            "source": f"data/e2e-replications-20261001/{case}/summary.json",
        })
    return rows


def acceptance_criteria() -> list[dict]:
    data = _load("data/criteria-expansion/results-20260921.json")
    c_target = next(r for r in data["by_arm"] if r["variant"] == "C" and r["is_target"])
    gens = data["generations"]
    total = sum(gens.values())
    rows = [{
        "row": "Acceptance criteria, target rule in arm C",
        "stated": "absent in 47 of 72; 25 unresolved",
        "recomputed": f"absent in {c_target['absent']} of {c_target['planned']}; {c_target['unresolved']} unresolved",
        "status": "reproduced" if (c_target["absent"], c_target["planned"], c_target["unresolved"]) == (47, 72, 25) else "mismatch",
        "source": "data/criteria-expansion/results-20260921.json (by_arm)",
    }, {
        "row": "Acceptance criteria, generations",
        "stated": "216 generations, 212 structurally valid",
        "recomputed": f"{total} generations, {gens.get('valid', 0)} structurally valid",
        "status": "reproduced" if (total, gens.get("valid")) == (216, 212) else "mismatch",
        "source": "data/criteria-expansion/results-20260921.json (generations)",
    }]
    return rows


def decontamination_successors() -> list[dict]:
    accounting = _load("docs/research/2026-10-01-e2e-accounting.json")
    totals, pairs = Counter(), 0
    for path, packet in accounting["paired_packets"].items():
        if "e2e-decontamination-20260929" in path:
            totals.update(packet["comparisons"])
            pairs += packet["pairs"]
    stated = (6, 8, 4, 18)
    got = (totals["improved"], totals["equal"], totals["unknown"], pairs)
    return [{
        "row": "Excerpt successors of three historical requirements",
        "stated": "6 improvements, 8 ties, 4 unknown in 18 pairs",
        "recomputed": f"{got[0]} improvements, {got[1]} ties, {got[2]} unknown in {got[3]} pairs",
        "status": "reproduced" if got == stated else "mismatch",
        "source": "docs/research/2026-10-01-e2e-accounting.json (paired_packets)",
    }]


NO_PUBLIC_SOURCE = [
    ("Kanboard subtasks, 18 journeys (A 6/6, B 6/6 pass; C 6/6 fail)",
     "no public results file found; only the arm texts are public (data/e2e-kanboard-close)"),
    ("Prospective E2E block, 11 obligations (7 with a C failure)",
     "stated in the evidence matrix document; no machine-readable summary found"),
    ("Historical old/new closure, 60 pairs (11 / 44 / 5)",
     "the original 48 comparisons were found in documents only, not in a data file"),
    ("Severity pairs, 34 A/C comparisons (14 / 11 / 1 / 8)",
     "no public results file found for this cohort"),
    ("Constructed demonstration, complete 9/9 versus deleted 6/9",
     "reported in docs/research; no public results file found"),
]


def build() -> list[dict]:
    rows = october_replications() + acceptance_criteria() + decontamination_successors()
    rows += [{"row": row, "stated": "", "recomputed": "", "status": "no_public_source_found", "source": why}
             for row, why in NO_PUBLIC_SOURCE]
    return rows


def render(rows: list[dict]) -> str:
    lines = ["| Evidence row | Stated | Recomputed | Status | Source |", "| --- | --- | --- | --- | --- |"]
    lines += [f"| {r['row']} | {r['stated']} | {r['recomputed']} | {r['status']} | {r['source']} |" for r in rows]
    return "\n".join(lines) + "\n"


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--out", type=Path, help="write the markdown table here")
    args = parser.parse_args(argv)
    rows = build()
    table = render(rows)
    if args.out:
        args.out.write_text(table)
    print(table)
    counts = Counter(r["status"] for r in rows)
    print(dict(counts))
    return 1 if counts["mismatch"] else 0


if __name__ == "__main__":
    sys.exit(main())
