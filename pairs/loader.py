from __future__ import annotations
from pathlib import Path
import json

DEFAULT_PAIRS_DIR = Path(__file__).resolve().parents[1] / "data" / "pairs"

def load_all_pairs(pairs_dir: Path | str = DEFAULT_PAIRS_DIR) -> list[dict]:
    root = Path(pairs_dir)
    out = []
    for path in sorted(root.glob("*.json")):
        with path.open(encoding="utf-8") as f:
            out.append(json.load(f))
    return out

def list_intent_ids(pairs: list[dict]) -> list[str]:
    return [p["intent_id"] for p in pairs]
