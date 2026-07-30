from __future__ import annotations

from typing import Any

MUTANTS_BY_INTENT: dict[str, list[dict[str, Any]]] = {
    "RF-04": [{"order_id_pattern": r"^P-\d+$"}],
    "RF-07": [{"sort_key": "order_code"}],
    "RF-09": [
        {"delay_threshold_minutes": 5, "comparator": ">="},
        {"delay_threshold_minutes": 4, "comparator": ">"},
    ],
    "RF-11": [{"refund_window_minutes": 15}],
    "RF-13": [{"cardinality": 10, "selection": "oldest_active"}],
}


def _delayed(minutes: int, threshold: int, comparator: str) -> bool:
    return minutes >= threshold if comparator == ">=" else minutes > threshold


def artifact_detects_mutant(
    test_artifact: dict[str, Any],
    codegen_mutant: dict[str, Any],
    clean_codegen: dict[str, Any],
) -> bool:
    if "delay_threshold_minutes" in clean_codegen:
        clean_threshold = int(clean_codegen["delay_threshold_minutes"])
        mutant_threshold = int(codegen_mutant.get("delay_threshold_minutes", clean_threshold))
        clean_comparator = clean_codegen.get("comparator", ">")
        mutant_comparator = codegen_mutant.get("comparator", clean_comparator)
        rejected = set(test_artifact.get("must_reject_minutes", []))
        accepted = set(test_artifact.get("must_accept_minutes", []))
        for minute in range(max(clean_threshold, mutant_threshold) + 3):
            clean = _delayed(minute, clean_threshold, clean_comparator)
            mutant = _delayed(minute, mutant_threshold, mutant_comparator)
            if clean != mutant and (
                (mutant and minute in rejected)
                or (not mutant and minute in accepted and clean)
                or (not mutant and minute in rejected)
            ):
                return True
        return False
    if "refund_window_minutes" in clean_codegen:
        mutant = codegen_mutant.get("refund_window_minutes")
        clean = clean_codegen.get("refund_window_minutes")
        rejected = set(test_artifact.get("must_reject_minutes", []))
        accepted = set(test_artifact.get("must_accept_minutes", []))
        return mutant == clean or mutant in rejected or (clean not in accepted and bool(rejected))
    if "order_id_pattern" in clean_codegen:
        return codegen_mutant.get("order_id_pattern") == clean_codegen.get("order_id_pattern") or bool(
            test_artifact.get("must_reject_ids", [])
        )
    if "sort_key" in clean_codegen:
        mutant = codegen_mutant.get("sort_key")
        clean = clean_codegen.get("sort_key")
        return (
            mutant == clean
            or mutant in set(test_artifact.get("forbidden_sort_keys", []))
            or test_artifact.get("required_sort_key") == clean != mutant
        )
    if "cardinality" in clean_codegen:
        mutant = codegen_mutant.get("cardinality")
        clean = clean_codegen.get("cardinality")
        return mutant == clean or test_artifact.get("exact_cardinality") == clean != mutant
    return False


def score_test_gen_mutation(
    intent_id: str,
    artifact: dict[str, Any],
    oracle_spec: dict[str, dict[str, Any]],
) -> float:
    mutants = MUTANTS_BY_INTENT.get(intent_id, [])
    if not mutants:
        return 1.0
    clean_codegen = oracle_spec.get("codegen", {})
    caught = sum(
        artifact_detects_mutant(artifact, mutant, clean_codegen) for mutant in mutants
    )
    return caught / len(mutants)
