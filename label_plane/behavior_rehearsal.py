"""Offline rehearsal using literal controls, never provider output or H1/H2 labels."""
from __future__ import annotations

import argparse
import json
from pathlib import Path

from label_plane.draft_packets import prepare, sha
from label_plane.behavior_pairs import analyze, key

CONTROLS = {
    "ARTA-NFR-002": ("def evaluate(authorized):\n    return 'deny'", "def evaluate(authorized):\n    return 'allow'"),
    "ARTA-PEERING-001": ("def evaluate(malicious):\n    return 'reject'", "def evaluate(malicious):\n    return 'allow'"),
    "DEV-ACCESS-001": ("def evaluate(authorized):\n    return 'allow' if authorized else 'deny'", "def evaluate(authorized):\n    return 'allow'"),
}


def encode(value):
    return (json.dumps(value, indent=2, sort_keys=True) + "\n").encode()


def rehearse(output: Path) -> dict:
    """Three scenarios, two source drafts and one original development contract."""
    from eval.codegen_sandbox import evaluate_trusted_fixture

    packet = prepare()
    # An original fully specified development contract; not an ARTA repair or corpus admission.
    scaffold = "\nDefine a pure Python function evaluate(authorized) for Boolean input. Return 'allow' or 'deny'. Return JSON with only source_code. Do not import modules or perform I/O.\n"
    for variant, requirement in (
        ("clean", "Allow authorized users. Deny unauthorized users."),
        ("defective", "Allow authorized users."),
    ):
        packet[f"generation/DEV-ACCESS-001/{variant}.txt"] = (requirement + scaffold).encode()
    packet["review/DEV-ACCESS-001.json"] = encode({
        "evidence_scope": "original_development_contract_not_source_derived",
        "confirmatory_eligible": False, "live_authorized": False,
        "executor_test_draft": {"hidden_tests": [
            {"id": "authorized", "constraint_id": "DEV-access-policy", "kwargs": {"authorized": True}, "expected": "allow"},
            {"id": "unauthorized", "constraint_id": "DEV-access-policy", "kwargs": {"authorized": False}, "expected": "deny"},
        ]},
    })
    files, all_summaries = dict(packet), {}
    configuration = sha(b"literal-controls/v1;two-repetitions;no-provider;trusted-fixture")
    for scenario in ("positive", "null", "reverse"):
        plan, outcomes = [], []
        for intent, (good, bad) in CONTROLS.items():
            review = json.loads(packet[f"review/{intent}.json"])
            tests = review["executor_test_draft"]["hidden_tests"]
            for replication in ("r1", "r2"):
                pair = {"run_id": "synthetic-" + scenario, "replication_id": replication,
                        "project_id": "synthetic-" + intent, "intent_id": intent,
                        "constraint_id": tests[0]["constraint_id"], "oracle_sha256": sha(encode(tests)),
                        "configuration_sha256": configuration}
                plan.append(pair)
                for variant in ("clean", "defective"):
                    # Only these checked-in literal controls can reach the trusted executor.
                    wrong = (scenario == "positive" and variant == "defective") or (scenario == "reverse" and variant == "clean")
                    source = bad if wrong else good
                    response = {"source_code": source}
                    decoded = json.loads(encode(response))["source_code"]
                    if decoded not in CONTROLS[intent]:
                        raise ValueError("source outside literal control inventory")
                    report = evaluate_trusted_fixture(decoded, tests)
                    prefix = f"episodes/{scenario}/{intent}/{replication}/{variant}"
                    artifacts = {"prompt.txt": packet[f"generation/{intent}/{variant}.txt"],
                                 "response.json": encode(response), "code.py": decoded.encode(),
                                 "oracle.json": encode(tests), "execution.json": encode(report)}
                    for name, raw in artifacts.items():
                        files[f"{prefix}/{name}"] = raw
                    outcomes.append({**pair, "variant": variant, "status": report["status"],
                                     "artifact_hashes": {f"{prefix}/{n}": sha(b) for n, b in artifacts.items()}})
        summary = analyze(plan, outcomes)
        all_summaries[scenario] = summary
        for name, value in (("plan", plan), ("outcomes", outcomes), ("analysis", summary)):
            files[f"analysis/{scenario}/{name}.json"] = encode(value)
    receipt = {"schema_version": "behavior-rehearsal/v1", "evidence_scope": "literal_fixture_pipeline_only",
               "live_authorized": False, "confirmatory_eligible": False,
               "files": {n: sha(b) for n, b in files.items()}}
    output = Path(output)
    output.mkdir(mode=0o700, parents=False, exist_ok=False)
    for name, raw in {**files, "receipt.json": encode(receipt)}.items():
        path = output / name
        path.parent.mkdir(mode=0o700, parents=True, exist_ok=True)
        with path.open("xb") as handle:
            handle.write(raw)
        path.chmod(0o600)
    return {"episodes": 3 * len(CONTROLS) * 2 * 2, "scenarios": {s: a["mean_project_delta"] for s, a in all_summaries.items()},
            "files": len(files) + 1, "live_authorized": False, "confirmatory_eligible": False}


