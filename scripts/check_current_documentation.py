"""Check which admitted rules are still in each project's documentation at the frame end.

The pre-registration defines arm A as "the project's current documentation".
This script fixes "current" as the last commit on the default branch at or
before the frame end (2026-09-30T23:59:59Z) and asks, for every admitted
candidate, whether the sentences its change added and removed are present
in that snapshot. Each documentation file is cleaned line by line exactly as
the miner cleaned diff lines and joined with spaces; a sentence counts as
present when its word tokens appear contiguously in some file's word tokens
(markup, punctuation and table padding are ignored). All documentation paths
of the project are searched, so a page that
moved (for example Zulip's help center migration) still counts.

Inputs are the screening results and frames only; no probe or E2E outcome.

  python scripts/check_current_documentation.py --repos REPOS --out data/requirement-selection/current-doc-check.json

REPOS holds one clone per project (any depth that contains the snapshot).
"""
from __future__ import annotations

import argparse
import hashlib
import json
import re
from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts.mine_requirement_candidates import DOC_EXT, PROJECTS, clean  # noqa: E402

FRAME_END = "2026-09-30T23:59:59Z"
# Pages can include shared snippets outside the mined paths; search those too.
EXTRA_PATHS = {"zulip": ["starlight_help/src/content/include"]}
SCREENING = [ROOT / "data/llm-screening-20261002/results.json",
             ROOT / "data/llm-screening-round2-20261003/results.json"]
FRAMES = [ROOT / "data/requirement-sampling/frame-20261002.jsonl",
          ROOT / "data/requirement-sampling/frame-ext-20261002.jsonl"]


def norm(text: str) -> str:
    """Lower-case word tokens: ignores markup, punctuation, table padding and emphasis."""
    return " " + " ".join(re.findall(r"[a-z0-9]+", text.lower())) + " "


def is_present(sentence: str, texts: list[str]) -> bool:
    needle = norm(sentence)
    return needle.strip() != "" and any(needle in text for text in texts)


def git(repo: Path, *args: str) -> str:
    return subprocess.run(["git", "-C", str(repo), *args], capture_output=True, text=True,
                          errors="replace", check=True).stdout


def snapshot_texts(repo: Path, project: str) -> tuple[str, list[str]]:
    try:
        default_ref = git(repo, "symbolic-ref", "--quiet", "refs/remotes/origin/HEAD").strip()
        git(repo, "rev-parse", "--verify", f"{default_ref}^{{commit}}")
    except subprocess.CalledProcessError as exc:
        raise ValueError(f"{project}: default branch identity is unavailable; refresh origin/HEAD") from exc
    if not default_ref.startswith("refs/remotes/origin/"):
        raise ValueError(f"{project}: default branch must identify an origin branch")
    sha = git(repo, "rev-list", "-1", f"--before={FRAME_END}", default_ref).strip()
    if not sha:
        raise ValueError(f"{project}: no default-branch commit at or before the frame end")
    paths = PROJECTS[project]["paths"] + EXTRA_PATHS.get(project, [])
    files = [f for f in git(repo, "ls-tree", "-r", "--name-only", sha, "--", *paths).splitlines()
             if f.lower().endswith(DOC_EXT)]
    found: list[str] = []
    # one batched read; blob-less clones fetch the needed blobs on demand
    batch = "".join(f"{sha}:{f}\n" for f in files)
    out = subprocess.run(["git", "-C", str(repo), "cat-file", "--batch"], input=batch.encode(),
                         capture_output=True, check=True).stdout
    pos = 0
    for file in files:
        header_end = out.find(b"\n", pos)
        if header_end < 0:
            raise ValueError(f"{project}: missing blob header for {file}")
        parts = out[pos:header_end].split()
        if (len(parts) != 3 or parts[1] != b"blob"
                or not re.fullmatch(rb"(?:[0-9a-f]{40}|[0-9a-f]{64})", parts[0]) or not parts[2].isdigit()):
            raise ValueError(f"{project}: missing or invalid document blob for {file}")
        size = int(parts[2])
        body_start, body_end = header_end + 1, header_end + 1 + size
        if body_end >= len(out) or out[body_end:body_end + 1] != b"\n":
            raise ValueError(f"{project}: incomplete document blob for {file}")
        body = out[body_start:body_end].decode("utf-8", "replace")
        found.append(norm(" ".join(clean(line) for line in body.splitlines())))
        pos = body_end + 1
    if pos != len(out):
        raise ValueError(f"{project}: unexpected extra document blobs")
    return sha, found


def check(repos: Path) -> dict:
    frame = {}
    for path in FRAMES:
        for line in path.read_text().splitlines():
            if line.strip():
                row = json.loads(line)
                frame[row["candidate_id"]] = row
    admitted = [r for p in SCREENING for r in json.loads(p.read_text())["rows"] if r["consensus"] == "admit"]
    cache: dict[str, tuple[str, list[str]]] = {}
    rows = []
    for row in sorted(admitted, key=lambda r: r["candidate_id"]):
        f = frame[row["candidate_id"]]
        project = f["project"]
        if project not in cache:
            cache[project] = snapshot_texts(repos / project, project)
        sha, present = cache[project]
        added = [s for s in f["added"]]
        removed = [s for s in f["removed"]]
        rows.append({
            "candidate_id": row["candidate_id"], "project": project, "kind": f["kind"],
            "added_present": sum(is_present(s, present) for s in added), "added_total": len(added),
            "removed_present": sum(is_present(s, present) for s in removed), "removed_total": len(removed),
            "target_rule": row["target_rule"],
        })
    return {"schema_version": "current-doc-check/v1", "frame_end": FRAME_END,
            "snapshots": {p: sha for p, (sha, _) in sorted(cache.items())},
            "inputs_sha256": {str(p.relative_to(ROOT)): hashlib.sha256(p.read_bytes()).hexdigest()
                              for p in [*SCREENING, *FRAMES]},
            "rows": rows}


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--repos", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    result = check(args.repos)
    args.out.write_text(json.dumps(result, indent=2, ensure_ascii=False) + "\n")
    print(json.dumps(result["snapshots"], indent=2))


if __name__ == "__main__":
    main()
