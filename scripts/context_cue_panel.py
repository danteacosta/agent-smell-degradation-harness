"""Blind LLM-panel coding of the pre-registered covariate context_cue.

context_cue = 1 if the omitted rule, or an observable consequence of it, can
be inferred from the text the coding model receives in arm C (other sentences
of the requirement, page labels, field or API names); otherwise 0.

The coders see only (a) the omitted span, computed mechanically as A minus C,
and (b) the exact arm-C prompt. They never see generated code, oracle results,
probe answers or which model was used. A "yes" must quote the arm-C text; a
quote that is not a literal substring of the prompt makes the vote invalid.

Same governance as the screening panel: two primary models, a third breaks
ties, every model must first reproduce five authored controls (any mismatch
stops the run), calls happen once without retry, and Cohen's kappa of the two
primary models is reported.

  prepare  freeze prompts for every selected case into a fresh private packet
  run      call the panel and write results.json
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

from scripts.abc_case import Case  # noqa: E402
from scripts.llm_screening_panel import cohen_kappa  # noqa: E402
from scripts.test_anchor_experiment import inventory, put, sha256_file  # noqa: E402

SCHEMA = "context-cue-panel/v2"
SEED = 2026100402
CASES_DIR = ROOT / "data/abc-cases"

INSTRUCTIONS = """You code one property of a software experiment. A coding model received the TEXT below and
had to implement a web page. One rule (the OMITTED RULE) was removed from the requirement before the
model saw it.

Question: can the omitted rule, or an observable consequence of it, be inferred from the TEXT alone?
Count other sentences of the requirement, labels or text on the page, element ids, field names, data
values and API names in the TEXT. Do not count general knowledge about the product or common practice:
only what the TEXT itself says or names.

Answer "yes" only if the TEXT states or implies what the rule requires: its condition AND the behavior or
outcome it demands (or forbids). It is NOT enough that the TEXT contains the elements, data or controls the
rule is about: a list of subtasks does not imply what happens to them, and a date field does not imply how
late items are shown. If the quoted passage would still be true of a page that violates the rule, answer "no".

