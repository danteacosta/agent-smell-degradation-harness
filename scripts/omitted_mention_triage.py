"""Deterministic triage: does a generated test suite mention the omitted obligation?

A lexical proxy, not an audit. For each requirement it extracts the words that appear
in the complete requirement (arm A) but not in the request with the obligation removed
(arm C), drops stop words and words that also occur in C, and reports which of those
"omitted tokens" occur in a suite's source (test names, strings, comments, code;
camelCase and snake_case are split). A suite that mentions none of them is unlikely to
check the obligation by name; a suite that mentions one may still not check it. The
blind human audit of the shared-omission suites (#185) remains pending and is not
replaced by this script.

It reads arm texts from data/abc-cases/<case>.json. Suites are files whose content is
read as text; a manifest maps each suite file to its case and source label.

Usage:
  python scripts/omitted_mention_triage.py tokens <case>
  python scripts/omitted_mention_triage.py scan --manifest M.json --out OUT.json
      M.json: [{"suite": "path/to/suite.cjs", "case": "...", "source": "...", "id": "..."}]
  python scripts/omitted_mention_triage.py test-anchor-demo
      runs the scan on the public test-anchor suites of openproject-invalid-remaining
"""
from __future__ import annotations

import argparse
from collections import defaultdict
import json
from pathlib import Path
import re
import sys

ROOT = Path(__file__).resolve().parents[1]
CASES = ROOT / "data/abc-cases"

STOP = set("""
a about above after again against all also an and any are as at be because been before being below
between both but by can could did do does doing down during each few for from further had has have having
he her here hers him his how i if in into is it its itself just me more most my no nor not now of off on once
only or other our out over own same she should so some such than that the their them then there these they
this those through to too under until up very was we were what when where which while who whom why will
with would you your yours user users page button click clicks clicked shows show shown display displayed
value values field fields item items list lists new set sets
""".split())


def words(text: str) -> list[str]:
    """Lower-case word tokens; camelCase and snake_case are split; numbers kept."""
    text = re.sub(r"([a-z])([A-Z])", r"\1 \2", text)
    return [w.lower() for w in re.findall(r"[A-Za-z]+|\d+(?:\.\d+)?", text.replace("_", " "))]


def stem(w: str) -> str:
    """Crude suffix stripping so that 'saved' and 'saving' compare equal."""
    for suf in ("ings", "ing", "ied", "ies", "ed", "es", "s"):
        if len(w) > len(suf) + 2 and w.endswith(suf):
            return w[: -len(suf)]
    return w


def omitted_tokens(a_text: str, c_text: str, project: str = "") -> list[str]:
    c = {stem(w) for w in words(c_text)}
    proj = set(words(project))
    out = []
    for w in words(a_text):
        if stem(w) in c or w in STOP or w in proj or w in out:
            continue
        if w.isdigit() or len(w) >= 4:
            out.append(w)
    return out


def case_tokens(case: str) -> list[str]:
    d = json.loads((CASES / f"{case}.json").read_text())
    return omitted_tokens(d["arms"]["A"], d["arms"]["C"], d.get("project_id", ""))


def mentions(suite_text: str, tokens: list[str]) -> list[str]:
    present = set(words(suite_text))
    return [t for t in tokens if t in present]


def scan(manifest: list[dict]) -> dict:
    cache: dict[str, list[str]] = {}
    rows = []
    for m in manifest:
        toks = cache.setdefault(m["case"], case_tokens(m["case"]))
        text = Path(m["suite"]).read_text(errors="replace")
        hit = mentions(text, toks)
        rows.append({"id": m.get("id", m["suite"]), "case": m["case"], "source": m["source"],
                     "omitted_tokens": len(toks), "hits": hit, "mentions": bool(hit)})
    by = defaultdict(lambda: [0, 0])
    for r in rows:
        by[(r["case"], r["source"])][0] += r["mentions"]
        by[(r["case"], r["source"])][1] += 1
    summary = [{"case": c, "source": s, "suites": n, "mentioning": k} for (c, s), (k, n) in sorted(by.items())]
    return {"schema_version": "omitted-mention-triage/v1", "proxy_only": True,
            "note": "Lexical proxy; a mention is not a check of the obligation. Does not replace the blind human audit.",
            "tokens": cache, "summary": summary, "rows": rows}


def test_anchor_manifest() -> list[dict]:
    base = ROOT / "data/test-anchor-20261002"
    sched = json.loads((base / "schedule.json").read_text())
    out = []
    for s in sched:
        if s["case"] != "openproject-invalid-remaining":
            continue
        f = base / "suites" / f"{s['call_id']}.cjs"
        if f.exists():
            out.append({"suite": str(f), "case": s["case"], "source": s["strategy"], "id": s["call_id"]})
    return out


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    sub = ap.add_subparsers(dest="cmd", required=True)
    t = sub.add_parser("tokens")
    t.add_argument("case")
    s = sub.add_parser("scan")
    s.add_argument("--manifest", required=True)
    s.add_argument("--out", required=True)
    sub.add_parser("test-anchor-demo")
    args = ap.parse_args(argv)
    if args.cmd == "tokens":
        print(json.dumps(case_tokens(args.case)))
    elif args.cmd == "scan":
        res = scan(json.loads(Path(args.manifest).read_text()))
        Path(args.out).write_text(json.dumps(res, indent=2) + "\n")
        for r in res["summary"]:
            print(r)
    else:
        res = scan(test_anchor_manifest())
        print(json.dumps(res["tokens"]))
        for r in res["summary"]:
            print(r)


if __name__ == "__main__":
    main()
