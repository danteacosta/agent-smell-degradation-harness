"""Test-anchor experiment: do generated browser tests catch an omitted rule?

Question.  When an agent's implementation lost a requirement condition, which
way of writing browser tests still detects it?

* ``code_request``: the tester sees the implementation and the request the
  coding agent received (for an omission artifact, the request without the
  rule).  This is how a PR-reviewing QA tool usually works.
* ``code_spec``: the tester sees the implementation and the complete
  requirement.
* ``spec_only``: the tester sees the complete requirement and the frozen
  scaffold, but no implementation.  One suite per case is run against every
  artifact of that case.

Ground truth is the frozen, qualified oracle verdict already recorded for each
artifact (``pass`` or ``target_only_failure``).  The tester never sees it.

The script reads existing private pilot packets, freezes every tester prompt
before any model call, generates suites once (no retry or repair), executes
each suite in the qualified network-disabled image and writes descriptive
counts.  It is exploratory: three cases are not a population.
"""
from __future__ import annotations

import argparse
from collections import Counter, defaultdict
import hashlib
import json
import os
from pathlib import Path
import random
import re
import subprocess
import sys
import uuid

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

SCHEMA = "test-anchor-experiment/v1"
IMAGE = "sha256:00d1265095773b7f8a12aa73e81d0bab75563cbd672dd0b5d91783ea1b6d4400"
NODE_PATH = "/opt/openproject-remaining-pilot/node_modules"
RUNNER = ROOT / "eval/fixtures/test-anchor/runner.cjs"
STRATEGIES = ("code_request", "code_spec", "spec_only")
SPEC_ONLY_SUITES = 3
SEED = 2026100201
GROUND_TRUTH = {"pass": False, "target_only_failure": True}
MARKER = "/* MODEL_BEHAVIOR */"

INSTRUCTIONS = """You are a QA engineer. Write automated browser tests for the feature described below.

The page is served at the URL passed to each test (http://localhost/). It runs offline;
localStorage works. A test may call context.addInitScript before page.goto, for example
to define window.initialState, which the page reads when nothing is stored yet.

Return only one JavaScript (CommonJS) module in a single ```js code block, shaped exactly as:

module.exports = {
  tests: [
    { name: "short description", run: async ({ context, page, url, assert }) => { /* ... */ } },
  ],
};

Rules: 1 to 8 tests. Use only the Playwright Page/BrowserContext API and the provided
assert (node:assert/strict). No require/import, no network, no file access. Each test
must finish within 20 seconds. A test passes when it returns and fails when it throws.
Test the behavior a user should observe for this feature."""


# --------------------------------------------------------------------------- utils

def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def sha256_file(path: Path) -> str:
    return sha256_bytes(path.read_bytes())


def put(path: Path, value) -> None:
    if path.exists():
        raise FileExistsError(f"refusing to overwrite {path}")
    path.parent.mkdir(mode=0o700, parents=True, exist_ok=True)
    data = value if isinstance(value, bytes) else (
        value.encode() if isinstance(value, str) else (json.dumps(value, indent=2, sort_keys=True) + "\n").encode())
    path.write_bytes(data)


def inventory(root: Path) -> dict[str, str]:
    return {str(p.relative_to(root)): sha256_file(p) for p in sorted(root.rglob("*")) if p.is_file()}


# ------------------------------------------------------------------ packet reading

def split_prompt(prompt: str) -> tuple[str, str]:
    """Return (requirement, frozen page) from a collector prompt."""
    match = re.search(r"\n\nRequirement:\n(.*?)\n\nFrozen page:\n(.*)\Z", prompt, re.S)
    if not match:
        raise ValueError("collector prompt lacks Requirement/Frozen page sections")
    return match.group(1).strip(), match.group(2)


