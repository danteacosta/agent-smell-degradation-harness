"""Confirmatory H1a selection: frozen order, substitution ledger and stop rule.

PROPOSAL. Nothing here selects a requirement or calls a model. The procedure
becomes binding only after approval and registration.

  order   write, for every project with provisionally admitted candidates, the
          complete processing order: all reserve candidates (registered frame,
          2025-01..2026-09) in a seeded random order, then all 2024-window
          candidates in a seeded random order. Unresolved panel rows are not
          admitted and are left out.
  walk    replay the ledger of review decisions against the frozen order and
          report, per project, the selected requirements or the insufficiency.

Rules (see docs/research/2026-10-05-confirmatory-selection-proposal.md):
  - each project is processed strictly in order; a candidate is decided only
    after every earlier candidate of its project has been decided;
  - a candidate is either qualified or excluded with one ALLOWED reason; every
    decision is a ledger event and is never edited or deleted;
  - a project stops when TARGET candidates are qualified; later candidates are
    not examined;
  - if a project's list is exhausted with fewer than TARGET qualified, the
    project is insufficient and the whole procedure stops with that record:
    no other project, window or design change fills the gap automatically.
"""
from __future__ import annotations

import argparse
from collections import Counter
import hashlib
import json
from pathlib import Path
import random
import sys

ROOT = Path(__file__).resolve().parents[1]
OPTIONS = (  # processing priority: reserve first, then the 2024 window
    ("reserve", ROOT / "data/llm-screening-confirmatory-reserve-20261005/results.json",
     ROOT / "data/requirement-sampling/screening-confirmatory-reserve-20261005.json"),
    ("w2024", ROOT / "data/llm-screening-confirmatory-w2024-20261005/results.json",
     ROOT / "data/requirement-sampling/screening-confirmatory-w2024-20261005.json"),
)
SEED = 2026100506
TARGET = 5
OUT_DIR = ROOT / "data/confirmatory-selection"
ORDER = OUT_DIR / "selection-order-proposal.json"
LEDGER = OUT_DIR / "selection-ledger.jsonl"

ALLOWED_REASONS = {
    "duplicate_semantic": "states the same rule as an earlier-ranked candidate (name it in duplicate_of)",
    "overlaps_exploratory": "states the same rule as one of the 46 exploratory cases, the 17 historical "
                            "cases or a pilot case (name it in duplicate_of)",
    "mapping_invalid": "the panel's target rule is not what the documentation change states",
    "not_constructible": "no self-contained page can exercise the rule with one passing and one failing observation",
    "oracle_not_qualified": "the oracle fails its authored qualification controls (correct and incorrect pages)",
    "human_audit_exclude": "the blind human audit (20% sample) excluded it; applies only to audited candidates",
}
ACTIONS = ("qualified", "excluded")


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def build_order() -> dict:
    projects: dict[str, list[dict]] = {}
    for option, results, sample in OPTIONS:
        texts = {c["candidate_id"]: c for c in json.loads(sample.read_text())["candidates"]}
        admitted: dict[str, list[dict]] = {}
        for r in json.loads(results.read_text())["rows"]:
            if r["consensus"] == "admit":
                admitted.setdefault(r["project"], []).append(r)
        for project, rows in admitted.items():
            rows = sorted(rows, key=lambda r: r["candidate_id"])
            random.Random(f"{SEED}:{project}:{option}").shuffle(rows)
            for r in rows:
                c = texts[r["candidate_id"]]
                projects.setdefault(project, []).append({
                    "candidate_id": r["candidate_id"], "option": option, "commit": c["commit"],
                    "date": c["date"], "file": c["file"], "panel_target_rule": r["target_rule"]})
    for rows in projects.values():
        for i, row in enumerate(rows, start=1):
            row["rank"] = i
    return {
        "schema_version": "confirmatory-selection-order/v1", "status": "proposal_not_approved",
        "seed": SEED, "target_per_project": TARGET, "priority": [o for o, _, _ in OPTIONS],
        "shuffle": "per project and option: candidates sorted by id, then random.Random(f'{seed}:{project}:{option}').shuffle",
        "allowed_exclusion_reasons": ALLOWED_REASONS,
        "inputs_sha256": {str(p.relative_to(ROOT)): sha(p) for _, a, b in OPTIONS for p in (a, b)},
        "projects": {p: {"reserve": sum(r["option"] == "reserve" for r in rows),
                         "w2024": sum(r["option"] == "w2024" for r in rows), "order": rows}
                     for p, rows in sorted(projects.items())},
    }


