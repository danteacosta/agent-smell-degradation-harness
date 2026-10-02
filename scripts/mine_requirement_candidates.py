"""Mine documentation commits for candidate behavioral-rule changes.

Sampling frame (pre-registered): every non-merge commit between SINCE and
UNTIL that edits user-facing documentation of a listed project, where an added
or removed sentence states a behavioral rule (a condition, limit, default,
permission, state change or prohibition). Formatting-only and near-identical
rewordings are excluded mechanically; whether the rule is verifiable in a user
interface is decided afterwards by blind review, not by this script.

Output: one JSON object per candidate change, with the exact removed and added
sentences, the commit, file, date and the rule cues that matched.
"""
from __future__ import annotations

import argparse
import difflib
import hashlib
import json
import re
import subprocess
from pathlib import Path

SINCE, UNTIL = "2025-01-01", "2026-09-30"
SCREEN_CAP_PER_PROJECT = 30
SCREEN_SEED = 2026100202

PROJECTS = {
    "kanboard": {"paths": ["."], "exclude": []},
    "paperless": {"paths": ["docs"], "exclude": ["changelog", "setup", "development", "api", "configuration", "troubleshooting"]},
    "nextcloud": {"paths": ["user_manual"], "exclude": ["release_notes", "locale"]},
    "realworld": {"paths": ["."], "exclude": ["CHANGELOG"]},
    "todomvc": {"paths": ["app-spec.md"], "exclude": []},
    "strictdoc": {"paths": ["docs"], "exclude": ["release_notes", "changelog"]},
    "openproject": {"paths": ["docs/user-guide", "docs/getting-started"], "exclude": ["release-notes"]},
    "immich": {"paths": ["docs/docs/features", "docs/docs/guides"], "exclude": []},
    "mealie": {"paths": ["docs/docs"], "exclude": ["changelog"]},
    "mattermost": {"paths": ["source/end-user-guide"], "exclude": ["changelog", "release", "deprecated"]},
    "zammad": {"paths": ["."], "exclude": ["admin", "api", "contributing", "appendix", "getting-started"]},
    "joplin": {"paths": ["readme/apps"], "exclude": []},
    "wekan": {"paths": ["docs/Features"], "exclude": ["translations", "admin-panel"]},
    # Frame extension, screening round 2 (deviation recorded 2026-10-02): round 1
    # admitted rules from seven projects and the plan needs eight.
    "zulip": {"paths": ["help", "starlight_help/src/content/docs"], "exclude": ["changelog"]},
    # functions.md is Grist's generated formula reference (signatures and search
    # anchors), excluded like API references in other projects.
    "grist": {"paths": ["help/en/docs"], "exclude": ["self-managed", "install", "api", "changelog", "newsletter",
                                                     "functions.md"]},
}
ROUND_1_PROJECTS = ("kanboard", "paperless", "nextcloud", "realworld", "todomvc", "strictdoc", "openproject",
                    "immich", "mealie", "mattermost", "zammad", "joplin", "wekan")
DOC_EXT = (".md", ".mdx", ".rst", ".txt", ".adoc")
# Installation, deployment and server administration describe operations, not
# behavior a user can check in the product's interface.
GLOBAL_EXCLUDE = ("install", "deploy", "upgrade", "migrat", "docker", "release", "changelog",
                  "contributing", "development", "developer", "/api", "faq", "translation")
VERSIONISH = re.compile(r"https?://|\bv?\d+\.\d+(\.\d+)?\b|[0-9a-f]{12,}")

RULE_CUES = re.compile(
    r"\b(must|must not|cannot|can't|can not|only|unless|if|when|whenever|automatically|"
    r"no longer|not allowed|not possible|is required|are required|at least|at most|maximum|"
    r"minimum|limit|limited|default|by default|prevent|prevents|reject|rejected|disabled|"
    r"enabled|hidden|visible|deleted|removed|restored|archived|expire|expires|until|before|"
    r"after|instead|overwrit\w*|duplicate\w*|permission\w*|read-only|locked|required)\b",
    re.I,
)
MARKUP = re.compile(r"(`+|\*\*|__|\[|\]\([^)]*\)|<[^>]+>|^[#>*\-+|=~ ]+|:\w+:`[^`]*`|\.\. \w+::.*$)")
STRONG_CUES = re.compile(
    r"\b(must|must not|cannot|can't|can not|only|unless|automatically|no longer|not allowed|"
    r"not possible|is required|are required|at least|at most|maximum|minimum|by default|default|"
    r"prevent\w*|reject\w*|expire\w*|read-only|locked|duplicate\w*|overwrit\w*|permission\w*|"
    r"never|always|instead|disabled|hidden|restored|deleted|archived)\b",
    re.I,
)
MAX_CHANGED_SENTENCES = 4  # larger hunks are rewrites, not one changed rule
MAX_DOC_FILES_PER_COMMIT = 15  # larger commits are reorganizations or translations
SENTENCE = re.compile(r"(?<=[.!?])\s+(?=[A-Z0-9])")


def clean(line: str) -> str:
    text = MARKUP.sub(" ", line)
    return re.sub(r"\s+", " ", text).strip()


def sentences(lines: list[str]) -> list[str]:
    text = " ".join(clean(line) for line in lines)
    return [s.strip() for s in SENTENCE.split(text) if len(s.split()) >= 4]


def git(repo: Path, *args: str) -> str:
    return subprocess.run(["git", "-C", str(repo), *args], capture_output=True, text=True,
                          errors="replace", check=True).stdout


