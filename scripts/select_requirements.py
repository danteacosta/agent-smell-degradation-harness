"""Turn screening admissions into the frozen requirement selection.

The pre-registration caps each project at six requirements, drawn with seed
2026100203 when a project has more. This script fixes how that draw consumes
the random generator, and refuses to select until every open question about
the admitted candidates has a recorded decision:

  audit   list admitted candidates that may be the same obligation
          (shared changed sentences, or the same commit and file)
  select  apply mapping decisions and duplicate groups, then draw

Selection order, fixed here and frozen with the script's hash:

1. Units are admitted candidates minus those a decision excludes. Each
   duplicate group keeps one unit: its lexicographically smallest candidate
   id (ids are hashes, so the choice is blind to content and outcomes).
2. Projects are visited in alphabetical order. One random.Random(seed) is
   created once. For a project with more than six units the generator is
   called once as rng.sample(sorted_ids, 6); a project with six or fewer
   units keeps all of them and does not touch the generator.
3. The selection is valid only with at least 30 units from at least eight
   projects; otherwise the result is "blocked" and names what is missing.

Probe outcomes are never an input. A decision file must say it was made
without them.
"""
from __future__ import annotations

import argparse
from collections import defaultdict
import difflib
import hashlib
import itertools
import json
from pathlib import Path
import random
import re
import sys

ROOT = Path(__file__).resolve().parents[1]
SEED = 2026100203
CAP = 6
MIN_UNITS = 30
MIN_PROJECTS = 8
DECISIONS = {"keep_frozen", "use_vote", "exclude"}


def sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def load_frame(paths: list[Path]) -> dict[str, dict]:
    frame = {}
    for path in paths:
        for line in path.read_text().splitlines():
            if line.strip():
                row = json.loads(line)
                frame[row["candidate_id"]] = row
    return frame


def load_admitted(paths: list[Path]) -> dict[str, dict]:
    admitted = {}
    for path in paths:
        data = json.loads(path.read_text())
        if data.get("status") != "complete":
            raise ValueError(f"{path} is not a complete screening run")
        for row in data["rows"]:
            if row["consensus"] == "admit":
                if row["candidate_id"] in admitted:
                    raise ValueError(f"{row['candidate_id']} admitted in two screening runs")
                admitted[row["candidate_id"]] = row
    return admitted


def _norm(sentence: str) -> str:
    return re.sub(r"\W+", " ", sentence.lower()).strip()


def duplicate_candidates(admitted: dict[str, dict], frame: dict[str, dict]) -> list[dict]:
    """Pairs that may be one obligation. A human or the decision file decides."""
    pairs = []
    for a, b in itertools.combinations(sorted(admitted), 2):
        fa, fb = frame[a], frame[b]
        if fa["project"] != fb["project"]:
            continue
        sa = {_norm(s) for s in fa["removed"] + fa["added"] if len(_norm(s)) > 20}
        sb = {_norm(s) for s in fb["removed"] + fb["added"] if len(_norm(s)) > 20}
        shared = sa & sb
        near = sum(1 for x in sa - shared for y in sb - shared
                   if difflib.SequenceMatcher(None, x, y).ratio() > 0.85)
        same_change = fa["commit"] == fb["commit"] and fa["file"] == fb["file"]
        if shared or near or same_change:
            pairs.append({"a": a, "b": b, "project": fa["project"], "shared_sentences": len(shared),
                          "near_identical_sentences": near, "same_commit_and_file": same_change})
    return pairs


def check_decisions(decisions: dict, admitted: dict[str, dict], unresolved: list[str]) -> list[str]:
    problems = []
    if decisions.get("probe_outcomes_consulted") is not False:
        problems.append("decision file must state probe_outcomes_consulted: false")
    entries = decisions.get("mappings", {})
    for cid in unresolved:
        if cid not in entries:
            problems.append(f"no mapping decision for {cid}")
    for cid, entry in entries.items():
        if cid not in admitted:
            problems.append(f"mapping decision for {cid}, which was not admitted")
            continue
        if entry.get("decision") not in DECISIONS:
            problems.append(f"{cid}: decision must be one of {sorted(DECISIONS)}")
        if entry.get("decision") == "use_vote":
            vote = admitted[cid]["votes"].get(entry.get("vote_model"), {}).get("vote") or {}
            if vote.get("decision") != "admit":
                problems.append(f"{cid}: use_vote names a model that did not vote admit")
        if not entry.get("reason"):
            problems.append(f"{cid}: a reason is required")
    seen = set()
    for group in decisions.get("duplicate_groups", []):
        ids = group.get("candidates", [])
        if len(ids) < 2 or any(c not in admitted for c in ids):
            problems.append(f"duplicate group {ids} must list two or more admitted candidates")
        if seen & set(ids):
            problems.append(f"candidate in two duplicate groups: {sorted(seen & set(ids))}")
        seen |= set(ids)
    return problems