def read_packet(case: str, packet: Path) -> dict:
    """Load arm texts, scaffold and oracle-labelled A/C artifacts from a pilot packet."""
    manifest = json.loads((packet / "frozen/manifest.json").read_text())
    results = json.loads((packet / "results.json").read_text())
    arm_of = {row["slot_id"]: row["arm"] for row in manifest["schedule"]}
    requirements: dict[str, str] = {}
    scaffold = None
    for slot_id, arm in arm_of.items():
        prompt = json.loads((packet / "frozen/requests" / f"{slot_id}.json").read_text())["prompt"]
        requirement, page = split_prompt(prompt)
        if requirements.setdefault(arm, requirement) != requirement:
            raise ValueError(f"{case}: arm {arm} has inconsistent requirement text")
        if scaffold is None:
            scaffold = page
        elif scaffold != page:
            raise ValueError(f"{case}: scaffold differs across requests")
    if {"A", "C"} - set(requirements) or scaffold is None or scaffold.count(MARKER) != 1:
        raise ValueError(f"{case}: packet must contain A and C arms and one behavior marker")
    artifacts = []
    for row in results["rows"]:
        if row.get("arm") not in ("A", "C") or row.get("category") not in GROUND_TRUTH:
            continue
        path = packet / "artifacts" / row["slot_id"] / "app.html"
        artifacts.append({
            "case": case, "slot_id": row["slot_id"], "arm": row["arm"], "model": row.get("model"),
            "replication": row.get("replication"), "oracle_category": row["category"],
            "oracle_target_failed": GROUND_TRUTH[row["category"]],
            "artifact_path": str(path.resolve()), "artifact_sha256": sha256_file(path),
        })
    return {"case": case, "packet": str(packet.resolve()), "requirements": requirements,
            "scaffold": scaffold, "artifacts": artifacts,
            "results_sha256": sha256_file(packet / "results.json")}


# --------------------------------------------------------------------- prompts

def tester_prompt(strategy: str, requirement: str, page: str) -> str:
    if strategy == "spec_only":
        view = ("Feature requirement (from the ticket):\n" + requirement
                + "\n\nPage scaffold (the feature's script is not shown; it is inserted at "
                + MARKER + "):\n" + page)
    elif strategy in ("code_request", "code_spec"):
        label = ("Change description (from the pull request):" if strategy == "code_request"
                 else "Feature requirement (from the ticket):")
        view = label + "\n" + requirement + "\n\nImplementation under test (complete page):\n" + page
    else:
        raise ValueError(strategy)
    return INSTRUCTIONS + "\n\n" + view


def plan(cases: list[dict]) -> list[dict]:
    """Every tester call, with the artifacts each resulting suite will run against."""
    calls = []
    for case in cases:
        complete = case["requirements"]["A"]
        for artifact in case["artifacts"]:
            implementation = Path(artifact["artifact_path"]).read_text()
            own_request = case["requirements"][artifact["arm"]]
            for strategy, requirement in (("code_request", own_request), ("code_spec", complete)):
                calls.append({"strategy": strategy, "case": case["case"], "for_slot": artifact["slot_id"],
                              "prompt": tester_prompt(strategy, requirement, implementation),
                              "targets": [artifact["slot_id"]]})
        for index in range(1, SPEC_ONLY_SUITES + 1):
            calls.append({"strategy": "spec_only", "case": case["case"], "for_slot": None,
                          "suite_index": index,
                          "prompt": tester_prompt("spec_only", complete, case["scaffold"]),
                          "targets": [a["slot_id"] for a in case["artifacts"]]})
    for call in calls:
        key = json.dumps([call["strategy"], call["case"], call.get("for_slot"), call.get("suite_index"), SEED])
        call["call_id"] = "ta-" + hashlib.sha256(key.encode()).hexdigest()[:20]
    random.Random(SEED).shuffle(calls)
    return calls


# ---------------------------------------------------------------- generation

SUITE_BLOCK = re.compile(r"```(?:js|javascript)?\s*\n(.*?)```", re.S)
FORBIDDEN = re.compile(r"\brequire\s*\(|\bimport\s*\(|^\s*import\s|\bprocess\.|\bchild_process\b|\bfs\.", re.M)


