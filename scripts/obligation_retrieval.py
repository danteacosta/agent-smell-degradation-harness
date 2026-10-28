"""Can the omitted obligation be retrieved from the project's own documentation?

Offline and deterministic; no model call. For each QP4 requirement, the incomplete
request (arm C) is used as a BM25 query over the project's documentation at the
snapshot the requirement was taken from, split into paragraph passages. A passage is a
"gold" passage when it contains at least half of the content words of the omitted span
(the words of arm A that the edit to arm C removed). The output is the rank of the best
gold passage, so recall@k says how often a test writer given the k top passages would
have the omitted obligation in front of it.

This measures retrievability only. Whether a tester given those passages writes a
suite that detects the loss is a separate, model-based question.

Documentation snapshots are fetched with:
  python scripts/obligation_retrieval.py fetch --cache DIR
which runs sparse, shallow git fetches of the commits listed in
data/obligation-retrieval/sources.json. Then:
  python scripts/obligation_retrieval.py run --cache DIR
writes data/obligation-retrieval/v1/results.json.
"""
from __future__ import annotations

import argparse
from collections import Counter
import difflib
import json
import math
from pathlib import Path
import re
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts.omitted_mention_triage import STOP, stem, words  # noqa: E402

SOURCES = ROOT / "data/obligation-retrieval/sources.json"
OUT = ROOT / "data/obligation-retrieval/v1/results.json"
CASES = ROOT / "data/abc-cases"
COUPLING = ROOT / "data/verifier-coupling/v1/results.json"
DOC_EXT = (".md", ".mdx", ".rst", ".txt")
KS = (1, 3, 5, 10, 20)


def content(ws: list[str]) -> list[str]:
    return [stem(w) for w in ws if w not in STOP and (len(w) >= 3 or w.isdigit())]


def omitted_span(a: str, c: str) -> list[str]:
    """Words of A that are not matched to C by a word-level diff."""
    aw, cw = words(a), words(c)
    out = []
    for tag, i1, i2, _, _ in difflib.SequenceMatcher(a=aw, b=cw, autojunk=False).get_opcodes():
        if tag in ("delete", "replace"):
            out.extend(aw[i1:i2])
    return out


def strip_markup(text: str) -> str:
    text = re.sub(r"```.*?```", " ", text, flags=re.S)
    text = re.sub(r"<[^>]+>", " ", text)
    text = re.sub(r"!\[[^\]]*\]\([^)]*\)", " ", text)
    text = re.sub(r"\[([^\]]*)\]\([^)]*\)", r"\1", text)
    text = re.sub(r":[a-z]+:`([^`]*)`", r"\1", text)
    return text


def passages(root: Path) -> list[dict]:
    out = []
    for f in sorted(root.rglob("*")):
        if not f.is_file() or f.suffix.lower() not in DOC_EXT or ".git" in f.parts:
            continue
        text = strip_markup(f.read_text(errors="replace"))
        for i, para in enumerate(re.split(r"\n\s*\n", text)):
            ws = words(para)
            if len(ws) >= 5:
                out.append({"file": str(f.relative_to(root)), "index": i, "terms": content(ws)})
    return out


class BM25:
    def __init__(self, docs: list[list[str]], k1: float = 1.5, b: float = 0.75):
        self.docs, self.k1, self.b = docs, k1, b
        self.avg = sum(len(d) for d in docs) / len(docs)
        df = Counter(t for d in docs for t in set(d))
        n = len(docs)
        self.idf = {t: math.log(1 + (n - c + 0.5) / (c + 0.5)) for t, c in df.items()}
        self.tf = [Counter(d) for d in docs]

    def scores(self, q: list[str]) -> list[float]:
        out = []
        for d, tf in zip(self.docs, self.tf):
            s = 0.0
            for t in set(q):
                if t in tf:
                    f = tf[t]
                    s += self.idf[t] * f * (self.k1 + 1) / (f + self.k1 * (1 - self.b + self.b * len(d) / self.avg))
            out.append(s)
        return out


def source_files(d: dict, root_rel: str) -> list[str]:
    """Documentation files the requirement was taken from, relative to the passage root."""
    src = d["source"]
    files = [src.get("snapshot_file") or src["file"]]
    files += [x for x in (src.get("snapshot_context") or [])]
    if src.get("snapshot_context_file"):
        files.append(src["snapshot_context_file"])
    out = []
    for f in files:
        out.append(f[len(root_rel) + 1:] if f.startswith(root_rel + "/") else f)
    return out


