"""Label oracle outcomes with degradation mode and severity."""

from dataclasses import dataclass

from taxonomy.catalog import DEGRADATION_MODES, INTENT_TO_MODE


@dataclass(frozen=True)
class DegradationLabel:
    mode: str
    severity: str


def label_degradation(
    *,
    intent_id: str,
    smell_type: str,
    oracle_passed: bool,
    task_family: str,
) -> DegradationLabel:
    if oracle_passed:
        return DegradationLabel(mode="none", severity="low")

    mode = INTENT_TO_MODE.get(intent_id, "unverifiable_output")
    if mode not in DEGRADATION_MODES:
        mode = "unverifiable_output"

    return DegradationLabel(mode=mode, severity="high")
