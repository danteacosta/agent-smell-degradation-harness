"""Offline cross-check of the pre-pilot plan's corpus declarations against the manifest.

``eval.prepilot_readiness`` accepts ``corpus.unique_intents``, ``all_sources_licensed``
and similar flags as self-declared values. This audit re-derives them from the
manifest file so a stale or optimistic declaration is visible. It never sets a
flag, approves a gate, calls a provider, or reads raw requirement text.

Findings are descriptive. In particular, ``llm_only_manipulation_review`` is a
warning, not a verdict: whether an LLM-only panel is acceptable before the
human 20% audit is a methodological decision for the advisor.
"""

from __future__ import annotations

import argparse
import json
from collections import Counter
from pathlib import Path
from typing import Any, Mapping

SCHEMA_VERSION = "corpus-declaration-audit/v1"
_REQUIRED_RIGHTS = ("derivative_use_allowed", "external_provider_processing_allowed")
_MANIPULATION_FLAGS = (
    "clean_variant_realistic",
    "constraint_independently_auditable",
    "defect_present",
    "intent_preserved",
    "no_secondary_defect",
)


def audit_corpus_declarations(plan: Mapping[str, Any], manifest: Mapping[str, Any]) -> dict[str, Any]:
    corpus = plan.get("corpus")
    corpus = corpus if isinstance(corpus, Mapping) else {}
    records = manifest.get("records")
    records = [r for r in records if isinstance(r, Mapping)] if isinstance(records, list) else []
    discrepancies: list[str] = []
    warnings: list[str] = []

    intent_ids = [str(r.get("source_intent_id", "")).strip() for r in records]
    unique_intents = len({i for i in intent_ids if i})
    duplicated = sorted(i for i, n in Counter(intent_ids).items() if i and n > 1)
    if duplicated:
        discrepancies.append(f"duplicate source_intent_id values: {duplicated}")
    declared = corpus.get("unique_intents")
    if isinstance(declared, bool) or not isinstance(declared, int) or declared != unique_intents:
        discrepancies.append(
            f"plan declares unique_intents={declared!r} but manifest has {unique_intents}"
        )
    if manifest.get("record_count") != len(records):
        discrepancies.append("manifest record_count disagrees with its records")

    if corpus.get("all_project_ids_present") is True and any(
        not str(r.get("project_id", "")).strip() for r in records
    ):
        discrepancies.append("plan declares all_project_ids_present but a record lacks project_id")
    if corpus.get("all_sources_licensed") is True:
        for r in records:
            rights = r.get("rights_review") if isinstance(r.get("rights_review"), Mapping) else {}
            if not str(r.get("license", "")).strip() or not str(r.get("license_evidence_url", "")).strip():
                discrepancies.append(f"{r.get('source_intent_id')}: missing license or evidence URL")
            elif any(rights.get(k) is not True for k in _REQUIRED_RIGHTS):
                discrepancies.append(f"{r.get('source_intent_id')}: rights review does not allow derivative/provider use")
    if corpus.get("near_clone_screening_complete") is True and any(
        r.get("near_clone_reviewed") is not True for r in records
    ):
        discrepancies.append("plan declares near-clone screening complete but a record is unreviewed")
    if corpus.get("manipulation_checks_complete") is True:
        for r in records:
            check = r.get("manipulation_check") if isinstance(r.get("manipulation_check"), Mapping) else {}
            if any(check.get(k) is not True for k in _MANIPULATION_FLAGS):
                discrepancies.append(f"{r.get('source_intent_id')}: manipulation check incomplete or failed")

    reviewers = {
        str((r.get("manipulation_check") or {}).get("reviewer_id", ""))
        for r in records
        if isinstance(r.get("manipulation_check"), Mapping)
    }
    if reviewers and all(x.startswith("llm") or "panel" in x for x in reviewers):
        warnings.append(
            "llm_only_manipulation_review: every manipulation check is by an LLM panel "
            f"({sorted(reviewers)}); human audit and independence remain open decisions"
        )
    projects = len({str(r.get("project_id", "")) for r in records if r.get("project_id")})
    if projects != manifest.get("project_count"):
        discrepancies.append("manifest project_count disagrees with records")
    per_project = Counter(str(r.get("project_id", "")) for r in records if r.get("project_id"))
    max_share = round(max(per_project.values()) / len(records), 4) if per_project and records else 0.0
    removed = [str(r.get("removed_constraint_id", "")).strip() for r in records]
    if any(not c for c in removed) or len(set(removed)) != len(removed):
        discrepancies.append("removed_constraint_id is missing or shared between records")
    if records and max_share > 0.5:
        warnings.append(
            f"project_concentration: one project holds {max_share:.0%} of records; "
            "project-level split and clustered bootstrap would be fragile"
        )
    if records:
        warnings.append(
            "single_constraint_load: each record removes exactly one constraint, so the corpus "
            "cannot probe constraint accumulation (cf. Constraint Decay, COLM 2026); a descriptive "
            "limitation, not a defect"
        )
    return {
        "schema_version": SCHEMA_VERSION,
        "claim_level": "non_confirmatory_pre_pilot",
        "consistent": not discrepancies,
        "discrepancies": discrepancies,
        "warnings": warnings,
        "derived": {
            "unique_intents": unique_intents,
            "projects": projects,
            "records": len(records),
            "max_project_share": max_share,
            "defect_family_counts": dict(sorted(Counter(str(r.get("defect_family", "")) for r in records).items())),
        },
        "approves_nothing": True,
    }


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--plan", type=Path, default=Path("data/prepilot/launch-plan.candidate.json"))
    p.add_argument("--manifest", type=Path)
    a = p.parse_args(argv)
    plan = json.loads(a.plan.read_text(encoding="utf-8"))
    manifest_path = a.manifest or Path(plan["corpus"]["manifest_path"])
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    report = audit_corpus_declarations(plan, manifest)
    print(json.dumps(report, indent=2, sort_keys=True))
    return 0 if report["consistent"] else 2


if __name__ == "__main__":
    raise SystemExit(main())
