"""Independent pre-generation review of the OpenProject invalid-save instrument."""
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

FIXTURE = ROOT / "eval/fixtures/openproject-invalid-remaining"
SOURCE = ROOT / "data/e2e-six-projects/sources/openproject/progress-tracking.md"
ARMS = ROOT / "data/e2e-openproject-invalid-remaining/arms-20260926.json"
QUALIFICATION = Path("/Users/dantecosta/Documents/GitHub/.private-research-evidence/openproject-invalid-remaining-qualification-20260926-v1")
OUTPUT = Path("/Users/dantecosta/Documents/GitHub/.private-research-evidence/openproject-invalid-remaining-review-20260926-v1")
MODELS = ("gpt-6-luna", "gpt-6-sol", "gpt-6-astra")


def request() -> str:
    source = SOURCE.read_text().split("### Work-based progress reporting", 1)[1][:6000]
    return ("You are an independent methods reviewer before any experimental generation. "
            "No generated outcomes are available. Return only a JSON object with keys verdict "
            "(ACCEPT or DEFER) and reasons (list of concise strings). DEFER for a material "
            "source-to-endpoint mismatch, A/B nonequivalence, C deleting more or less than one "
            "obligation, target leakage through the common page, unassessable interfaces scored "
            "as defects, or target/non-target confusion. The common Save button only calls "
            "the model's handler; only model code can call app.persist. The browser first "
            "checks a valid save, then tries an invalid Remaining work value and reloads. "
            "Assess whether valid saving and Work preservation are sound non-target controls, "
            "whether rejection is actually observed, and whether not asserting the displayed "
            "error message narrows the endpoint appropriately. Do not infer effects "
            "from authored qualification cases.\n\nSOURCE EXCERPT:\n" + source + "\n\n"
            "A/B/C REQUIREMENTS:\n" + ARMS.read_text() + "\n\n"
            "COMMON PAGE (the model replaces only MODEL_BEHAVIOR):\n" + (FIXTURE / "page.html").read_text() + "\n\n"
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