def read_ledger(path: Path) -> list[dict]:
    if not path.exists():
        return []
    return [json.loads(line) for line in path.read_text().splitlines() if line.strip()]


def walk(order: dict, events: list[dict]) -> dict:
    """Replay the ledger; raise on any rule violation, report selection or insufficiency."""
    projects = order["projects"]
    position = {p: 0 for p in projects}
    qualified: dict[str, list[dict]] = {p: [] for p in projects}
    excluded: dict[str, list[dict]] = {p: [] for p in projects}
    for n, e in enumerate(events, start=1):
        if e.get("seq") != n:
            raise ValueError(f"event {n}: seq must be {n} (append-only, no gaps)")
        p = e.get("project")
        if p not in projects:
            raise ValueError(f"event {n}: unknown project {p!r}")
        if len(qualified[p]) >= order["target_per_project"]:
            raise ValueError(f"event {n}: {p} already has {order['target_per_project']} qualified; stop examining")
        rows = projects[p]["order"]
        if position[p] >= len(rows):
            raise ValueError(f"event {n}: {p} order exhausted")
        expected = rows[position[p]]
        if e.get("candidate_id") != expected["candidate_id"] or e.get("rank") != expected["rank"]:
            raise ValueError(f"event {n}: {p} must decide rank {expected['rank']} "
                             f"({expected['candidate_id']}) before any later candidate")
        if e.get("action") not in ACTIONS:
            raise ValueError(f"event {n}: action must be one of {ACTIONS}")
        if not e.get("decided_by") or not e.get("date") or not e.get("evidence"):
            raise ValueError(f"event {n}: decided_by, date and evidence are required")
        if e["action"] == "excluded":
            if e.get("reason") not in order["allowed_exclusion_reasons"]:
                raise ValueError(f"event {n}: reason must be one of {sorted(order['allowed_exclusion_reasons'])}")
            if e["reason"] in ("duplicate_semantic", "overlaps_exploratory") and not e.get("duplicate_of"):
                raise ValueError(f"event {n}: {e['reason']} needs duplicate_of")
            excluded[p].append(e)
        else:
            if e.get("reason"):
                raise ValueError(f"event {n}: a qualified candidate carries no exclusion reason")
            qualified[p].append(e)
        position[p] += 1
    status = {}
    for p, info in projects.items():
        k = len(qualified[p])
        if k >= order["target_per_project"]:
            status[p] = "complete"
        elif position[p] >= len(info["order"]):
            status[p] = "insufficient"
        else:
            status[p] = "in_progress"
    overall = ("stopped_insufficient" if "insufficient" in status.values() else
               "complete" if set(status.values()) == {"complete"} else "in_progress")
    return {
        "status": overall, "project_status": status,
        "selected": {p: [e["candidate_id"] for e in qualified[p]] for p in projects},
        "selected_from_w2024": {p: sum(1 for e in qualified[p]
                                       if projects[p]["order"][e["rank"] - 1]["option"] == "w2024")
                                for p in projects},
        "exclusions": {p: dict(Counter(e["reason"] for e in excluded[p])) for p in projects},
        "examined": position,
        "note": ("stopped_insufficient: at least one project exhausted its list below the target; the "
                 "procedure stops here and any remedy (another project, window or design) is a new, "
                 "recorded decision") if overall == "stopped_insufficient" else None,
    }


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    sub = parser.add_subparsers(dest="mode", required=True)
    sub.add_parser("order")
    w = sub.add_parser("walk")
    w.add_argument("--ledger", type=Path, default=LEDGER)
    args = parser.parse_args(argv)
    if args.mode == "order":
        if ORDER.exists():
            raise FileExistsError(f"{ORDER} exists; the order is written once")
        OUT_DIR.mkdir(parents=True, exist_ok=True)
        doc = build_order()
        ORDER.write_text(json.dumps(doc, indent=2, ensure_ascii=False) + "\n")
        print(json.dumps({p: {k: v for k, v in i.items() if k != "order"} for p, i in doc["projects"].items()},
                         indent=2))
    else:
        order = json.loads(ORDER.read_text())
        print(json.dumps(walk(order, read_ledger(args.ledger)), indent=2))


if __name__ == "__main__":
    sys.exit(main())
