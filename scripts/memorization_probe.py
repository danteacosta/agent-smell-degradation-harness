"""Memorization probe: does the coding model already know the rule?

For every rule the screening panel admitted, each coding model is asked the
panel's neutral probe question with no requirement, scaffold or page, three
times. Two judge models then decide whether each answer states the target
rule. The pre-registered covariate `memorized` is 1 for a (rule, coding
model) when at least two of the three answers are judged to state the rule
by both judges (the second judge is consulted only after a first "yes").

Judges are qualified first on four authored answers (two that state the
rule, two that do not); a mismatch stops the run. Calls happen once and are
never retried.

Modes: prepare (freeze probe and judge prompts) and run.
"""
from __future__ import annotations

import argparse
from collections import Counter, defaultdict
import json
from pathlib import Path
import re
import sys

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts.test_anchor_experiment import inventory, put, sha256_file  # noqa: E402

SCHEMA = "memorization-probe/v1"
REPETITIONS = 3

PROBE_TEMPLATE = (
    "You are asked about the open-source application {project}. Answer from what you know about "
    "how the application behaves, in at most three sentences. If you do not know, say so.\n\n"
    "Question: {question}"
)

JUDGE_TEMPLATE = (
    "Decide whether an answer states a given product rule.\n\n"
    "Rule: {rule}\n\nAnswer: {answer}\n\n"
    'Reply with a single JSON object: {{"states_rule": "yes" or "no"}}. Say "yes" only if the answer '
    "describes the same behavior as the rule, including its condition and outcome. An answer that is "
    "vague, says it does not know, or describes different behavior is \"no\"."
)

JUDGE_CONTROLS = [
    {"id": "jc-yes-1", "expected": "yes",
     "rule": "Closing a task marks all of its unfinished subtasks as done.",
     "answer": "When you close a task, any subtasks that were still open or in progress are set to done."},
    {"id": "jc-yes-2", "expected": "yes",
     "rule": "A shopping list combines items with the same food: 1 cup plus 2 cups of cheese shows 3 cups.",
     "answer": "Duplicate foods are merged into one line and their quantities added, so 1 and 2 cups become 3 cups."},
    {"id": "jc-no-1", "expected": "no",
     "rule": "Closing a task marks all of its unfinished subtasks as done.",
     "answer": "Closing a task hides it from the board; its subtasks keep whatever status they had."},
    {"id": "jc-no-2", "expected": "no",
     "rule": "Only administrators can set a project as a template.",
     "answer": "I am not sure how templates work in this application."},
]


def parse_judgment(raw: str) -> str:
    match = re.search(r"\{.*\}", raw, re.S)
    if not match:
        raise ValueError("no JSON object")
    value = json.loads(match.group(0)).get("states_rule")
    if value not in ("yes", "no"):
        raise ValueError("states_rule must be yes or no")
    return value


def admitted_rules(panel_results: Path) -> list[dict]:
    data = json.loads(panel_results.read_text())
    if data.get("status") != "complete":
        raise ValueError("screening panel did not complete")
    return [{"candidate_id": r["candidate_id"], "project": r["project"], "rule": r["target_rule"],
             "question": r["probe_question"]}
            for r in data["rows"] if r.get("consensus") == "admit"]


def prepare(out: Path, panel_results: Path, coders: list[str], judges: list[str], executable: Path) -> dict:
    if out.exists():
        raise FileExistsError("fresh output directory required")
    rules = admitted_rules(panel_results)
    out.mkdir(mode=0o700, parents=True)
    for rule in rules:
        prompt = PROBE_TEMPLATE.format(project=rule["project"], question=rule["question"])
        if rule["rule"].lower() in prompt.lower():
            raise ValueError(f"probe question for {rule['candidate_id']} contains the rule itself")
        put(out / "frozen/probes" / f"{rule['candidate_id']}.txt", prompt)
    for control in JUDGE_CONTROLS:
        put(out / "frozen/judge-controls" / f"{control['id']}.txt",
            JUDGE_TEMPLATE.format(rule=control["rule"], answer=control["answer"]))
    manifest = {"schema_version": SCHEMA, "coders": coders, "judges": judges, "repetitions": REPETITIONS,
                "executable": str(executable), "panel_results_sha256": sha256_file(panel_results),
                "script_sha256": sha256_file(Path(__file__)), "rules": rules,
                "judge_controls": JUDGE_CONTROLS, "retry_policy": "no_retry_no_repair"}
    put(out / "frozen/manifest.json", manifest)
    put(out / "frozen/receipt.json", {"files": inventory(out / "frozen")})
    return {"rules": len(rules), "probe_calls": len(rules) * len(coders) * REPETITIONS,
            "judge_calls_at_most": len(rules) * len(coders) * REPETITIONS * len(judges) + len(JUDGE_CONTROLS) * len(judges)}


