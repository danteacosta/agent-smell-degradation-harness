"""Historical arm H: does the pre-commit requirement text produce the defect?

The 46-case collection compared the frame-end documentation (A) with a
constructed omission (C). This study adds the natural counterpart: H is the
requirement as the project documented it *before* the commit that introduced
or changed the target rule, with everything else held equal to A.

  classify       mechanical triage of the 46 cases from source texts only:
                 excluded_deletion (the old text held the rule), excluded_moved
                 (the commit moved text that already stated the rule), and the
                 rest go to the review panel with the parent-commit excerpt
  prepare-panel  freeze the blind old-documentation review (two coders and a
                 tiebreaker, authored controls first, no retry)
  run-panel      call the panel (on the machine that has the Codex CLI)
  build          admission and H texts from the panel decisions, plus the
                 derived case configs that collect arms A and H together
  analyse        H vs A (contemporaneous) from the new packets

Admission (frozen before any H generation): the old documentation describes
the feature of the requirement, and the target rule there is either absent
or stated in a vaguer form. Absent: H is C. Vaguer: H is A with the sentences
that carry the rule replaced by the old passage quoted verbatim; if the old
passage already survives in C, H is C. Same or different (a behavior change,
not an underspecification) and undocumented features are excluded.

No outcome of any run is read by classify, the panel or build.
"""
from __future__ import annotations

import argparse
from collections import Counter
import hashlib
import json
from pathlib import Path
import random
import re
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts.check_current_documentation import EXTRA_PATHS, is_present, norm  # noqa: E402
from scripts.mine_requirement_candidates import DOC_EXT, PROJECTS, clean  # noqa: E402
from scripts.llm_screening_panel import cohen_kappa  # noqa: E402
from scripts.test_anchor_experiment import inventory, put, sha256_file  # noqa: E402

CASES_DIR = ROOT / "data/abc-cases"
FRAMES = [ROOT / "data/requirement-sampling/frame-20261002.jsonl",
          ROOT / "data/requirement-sampling/frame-ext-20261002.jsonl"]
SELECTION = ROOT / "data/requirement-selection/selection.json"
COVERAGE = 0.9  # share of C-span word tokens that must come from the commit's added text


def tokens(text: str) -> set[str]:
    return set(re.findall(r"[a-z0-9]+", text.lower()))


def omitted_span(a: str, c: str) -> tuple[int, int]:
    i = 0
    while i < len(c) and a[i] == c[i]:
        i += 1
    j = 0
    while j < len(c) - i and a[-1 - j] == c[-1 - j]:
        j += 1
    if i + j != len(c):
        raise ValueError("C is not A with one contiguous span removed")
    return i, len(a) - j


def parent_texts(repo: Path, project: str, commit: str) -> list[str]:
    def git(*args):
        return subprocess.run(["git", "-C", str(repo), *args], capture_output=True, text=True, check=True).stdout
    parent = git("rev-parse", f"{commit}^").strip()
    paths = PROJECTS[project]["paths"] + EXTRA_PATHS.get(project, [])
    files = [f for f in git("ls-tree", "-r", "--name-only", parent, "--", *paths).splitlines()
             if f.lower().endswith(DOC_EXT)]
    if not files:
        return []
    batch = subprocess.run(["git", "-C", str(repo), "cat-file", "--batch"],
                           input="".join(f"{parent}:{f}\n" for f in files).encode(),
                           capture_output=True, check=True).stdout
    texts, pos = [], 0
    while pos < len(batch):
        nl = batch.index(b"\n", pos)
        header = batch[pos:nl].split()
        pos = nl + 1
        if len(header) < 3 or header[1] == b"missing":
            continue
        size = int(header[2])
        body = batch[pos:pos + size].decode("utf-8", "replace")
        pos += size + 1
        texts.append(norm(" ".join(clean(line) for line in body.splitlines())))
    return texts


EXCERPT_CONTEXT = 25  # unified-diff context lines around each change
EXCERPT_MAX_CHARS = 9000


