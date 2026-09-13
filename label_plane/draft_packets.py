"""Prepare unapproved reviewer drafts, without providers or code execution.

Prompt text is projected from two explicitly allowed fields. Oracle metadata
stays in a separate review directory; exporting never admits a corpus.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

from label_plane.oracle_review import ROOT, PAIRS, TRUSTED_PAIR_HASHES

DRAFTS = [ROOT / "data/oracle_review" / name for name in (
    "nfr-single-deletion-candidate-v1.json",
    "peering-single-deletion-candidate-v1.json",
)]

INTERFACES = {
    "ARTA-NFR-002": ("authorized", "allow", "deny"),
    "ARTA-PEERING-001": ("malicious", "allow", "reject"),
}


def prompt(requirement: str, intent: str) -> str:
    argument, first, second = INTERFACES[intent]
    return (
        "Requirement:\n" + requirement + "\n\n"
        "Shared implementation interface:\n"
        "Implement only the policy-decision component. The Boolean input is an "
        "externally established classification; do not implement a classifier. "
        f"Define a pure Python function evaluate({argument}). "
        f"Return either '{first}' or '{second}' for a Boolean input. "
        "Do not import modules or perform I/O. Return one JSON object with only "
        "the key source_code containing the Python source.\n"
    )


def sha(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


def oracle_diagnostic(oracle: dict, intent: str, constraint: str) -> dict:
    """Enumerate the finite decision tables; compatibility is not correctness."""
    argument, first, second = INTERFACES[intent]
    scored, unscored = oracle["scored_points"], oracle["unscored_points"]
    if not isinstance(scored, list) or not isinstance(unscored, list) or not scored or not unscored:
        raise ValueError("partial oracle needs scored and unspecified regions")
    seen = set()
    for point in scored + unscored:
        value = point.get("input", {})
        if set(value) != {argument} or type(value[argument]) is not bool or value[argument] in seen:
            raise ValueError("oracle inputs must partition the Boolean domain")
        seen.add(value[argument])
    if seen != {False, True}:
        raise ValueError("oracle inputs must partition the Boolean domain")
    if any(p.get("expected_decision") not in (first, second) or p.get("constraint_id") != constraint for p in scored):
        raise ValueError("scored point must bind a legal decision to the target constraint")
    if any("expected_decision" in p for p in unscored):
        raise ValueError("unspecified points cannot supply expected outcomes")
    tables = [{False: left, True: right} for left in (first, second) for right in (first, second)]
    compatible = [table for table in tables if all(table[p["input"][argument]] == p["expected_decision"] for p in scored)]
    return {"scope": "finite_decision_table_check_not_a_model_experiment",
            "possible_tables": len(tables), "compatible_tables": len(compatible),
            "constant_responses_compatible": [table[False] for table in compatible if table[False] == table[True]],
            "full_behavior_validated": False,
            "interpretation": "Compatibility checks only the scored condition; unspecified behavior is not validated."}


def prepare(paths=DRAFTS, pairs_dir=PAIRS) -> dict[str, bytes]:
    """Validate every draft before producing an in-memory output bundle."""
    files, seen, manifest = {}, set(), []
    for path in paths:
        raw = Path(path).read_bytes()
        draft = json.loads(raw)
        intent = draft.get("intent_id")
        if intent not in ("ARTA-NFR-002", "ARTA-PEERING-001") or intent in seen:
            raise ValueError("unknown or duplicate intent")
        seen.add(intent)
        if (draft.get("schema_version") != "source-pair-draft/v1"
                or draft.get("review_status") != "pending_independent_review"
                or draft.get("live_authorized") is not False
                or draft.get("confirmatory_eligible") is not False):
            raise ValueError("only unapproved drafts can be exported")
        legacy = (pairs_dir / (intent.lower() + ".json")).read_bytes()
        if sha(legacy) != TRUSTED_PAIR_HASHES[intent] or draft.get("legacy_pair_sha256") != sha(legacy):
            raise ValueError("legacy source binding mismatch")
        source = json.loads(legacy)["source"]
        if (draft.get("source_revision") != source["dataset_commit"]
                or draft.get("source_record_id") != source["source_record_id"]):
            raise ValueError("source identity mismatch")
        plane, review = draft["generation_plane"], draft["review_plane"]
        if set(plane) != {"clean_requirement", "defective_requirement"}:
            raise ValueError("generation plane contains unexpected metadata")
        if any(not isinstance(s, str) or not s.strip() for s in plane.values()):
            raise ValueError("requirements must be nonempty text")
        removed = review["removed_sentence"]
        if not isinstance(removed, str) or not removed.strip() or plane["clean_requirement"] != plane["defective_requirement"] + " " + removed:
            raise ValueError("draft must be an exact single-sentence deletion")
        oracle = review["common_oracle"]
        diagnostic = oracle_diagnostic(oracle, intent, review["target_constraint_id"])
        for variant, field in (("clean", "clean_requirement"), ("defective", "defective_requirement")):
            files[f"generation/{intent}/{variant}.txt"] = prompt(plane[field], intent).encode()
        files[f"review/{intent}.json"] = (json.dumps(draft, indent=2, sort_keys=True) + "\n").encode()
        manifest.append({"intent_id": intent, "candidate_sha256": sha(raw),
                         "common_oracle_sha256": sha(json.dumps(oracle, sort_keys=True).encode()),
                         "oracle_scope_diagnostic": diagnostic})
    if not seen:
        raise ValueError("no candidates")
    receipt = {"schema_version": "draft-packet-receipt/v1", "review_status": "pending_independent_review",
               "live_authorized": False, "confirmatory_eligible": False,
               "scope": "review_preparation_only_not_a_frozen_experiment",
               "candidates": manifest, "files": {name: sha(raw) for name, raw in files.items()}}
    files["review/receipt.json"] = (json.dumps(receipt, indent=2, sort_keys=True) + "\n").encode()
    return files


def export(output: Path, paths=DRAFTS) -> dict:
    files = prepare(paths)  # No directory is created for invalid input.
    output = Path(output)
    output.mkdir(mode=0o700, parents=False, exist_ok=False)
    for name, raw in files.items():
        target = output / name
        target.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
        with target.open("xb") as stream:
            stream.write(raw)
        target.chmod(0o600)
    return {"status": "drafts_prepared", "file_count": len(files),
            "live_authorized": False, "confirmatory_eligible": False}


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", required=True, type=Path, help="new directory under an existing private parent")
    args = parser.parse_args()
    print(json.dumps(export(args.output), sort_keys=True))
