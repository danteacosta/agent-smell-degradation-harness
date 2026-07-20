from enum import Enum


class Policy(str, Enum):
    DIRECT = "direct"
    STATIC_SMELL = "static_smell"
    REWRITE = "rewrite"
    CLARIFY = "clarify"
