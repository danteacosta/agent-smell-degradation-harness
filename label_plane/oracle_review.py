"""Offline sensitivity audit of hash-pinned, checked-in reference fixtures.

No provider or arbitrary source-code input is accepted. Candidate decisions are
unreviewed hypotheses about oracle scope, never labels or live-run permission.
"""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
CANDIDATE = ROOT / "data/oracle_review/candidate-v1.json"
PAIRS = ROOT / "data/pairs/discovery"
# Execution is restricted to these audited historical files, even if a caller
# supplies a different candidate and pair directory. A candidate cannot grant
# itself permission to execute arbitrary code by hashing its own payload.
TRUSTED_PAIR_HASHES = {
    "ARTA-GAMMA-002": "6e5a6210fabec872f36ed02b77c97f71a9672ffba490875778d8506140821527",
    "ARTA-ERTMS-002": "a03ef54be88ec59c5586de30613c29b0ebdcefe265dd6b8382129c14240317c0",
    "ARTA-NFR-002": "11b7591cda491012f8399c4af3a5148218355753f0b25af23c5ab2e9d0f4827c",
    "ARTA-PEERING-001": "98cf6caa80ecd4df6fa233b1ebdeeff6ab22311fdc6a19e09e5e8f98923f6916",
}


def digest(value: Any) -> str:
    return hashlib.sha256(
        json.dumps(value, sort_keys=True, separators=(",", ":"), allow_nan=False).encode()
    ).hexdigest()


def prepare(candidate: dict, pairs_dir: Path = PAIRS) -> list[tuple[dict, dict]]:
    """Validate the entire inventory before executing any reference."""
    if (
        not isinstance(candidate, dict)
        or candidate.get("schema_version") != "partial-oracle-review/v1"
        or candidate.get("review_status") != "pending_independent_review"
        or candidate.get("evidence_scope") != "offline_reference_sensitivity_only"
    ):
        raise ValueError("unsupported candidate schema, scope or review status")
    records = candidate.get("cases")
    if not isinstance(records, list) or not records:
        raise ValueError("candidate must contain cases")
    available = {p.stem.upper(): p for p in pairs_dir.glob("arta-*.json")}
    prepared, seen = [], set()
    for record in records:
        if not isinstance(record, dict):
            raise ValueError("invalid candidate record")
        intent = record.get("intent_id")
        if not isinstance(intent, str) or intent not in available or intent in seen:
            raise ValueError("unknown or duplicate candidate intent")
        seen.add(intent)
        if intent not in TRUSTED_PAIR_HASHES or record.get("pair_sha256") != TRUSTED_PAIR_HASHES[intent]:
            raise ValueError("reference is outside the trusted historical inventory")
        raw = available[intent].read_bytes()
        if hashlib.sha256(raw).hexdigest() != record.get("pair_sha256"):
            raise ValueError("candidate pair hash mismatch")
        case = json.loads(raw)
        if case["intent_id"] != intent or digest(case["oracle_spec"]) != record.get("oracle_sha256"):
            raise ValueError("candidate oracle identity mismatch")
        execution = case["oracle_spec"]["behavior_codegen"]["_execution"]
        ids = [test["id"] for test in execution["hidden_tests"]]
        decisions = record.get("decisions")
        if (
            len(ids) != len(set(ids))
            or not isinstance(decisions, dict)
            or set(decisions) != set(ids)
            or any(value not in ("retain", "unspecified") for value in decisions.values())
            or "retain" not in decisions.values()
        ):
            raise ValueError("each test needs one explicit decision and at least one retained point")
        if not isinstance(record.get("rationale"), str) or not record["rationale"].strip():
            raise ValueError("candidate rationale is required")
        refs = execution.get("reference_implementations", {})
        if any(not isinstance(refs.get(name), str) for name in ("clean", "smelly_plausible")):
            raise ValueError("missing checked-in reference")
        prepared.append((record, case))
    return prepared


def run_reference_audit(candidate: dict, pairs_dir: Path = PAIRS) -> dict:
    prepared = prepare(candidate, pairs_dir)
    # Only the hash-bound checked-in source is passed to the trusted fixture
    # executor. This utility must never be wired into generated-code execution.
    from eval.codegen_sandbox import evaluate_trusted_fixture
    from eval.task_adapters import BehavioralCodeGenerationAdapter

    results = []
    for record, case in prepared:
        execution = case["oracle_spec"]["behavior_codegen"]["_execution"]
        tests = BehavioralCodeGenerationAdapter._hidden_tests(execution)
        retained = [t for t in tests if record["decisions"][t["id"]] == "retain"]
        unscored = [t["id"] for t in tests if record["decisions"][t["id"]] == "unspecified"]
        oracle_hash = digest({"pair_sha256": record["pair_sha256"], "tests": retained,
                              "unspecified_test_ids": unscored})
        references = {}
        for name in ("clean", "smelly_plausible"):
            source = execution["reference_implementations"][name]
            legacy = evaluate_trusted_fixture(source, tests)
            partial = evaluate_trusted_fixture(source, retained)
            complete = (
                partial["status"] in {"passed", "failed"}
                and len(partial["cases"]) == len(retained)
                and not partial["errors"]
            )
            status = "execution_incomplete"
            if complete:
                status = "violated_candidate_condition" if partial["failed"] else "compatible_on_checked_points"
            references[name] = {
                "source_sha256": hashlib.sha256(source.encode()).hexdigest(),
                "candidate_oracle_sha256": oracle_hash,
                "legacy_status": legacy["status"],
                "candidate_status": status,
                "checked_points": len(partial["cases"]),
                "retained_points": len(retained),
                "violations": partial["failed"],
                "execution_errors": partial["errors"],
                "unscored_test_ids": unscored,
            }
        left, right = references["clean"], references["smelly_plausible"]
        # An execution failure cannot become a zero-violation or null-effect claim.
        comparable = all(r["candidate_status"] != "execution_incomplete" for r in references.values())
        legacy_comparable = all(r["legacy_status"] in {"passed", "failed"} for r in references.values())
        results.append({
            "intent_id": case["intent_id"], "project_id": case["project_id"],
            "pair_sha256": record["pair_sha256"], "legacy_oracle_sha256": record["oracle_sha256"],
            "candidate_oracle_sha256": oracle_hash, "references": references,
            "legacy_reference_contrast": (
                left["legacy_status"] == "passed" and right["legacy_status"] == "failed"
            ) if legacy_comparable else None,
            "candidate_reference_contrast": (
                left["candidate_status"] == "compatible_on_checked_points"
                and right["candidate_status"] == "violated_candidate_condition"
            ) if comparable else None,
        })
    return {
        "schema_version": "partial-oracle-reference-audit/v1",
        "candidate_sha256": digest(candidate),
        "review_status": "pending_independent_review",
        "evidence_scope": "offline_reference_sensitivity_only",
        "live_authorized": False, "confirmatory_eligible": False,
        "case_count": len(results), "reference_count": 2 * len(results),
        "interpretation": "Unspecified points are unscored, never correct negatives. No model effect, prevalence or semantic accuracy is estimated.",
        "cases": results,
    }


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, help="Optional new report; existing files are never overwritten")
    args = parser.parse_args(argv)
    # Deliberately no candidate/source override or provider flag in the CLI.
    report = run_reference_audit(json.loads(CANDIDATE.read_text()))
    text = json.dumps(report, indent=2, sort_keys=True) + "\n"
    if args.output:
        with args.output.open("x", encoding="utf-8") as handle:
            handle.write(text)
    else:
        print(text, end="")


if __name__ == "__main__":
    main()