def extract_suite(raw: str) -> str:
    blocks = SUITE_BLOCK.findall(raw)
    if len(blocks) != 1:
        raise ValueError(f"expected one code block, found {len(blocks)}")
    code = blocks[0].strip() + "\n"
    if "module.exports" not in code:
        raise ValueError("suite does not assign module.exports")
    if FORBIDDEN.search(code):
        raise ValueError("suite uses a forbidden module, process or file API")
    return code


# ----------------------------------------------------------------- execution

def docker_execute(artifact: Path, suite: Path, output: Path) -> dict:
    """Run one suite against one artifact in the qualified, network-disabled image."""
    staging = output / "input"
    staging.mkdir(mode=0o700, parents=True)
    (staging / "app.html").write_bytes(artifact.read_bytes())
    (staging / "suite.cjs").write_bytes(suite.read_bytes())
    command = [
        "docker", "run", "--rm", "--init", "--name", "test-anchor-" + uuid.uuid4().hex,
        "--network", "none", "--user", f"{os.getuid()}:{os.getgid()}", "--read-only",
        "--cap-drop", "ALL", "--security-opt", "no-new-privileges", "--pids-limit", "256",
        "--memory", "1g", "--cpus", "2", "--shm-size", "256m",
        "--tmpfs", "/tmp:rw,nosuid,size=256m", "--env", "HOME=/tmp", "--env", f"NODE_PATH={NODE_PATH}",
        "--mount", f"type=bind,src={staging.resolve()},dst=/input,readonly",
        "--mount", f"type=bind,src={output.resolve()},dst=/output",
        "--mount", f"type=bind,src={RUNNER.resolve()},dst=/runner.cjs,readonly",
        "--entrypoint", "node", IMAGE, "/runner.cjs",
    ]
    result = subprocess.run(command, capture_output=True, timeout=300, check=False)
    (output / "stderr.txt").write_bytes(result.stderr[-20000:])
    report_path = output / "report.json"
    if not report_path.is_file():
        return {"status": "runner_error", "returncode": result.returncode}
    return json.loads(report_path.read_text())


def classify(report: dict) -> str:
    """Suite verdict: alarm (some test failed), assertion_alarm subset, quiet, or unusable."""
    if report.get("status") == "suite_invalid":
        return "suite_invalid"
    if report.get("status") != "complete":
        return "runner_error"
    outcomes = [t["outcome"] for t in report.get("tests", [])]
    if "assertion_failure" in outcomes:
        return "assertion_alarm"
    if "error" in outcomes:
        return "error_alarm"
    return "quiet"


# ------------------------------------------------------------------ controls

CONTROL_SCAFFOLD = ROOT / "eval/fixtures/openproject-invalid-remaining/page.html"
CONTROL_BEHAVIOR = {
    "keeps_rule": "app.onSave(v=>{if(Number(v.remaining)>Number(v.work)){app.message('Remaining work cannot exceed Work');return}app.persist(v)});",
    "lost_rule": "app.onSave(v=>{app.persist(v)});",
    "broken_save": "app.onSave(()=>{});",
}
CONTROL_SUITE = """module.exports = { tests: [
  { name: 'valid save persists', run: async ({ context, page, url, assert }) => {
      await context.addInitScript(() => { window.initialState = { work: '8', remaining: '7' }; });
      await page.goto(url);
      await page.getByLabel('Remaining work').fill('6');
      await page.locator('#save').click();
      await page.reload();
      assert.equal(await page.getByLabel('Remaining work').inputValue(), '6');
  } },
  { name: 'remaining above work is rejected', run: async ({ context, page, url, assert }) => {
      await context.addInitScript(() => { window.initialState = { work: '8', remaining: '7' }; });
      await page.goto(url);
      await page.getByLabel('Remaining work').fill('9');
      await page.locator('#save').click();
      await page.reload();
      assert.equal(await page.getByLabel('Remaining work').inputValue(), '7');
  } },
] };
"""
CONTROL_EXPECTED = {"keeps_rule": "quiet", "lost_rule": "assertion_alarm", "broken_save": "assertion_alarm"}


