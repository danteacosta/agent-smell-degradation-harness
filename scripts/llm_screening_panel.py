"""LLM-consensus screening of requirement candidates (reviewer stand-in).

The advisor-approved interim protocol replaces the two human screeners with a
panel of two language models; a third model breaks ties. The panel never sees
the assistant pre-screen, any pilot status or any outcome. Before candidates
are screened, every panel model must reproduce the expected decision on six
authored controls (three admissible rules, three non-rules); a mismatch stops
the run.

Modes:
  prepare   freeze controls, blinded candidate prompts and the panel config
  run       call the panel once per prompt (no retry), then the tiebreaker on
            disagreements, and write consensus decisions
"""
from __future__ import annotations

import argparse
from collections import Counter
import json
from pathlib import Path
import random
import re
import sys

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts.test_anchor_experiment import inventory, put, sha256_file  # noqa: E402

SCHEMA = "llm-screening-panel/v1"
SEED = 2026100204
SCREENING = ROOT / "data/requirement-sampling/screening-20261002.json"
PILOT_CANDIDATES = {"rc-f7aa63a16f88", "rc-29dd3b4e767b", "rc-13e3558f8cbe"}
REASONS = ("admit", "operations_or_configuration", "not_web_interface",
           "no_rule_change", "no_single_testable_rule", "needs_multiple_systems")

INSTRUCTIONS = f"""You screen candidate requirements for a software engineering experiment.

Each candidate is a change to an open-source project's user documentation: sentences that
were removed (-) and added (+). Decide whether the change contains a behavioral rule that
meets ALL three criteria:

1. A user can observe it in the product's WEB interface. Not installation, server or
   authentication configuration, command-line tools, APIs only, mobile-only or desktop-only
   features, and not setups that need several servers.
2. It can be stated as ONE testable obligation, with one observation that passes and one
   that fails.
3. A small self-contained web page imitating that screen could exercise it, without the
   whole product.

Answer with a single JSON object and nothing else:
{{"decision": "admit" or "exclude",
  "reason": one of {list(REASONS)},
  "target_rule": the rule as one sentence (null if excluded),
  "pass_observation": what a user sees when the rule holds (null if excluded),
  "fail_observation": what a user sees when it is violated (null if excluded),
  "numeric": true if the rule fixes a number, threshold, sum or limit,
  "derived_state": true if the rule changes the state of an entity other than the one the user acts on,
  "probe_question": a neutral question about this behavior that does NOT state the rule (null if excluded)}}
Use "admit" as the reason exactly when the decision is admit."""

CONTROLS = [
    {"id": "ctl-pos-kanboard", "expected": "admit", "project": "kanboard", "file": "user/tasks.md",
     "removed": [], "added": ["When you close a task, all its subtasks that are not done are automatically marked as done."]},
    {"id": "ctl-pos-openproject", "expected": "admit", "project": "openproject", "file": "user-guide/progress.md",
     "removed": [], "added": ["A Remaining work value greater than Work cannot be saved; the form shows an error."]},
    {"id": "ctl-pos-shopping", "expected": "admit", "project": "recipes", "file": "usage/shopping-list.md",
     "removed": [], "added": ["Checking an item moves it to the bottom of the shopping list under Done."]},
    {"id": "ctl-neg-install", "expected": "exclude", "project": "tracker", "file": "admin/requirements.md",
     "removed": ["PostgreSQL 13 or newer is required."], "added": ["PostgreSQL 15 or newer is required."]},
    {"id": "ctl-neg-format", "expected": "exclude", "project": "wiki", "file": "user/editor.md",
     "removed": ["Click Save to keep your changes ."], "added": ["Click **Save** to keep your changes."]},
    {"id": "ctl-neg-cli", "expected": "exclude", "project": "photos", "file": "features/cli.md",
     "removed": [], "added": ["The upload command accepts --album to add uploaded files to an album."]},
]


def candidate_prompt(item: dict) -> str:
    lines = [f"Project: {item['project']}", f"File: {item['file']}"]
    lines += [f"- {s}" for s in item["removed"]] + [f"+ {s}" for s in item["added"]]
    return INSTRUCTIONS + "\n\nCandidate:\n" + "\n".join(lines)