def old_excerpt(repo: Path, commit: str, file: str, removed: list[str], added: list[str]) -> str:
    """The parent-commit text of the hunks that carry the frame's change, markup cleaned.

    Only the old side is kept (context and removed lines): this is what the
    documentation said before the commit. Hunks that touch none of the frame's
    added or removed sentences are dropped; if none match, all hunks are kept.
    """
    diff = subprocess.run(["git", "-C", str(repo), "diff", "--no-color", f"-U{EXCERPT_CONTEXT}",
                           f"{commit}^", commit, "--", file], capture_output=True, check=True
                          ).stdout.decode("utf-8", "replace")
    lines = []  # (kind, text) in diff order, hunks separated by ("@", "")
    for line in diff.splitlines():
        if line.startswith("@@"):
            lines.append(("@", ""))
        elif not lines or line.startswith(("---", "+++", "\\")):
            continue
        else:
            lines.append((line[0] if line[0] in "+-" else " ", clean(line[1:])))
    target_tokens = [tokens(s) for s in [*removed, *added] if tokens(s)]

    def matches(text: str) -> bool:
        t = tokens(text)
        return len(t) >= 2 and any(len(t & s) >= 0.6 * len(t) for s in target_tokens)

    anchors = [i for i, (k, t) in enumerate(lines) if k in "+-" and matches(t)]
    if not anchors:
        anchors = [i for i, (k, _) in enumerate(lines) if k in "+-"]
    keep = {j for i in anchors for j in range(i - EXCERPT_CONTEXT, i + EXCERPT_CONTEXT + 1)}
    out, gap = [], False
    for i, (kind, text) in enumerate(lines):
        if kind in " -" and i in keep and text:
            if gap and out:
                out.append("[...]")
            out.append(text)
            gap = False
        elif kind == "@" or i not in keep:
            gap = True
    return "\n".join(out)[:EXCERPT_MAX_CHARS]


def classify(repos: Path) -> dict:
    frame = {}
    for path in FRAMES:
        for line in path.read_text().splitlines():
            if line.strip():
                row = json.loads(line)
                frame[row["candidate_id"]] = row
    selected = {u["candidate_id"] for us in json.loads(SELECTION.read_text())["selected"].values() for u in us}
    parents: dict[tuple[str, str], list[str]] = {}
    rows = []
    for path in sorted(CASES_DIR.glob("*.json")):
        config = json.loads(path.read_text())
        cid = config.get("candidate_id")
        if cid not in selected:
            continue
        f = frame[cid]
        a, c = config["arms"]["A"], config["arms"]["C"]
        start, end = omitted_span(a, c)
        span = a[start:end]
        span_tokens = tokens(span)
        coverage = len(span_tokens & tokens(" ".join(f["added"]))) / max(1, len(span_tokens))
        row = {"case": config["case"], "candidate_id": cid, "project": f["project"], "commit": f["commit"],
               "file": f["file"], "kind": f["kind"], "c_span": span, "c_span_coverage_by_added": round(coverage, 3),
               "removed": f["removed"], "added": f["added"]}
        if f["kind"] == "deletion":
            row["class"] = "excluded_deletion"
            row["reason"] = "the pre-commit text contained the rule; it is not an omission"
        elif f["kind"] == "addition":
            key = (f["project"], f["commit"])
            if key not in parents:
                parents[key] = parent_texts(repos / f["project"], f["project"], f["commit"])
            # The rule is what C removes; only its presence in the parent tree
            # disqualifies (generic added steps such as "Visit settings" may recur).
            row["added_present_in_parent"] = [s for s in f["added"] if is_present(s, parents[key])]
            moved = tokens(" ".join(row["added_present_in_parent"]))
            row["c_span_coverage_by_moved"] = round(len(span_tokens & moved) / max(1, len(span_tokens)), 3)
            if row["c_span_coverage_by_moved"] >= COVERAGE:
                row["class"] = "excluded_moved"
                row["reason"] = "the added text already existed in the parent documentation (moved, not added)"
            else:
                row["class"] = "panel"
                row["reason"] = "addition: the review panel decides whether the old text documented the feature"
        else:
            row["class"] = "panel"
            row["reason"] = "modification: the review panel compares the old passage with the target rule"
        if row["class"] == "panel":
            row["old_excerpt"] = old_excerpt(repos / f["project"], f["commit"], f["file"], f["removed"], f["added"])
            row["requirement_without_rule"] = c
        rows.append(row)
    return {"schema_version": "historical-arm-classification/v2", "coverage_threshold": COVERAGE,
            "excerpt_context_lines": EXCERPT_CONTEXT, "outcomes_read": False,
            "counts": dict(Counter(r["class"] for r in rows)),
            "inputs_sha256": {str(p.relative_to(ROOT)): hashlib.sha256(p.read_bytes()).hexdigest()
                              for p in [*FRAMES, SELECTION]},
            "rows": rows}