def commits(repo: Path, paths: list[str]) -> list[dict]:
    out = git(repo, "log", "--no-merges", f"--since={SINCE}", f"--until={UNTIL}",
              "--format=%x1e%H%x1f%cs%x1f%s", "-p", "--unified=0", "--no-color", "--", *paths)
    records = []
    for chunk in out.split("\x1e")[1:]:
        header, _, body = chunk.partition("\n")
        sha, date, subject = header.split("\x1f", 2)
        records.append({"sha": sha, "date": date, "subject": subject, "diff": body})
    return records


def hunks(diff: str):
    current_file, removed, added = None, [], []
    for line in diff.splitlines():
        if line.startswith("diff --git"):
            if current_file and (removed or added):
                yield current_file, removed, added
            current_file, removed, added = None, [], []
        elif line.startswith("+++ b/"):
            current_file = line[6:]
        elif line.startswith("@@"):
            if current_file and (removed or added):
                yield current_file, removed, added
            removed, added = [], []
        elif line.startswith("-") and not line.startswith("---"):
            removed.append(line[1:])
        elif line.startswith("+") and not line.startswith("+++"):
            added.append(line[1:])
    if current_file and (removed or added):
        yield current_file, removed, added


def candidates(project: str, repo: Path) -> list[dict]:
    spec = PROJECTS[project]
    found = []
    for commit in commits(repo, spec["paths"]):
        doc_files = {p for p, _, _ in hunks(commit["diff"]) if p.lower().endswith(DOC_EXT)}
        if len(doc_files) > MAX_DOC_FILES_PER_COMMIT:
            continue
        for path, removed, added in hunks(commit["diff"]):
            low = path.lower()
            if (not low.endswith(DOC_EXT) or any(x in low for x in spec["exclude"])
                    or any(x in low for x in GLOBAL_EXCLUDE)):
                continue
            if "```" in "\n".join(removed + added):
                continue
            old, new = sentences(removed), sentences(added)
            gone = [s for s in old if s not in new]
            came = [s for s in new if s not in old]
            if not gone and not came or len(gone) + len(came) > MAX_CHANGED_SENTENCES:
                continue
            old_text, new_text = " ".join(gone), " ".join(came)
            similarity = difflib.SequenceMatcher(None, old_text.lower(), new_text.lower()).ratio()
            numbers_changed = sorted(re.findall(r"\d+", old_text)) != sorted(re.findall(r"\d+", new_text))
            if gone and came and similarity > 0.93 and not numbers_changed:
                continue  # typo or wording polish
            cues_old = {m.lower() for m in RULE_CUES.findall(old_text)}
            cues_new = {m.lower() for m in RULE_CUES.findall(new_text)}
            delta = sorted(cues_old ^ cues_new)
            strong = sorted({m.lower() for m in STRONG_CUES.findall(old_text)}
                            ^ {m.lower() for m in STRONG_CUES.findall(new_text)})
            if numbers_changed and VERSIONISH.search(old_text + " " + new_text):
                numbers_changed = False  # versions, URLs and hashes are not rule quantities
            if not strong and not numbers_changed:
                continue  # no strong rule cue entered or left the text
            found.append({
                "project": project, "commit": commit["sha"], "date": commit["date"],
                "subject": commit["subject"][:160], "file": path,
                "removed": gone[:6], "added": came[:6],
                "cue_delta": delta, "strong_cue_delta": strong, "numbers_changed": numbers_changed,
                "kind": "addition" if not gone else "deletion" if not came else "modification",
                "similarity": round(similarity, 3),
            })
    return found


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--repos", type=Path, required=True, help="directory holding one clone per project")
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--projects", help="comma-separated subset of PROJECTS (default: round-1 projects)")
    args = parser.parse_args()
    selected = args.projects.split(",") if args.projects else list(ROUND_1_PROJECTS)
    unknown = set(selected) - set(PROJECTS)
    if unknown:
        parser.error(f"unknown projects: {sorted(unknown)}")
    rows = []
    for project in selected:
        repo = args.repos / project
        if not (repo / ".git").exists():
            print(f"skip {project}: no clone")
            continue
        found = candidates(project, repo)
        print(f"{project}: {len(found)} candidates")
        rows.extend(found)
    for index, row in enumerate(rows):
        key = f"{row['project']}:{row['commit']}:{row['file']}:{index}"
        row["candidate_id"] = "rc-" + hashlib.sha256(key.encode()).hexdigest()[:12]
    args.out.write_text("".join(json.dumps(r, ensure_ascii=False) + "\n" for r in rows))
    print(f"total {len(rows)}")
    screen = screening_sample(rows, selected)
    args.out.with_name(args.out.stem + "-screening.jsonl").write_text(
        "".join(json.dumps(r, ensure_ascii=False) + "\n" for r in screen))
    print(f"screening sample {len(screen)}")


def screening_sample(rows: list[dict], projects=None) -> list[dict]:
    """Seeded sample of at most SCREEN_CAP_PER_PROJECT candidates per project.

    A fresh generator is seeded for each mining run, so a frame extension mined
    with --projects draws its own sample without touching round 1.
    """
    import random
    rng = random.Random(SCREEN_SEED)
    sample = []
    for project in (projects or ROUND_1_PROJECTS):
        pool = sorted((r for r in rows if r["project"] == project), key=lambda r: r["candidate_id"])
        sample.extend(pool if len(pool) <= SCREEN_CAP_PER_PROJECT else rng.sample(pool, SCREEN_CAP_PER_PROJECT))
    return sample


if __name__ == "__main__":
    main()