def parse_vote(raw: str) -> dict:
    match = re.search(r"\{.*\}", raw, re.S)
    if not match:
        raise ValueError("no JSON object in response")
    vote = json.loads(match.group(0))
    if vote.get("decision") not in ("admit", "exclude") or vote.get("reason") not in REASONS:
        raise ValueError("decision or reason outside the allowed values")
    if (vote["decision"] == "admit") != (vote["reason"] == "admit"):
        raise ValueError("reason must be 'admit' exactly when the decision is admit")
    if vote["decision"] == "admit" and not all(isinstance(vote.get(k), str) and vote[k].strip()
                                                for k in ("target_rule", "pass_observation",
                                                          "fail_observation", "probe_question")):
        raise ValueError("an admitted candidate needs rule, observations and probe question")
    return vote


def cohen_kappa(a: list[str], b: list[str]) -> float | None:
    if not a:
        return None
    labels = sorted(set(a) | set(b))
    observed = sum(x == y for x, y in zip(a, b)) / len(a)
    expected = sum((a.count(l) / len(a)) * (b.count(l) / len(b)) for l in labels)
    return None if expected == 1 else (observed - expected) / (1 - expected)


def prepare(out: Path, models: list[str], tiebreaker: str, executable: Path,
            screening_path: Path | None = None) -> dict:
    screening_path = screening_path or SCREENING
    if out.exists():
        raise FileExistsError("fresh output directory required")
    screening = json.loads(screening_path.read_text())
    blinded = [{k: c[k] for k in ("candidate_id", "project", "file", "removed", "added")}
               for c in screening["candidates"]]
    order = blinded[:]
    random.Random(SEED).shuffle(order)
    out.mkdir(mode=0o700, parents=True)
    for control in CONTROLS:
        put(out / "frozen/prompts" / f"{control['id']}.txt", candidate_prompt(control))
    for item in order:
        put(out / "frozen/prompts" / f"{item['candidate_id']}.txt", candidate_prompt(item))
    manifest = {
        "schema_version": SCHEMA, "seed": SEED, "models": models, "tiebreaker": tiebreaker,
        "executable": str(executable), "screening_sha256": sha256_file(screening_path),
        "screening_file": str(screening_path.relative_to(ROOT) if screening_path.is_relative_to(ROOT) else screening_path),
        "script_sha256": sha256_file(Path(__file__)), "controls": CONTROLS,
        "candidates": order, "retry_policy": "no_retry_no_repair",
        "blinding": "panel sees project, file and changed sentences only; no pre-screen, pilot status or outcome",
    }
    put(out / "frozen/manifest.json", manifest)
    put(out / "frozen/receipt.json", {"files": inventory(out / "frozen")})
    return {"controls": len(CONTROLS), "candidates": len(order), "models": models, "tiebreaker": tiebreaker}


def _verify(out: Path) -> dict:
    receipt = json.loads((out / "frozen/receipt.json").read_text())["files"]
    if {k: v for k, v in inventory(out / "frozen").items() if k != "receipt.json"} != receipt:
        raise ValueError("frozen packet drift")
    return json.loads((out / "frozen/manifest.json").read_text())


def _call(out: Path, provider_factory, model: str, item_id: str) -> dict:
    directory = out / "calls" / model / item_id
    put(directory / "attempt.json", {"model": model, "item": item_id})
    prompt = (out / "frozen/prompts" / f"{item_id}.txt").read_text()
    try:
        from agents.providers import ProviderRequest
        raw = provider_factory(model, directory / "capture").complete(
            ProviderRequest(prompt, {}, "opaque", "screening"))
    except Exception as error:  # an outcome, never retried
        result = {"status": "call_failed", "error_type": type(error).__name__}
    else:
        put(directory / "response.txt", raw)
        try:
            result = {"status": "ok", "vote": parse_vote(raw)}
        except (ValueError, json.JSONDecodeError) as error:
            result = {"status": "invalid", "error": str(error)[:300]}
    put(directory / "result.json", result)
    return result