def run_controls(out: Path, executor=docker_execute) -> dict:
    """Qualify the generic runner on authored artifacts before any generated suite runs."""
    if out.exists():
        raise FileExistsError("fresh controls directory required")
    page = CONTROL_SCAFFOLD.read_text()
    if page.count(MARKER) != 1:
        raise ValueError("control scaffold must contain one behavior marker")
    put(out / "suite.cjs", CONTROL_SUITE)
    observed = {}
    for name, behavior in CONTROL_BEHAVIOR.items():
        put(out / "artifacts" / name / "app.html", page.replace(MARKER, behavior))
        report = executor(out / "artifacts" / name / "app.html", out / "suite.cjs", out / "execution" / name)
        observed[name] = classify(report)
    result = {"expected": CONTROL_EXPECTED, "observed": observed, "qualified": observed == CONTROL_EXPECTED,
              "runner_sha256": sha256_file(RUNNER)}
    put(out / "controls.json", result)
    return result


# ----------------------------------------------------------------- analysis

UNUSABLE = ("generation_failed", "suite_invalid", "runner_error")


def analyze(rows: list[dict]) -> dict:
    """Detection on oracle failures and false alarms on oracle passes.

    Primary (intention-to-test): every planned suite/artifact pair stays in the
    denominator, and an unusable suite counts as no alarm, because a tool that
    produces no runnable test detects nothing.  ``usable_only`` drops unusable
    pairs.  Counts are reported per case; repetitions inside a case are not
    independent requirements.
    """
    summary: dict = {}
    for strategy in STRATEGIES:
        by_case: dict = {}
        for case in sorted({r["case"] for r in rows if r["strategy"] == strategy}):
            entry: dict = {}
            for truth, flag in (("oracle_failure", True), ("oracle_pass", False)):
                group = [r for r in rows if r["strategy"] == strategy and r["case"] == case
                         and r["oracle_target_failed"] is flag]
                verdicts = Counter(r["verdict"] for r in group)
                alarms = verdicts["assertion_alarm"] + verdicts["error_alarm"]
                usable = len(group) - sum(verdicts[v] for v in UNUSABLE)
                entry[truth] = {
                    "pairs": len(group), "verdicts": dict(verdicts), "alarms": alarms,
                    "assertion_alarms": verdicts["assertion_alarm"], "usable": usable,
                }
            by_case[case] = entry
        pooled = {truth: Counter() for truth in ("oracle_failure", "oracle_pass")}
        for entry in by_case.values():
            for truth in pooled:
                pooled[truth].update({k: v for k, v in entry[truth].items() if k != "verdicts"})
        def rate(n, d):
            return None if not d else n / d
        summary[strategy] = {
            "by_case": by_case,
            "pooled_counts": {t: dict(c) for t, c in pooled.items()},
            "detection_itt": rate(pooled["oracle_failure"]["alarms"], pooled["oracle_failure"]["pairs"]),
            "false_alarm_itt": rate(pooled["oracle_pass"]["alarms"], pooled["oracle_pass"]["pairs"]),
            "detection_assertion_itt": rate(pooled["oracle_failure"]["assertion_alarms"], pooled["oracle_failure"]["pairs"]),
            "false_alarm_assertion_itt": rate(pooled["oracle_pass"]["assertion_alarms"], pooled["oracle_pass"]["pairs"]),
            "detection_usable_only": rate(pooled["oracle_failure"]["alarms"], pooled["oracle_failure"]["usable"]),
            "false_alarm_usable_only": rate(pooled["oracle_pass"]["alarms"], pooled["oracle_pass"]["usable"]),
        }
    return summary


# -------------------------------------------------------------------- locate

PUBLIC_SUMMARIES = ROOT / "data/e2e-replications-20261001"
CASES = ("realworld-favorites", "openproject-invalid-remaining", "paperless-duplicate-consumption")