def units(admitted: dict[str, dict], decisions: dict) -> dict[str, dict]:
    entries = decisions.get("mappings", {})
    kept = {cid: row for cid, row in admitted.items() if entries.get(cid, {}).get("decision") != "exclude"}
    for group in decisions.get("duplicate_groups", []):
        members = sorted(c for c in group["candidates"] if c in kept)
        for cid in members[1:]:
            kept.pop(cid)
    result = {}
    for cid, row in kept.items():
        entry = entries.get(cid, {"decision": "keep_frozen"})
        if entry["decision"] == "use_vote":
            vote = row["votes"][entry["vote_model"]]["vote"]
            rule = {k: vote[k] for k in ("target_rule", "pass_observation", "fail_observation", "probe_question")}
            source = f"vote:{entry['vote_model']}"
        else:
            rule = {k: row[k] for k in ("target_rule", "pass_observation", "fail_observation", "probe_question")}
            source = "frozen_first_admitting_vote"
        result[cid] = {"candidate_id": cid, "project": row["project"], "rule_source": source, **rule}
    return result


def draw(unit_rows: dict[str, dict], seed: int = SEED, cap: int = CAP) -> dict[str, list[str]]:
    by_project = defaultdict(list)
    for cid, row in unit_rows.items():
        by_project[row["project"]].append(cid)
    rng = random.Random(seed)
    chosen = {}
    for project in sorted(by_project):
        ids = sorted(by_project[project])
        chosen[project] = sorted(rng.sample(ids, cap)) if len(ids) > cap else ids
    return chosen


def select(screening: list[Path], frame_paths: list[Path], decisions_path: Path,
           unresolved: list[str], preview: bool = False) -> dict:
    admitted = load_admitted(screening)
    load_frame(frame_paths)  # every admitted id must come from a frame we hash
    decisions = json.loads(decisions_path.read_text())
    problems = check_decisions(decisions, admitted, unresolved)
    if decisions.get("status") != "approved" and not preview:
        problems.append("decision file status is not 'approved' (use --preview for a non-binding run)")
    inputs = {str(p.relative_to(ROOT) if p.is_relative_to(ROOT) else p): sha256_file(p)
              for p in [*screening, *frame_paths, decisions_path, Path(__file__)]}
    if problems:
        return {"status": "blocked", "problems": problems, "inputs_sha256": inputs}
    unit_rows = units(admitted, decisions)
    chosen = draw(unit_rows)
    n_units = sum(len(v) for v in chosen.values())
    shortfall = []
    if len(chosen) < MIN_PROJECTS:
        shortfall.append(f"{len(chosen)} projects, at least {MIN_PROJECTS} required")
    if n_units < MIN_UNITS:
        shortfall.append(f"{n_units} requirements, at least {MIN_UNITS} required")
    status = "preview_not_admission" if preview else ("blocked" if shortfall else "selected")
    return {"schema_version": "requirement-selection/v1", "status": status, "seed": SEED, "cap_per_project": CAP,
            "shortfall": shortfall, "units_before_cap": len(unit_rows),
            "per_project_before_cap": {p: sum(1 for r in unit_rows.values() if r["project"] == p)
                                       for p in sorted({r["project"] for r in unit_rows.values()})},
            "selected": {p: [unit_rows[c] for c in ids] for p, ids in chosen.items()},
            "selected_count": n_units, "inputs_sha256": inputs}


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    sub = parser.add_subparsers(dest="mode", required=True)
    for name in ("audit", "select"):
        p = sub.add_parser(name)
        p.add_argument("--screening", type=Path, action="append", required=True)
        p.add_argument("--frame", type=Path, action="append", required=True)
    s = sub.choices["select"]
    s.add_argument("--decisions", type=Path, required=True)
    s.add_argument("--mapping-audit", type=Path, action="append", default=[])
    s.add_argument("--out", type=Path)
    s.add_argument("--preview", action="store_true")
    args = parser.parse_args(argv)
    if args.mode == "audit":
        result = duplicate_candidates(load_admitted(args.screening), load_frame(args.frame))
    else:
        unresolved = [c for path in args.mapping_audit
                      for c in json.loads(path.read_text()).get("unresolved_target_selection", [])]
        result = select(args.screening, args.frame, args.decisions, unresolved, args.preview)
        if args.out:
            args.out.write_text(json.dumps(result, indent=2, ensure_ascii=False) + "\n")
    print(json.dumps(result, indent=2, ensure_ascii=False))
    if args.mode == "select" and result["status"] == "blocked":
        sys.exit(2)


if __name__ == "__main__":
    main()