def run(out: Path, provider_factory=None) -> dict:
    manifest = _verify(out)
    if (out / "run-started.json").exists():
        raise FileExistsError("no resume or retry")
    put(out / "run-started.json", {"frozen_receipt_sha256": sha256_file(out / "frozen/receipt.json")})
    if provider_factory is None:
        from agents.codex_cli import CodexCLIProvider
        provider_factory = lambda model, evidence: CodexCLIProvider(  # noqa: E731
            executable=manifest["executable"], model=model, timeout_seconds=240,
            evidence_directory=evidence)
    models, tiebreaker = manifest["models"], manifest["tiebreaker"]

    control_rows = []
    for control in manifest["controls"]:
        votes = {m: _call(out, provider_factory, m, control["id"]) for m in [*models, tiebreaker]}
        decisions = {m: v.get("vote", {}).get("decision") for m, v in votes.items()}
        control_rows.append({"id": control["id"], "expected": control["expected"], "decisions": decisions})
    qualified = all(set(r["decisions"].values()) == {r["expected"]} for r in control_rows)
    put(out / "controls.json", {"qualified": qualified, "rows": control_rows})
    if not qualified:
        put(out / "results.json", {"schema_version": SCHEMA + "-results", "status": "stopped_controls_failed",
                                   "controls": control_rows})
        return {"status": "stopped_controls_failed", "controls": control_rows}

    rows = []
    for item in manifest["candidates"]:
        cid = item["candidate_id"]
        votes = {m: _call(out, provider_factory, m, cid) for m in models}
        decisions = [votes[m].get("vote", {}).get("decision") for m in models]
        row = {"candidate_id": cid, "project": item["project"], "votes": votes}
        if None not in decisions and len(set(decisions)) == 1:
            row["consensus"], row["route"] = decisions[0], "agreement"
        else:
            tie = _call(out, provider_factory, tiebreaker, cid)
            row["votes"][tiebreaker] = tie
            row["consensus"] = tie.get("vote", {}).get("decision") or "unresolved"
            row["route"] = "tiebreaker"
        if row["consensus"] == "admit" and cid in PILOT_CANDIDATES:
            row["consensus"], row["route"] = "exclude", "pilot_case_mechanical"
        admitting = [votes[m]["vote"] for m in [*models, tiebreaker]
                     if m in row["votes"] and row["votes"][m].get("vote", {}).get("decision") == "admit"]
        if row["consensus"] == "admit" and admitting:
            first = admitting[0]
            row["target_rule"] = first["target_rule"]
            row["pass_observation"], row["fail_observation"] = first["pass_observation"], first["fail_observation"]
            row["probe_question"] = first["probe_question"]
            row["numeric"] = sum(bool(v.get("numeric")) for v in admitting) * 2 > len(admitting)
            row["derived_state"] = sum(bool(v.get("derived_state")) for v in admitting) * 2 > len(admitting)
        rows.append(row)
        print(json.dumps({"phase": "screening", "done": len(rows), "of": len(manifest["candidates"]),
                          "consensus": row["consensus"]}), flush=True)

    both = [r for r in rows if all(r["votes"][m].get("vote") for m in models)]
    summary = {
        "candidates": len(rows),
        "consensus": dict(Counter(r["consensus"] for r in rows)),
        "routes": dict(Counter(r["route"] for r in rows)),
        "admitted_by_project": dict(Counter(r["project"] for r in rows if r["consensus"] == "admit")),
        "primary_kappa": cohen_kappa([r["votes"][models[0]]["vote"]["decision"] for r in both],
                                     [r["votes"][models[1]]["vote"]["decision"] for r in both]),
        "primary_pairs_with_two_valid_votes": len(both),
    }
    put(out / "results.json", {"schema_version": SCHEMA + "-results", "status": "complete",
                               "controls": control_rows, "summary": summary, "rows": rows})
    put(out / "receipt.json", {"files": inventory(out)})
    return summary


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    sub = parser.add_subparsers(dest="mode", required=True)
    p = sub.add_parser("prepare")
    p.add_argument("--out", type=Path, required=True)
    p.add_argument("--model", action="append", required=True, help="primary panel model; pass twice")
    p.add_argument("--tiebreaker", required=True)
    p.add_argument("--executable", type=Path, default=Path("/opt/homebrew/bin/codex"))
    p.add_argument("--screening", type=Path, help="screening sample (default: round 1)")
    sub.add_parser("run").add_argument("--out", type=Path, required=True)
    args = parser.parse_args(argv)
    if args.mode == "prepare":
        if len(args.model) != 2 or args.tiebreaker in args.model:
            parser.error("two distinct primary models and a different tiebreaker are required")
        result = prepare(args.out, args.model, args.tiebreaker, args.executable,
                         args.screening.resolve() if args.screening else None)
    else:
        result = run(args.out)
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