Answer with a single JSON object and nothing else:
{"context_cue": "yes" or "no",
 "quote": the shortest exact passage copied from the TEXT that supports "yes" (null for "no")}"""


def omitted_span(a: str, c: str) -> str:
    prefix = 0
    while prefix < len(c) and a[prefix] == c[prefix]:
        prefix += 1
    suffix = 0
    while suffix < len(c) - prefix and a[-1 - suffix] == c[-1 - suffix]:
        suffix += 1
    if prefix + suffix != len(c):
        raise ValueError("arm C is not arm A with one contiguous span removed")
    return a[prefix:len(a) - suffix].strip()


def item_prompt(omitted: str, text: str) -> str:
    return f"{INSTRUCTIONS}\n\nOMITTED RULE:\n{omitted}\n\nTEXT (what the model received):\n<<<\n{text}\n>>>"


CONTROLS = [
    {"id": "ctl-cue-restated", "expected": "yes", "omitted": "Archived projects are not listed in the project selector.",
     "text": "Requirement:\nShow the project selector. The selector lists active projects only; archived projects stay "
             "in the Project lists page.\n\nFrozen page:\n<select id=\"projects\"></select>"},
    {"id": "ctl-cue-field-name", "expected": "yes", "omitted": "A guest invitation needs at least one channel.",
     "text": "Requirement:\nInvite a guest by email and choose their channels.\n\nFrozen page:\n<form><input id=\"email\">"
             "<select id=\"channels\" multiple required aria-label=\"Channels (at least one)\"></select></form>"},
    {"id": "ctl-cue-none", "expected": "no", "omitted": "Closing a task marks all of its unfinished subtasks as done.",
     "text": "Requirement:\nAdd a Close button to the task view. Clicking it closes the task.\n\nFrozen page:\n"
             "<section id=\"task\"><h1 id=\"title\"></h1><ul id=\"subtasks\"></ul><button id=\"close\">Close</button></section>"},
    {"id": "ctl-cue-element-only", "expected": "no", "omitted": "Overdue tasks are shown in red in the task list.",
     "text": "Requirement:\nShow the task list with each task's title and due date.\n\nFrozen page:\n"
             "<ul id=\"tasks\"></ul><template id=\"row\"><li><span class=\"title\"></span> "
             "<time class=\"due\"></time></li></template>"},
    {"id": "ctl-cue-knowledge-only", "expected": "no", "omitted": "Pasting a URL that matches a linkifier converts it to its linked text.",
     "text": "Requirement:\nImplement paste handling in the compose box using app.insertText(text).\n\nFrozen page:\n"
             "<textarea id=\"compose\"></textarea>"},
]


def parse_vote(raw: str, text: str) -> dict:
    match = re.search(r"\{.*\}", raw, re.S)
    if not match:
        raise ValueError("no JSON object")
    vote = json.loads(match.group(0))
    if vote.get("context_cue") not in ("yes", "no"):
        raise ValueError("context_cue must be yes or no")
    if vote["context_cue"] == "yes":
        quote = vote.get("quote")
        if not isinstance(quote, str) or not quote.strip() or " ".join(quote.split()) not in " ".join(text.split()):
            raise ValueError("a yes needs a literal quote from the text")
    return vote


def selected_cases(cases_dir: Path = CASES_DIR) -> list[dict]:
    items = []
    for path in sorted(cases_dir.glob("*.json")):
        config = json.loads(path.read_text())
        if not config.get("candidate_id"):
            continue
        case = Case(config)
        items.append({"case": config["case"], "candidate_id": config["candidate_id"],
                      "omitted": omitted_span(config["arms"]["A"], config["arms"]["C"]),
                      "text": case.prompt("C")})
    return items


def prepare(out: Path, models: list[str], tiebreaker: str, executable: Path, cases_dir: Path = CASES_DIR) -> dict:
    if out.exists():
        raise FileExistsError("fresh output directory required")
    items = selected_cases(cases_dir)
    order = items[:]
    random.Random(SEED).shuffle(order)
    out.mkdir(mode=0o700, parents=True)
    for item in [*CONTROLS, *[{"id": i["case"], **i} for i in order]]:
        put(out / "frozen/prompts" / f"{item['id']}.txt", item_prompt(item["omitted"], item["text"]))
    manifest = {"schema_version": SCHEMA, "seed": SEED, "models": models, "tiebreaker": tiebreaker,
                "executable": str(executable), "script_sha256": sha256_file(Path(__file__)),
                "controls": CONTROLS, "items": order, "retry_policy": "no_retry_no_repair",
                "blinding": "coders see the omitted span and the arm-C prompt only; no outputs, oracle results or probe answers"}
    put(out / "frozen/manifest.json", manifest)
    put(out / "frozen/receipt.json", {"files": inventory(out / "frozen")})
    return {"controls": len(CONTROLS), "cases": len(order), "calls_at_least": (len(CONTROLS) * 3) + 2 * len(order)}


def _call(out: Path, provider_factory, model: str, item_id: str, text: str) -> dict:
    directory = out / "calls" / model / item_id
    put(directory / "attempt.json", {"model": model, "item": item_id})
    prompt = (out / "frozen/prompts" / f"{item_id}.txt").read_text()
    try:
        from agents.providers import ProviderRequest
        raw = provider_factory(model, directory / "capture").complete(ProviderRequest(prompt, {}, "opaque", "coding"))
    except Exception as error:  # an outcome, never retried
        result = {"status": "call_failed", "error_type": type(error).__name__}
    else:
        put(directory / "response.txt", raw)
        try:
            result = {"status": "ok", "vote": parse_vote(raw, text)}
        except (ValueError, json.JSONDecodeError) as error:
            result = {"status": "invalid", "error": str(error)[:300]}
    put(directory / "result.json", result)
    return result


def run(out: Path, provider_factory=None) -> dict:
    receipt = json.loads((out / "frozen/receipt.json").read_text())["files"]
    if {k: v for k, v in inventory(out / "frozen").items() if k != "receipt.json"} != receipt:
        raise ValueError("frozen packet drift")
    manifest = json.loads((out / "frozen/manifest.json").read_text())
    if (out / "run-started.json").exists():
        raise FileExistsError("no resume or retry")
    put(out / "run-started.json", {"frozen_receipt_sha256": sha256_file(out / "frozen/receipt.json")})
    if provider_factory is None:
        from agents.codex_cli import CodexCLIProvider
        provider_factory = lambda model, evidence: CodexCLIProvider(  # noqa: E731
            executable=manifest["executable"], model=model, timeout_seconds=240, evidence_directory=evidence)
    models, tiebreaker = manifest["models"], manifest["tiebreaker"]

    controls = []
    for control in manifest["controls"]:
        votes = {m: _call(out, provider_factory, m, control["id"], control["text"]) for m in [*models, tiebreaker]}
        controls.append({"id": control["id"], "expected": control["expected"],
                         "decisions": {m: v.get("vote", {}).get("context_cue") for m, v in votes.items()}})
    if not all(set(c["decisions"].values()) == {c["expected"]} for c in controls):
        result = {"schema_version": SCHEMA + "-results", "status": "stopped_controls_failed", "controls": controls}
        put(out / "results.json", result)
        return result

    rows = []
    for item in manifest["items"]:
        votes = {m: _call(out, provider_factory, m, item["case"], item["text"]) for m in models}
        decisions = [votes[m].get("vote", {}).get("context_cue") for m in models]
        if None not in decisions and len(set(decisions)) == 1:
            final, route = decisions[0], "agreement"
        else:
            votes[tiebreaker] = _call(out, provider_factory, tiebreaker, item["case"], item["text"])
            final, route = votes[tiebreaker].get("vote", {}).get("context_cue"), "tiebreaker"
        rows.append({"case": item["case"], "candidate_id": item["candidate_id"], "route": route,
                     "context_cue": None if final is None else int(final == "yes"), "votes": votes})
        print(json.dumps({"phase": "context_cue", "done": len(rows), "of": len(manifest["items"])}), flush=True)
    both = [r for r in rows if all(r["votes"][m].get("vote") for m in models)]
    summary = {"cases": len(rows), "context_cue": dict(Counter(str(r["context_cue"]) for r in rows)),
               "routes": dict(Counter(r["route"] for r in rows)),
               "primary_kappa": cohen_kappa([r["votes"][models[0]]["vote"]["context_cue"] for r in both],
                                            [r["votes"][models[1]]["vote"]["context_cue"] for r in both]),
               "primary_pairs_with_two_valid_votes": len(both)}
    result = {"schema_version": SCHEMA + "-results", "status": "complete", "controls": controls,
              "summary": summary, "rows": rows}
    put(out / "results.json", result)
    put(out / "receipt.json", {"files": inventory(out)})
    return summary


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    sub = parser.add_subparsers(dest="mode", required=True)
    p = sub.add_parser("prepare")
    p.add_argument("--out", type=Path, required=True)
    p.add_argument("--model", action="append", required=True)
    p.add_argument("--tiebreaker", required=True)
    p.add_argument("--executable", type=Path, default=Path("/opt/homebrew/bin/codex"))
    sub.add_parser("run").add_argument("--out", type=Path, required=True)
    args = parser.parse_args(argv)
    if args.mode == "prepare":
        if len(args.model) != 2 or args.tiebreaker in args.model:
            parser.error("two distinct primary models and a different tiebreaker are required")
        result = prepare(args.out, args.model, args.tiebreaker, args.executable)
    else:
        result = run(args.out)
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
