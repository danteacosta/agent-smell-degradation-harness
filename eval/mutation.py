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


def _is_delayed(minutes: int, threshold: int, comparator: str) -> bool:
    if comparator == ">=":
        return minutes >= threshold
    if comparator == ">":
        return minutes > threshold
    return False


def _detects_threshold_mutant(
    test_artifact: dict[str, Any],
    codegen_mutant: dict[str, Any],
    clean_codegen: dict[str, Any],
) -> bool:
    clean_threshold = int(clean_codegen["delay_threshold_minutes"])
    clean_comp = clean_codegen.get("comparator", ">")
    mut_threshold = int(codegen_mutant.get("delay_threshold_minutes", clean_threshold))
    mut_comp = codegen_mutant.get("comparator", clean_comp)

    must_reject = set(test_artifact.get("must_reject_minutes", []))
    must_accept = set(test_artifact.get("must_accept_minutes", []))

    for minute in range(0, max(clean_threshold, mut_threshold) + 3):
        clean_delayed = _is_delayed(minute, clean_threshold, clean_comp)
        mut_delayed = _is_delayed(minute, mut_threshold, mut_comp)
        if clean_delayed == mut_delayed:
            continue
        if mut_delayed and minute in must_reject:
            return True
        if not mut_delayed and minute in must_accept and clean_delayed:
            return True
        if not mut_delayed and minute in must_reject:
            return True
    return False


def _detects_refund_mutant(
    test_artifact: dict[str, Any],
    codegen_mutant: dict[str, Any],
    clean_codegen: dict[str, Any],
) -> bool:
    mut_val = codegen_mutant.get("refund_window_minutes")
    clean_val = clean_codegen.get("refund_window_minutes")
    if mut_val == clean_val:
        return True
    must_reject = set(test_artifact.get("must_reject_minutes", []))
    must_accept = set(test_artifact.get("must_accept_minutes", []))
    if mut_val in must_reject:
        return True
    if clean_val in must_accept and mut_val not in must_reject:
        return False
    return bool(must_reject)


def _detects_pattern_mutant(
    test_artifact: dict[str, Any],
    codegen_mutant: dict[str, Any],
    clean_codegen: dict[str, Any],
) -> bool:
    if codegen_mutant.get("order_id_pattern") == clean_codegen.get("order_id_pattern"):
        return True
    must_reject_ids = test_artifact.get("must_reject_ids", [])
    return bool(must_reject_ids)


def _detects_sort_mutant(
    test_artifact: dict[str, Any],
    codegen_mutant: dict[str, Any],
    clean_codegen: dict[str, Any],
) -> bool:
    mut_key = codegen_mutant.get("sort_key")
    clean_key = clean_codegen.get("sort_key")
    if mut_key == clean_key:
        return True
    forbidden = set(test_artifact.get("forbidden_sort_keys", []))
    required = test_artifact.get("required_sort_key")
    if mut_key in forbidden:
        return True
    return required == clean_key and mut_key != required


def _detects_cardinality_mutant(
    test_artifact: dict[str, Any],
    codegen_mutant: dict[str, Any],
    clean_codegen: dict[str, Any],
) -> bool:
    mut_card = codegen_mutant.get("cardinality")
    clean_card = clean_codegen.get("cardinality")
    if mut_card == clean_card:
        return True
    exact = test_artifact.get("exact_cardinality")
    return exact == clean_card and mut_card != exact


def artifact_detects_mutant(
    test_artifact: dict[str, Any],
    codegen_mutant: dict[str, Any],
    clean_codegen: dict[str, Any],
) -> bool:
    if "delay_threshold_minutes" in clean_codegen:
        return _detects_threshold_mutant(test_artifact, codegen_mutant, clean_codegen)
    if "refund_window_minutes" in clean_codegen:
        return _detects_refund_mutant(test_artifact, codegen_mutant, clean_codegen)
    if "order_id_pattern" in clean_codegen:
        return _detects_pattern_mutant(test_artifact, codegen_mutant, clean_codegen)
    if "sort_key" in clean_codegen:
        return _detects_sort_mutant(test_artifact, codegen_mutant, clean_codegen)
    if "cardinality" in clean_codegen:
        return _detects_cardinality_mutant(test_artifact, codegen_mutant, clean_codegen)
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
        1
        for mutant in mutants
        if artifact_detects_mutant(artifact, mutant, clean_codegen)
    )
    return caught / len(mutants)
