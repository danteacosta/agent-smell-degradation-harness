from enum import Enum


class Policy(str, Enum):
    DIRECT = "direct"
    STATIC_SMELL = "static_smell"
    STRUCTURED_REWRITE = "structured_rewrite"
    TARGETED_CLARIFICATION = "targeted_clarification"
    ORACLE_REWRITE_UPPER_BOUND = "oracle_rewrite_upper_bound"
    ORACLE_CLARIFICATION_UPPER_BOUND = "oracle_clarification_upper_bound"
