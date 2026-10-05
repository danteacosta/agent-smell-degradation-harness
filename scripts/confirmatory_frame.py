"""Candidate frames for the confirmatory H1a collection (no model calls).

Two options are prepared so the frame can be chosen with real eligibility
counts; neither has been seen by any model or used in any A/B/C run.

  reserve  candidates of the registered frame (2025-01-01..2026-09-30) that
           were never drawn into a screening sample
  w2024    a new frame mined with the same filters over 2024-01-01..2024-12-31
           (data/requirement-sampling/frame-2024-candidates.jsonl)

For each option a seeded screening sample of at most CAP candidates per
project is written in the format scripts/llm_screening_panel.py reads.
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
SAMPLING = ROOT / "data/requirement-sampling"
FRAMES = [SAMPLING / "frame-20261002.jsonl", SAMPLING / "frame-ext-20261002.jsonl"]
SCREENED = [SAMPLING / "screening-20261002.json", SAMPLING / "screening-ext-20261002.json"]
W2024 = SAMPLING / "frame-2024-candidates.jsonl"
CAP = 30
SEED = 2026100502


def read_jsonl(path: Path) -> list[dict]:
    return [json.loads(line) for line in path.read_text().splitlines() if line.strip()]


def sample(rows: list[dict], seed: int, cap: int = CAP) -> list[dict]:
    rng = random.Random(seed)
    out = []
    for project in sorted({r["project"] for r in rows}):
        pool = sorted((r for r in rows if r["project"] == project), key=lambda r: r["candidate_id"])
        out.extend(pool if len(pool) <= cap else rng.sample(pool, cap))
    return out


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def build() -> dict:
    screened = {c["candidate_id"] for p in SCREENED for c in json.loads(p.read_text())["candidates"]}
    reserve = [r for p in FRAMES for r in read_jsonl(p) if r["candidate_id"] not in screened]
    w2024 = read_jsonl(W2024)
    if {r["candidate_id"] for r in w2024} & {r["candidate_id"] for p in FRAMES for r in read_jsonl(p)}:
        raise ValueError("2024 candidate ids collide with the registered frame")
    summary = {}
    for name, rows, seed in (("reserve", reserve, SEED), ("w2024", w2024, SEED + 1)):
        chosen = sample(rows, seed)
        doc = {"schema_version": "requirement-screening/v1", "date": "2026-10-05", "round": f"confirmatory-{name}",
               "screened_by": None,
               "note": (f"Confirmatory frame option '{name}'. Seeded sample of at most {CAP} per project, "
                        f"seed {seed}. No assistant pre-screen; no model has seen these candidates."),
               "inputs_sha256": {str(p.relative_to(ROOT)): sha(p) for p in [*FRAMES, *SCREENED, W2024]},
               "candidates": chosen}
        out = SAMPLING / f"screening-confirmatory-{name}-20261005.json"
        out.write_text(json.dumps(doc, indent=2, ensure_ascii=False) + "\n")
        summary[name] = {"frame_candidates": dict(sorted(Counter(r["project"] for r in rows).items())),
                         "screening_sample": dict(sorted(Counter(r["project"] for r in chosen).items())),
                         "screening_total": len(chosen), "file": str(out.relative_to(ROOT))}
    return summary


def main(argv: list[str] | None = None) -> None:
    argparse.ArgumentParser(description=__doc__.splitlines()[0]).parse_args(argv)
    result = build()
    (ROOT / "data/confirmatory-planning").mkdir(parents=True, exist_ok=True)
    (ROOT / "data/confirmatory-planning/frame-options.json").write_text(json.dumps(result, indent=2) + "\n")
    json.dump(result, sys.stdout, indent=2)


if __name__ == "__main__":
    main()
