"""Offline rehearsal using literal controls, never provider output or H1/H2 labels."""
from __future__ import annotations

import argparse
from collections import Counter, defaultdict
import json
from pathlib import Path

from label_plane.draft_packets import prepare, sha
from protocol.paired_stats import clustered_bootstrap_ci

IDENTITY = ("run_id", "replication_id", "project_id", "intent_id", "constraint_id")
STATUSES = {"passed", "failed", "runtime_error", "timeout", "rejected", "not_executed", "worker_error"}
CONTROLS = {
    "ARTA-NFR-002": ("def evaluate(authorized):\n    return 'deny'", "def evaluate(authorized):\n    return 'allow'"),
    "ARTA-PEERING-001": ("def evaluate(malicious):\n    return 'reject'", "def evaluate(malicious):\n    return 'allow'"),
    "DEV-ACCESS-001": ("def evaluate(authorized):\n    return 'allow' if authorized else 'deny'", "def evaluate(authorized):\n    return 'allow'"),
}


def key(row):
    values = tuple(row.get(name) for name in IDENTITY)
    if any(not isinstance(value, str) or not value for value in values):
        raise ValueError("complete string identities are required")
    return values


def analyze(plan: list[dict], outcomes: list[dict]) -> dict:
    """Equal project weights; only complete matched execution enters the delta.

    This diagnostic estimator is not the registered confirmatory analysis.
    Positive delta means more violations in the defective arm.
    """
    expected, observed = {}, {}
    for pair in plan:
        identity = key(pair)
        if identity in expected:
            raise ValueError("duplicate planned pair")
        for field in ("oracle_sha256", "configuration_sha256"):
            digest = pair.get(field)
            if not isinstance(digest, str) or len(digest) != 64 or any(c not in "0123456789abcdef" for c in digest):
                raise ValueError("valid frozen-input hashes are required")
        expected[identity] = pair
    for row in outcomes:
        identity, variant = key(row), row.get("variant")
        if identity not in expected or variant not in {"clean", "defective"}:
            raise ValueError("unexpected episode")
        if (identity, variant) in observed:
            raise ValueError("duplicate episode; repetitions must not overwrite")
        if row.get("status") not in STATUSES:
            raise ValueError("unknown execution status")
        if any(row.get(f) != expected[identity][f] for f in ("oracle_sha256", "configuration_sha256")):
            raise ValueError("pair oracle/configuration mismatch")
        observed[identity, variant] = row
    projects, incomplete, counts = defaultdict(list), [], {v: Counter() for v in ("clean", "defective")}
    paired = []
    for identity, pair in expected.items():
        statuses = {v: observed.get((identity, v), {}).get("status", "missing") for v in counts}
        for variant, status in statuses.items():
            counts[variant][status] += 1
        if any(s not in {"passed", "failed"} for s in statuses.values()):
            incomplete.append({**{f: pair[f] for f in IDENTITY}, "statuses": statuses})
            continue
        delta = int(statuses["defective"] == "failed") - int(statuses["clean"] == "failed")
        projects[pair["project_id"]].append(delta)
        paired.append({**{f: pair[f] for f in IDENTITY}, "delta": delta})
    means = {p: sum(v) / len(v) for p, v in sorted(projects.items())}
    interval = clustered_bootstrap_ci(projects, n_boot=2000, seed=0) if len(projects) >= 2 else None
    return {"schema_version": "behavior-paired-diagnostic/v1", "confirmatory_eligible": False,
            "planned_pairs": len(plan), "complete_pairs": len(paired), "incomplete_pairs": incomplete,
            "status_counts": {v: dict(c) for v, c in counts.items()}, "paired_deltas": paired,
            "project_means": means, "project_count": len(means),
            "mean_project_delta": sum(means.values()) / len(means) if means else None,
            "diagnostic_project_bootstrap_ci": interval,
            "interpretation": "Complete-pair diagnostic only; missingness can select the sample. Synthetic intervals do not measure empirical uncertainty. No H1/H2 decision."}


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
    for name, digest in receipt["files"].items():
        path = (output / name).resolve()
        if not path.is_relative_to(output) or sha(path.read_bytes()) != digest:
            raise ValueError("artifact identity mismatch")
    for scenario in ("positive", "null", "reverse"):
        base = output / "analysis" / scenario
        plan = json.loads((base / "plan.json").read_text())
        rows = json.loads((base / "outcomes.json").read_text())
        for row in rows:
            for name, digest in row["artifact_hashes"].items():
                if receipt["files"].get(name) != digest:
                    raise ValueError("episode artifact binding mismatch")
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