# ------------------------------------------------------------------ review panel

PANEL_SCHEMA = "historical-review-panel/v1"
PANEL_SEED = 2026100403
STATUSES = ("same", "vaguer", "absent", "different")

INSTRUCTIONS = """You compare an old version of a software project's documentation with one rule of a newer
requirement. This is for a study of how requirement text changed over time.

You receive:
- FEATURE: the requirement as it reads without the rule (what the feature is and how it is used);
- RULE: the target rule, as it is stated in the newer requirement;
- OLD DOCUMENTATION: an excerpt of the project's documentation before the rule was written.

Answer two questions about the OLD DOCUMENTATION only. Do not use general knowledge of the product.

1. feature_documented: does the OLD DOCUMENTATION already describe the feature of FEATURE, so that a
   reader would know it exists and roughly how it is used? A different feature on the same page does not
   count. Answer "yes" (quote the passage that describes it) or "no".

2. rule_status: what does the OLD DOCUMENTATION say about the behavior the RULE governs?
   "same"      it states the rule with the same meaning (other words are fine);
   "vaguer"    it states this behavior less precisely, in a way consistent with the rule but that does not
               determine it (a reader could implement it either way);
   "absent"    it says nothing about this behavior;
   "different" it states a behavior that contradicts the rule (the product's behavior changed).
   For "same", "vaguer" and "different" quote the shortest passage that states it; for "absent" use null.

Quotes must be copied exactly from the OLD DOCUMENTATION.

Answer with a single JSON object and nothing else:
{"feature_documented": "yes" or "no", "feature_quote": string or null,
 "rule_status": "same" or "vaguer" or "absent" or "different", "rule_quote": string or null}"""


def panel_prompt(feature: str, rule: str, old: str) -> str:
    return (f"{INSTRUCTIONS}\n\nFEATURE:\n<<<\n{feature}\n>>>\n\nRULE:\n<<<\n{rule}\n>>>"
            f"\n\nOLD DOCUMENTATION:\n<<<\n{old}\n>>>")


PANEL_CONTROLS = [
    {"id": "ctl-hist-same", "expected": {"feature_documented": "yes", "rule_status": "same"},
     "feature": "Implement the password form of the sign-up page. When the user clicks Create account, validate the password with app.check(password).",
     "rule": "The password must have at least 12 characters.",
     "old": "Sign up\nOpen the sign-up page and enter your email address and a password.\nPasswords need a minimum length of twelve characters.\nClick Create account."},
    {"id": "ctl-hist-vaguer", "expected": {"feature_documented": "yes", "rule_status": "vaguer"},
     "feature": "Implement the password form of the sign-up page. When the user clicks Create account, validate the password with app.check(password).",
     "rule": "The password must have at least 12 characters.",
     "old": "Sign up\nOpen the sign-up page and enter your email address and a password.\nChoose a long password.\nClick Create account."},
    {"id": "ctl-hist-absent", "expected": {"feature_documented": "yes", "rule_status": "absent"},
     "feature": "Implement the password form of the sign-up page. When the user clicks Create account, validate the password with app.check(password).",
     "rule": "The password must have at least 12 characters.",
     "old": "Sign up\nOpen the sign-up page and enter your email address and a password.\nClick Create account. You will receive a confirmation email."},
    {"id": "ctl-hist-different", "expected": {"feature_documented": "yes", "rule_status": "different"},
     "feature": "Implement the board list. Show each board with app.showBoard(board).",
     "rule": "Archived boards are hidden from the board list.",
     "old": "Boards\nThe board list shows all of your boards. Archived boards stay in the list with a grey Archived label."},
    {"id": "ctl-hist-undocumented", "expected": {"feature_documented": "no", "rule_status": "absent"},
     "feature": "Implement the board list. Show each board with app.showBoard(board).",
     "rule": "Archived boards are hidden from the board list.",
     "old": "Notifications\nYou receive an email when someone mentions you in a card comment. Turn this off in your profile settings."},
]


