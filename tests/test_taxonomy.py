from taxonomy.catalog import DEGRADATION_MODES
from taxonomy.label import label_degradation


def test_rf09_maps_to_vague_threshold_mode():
    result = label_degradation(
        intent_id="RF-09",
        smell_type="vague_threshold",
        oracle_passed=False,
        task_family="codegen",
    )
    assert result.mode in DEGRADATION_MODES
    assert result.mode == "wrong_numeric_threshold"
    assert result.severity in {"low", "medium", "high"}


def test_oracle_passed_yields_none_mode_and_low_severity():
    result = label_degradation(
        intent_id="RF-09",
        smell_type="vague_threshold",
        oracle_passed=True,
        task_family="codegen",
    )
    assert result.mode == "none"
    assert result.severity == "low"


def test_rf04_maps_to_identifier_format_ambiguity():
    result = label_degradation(
        intent_id="RF-04",
        smell_type="identifier_format",
        oracle_passed=False,
        task_family="codegen",
    )
    assert result.mode == "identifier_format_ambiguity"
    assert result.severity == "high"


def test_rf07_maps_to_ordering_ambiguity():
    result = label_degradation(
        intent_id="RF-07",
        smell_type="ordering_ambiguity",
        oracle_passed=False,
        task_family="codegen",
    )
    assert result.mode == "ordering_ambiguity"
    assert result.severity == "high"


def test_rf13_maps_to_cardinality_ambiguity():
    result = label_degradation(
        intent_id="RF-13",
        smell_type="cardinality_ambiguity",
        oracle_passed=False,
        task_family="test_gen",
    )
    assert result.mode == "cardinality_ambiguity"
    assert result.severity == "high"