def _complete(provider_factory, model: str, prompt: str, directory: Path) -> tuple[str | None, str | None]:
    from agents.providers import ProviderRequest
    put(directory / "attempt.json", {"model": model})
    try:
        raw = provider_factory(model, directory / "capture").complete(ProviderRequest(prompt, {}, "opaque", "probe"))
    except Exception as error:  # an outcome, never retried
        put(directory / "result.json", {"status": "call_failed", "error_type": type(error).__name__})
        return None, type(error).__name__
    put(directory / "response.txt", raw)
    return raw, None


def _judge(provider_factory, judge: str, prompt: str, directory: Path) -> str | None:
    raw, _ = _complete(provider_factory, judge, prompt, directory)
    if raw is None:
        return None
    try:
        verdict = parse_judgment(raw)
    except (ValueError, json.JSONDecodeError):
        verdict = None
    put(directory / "result.json", {"verdict": verdict})
    return verdict


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
            executable=manifest["executable"], model=model, timeout_seconds=180, evidence_directory=evidence)

    controls = []
    for control in manifest["judge_controls"]:
        prompt = (out / "frozen/judge-controls" / f"{control['id']}.txt").read_text()
        verdicts = {j: _judge(provider_factory, j, prompt, out / "calls/judge-controls" / j / control["id"])
                    for j in manifest["judges"]}
        controls.append({"id": control["id"], "expected": control["expected"], "verdicts": verdicts})
    qualified = all(set(c["verdicts"].values()) == {c["expected"]} for c in controls)
    if not qualified:
        result = {"schema_version": SCHEMA + "-results", "status": "stopped_judge_controls_failed", "controls": controls}
        put(out / "results.json", result)
        return result

    rows = []
    for rule in manifest["rules"]:
        prompt = (out / "frozen/probes" / f"{rule['candidate_id']}.txt").read_text()
        for coder in manifest["coders"]:
            answers = []
            for rep in range(1, manifest["repetitions"] + 1):
                base = out / "calls/probes" / rule["candidate_id"] / coder / f"rep{rep}"
                raw, error = _complete(provider_factory, coder, prompt, base)
                if raw is None:
                    answers.append({"rep": rep, "status": "call_failed", "states_rule": None})
                    continue
                # The second judge is asked only when the first says yes: a "yes" needs
                # both judges, so a first "no" already decides the answer.
                judge_prompt = JUDGE_TEMPLATE.format(rule=rule["rule"], answer=raw.strip()[:4000])
                first, second = manifest["judges"]
                verdicts = {first: _judge(provider_factory, first, judge_prompt, base / "judges" / first)}
                if verdicts[first] == "yes":
                    verdicts[second] = _judge(provider_factory, second, judge_prompt, base / "judges" / second)
                if verdicts[first] == "no":
                    states = "no"
                elif verdicts[first] == "yes" and verdicts.get(second) in ("yes", "no"):
                    states = verdicts[second]
                else:
                    states = None  # a judge call failed or was invalid
                answers.append({"rep": rep, "status": "ok", "verdicts": verdicts, "states_rule": states})
            yes = sum(a["states_rule"] == "yes" for a in answers)
            rows.append({"candidate_id": rule["candidate_id"], "project": rule["project"], "coder": coder,
                         "answers": answers, "yes": yes, "memorized": int(yes >= 2)})
            print(json.dumps({"phase": "probe", "rule": rule["candidate_id"], "coder": coder, "yes": yes}), flush=True)

    by_coder = defaultdict(Counter)
    for row in rows:
        by_coder[row["coder"]][row["memorized"]] += 1
    summary = {"rules": len(manifest["rules"]),
               "memorized_by_coder": {c: dict(v) for c, v in by_coder.items()},
               "unjudged_answers": sum(a.get("states_rule") is None and a["status"] == "ok"
                                          for r in rows for a in r["answers"])}
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
    p.add_argument("--panel-results", type=Path, required=True)
    p.add_argument("--coder", action="append", required=True)
    p.add_argument("--judge", action="append", required=True)
    p.add_argument("--executable", type=Path, default=Path("/opt/homebrew/bin/codex"))
    sub.add_parser("run").add_argument("--out", type=Path, required=True)
    args = parser.parse_args(argv)
    if args.mode == "prepare":
        if len(args.judge) != 2 or set(args.judge) & set(args.coder):
            parser.error("two judges, none of them a coding model, are required")
        result = prepare(args.out, args.panel_results, args.coder, args.judge, args.executable)
    else:
        result = run(args.out)
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