def evaluate(case: str, root: Path, cache: dict, root_rel: str = "") -> dict:
    d = json.loads((CASES / f"{case}.json").read_text())
    a, c = d["arms"]["A"], d["arms"]["C"]
    span = sorted(set(content(omitted_span(a, c))))
    key = str(root)
    if key not in cache:
        ps = passages(root)
        cache[key] = (ps, BM25([p["terms"] for p in ps]))
    ps, bm = cache[key]
    need = max(1, math.ceil(len(span) / 2))
    cover = [len(set(p["terms"]) & set(span)) for p in ps]
    loose = [i for i, k in enumerate(cover) if k >= need]
    srcs = source_files(d, root_rel)
    gold = [i for i in loose if any(ps[i]["file"] == f or ps[i]["file"].endswith("/" + f) for f in srcs)]

    def best_rank(query: list[str]):
        sc = bm.scores(query)
        order = sorted(range(len(ps)), key=lambda i: -sc[i])
        rank = {i: r + 1 for r, i in enumerate(order)}
        return min((rank[i] for i in gold), default=None)

    r_c = best_rank(content(words(c)))
    r_a = best_rank(content(words(a)))
    gold_strict = gold
    gold = loose
    r_c_loose = best_rank(content(words(c)))
    gold = gold_strict
    best = max(range(len(ps)), key=lambda i: cover[i]) if ps else None
    return {"case": case, "project_id": d["project_id"], "omitted_content_words": span,
            "source_files": srcs, "passages": len(ps), "gold_passages": len(gold),
            "loose_gold_passages": len(loose), "rank_query_incomplete_loose": r_c_loose, "words_needed": need,
            "max_cover": max(cover) if cover else 0,
            "best_cover_file": ps[best]["file"] if best is not None else None,
            "rank_query_incomplete": r_c, "rank_query_complete": r_a}


def run(cache_dir: Path) -> dict:
    src = json.loads(SOURCES.read_text())
    coupling = json.loads(COUPLING.read_text())
    cases = sorted(coupling["Q1_ensemble"]["per_requirement"])
    det = {r["case"]: r for r in coupling["Q3_coupling"]["per_requirement"]}
    cache: dict = {}
    rows = []
    for case in cases:
        s = src["cases"][case]
        rows.append(evaluate(case, cache_dir / s["dir"] / s["root"], cache, s["root"]))
    usable = [r for r in rows if r["gold_passages"]]
    recall = {str(k): (sum(1 for r in usable if r["rank_query_incomplete"] and r["rank_query_incomplete"] <= k)
                       / len(usable)) if usable else None for k in KS}
    by_group = {}
    for label, sel in (("zero_recovery", [r for r in usable if det[r["case"]]["generator_recovery"] == 0]),
                       ("some_recovery", [r for r in usable if det[r["case"]]["generator_recovery"] > 0])):
        by_group[label] = {"requirements": len(sel),
                           "recall_at_5": (sum(1 for r in sel if r["rank_query_incomplete"] and r["rank_query_incomplete"] <= 5)
                                           / len(sel)) if sel else None}
    return {"schema_version": "obligation-retrieval/v1", "exploratory": True, "model_calls": 0,
            "method": "BM25 (k1 1.5, b 0.75) over paragraph passages of the documentation snapshot; "
                      "query = arm C text; gold = passage in the requirement's source documentation file with >= half of the "
                      "omitted span's content words (loose variant: any file, reported per row)",
            "requirements": len(rows), "requirements_with_gold_passage": len(usable),
            "recall_query_incomplete": recall,
            "recall_query_complete_at_1": (sum(1 for r in usable if r["rank_query_complete"] == 1) / len(usable))
            if usable else None,
            "recall_at_5_by_recovery_group": by_group, "rows": rows}


def fetch(cache_dir: Path) -> None:
    src = json.loads(SOURCES.read_text())
    cache_dir.mkdir(parents=True, exist_ok=True)
    for name, s in src["snapshots"].items():
        d = cache_dir / name
        if (d / ".git").exists():
            continue
        d.mkdir(parents=True, exist_ok=True)
        sh = lambda *a: subprocess.run(["git", "-C", str(d), *a], check=True, capture_output=True)  # noqa: E731
        sh("init", "-q")
        sh("remote", "add", "origin", s["url"])
        sh("sparse-checkout", "set", "--no-cone", *s["paths"])
        sh("fetch", "-q", "--depth", "1", "--filter=blob:none", "origin", s["sha"])
        sh("checkout", "-q", "FETCH_HEAD")
        print(f"fetched {name}")


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("cmd", choices=["fetch", "run"])
    ap.add_argument("--cache", required=True, type=Path)
    args = ap.parse_args(argv)
    if args.cmd == "fetch":
        fetch(args.cache)
        return
    res = run(args.cache)
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(res, indent=2) + "\n")
    print(json.dumps({k: v for k, v in res.items() if k != "rows"}, indent=1))


if __name__ == "__main__":
    main()