def verify(output: Path) -> dict:
    output = Path(output).resolve()
    receipt = json.loads((output / "receipt.json").read_text())
    if (receipt.get("schema_version") != "behavior-rehearsal/v1"
            or receipt.get("evidence_scope") != "literal_fixture_pipeline_only"
            or receipt.get("live_authorized") is not False
            or receipt.get("confirmatory_eligible") is not False):
        raise ValueError("unsupported rehearsal receipt or eligibility")
    scenarios = ("positive", "null", "reverse")
    variants = ("clean", "defective")
    artifacts = ("prompt.txt", "response.json", "code.py", "oracle.json", "execution.json")
    inventory = {"review/receipt.json"}
    for intent in CONTROLS:
        inventory.add(f"review/{intent}.json")
        inventory.update(f"generation/{intent}/{v}.txt" for v in variants)
        for scenario in scenarios:
            for replication in ("r1", "r2"):
                for variant in variants:
                    inventory.update(f"episodes/{scenario}/{intent}/{replication}/{variant}/{n}" for n in artifacts)
    inventory.update(f"analysis/{s}/{n}.json" for s in scenarios for n in ("plan", "outcomes", "analysis"))
    if set(receipt.get("files", {})) != inventory:
        raise ValueError("incomplete or unexpected artifact inventory")
    for name, digest in receipt["files"].items():
        path = (output / name).resolve()
        if not path.is_relative_to(output) or sha(path.read_bytes()) != digest:
            raise ValueError("artifact identity mismatch")
    # Cache only small shared metadata, not all episode artifacts in memory.
    reviews = {intent: json.loads((output / "review" / (intent + ".json")).read_text())
               for intent in CONTROLS}
    prompts = {(intent, variant): (output / "generation" / intent / (variant + ".txt")).read_bytes()
               for intent in CONTROLS for variant in variants}
    for scenario in scenarios:
        base = output / "analysis" / scenario
        plan = json.loads((base / "plan.json").read_text())
        rows = json.loads((base / "outcomes.json").read_text())
        expected_pairs = {(f"synthetic-{scenario}", rep, f"synthetic-{intent}", intent)
                          for intent in CONTROLS for rep in ("r1", "r2")}
        if ({key(p)[:4] for p in plan} != expected_pairs or len(plan) != len(expected_pairs)
                or len(rows) != 2 * len(plan)):
            raise ValueError("incomplete planned rehearsal inventory")
        for row in rows:
            prefix = f"episodes/{scenario}/{row['intent_id']}/{row['replication_id']}/{row['variant']}"
            if set(row["artifact_hashes"]) != {f"{prefix}/{n}" for n in artifacts}:
                raise ValueError("incomplete episode artifact binding")
            for name, digest in row["artifact_hashes"].items():
                if receipt["files"].get(name) != digest:
                    raise ValueError("episode artifact binding mismatch")
            location = output / prefix
            code = (location / "code.py").read_text()
            response = json.loads((location / "response.json").read_text())
            execution = json.loads((location / "execution.json").read_text())
            oracle = (location / "oracle.json").read_bytes()
            parsed_oracle = json.loads(oracle)
            review = reviews[row["intent_id"]]
            if (response != {"source_code": code} or execution.get("status") != row["status"]
                    or sha(oracle) != row["oracle_sha256"]
                    or parsed_oracle != review["executor_test_draft"]["hidden_tests"]
                    or any(t.get("constraint_id") != row["constraint_id"] for t in parsed_oracle)
                    or (location / "prompt.txt").read_bytes() != prompts[row["intent_id"], row["variant"]]):
                raise ValueError("episode content binding mismatch")
        if encode(analyze(plan, rows)) != (base / "analysis.json").read_bytes():
            raise ValueError("analysis is not reproducible")
    return {"verified_files": len(receipt["files"]), "analysis_recomputed": 3,
            "scope": "internal_consistency_not_independent_authentication"}


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument("--verify-only", action="store_true")
    args = parser.parse_args()
    if args.verify_only:
        print(json.dumps(verify(args.output), sort_keys=True))
    else:
        print(json.dumps({**rehearse(args.output), "verification": verify(args.output)}, sort_keys=True))
