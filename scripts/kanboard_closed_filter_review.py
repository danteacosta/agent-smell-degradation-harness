"""Independent pre-generation review of the Kanboard Closed tasks filter instrument."""
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

FIXTURE = ROOT / "eval/fixtures/kanboard-closed-filter"
SOURCE = ROOT / "data/e2e-six-projects/sources/kanboard/tasks.md"
ARMS = ROOT / "data/e2e-kanboard-closed-filter/arms-20260927.json"
QUALIFICATION = Path("/Users/dantecosta/Documents/GitHub/.private-research-evidence/kanboard-closed-filter-qualification-20260927-v1")
OUTPUT = Path("/Users/dantecosta/Documents/GitHub/.private-research-evidence/kanboard-closed-filter-review-20260927-v1")
MODELS = ("gpt-6-luna", "gpt-6-sol", "gpt-6-astra")


def request() -> str:
    source = SOURCE.read_text().split("Closing Tasks", 1)[1].split("There are two ways", 1)[0]
    return ("You are an independent methods reviewer before experimental generation. "
            "No generated outcomes are available. Return only JSON with verdict (ACCEPT or DEFER) "
            "and reasons (list of concise strings). DEFER for material source-to-endpoint mismatch, "
            "A/B nonequivalence, C deleting more or less than one obligation, target behavior "
            "supplied by the common page, unassessable interface scored as target failure, or "
            "target/non-target confusion. This replaces an earlier deferred instrument that "
            "combined closing a task, hiding it from the board, and retrieving it with the "
            "Closed tasks filter. The new fixture starts with one open and one already closed "
            "task; it tests the board view as a control and scores only whether selecting "
            "Closed tasks visibly retrieves the closed task. The common page renders exactly "
            "the items provided by model code and does not filter. Two task/title fixtures "
            "counter hardcoding. Assess this narrowed endpoint on its own merits, not the "
            "earlier instrument. Do not infer effects from authored qualification cases.\n\n"
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
