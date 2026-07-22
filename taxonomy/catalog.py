"""C1 degradation mode catalog and intent mappings."""

DEGRADATION_MODES = frozenset(
    {
        "identifier_format_ambiguity",
        "ordering_ambiguity",
        "wrong_numeric_threshold",
        "cardinality_ambiguity",
        "numerical_inconsistency",
        "unverifiable_output",
        "none",
    }
)

INTENT_TO_MODE: dict[str, str] = {
    "RF-04": "identifier_format_ambiguity",
    "RF-07": "ordering_ambiguity",
    "RF-09": "wrong_numeric_threshold",
    "RF-13": "cardinality_ambiguity",
    "RF-11": "numerical_inconsistency",
}