def _in(quote, text: str) -> bool:
    return isinstance(quote, str) and bool(quote.strip()) and " ".join(quote.split()) in " ".join(text.split())


def parse_review(raw: str, old: str) -> dict:
    match = re.search(r"\{.*\}", raw, re.S)
    if not match:
        raise ValueError("no JSON object")
    vote = json.loads(match.group(0))
    if vote.get("feature_documented") not in ("yes", "no"):
        raise ValueError("feature_documented must be yes or no")
    if vote.get("rule_status") not in STATUSES:
        raise ValueError(f"rule_status must be one of {STATUSES}")
    if vote["feature_documented"] == "yes" and not _in(vote.get("feature_quote"), old):
        raise ValueError("feature_documented=yes needs a literal quote from the old documentation")
    if vote["rule_status"] != "absent" and not _in(vote.get("rule_quote"), old):
        raise ValueError(f"rule_status={vote['rule_status']} needs a literal quote from the old documentation")
    return {k: vote.get(k) for k in ("feature_documented", "feature_quote", "rule_status", "rule_quote")}


def decision(vote: dict | None) -> tuple[str, str] | None:
    return None if not vote else (vote["feature_documented"], vote["rule_status"])


def panel_items(classification: dict) -> list[dict]:
    return [{"id": r["case"], "case": r["case"], "candidate_id": r["candidate_id"],
             "feature": r["requirement_without_rule"], "rule": r["c_span"].strip(), "old": r["old_excerpt"]}
            for r in classification["rows"] if r["class"] == "panel"]


def prepare_panel(out: Path, classification_path: Path, models: list[str], tiebreaker: str, executable: Path) -> dict:
    if out.exists():
        raise FileExistsError("fresh output directory required")
    classification = json.loads(classification_path.read_text())
    items = panel_items(classification)
    order = items[:]
    random.Random(PANEL_SEED).shuffle(order)
    out.mkdir(mode=0o700, parents=True)
    for item in [*PANEL_CONTROLS, *order]:
        put(out / "frozen/prompts" / f"{item['id']}.txt", panel_prompt(item["feature"], item["rule"], item["old"]))
    manifest = {"schema_version": PANEL_SCHEMA, "seed": PANEL_SEED, "models": models, "tiebreaker": tiebreaker,
                "executable": str(executable), "script_sha256": sha256_file(Path(__file__)),
                "classification_sha256": sha256_file(classification_path),
                "controls": PANEL_CONTROLS, "items": order, "retry_policy": "no_retry_no_repair",
                "blinding": "coders see the requirement without the rule, the rule and the parent-commit excerpt; "
                            "no generated code, oracle results, arm outcomes or model names"}
    put(out / "frozen/manifest.json", manifest)
    put(out / "frozen/receipt.json", {"files": inventory(out / "frozen")})
    return {"controls": len(PANEL_CONTROLS), "cases": len(order),
            "calls_at_least": 3 * len(PANEL_CONTROLS) + 2 * len(order)}


def _review_call(out: Path, provider_factory, model: str, item: dict) -> dict:
    directory = out / "calls" / model / item["id"]
    put(directory / "attempt.json", {"model": model, "item": item["id"]})
    prompt = (out / "frozen/prompts" / f"{item['id']}.txt").read_text()
    try:
        from agents.providers import ProviderRequest
        raw = provider_factory(model, directory / "capture").complete(ProviderRequest(prompt, {}, "opaque", "coding"))
    except Exception as error:  # an outcome, never retried
        result = {"status": "call_failed", "error_type": type(error).__name__}
    else:
        put(directory / "response.txt", raw)
        try:
            result = {"status": "ok", "vote": parse_review(raw, item["old"])}
        except (ValueError, json.JSONDecodeError) as error:
            result = {"status": "invalid", "error": str(error)[:300]}
    put(directory / "result.json", result)
    return result