def locate(evidence_root: Path) -> dict[str, str]:
    """Bind a collection by both receipts; replications may reuse a freeze."""
    wanted = {}
    for case in CASES:
        summary = json.loads((PUBLIC_SUMMARIES / case / "summary.json").read_text())
        wanted[(summary["frozen_receipt_sha256"], summary["collection_receipt_sha256"])] = case
    found: dict[str, list[str]] = defaultdict(list)
    for receipt in sorted(evidence_root.glob("*/frozen/receipt.json")):
        packet = receipt.parent.parent
        collection_receipt = packet / "receipt.json"
        if not collection_receipt.is_file() or not (packet / "results.json").is_file():
            continue
        case = wanted.get((sha256_file(receipt), sha256_file(collection_receipt)))
        if case:
            found[case].append(str(packet))
    missing = [case for case in CASES if len(found.get(case, [])) != 1]
    if missing:
        raise SystemExit(f"could not identify exactly one packet for: {', '.join(missing)}")
    return {case: paths[0] for case, paths in found.items()}


# --------------------------------------------------------------------- modes

def prepare(out: Path, packets: dict[str, Path], model: str, executable: Path) -> dict:
    if out.exists():
        raise FileExistsError("fresh output directory required")
    cases = [read_packet(case, path) for case, path in sorted(packets.items())]
    calls = plan(cases)
    out.mkdir(mode=0o700, parents=True)
    for call in calls:
        put(out / "frozen/prompts" / f"{call['call_id']}.txt", call["prompt"])
    schedule = [{k: v for k, v in call.items() if k != "prompt"} for call in calls]
    manifest = {
        "schema_version": SCHEMA, "status": "pre_generation", "seed": SEED, "model": model,
        "executable": str(executable), "image": IMAGE, "strategies": STRATEGIES,
        "spec_only_suites_per_case": SPEC_ONLY_SUITES,
        "runner_sha256": sha256_file(RUNNER), "script_sha256": sha256_file(Path(__file__)),
        "cases": [{k: case[k] for k in ("case", "packet", "results_sha256", "requirements")}
                  | {"artifacts": case["artifacts"]} for case in cases],
        "schedule": schedule, "retry_policy": "no_retry_no_repair", "confirmatory_eligible": False,
        "ground_truth": "frozen qualified oracle category recorded in each packet's results.json",
    }
    put(out / "frozen/manifest.json", manifest)
    put(out / "frozen/receipt.json", {"files": inventory(out / "frozen")})
    return {"calls": len(calls), "cases": {c["case"]: len(c["artifacts"]) for c in cases}}


def verify_frozen(out: Path) -> dict:
    receipt = json.loads((out / "frozen/receipt.json").read_text())["files"]
    current = {k: v for k, v in inventory(out / "frozen").items() if k != "receipt.json"}
    if current != receipt:
        raise ValueError("frozen packet drift")
    manifest = json.loads((out / "frozen/manifest.json").read_text())
    if manifest["runner_sha256"] != sha256_file(RUNNER):
        raise ValueError("runner drift since freeze")
    for case in manifest["cases"]:
        for artifact in case["artifacts"]:
            if sha256_file(Path(artifact["artifact_path"])) != artifact["artifact_sha256"]:
                raise ValueError(f"artifact drift: {artifact['slot_id']}")
    return manifest


def generate(out: Path, provider_factory=None) -> dict:
    manifest = verify_frozen(out)
    if (out / "generation-started.json").exists():
        raise FileExistsError("no resume or retry")
    put(out / "generation-started.json", {"frozen_receipt_sha256": sha256_file(out / "frozen/receipt.json")})
    if provider_factory is None:
        from agents.codex_cli import CodexCLIProvider
        provider_factory = lambda evidence: CodexCLIProvider(  # noqa: E731
            executable=manifest["executable"], model=manifest["model"], timeout_seconds=300,
            evidence_directory=evidence)
    from agents.providers import ProviderRequest
    status = Counter()
    for call in manifest["schedule"]:
        directory = out / "calls" / call["call_id"]
        prompt = (out / "frozen/prompts" / f"{call['call_id']}.txt").read_text()
        put(directory / "attempt.json", {"call_id": call["call_id"]})
        try:
            provider = provider_factory(directory / "capture")
            raw = provider.complete(ProviderRequest(prompt, {}, "opaque", "code"))
        except Exception as error:  # preserved as an outcome, never retried
            put(directory / "result.json", {"status": "generation_failed", "error_type": type(error).__name__,
                                            "error": str(error)[:500]})
            status["generation_failed"] += 1
            continue
        put(directory / "response.txt", raw)
        try:
            suite = extract_suite(raw)
        except ValueError as error:
            put(directory / "result.json", {"status": "suite_invalid", "reason": str(error)})
            status["suite_invalid"] += 1
        else:
            put(directory / "suite.cjs", suite)
            put(directory / "result.json", {"status": "suite_ready", "suite_sha256": sha256_bytes(suite.encode())})
            status["suite_ready"] += 1
        print(json.dumps({"phase": "generation", "done": sum(status.values()),
                          "of": len(manifest["schedule"])}), flush=True)
    put(out / "generation.json", dict(status))
    return dict(status)


