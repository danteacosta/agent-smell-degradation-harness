"""Independent pre-generation review of the Nextcloud restore instrument."""
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

FIXTURE = ROOT / "eval/fixtures/nextcloud-restore-conflict-v4"
SOURCE = ROOT / "data/e2e-six-projects/sources/nextcloud/deleted_file_management.rst"
ARMS = ROOT / "data/e2e-nextcloud-restore-conflict/arms-20260926.json"
QUALIFICATION = Path("/Users/dantecosta/Documents/GitHub/.private-research-evidence/nextcloud-restore-conflict-qualification-20260927-v4")
OUTPUT = Path("/Users/dantecosta/Documents/GitHub/.private-research-evidence/nextcloud-restore-conflict-review-20260927-v4b")
MODELS = ("gpt-6-luna", "gpt-6-sol", "gpt-6-astra")


def request() -> str:
    source = SOURCE.read_text().split("Quotas", 1)[0]
    return ("You are an independent methods reviewer before any experimental generation. "
            "No generated outcomes are available. The bounded page has explicit directory "
            "path and writability, active file paths and deleted original paths. The oracle "
            "checks uniqueness against every active file name in that directory after reload. "
            "Return only a JSON object with keys verdict "
            "(ACCEPT or DEFER) and reasons (list of concise strings). DEFER for any material "
            "source-to-endpoint mismatch, A/B nonequivalence, C deleting more or less than one "
            "obligation, target leakage through the common interface, unassessable cases being "
            "misclassified as defects, or an oracle that fails to distinguish target and "
            "non-target failures. Do not require a prescribed suffix: the source only requires "
            "a unique name. Do not infer results from qualification controls.\n\n"
            "SOURCE EXCERPT:\n" + source + "\n\n"
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