def run_panel(out: Path, provider_factory=None) -> dict:
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
        votes = {m: _review_call(out, provider_factory, m, control) for m in [*models, tiebreaker]}
        controls.append({"id": control["id"], "expected": control["expected"],
                         "decisions": {m: v.get("vote") and {k: v["vote"][k] for k in ("feature_documented", "rule_status")}
                                       for m, v in votes.items()}})
    if not all(d == c["expected"] for c in controls for d in c["decisions"].values()):
        result = {"schema_version": PANEL_SCHEMA + "-results", "status": "stopped_controls_failed", "controls": controls}
        put(out / "results.json", result)
        return result

    rows = []
    for item in manifest["items"]:
        votes = {m: _review_call(out, provider_factory, m, item) for m in models}
        decisions = [decision(votes[m].get("vote")) for m in models]
        if None not in decisions and decisions[0] == decisions[1]:
            route, decider = "agreement", models[0]
        else:
            votes[tiebreaker] = _review_call(out, provider_factory, tiebreaker, item)
            route, decider = "tiebreaker", tiebreaker
        final = votes[decider].get("vote")
        rows.append({"case": item["case"], "candidate_id": item["candidate_id"], "route": route,
                     "decided_by": decider, "final": final, "votes": votes})
        print(json.dumps({"phase": "historical_review", "done": len(rows), "of": len(manifest["items"])}), flush=True)
    both = [r for r in rows if all(r["votes"][m].get("vote") for m in models)]
    summary = {"cases": len(rows),
               "decisions": dict(Counter("invalid" if r["final"] is None else
                                         f"{r['final']['feature_documented']}/{r['final']['rule_status']}" for r in rows)),
               "routes": dict(Counter(r["route"] for r in rows)),
               "kappa_feature_documented": cohen_kappa([r["votes"][models[0]]["vote"]["feature_documented"] for r in both],
                                                       [r["votes"][models[1]]["vote"]["feature_documented"] for r in both]),
               "kappa_rule_status": cohen_kappa([r["votes"][models[0]]["vote"]["rule_status"] for r in both],
                                                [r["votes"][models[1]]["vote"]["rule_status"] for r in both]),
               "primary_pairs_with_two_valid_votes": len(both)}
    result = {"schema_version": PANEL_SCHEMA + "-results", "status": "complete", "controls": controls,
              "summary": summary, "rows": rows}
    put(out / "results.json", result)
    put(out / "receipt.json", {"files": inventory(out)})
    return summary


# ------------------------------------------------------------------ admission and H texts

SENTENCE_BREAK = re.compile(r"(?<=[.!?])\s+(?=\S)")
H_SEED_OFFSET = 7_000_000


def sentence_bounds(a: str, start: int, end: int) -> tuple[int, int]:
    """Widen [start, end) to whole sentences of A."""
    while start < end and a[start].isspace():
        start += 1
    while end > start and a[end - 1].isspace():
        end -= 1
    starts = [0] + [m.end() for m in SENTENCE_BREAK.finditer(a)]
    ends = [m.start() for m in SENTENCE_BREAK.finditer(a)] + [len(a)]
    return max(s for s in starts if s <= start), min(e for e in ends if e >= end)


def h_text(a: str, c: str, status: str, quote: str | None) -> tuple[str, str]:
    """(H, construction). Absent: H is C. Vaguer: old passage in place of the rule's sentences."""
    if status == "absent":
        return c, "absent_h_equals_c"
    quote = " ".join(quote.split())
    q = tokens(quote)
    if q and len(q & tokens(c)) / len(q) >= COVERAGE:
        return c, "vaguer_passage_survives_in_c"
    start, end = omitted_span(a, c)
    xs, xe = sentence_bounds(a, start, end)
    if quote[-1] not in ".!?":
        quote += "."
    h = (a[:xs] + quote + a[xe:]).strip()
    return re.sub(r"[ \t]+", " ", h), "vaguer_old_passage_spliced"