def execute(out: Path, executor=docker_execute) -> dict:
    manifest = verify_frozen(out)
    if (out / "execution-started.json").exists():
        raise FileExistsError("no resume or retry")
    put(out / "execution-started.json", {"generation_sha256": sha256_file(out / "generation.json")})
    artifacts = {a["slot_id"]: a for case in manifest["cases"] for a in case["artifacts"]}
    rows = []
    for call in manifest["schedule"]:
        directory = out / "calls" / call["call_id"]
        result = json.loads((directory / "result.json").read_text())
        for slot_id in call["targets"]:
            artifact = artifacts[slot_id]
            row = {"call_id": call["call_id"], "strategy": call["strategy"], "case": call["case"],
                   "suite_index": call.get("suite_index"), "slot_id": slot_id, "arm": artifact["arm"],
                   "model": artifact["model"], "oracle_category": artifact["oracle_category"],
                   "oracle_target_failed": artifact["oracle_target_failed"]}
            if result["status"] != "suite_ready":
                row["verdict"] = result["status"]
            else:
                try:
                    report = executor(Path(artifact["artifact_path"]), directory / "suite.cjs",
                                      out / "execution" / call["call_id"] / slot_id)
                except Exception as error:
                    report = {"status": "runner_error", "error": f"{type(error).__name__}: {error}"[:500]}
                row["verdict"] = classify(report)
                row["tests"] = report.get("tests", [])
            rows.append(row)
            print(json.dumps({"phase": "execution", "strategy": row["strategy"], "slot": slot_id,
                              "verdict": row["verdict"]}), flush=True)
    results = {"schema_version": SCHEMA + "-results", "rows": rows, "summary": analyze(rows),
               "confirmatory_eligible": False}
    put(out / "results.json", results)
    put(out / "receipt.json", {"files": inventory(out)})
    return results["summary"]


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    sub = parser.add_subparsers(dest="mode", required=True)
    p = sub.add_parser("prepare")
    p.add_argument("--out", type=Path, required=True)
    p.add_argument("--packet", action="append", required=True, metavar="CASE=PATH")
    p.add_argument("--model", required=True)
    p.add_argument("--executable", type=Path, default=Path("/opt/homebrew/bin/codex"))
    sub.add_parser("locate").add_argument("--evidence-root", type=Path, required=True)
    for mode in ("controls", "generate", "execute", "summary"):
        sub.add_parser(mode).add_argument("--out", type=Path, required=True)
    args = parser.parse_args(argv)
    if args.mode == "locate":
        result = locate(args.evidence_root)
    elif args.mode == "prepare":
        packets = dict(item.split("=", 1) for item in args.packet)
        result = prepare(args.out, {k: Path(v) for k, v in packets.items()}, args.model, args.executable)
    elif args.mode == "controls":
        result = run_controls(args.out)
        if not result["qualified"]:
            print(json.dumps(result, indent=2))
            raise SystemExit("runner controls did not match; do not run generated suites")
    elif args.mode == "generate":
        result = generate(args.out)
    elif args.mode == "execute":
        result = execute(args.out)
    else:
        result = json.loads((args.out / "results.json").read_text())["summary"]
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
