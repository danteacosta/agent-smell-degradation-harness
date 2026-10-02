"""One A/B/C browser case = one JSON config plus a fixture folder.

Replaces the per-case collector scripts (which copied the same schedule,
prompt, admit and run code). A case config in data/abc-cases/<case>.json names
its fixture folder (page.html with one behavior marker, runner.cjs, qualify.py),
the instruction prefix, the three requirement arms, models, repetitions, seed
and the qualified image. Nothing else is case-specific.

  prepare  freeze requests and runtime hashes into a fresh private packet
  run      generate once per slot (no retry, repair or resume), admit, then
           execute every admitted page with the case oracle
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
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

CASES_DIR = ROOT / "data/abc-cases"
ARMS = ("A", "B", "C")
REQUIRED = ("case", "intent_id", "project_id", "fixture", "marker", "instruction", "arms",
            "models", "repetitions", "seed", "image")


class Case:
    def __init__(self, config: dict):
        missing = [k for k in REQUIRED if k not in config]
        if missing:
            raise ValueError(f"case config misses {missing}")
        if set(config["arms"]) != set(ARMS):
            raise ValueError("arms must be exactly A, B and C")
        self.config = config
        self.fixture = ROOT / config["fixture"]
        self.marker = config["marker"]
        page = (self.fixture / "page.html").read_text()
        if page.count(self.marker) != 1:
            raise ValueError("fixture page must contain the behavior marker exactly once")

    @classmethod
    def load(cls, name_or_path: str) -> "Case":
        path = Path(name_or_path)
        if not path.suffix:
            path = CASES_DIR / f"{name_or_path}.json"
        return cls(json.loads(path.read_text()))

    @property
    def name(self) -> str:
        return self.config["case"]

    def prompt(self, arm: str) -> str:
        page = (self.fixture / "page.html").read_text()
        return (self.config["instruction"] + "\n\nRequirement:\n" + self.config["arms"][arm]
                + "\n\nFrozen page:\n" + page)

    def admit(self, raw: str) -> bytes:
        """The scaffold rule every case shares: only the marker may change."""
        from scripts.persistence_collection import html_bytes
        artifact = html_bytes(raw)
        page = (self.fixture / "page.html").read_bytes()
        marker = self.marker.encode()
        prefix, suffix = page.split(marker)
        if suffix.endswith(b"\n") and not artifact.endswith(b"\n"):
            suffix = suffix[:-1]
        if not artifact.startswith(prefix) or not artifact.endswith(suffix):
            raise ValueError("generated output changed frozen scaffold")
        behavior = artifact[len(prefix):len(artifact) - len(suffix)]
        if not behavior.strip() or marker in behavior or b"</script" in behavior.lower():
            raise ValueError("invalid behavior insertion")
        return artifact

    def schedule(self) -> list[dict]:
        rows = []
        for model in self.config["models"]:
            for repetition in range(1, self.config["repetitions"] + 1):
                for arm in ARMS:
                    key = json.dumps([self.name, model, repetition, arm, self.config["seed"]])
                    rows.append({"slot_id": f"{self.name}-" + hashlib.sha256(key.encode()).hexdigest()[:24],
                                 "intent_id": self.config["intent_id"], "project_id": self.config["project_id"],
                                 "model": model, "replication": repetition, "arm": arm})
        random.Random(self.config["seed"]).shuffle(rows)
        return rows

    def runtime_files(self) -> list[Path]:
        return [Path(__file__), self.fixture / "page.html", self.fixture / "runner.cjs", self.fixture / "qualify.py"]


def prepare(case: Case, packet: Path, executable: Path) -> dict:
    from scripts.persistence_collection import hash_file, hash_inventory, put
    if packet.exists() or not packet.is_absolute() or packet.resolve().is_relative_to(ROOT):
        raise ValueError("fresh private destination outside the repository required")
    packet.mkdir(mode=0o700, parents=True)
    rows = case.schedule()
    for path in case.runtime_files():
        put(packet / "frozen/runtime" / path.relative_to(ROOT), path.read_bytes())
    requests = {}
    for row in rows:
        path = packet / "frozen/requests" / (row["slot_id"] + ".json")
        put(path, {"prompt": case.prompt(row["arm"])})
        requests[row["slot_id"]] = hash_file(path)
    manifest = {"schema_version": "abc-case-packet/v1", "case": case.config, "schedule": rows,
                "planned_slots": len(rows), "request_sha256": requests,
                "runtime_sha256": {str(p.relative_to(ROOT)): hash_file(p) for p in case.runtime_files()},
                "executable": str(executable), "billing_mode": "chatgpt_subscription",
                "retry_policy": "no_retry_no_resume_no_repair", "generation_before_browser": True,
                "confirmatory_eligible": False}
    put(packet / "frozen/manifest.json", manifest)
    put(packet / "frozen/receipt.json", {"files": hash_inventory(packet / "frozen")})
    return {"case": case.name, "planned_slots": len(rows)}


def run(packet: Path, provider_factory=None, executor=None) -> dict:
    from scripts.persistence_collection import hash_file, hash_inventory, put, verify_inventory
    verify_inventory(packet / "frozen")
    manifest = json.loads((packet / "frozen/manifest.json").read_text())
    case = Case(manifest["case"])
    if manifest["runtime_sha256"] != {str(p.relative_to(ROOT)): hash_file(p) for p in case.runtime_files()}:
        raise ValueError("runtime drift since freeze")
    if (packet / "run-started.json").exists():
        raise FileExistsError("no resume or retry")
    put(packet / "run-started.json", {"frozen_receipt_sha256": hash_file(packet / "frozen/receipt.json")})
    if provider_factory is None:
        from agents.codex_cli import CodexCLIProvider
        provider_factory = lambda model, evidence: CodexCLIProvider(  # noqa: E731
            executable=manifest["executable"], model=model, timeout_seconds=240, evidence_directory=evidence)
    if executor is None:
        from scripts.kanboard_duplicate_collect import execute

        def executor(inputs: Path, output: Path) -> dict:
            return execute(case.config["image"], inputs, output, case.fixture / "runner.cjs",
                           case.fixture / "qualify.py")
    from agents.providers import ProviderRequest
    rows = [{**row, "category": "not_attempted"} for row in manifest["schedule"]]
    for row in rows:
        sid = row["slot_id"]
        call = packet / "calls" / sid
        request = packet / "frozen/requests" / (sid + ".json")
        if manifest["request_sha256"][sid] != hash_file(request):
            raise ValueError(f"request drift: {sid}")
        put(call / "attempt.json", {"slot_id": sid})
        try:
            raw = provider_factory(row["model"], call / "capture").complete(
                ProviderRequest(json.loads(request.read_text())["prompt"], {}, "opaque", "code"))
        except Exception as error:  # preserved; the run stops like the per-case collectors did
            row.update(category="provider_error", error_type=type(error).__name__)
            break
        put(call / "response.txt", raw.encode())
        try:
            put(packet / "artifacts" / sid / "app.html", case.admit(raw))
            row["generation_valid"] = True
        except (UnicodeError, ValueError) as error:
            row.update(category="invalid_output", invalid_reason=str(error))
    for row in rows:
        if not row.get("generation_valid"):
            continue
        try:
            result = executor(packet / "artifacts" / row["slot_id"], packet / "execution" / row["slot_id"])
        except Exception as error:
            result = {"category": "browser_error", "error_type": type(error).__name__}
        row["category"] = result["category"]
        row["execution"] = result
    counts = {model: {arm: dict(Counter(r["category"] for r in rows if r["model"] == model and r["arm"] == arm))
                      for arm in ARMS} for model in case.config["models"]}
    results = {"schema_version": "abc-case-results/v1", "case": case.name, "planned_slots": len(rows),
               "counts": counts, "rows": rows, "confirmatory_eligible": False}
    put(packet / "results.json", results)
    put(packet / "receipt.json", {"files": hash_inventory(packet)})
    return {"case": case.name, "counts": counts}


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    sub = parser.add_subparsers(dest="mode", required=True)
    p = sub.add_parser("prepare")
    p.add_argument("case", help="case name in data/abc-cases or a path to a config")
    p.add_argument("--packet", type=Path, required=True)
    p.add_argument("--executable", type=Path, default=Path("/opt/homebrew/bin/codex"))
    r = sub.add_parser("run")
    r.add_argument("--packet", type=Path, required=True)
    sub.add_parser("list")
    args = parser.parse_args(argv)
    if args.mode == "list":
        result = sorted(p.stem for p in CASES_DIR.glob("*.json"))
    elif args.mode == "prepare":
        result = prepare(Case.load(args.case), args.packet, args.executable)
    else:
        result = run(args.packet)
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