def build(classification_path: Path, panel_results: Path, out_dir: Path, cases_dir: Path = CASES_DIR) -> dict:
    classification = json.loads(classification_path.read_text())
    panel = json.loads(panel_results.read_text())
    if panel.get("status") != "complete":
        raise ValueError("panel did not complete")
    final = {r["case"]: r for r in panel["rows"]}
    rows = []
    for r in classification["rows"]:
        entry = {"case": r["case"], "project": r["project"], "kind": r["kind"], "class": r["class"]}
        if r["class"] != "panel":
            entry.update(admitted=False, reason=r["reason"])
            rows.append(entry)
            continue
        vote = final[r["case"]]["final"]
        entry["panel"] = {"route": final[r["case"]]["route"], "decided_by": final[r["case"]]["decided_by"], "final": vote}
        if vote is None:
            entry.update(admitted=False, reason="no valid panel decision")
        elif vote["feature_documented"] != "yes":
            entry.update(admitted=False, reason="the old documentation did not describe the feature")
        elif vote["rule_status"] in ("same", "different"):
            entry.update(admitted=False, reason=f"old documentation: rule {vote['rule_status']}")
        else:
            config = json.loads((cases_dir / f"{r['case']}.json").read_text())
            h, how = h_text(config["arms"]["A"], config["arms"]["C"], vote["rule_status"], vote.get("rule_quote"))
            entry.update(admitted=True, construction=how, H=h)
            derived = {**config, "arms": {**config["arms"], "H": h}, "collect_arms": ["A", "H"],
                       "seed": config["seed"] + H_SEED_OFFSET,
                       "historical": {"construction": how, "rule_status": vote["rule_status"],
                                      "old_quote": vote.get("rule_quote"),
                                      "commit": r["commit"], "file": r["file"]}}
            out_dir.mkdir(parents=True, exist_ok=True)
            (out_dir / f"{r['case']}.json").write_text(json.dumps(derived, indent=2, ensure_ascii=False) + "\n")
        rows.append(entry)
    admitted = [e for e in rows if e["admitted"]]
    return {"schema_version": "historical-arm-admission/v1", "outcomes_read": False,
            "classification_sha256": sha256_file(classification_path),
            "panel_results_sha256": sha256_file(panel_results),
            "counts": {"admitted": len(admitted), "excluded": len(rows) - len(admitted),
                       "constructions": dict(Counter(e["construction"] for e in admitted)),
                       "planned_calls": sum(2 * len(json.loads((out_dir / f"{e['case']}.json").read_text())["models"])
                                            * json.loads((out_dir / f"{e['case']}.json").read_text())["repetitions"]
                                            for e in admitted)},
            "rows": rows}


# ------------------------------------------------------------------ analysis

def analyse(results_root: Path, configs_dir: Path, seed: int = 2026100404,
            previous_root: Path = ROOT / "data/selection-abc-results/20261003") -> dict:
    from protocol.paired_stats import paired_probability_of_superiority
    from scripts.selected46_report import severity
    configs = {p.stem: json.loads(p.read_text()) for p in sorted(configs_dir.glob("*.json"))}
    out = {}
    for mode in ("drop", "worst", "best"):
        rows, finished = [], 0
        for case, config in configs.items():
            path = results_root / case / "results.json"
            if not path.exists():
                continue
            finished += 1
            by = {(r["model"], r["replication"], r["arm"]): r for r in json.loads(path.read_text())["rows"]}
            for model in config["models"]:
                for rep in range(1, config["repetitions"] + 1):
                    a = severity(by.get((model, rep, "A"), {}).get("category"))
                    h = severity(by.get((model, rep, "H"), {}).get("category"))
                    if a is None or h is None:
                        if mode == "drop":
                            continue
                        a = (0 if mode == "worst" else 1) if a is None else a
                        h = (1 if mode == "worst" else 0) if h is None else h
                    rows.append({"intent_id": case, "project_id": config["project_id"], "model": model,
                                 "replication": rep, "clean_severity": a, "defective_severity": h})
        est = paired_probability_of_superiority(rows, seed=seed) if rows else {"estimate": None}
        if mode != "drop":
            est = {**est, "analysis_scope": "deterministic_sensitivity_bound", "valid_for_inference": False}
        out[mode] = est
    by_construction = {}
    for how in sorted({c["historical"]["construction"] for c in configs.values()}):
        sub = {k: v for k, v in configs.items() if v["historical"]["construction"] == how}
        rows = []
        for case, config in sub.items():
            path = results_root / case / "results.json"
            if path.exists():
                by = {(r["model"], r["replication"], r["arm"]): r for r in json.loads(path.read_text())["rows"]}
                for model in config["models"]:
                    for rep in range(1, config["repetitions"] + 1):
                        a = severity(by.get((model, rep, "A"), {}).get("category"))
                        h = severity(by.get((model, rep, "H"), {}).get("category"))
                        if a is not None and h is not None:
                            rows.append({"intent_id": case, "project_id": config["project_id"], "model": model,
                                         "replication": rep, "clean_severity": a, "defective_severity": h})
        by_construction[how] = {"cases": len(sub), **(paired_probability_of_superiority(rows, seed=seed)
                                                       if rows else {"estimate": None})}
    return {"schema_version": "historical-arm-report/v1", "confirmatory_eligible": False,
            "admitted_cases": len(configs), "finished_cases": finished, "h_vs_a": out,
            "h_vs_a_by_construction": by_construction,
            "diagnostics": drift(results_root, previous_root, configs)}


