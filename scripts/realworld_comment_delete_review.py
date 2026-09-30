"""Independent pre-generation review of the RealWorld comment Delete instrument."""
from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from agents.codex_cli import CodexCLIProvider
from agents.providers import ProviderRequest
from scripts.persistence_collection import hash_inventory, put

FIXTURE = ROOT / "eval/fixtures/realworld-comment-delete"
SOURCE = ROOT / "data/criteria-expansion/sources/realworld/docs__src__content__docs__specifications__frontend__routing.md"
ARMS = ROOT / "data/e2e-realworld-comment-delete/arms-20260927.json"
QUALIFICATION = Path("/Users/dantecosta/Documents/GitHub/.private-research-evidence/realworld-comment-delete-qualification-20260927-v2")
OUTPUT = Path("/Users/dantecosta/Documents/GitHub/.private-research-evidence/realworld-comment-delete-review-20260927-v1")
MODELS = ("gpt-6-luna", "gpt-6-sol", "gpt-6-astra")


def request() -> str:
    source = SOURCE.read_text().split("- Article page", 1)[1].split("- Profile page", 1)[0]
    return ("You are an independent methods reviewer before experimental generation. "
            "No generated outcomes are available. Return only JSON with verdict (ACCEPT or DEFER) "
            "and reasons (list of concise strings). DEFER for material source-to-endpoint mismatch, "
            "A/B nonequivalence, C deleting more or less than one obligation, target behavior "
            "supplied by the common page, unassessable interface scored as target failure, or "
            "target/non-target confusion. The common page renders a frozen comment and viewer "
            "identity but does not add or hide the Delete button. The generated handler owns "
            "visibility. The browser compares a comment author and a different authenticated "
            "viewer in separate contexts, in two ID/name fixtures. The source only requires "
            "author-only visibility, not actual deletion. Do not infer experimental effects "
            "from authored qualification cases.\n\n"
            "SOURCE EXCERPT:\n" + source + "\n\nA/B/C REQUIREMENTS:\n" + ARMS.read_text() + "\n\n"
            "COMMON PAGE:\n" + (FIXTURE / "page.html").read_text() + "\n\n"
            "BROWSER ORACLE:\n" + (FIXTURE / "runner.cjs").read_text() + "\n\n"
            "QUALIFICATION CASE CATEGORIES:\n" + (QUALIFICATION / "qualification.json").read_text())


def review(model: str, executable: Path) -> dict:
    if model not in MODELS:
        raise ValueError("unknown reviewer")
    target = OUTPUT / model
    if target.exists():
        raise FileExistsError("review already attempted")
    prompt = request()
    put(target / "request.txt", prompt.encode())
    provider = CodexCLIProvider(executable=str(executable), model=model, timeout_seconds=240,
                                evidence_directory=target / "capture")
    raw = provider.complete(ProviderRequest(prompt, {}, "opaque", "judge"))
    put(target / "response.txt", raw.encode())
    put(target / "provider-metadata.json", provider.last_call_metadata)
    try:
        parsed = json.loads(raw)
    except json.JSONDecodeError:
        parsed = {"verdict": "INVALID", "reasons": ["malformed JSON"]}
    if (parsed.get("verdict") not in ("ACCEPT", "DEFER") or
            not isinstance(parsed.get("reasons"), list) or
            not all(isinstance(reason, str) for reason in parsed["reasons"])):
        parsed = {"verdict": "INVALID", "reasons": ["invalid schema"]}
    put(target / "parsed.json", parsed)
    return parsed


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("model", choices=MODELS)
    parser.add_argument("--executable", type=Path, default=Path("/opt/homebrew/bin/codex"))
    args = parser.parse_args()
    result = review(args.model, args.executable)
    if all((OUTPUT / model / "parsed.json").exists() for model in MODELS):
        put(OUTPUT / "receipt.json", {"files": hash_inventory(OUTPUT)})
    print(json.dumps(result))