def _violation(path: Path, arm: str) -> dict:
    from scripts.selected46_report import severity
    sev = [severity(r.get("category")) for r in json.loads(path.read_text())["rows"] if r["arm"] == arm]
    return {"violated": sev.count(1), "held": sev.count(0), "unknown": sev.count(None)}


def drift(results_root: Path, previous_root: Path, configs: dict) -> dict:
    """A now vs A in the 46-case collection; H vs the old C where H is C."""
    out = {}
    for case, config in configs.items():
        now, then = results_root / case / "results.json", previous_root / case / "results.json"
        if not now.exists() or not then.exists():
            continue
        row = {"A_now": _violation(now, "A"), "A_then": _violation(then, "A")}
        if config["arms"]["H"] == config["arms"]["C"]:
            row.update(H_now=_violation(now, "H"), C_then=_violation(then, "C"))
        out[case] = row
    return out


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    sub = parser.add_subparsers(dest="mode", required=True)
    c = sub.add_parser("classify")
    c.add_argument("--repos", type=Path, required=True)
    c.add_argument("--out", type=Path, required=True)
    p = sub.add_parser("prepare-panel")
    p.add_argument("--classification", type=Path, default=ROOT / "data/historical-arm/classification.json")
    p.add_argument("--out", type=Path, required=True)
    p.add_argument("--model", action="append", required=True)
    p.add_argument("--tiebreaker", required=True)
    p.add_argument("--executable", type=Path, default=Path("/opt/homebrew/bin/codex"))
    sub.add_parser("run-panel").add_argument("--out", type=Path, required=True)
    b = sub.add_parser("build")
    b.add_argument("--classification", type=Path, default=ROOT / "data/historical-arm/classification.json")
    b.add_argument("--panel-results", type=Path, required=True)
    b.add_argument("--cases-out", type=Path, default=ROOT / "data/historical-arm/cases")
    b.add_argument("--out", type=Path, default=ROOT / "data/historical-arm/admission.json")
    a = sub.add_parser("analyse")
    a.add_argument("--results", type=Path, required=True)
    a.add_argument("--cases", type=Path, default=ROOT / "data/historical-arm/cases")
    args = parser.parse_args(argv)
    if args.mode == "classify":
        result = classify(args.repos)
        args.out.write_text(json.dumps(result, indent=2, ensure_ascii=False) + "\n")
        print(json.dumps(result["counts"], indent=2))
        for r in result["rows"]:
            print(f"{r['class']:<20} {r['case']:<42} cov={r['c_span_coverage_by_added']}")
    elif args.mode == "prepare-panel":
        if len(args.model) != 2 or args.tiebreaker in args.model:
            parser.error("two distinct primary models and a different tiebreaker are required")
        print(json.dumps(prepare_panel(args.out, args.classification, args.model, args.tiebreaker,
                                       args.executable), indent=2))
    elif args.mode == "run-panel":
        print(json.dumps(run_panel(args.out), indent=2))
    elif args.mode == "build":
        if args.cases_out.exists() and any(args.cases_out.iterdir()):
            raise FileExistsError(f"{args.cases_out} is not empty; the H texts are frozen once built")
        result = build(args.classification, args.panel_results, args.cases_out)
        args.out.write_text(json.dumps(result, indent=2, ensure_ascii=False) + "\n")
        print(json.dumps(result["counts"], indent=2))
    else:
        print(json.dumps(analyse(args.results, args.cases), indent=2))


if __name__ == "__main__":
    main()
