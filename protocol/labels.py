from __future__ import annotations

from collections.abc import Mapping
from typing import Any


def exploratory_loss_label(episode: Mapping[str, Any]) -> int:
    """Exploratory H2 label: the terminal oracle observed a target failure.

    The label deliberately ignores which arm produced the episode.  Deriving
    it from ``variant == "smelly"`` made a clean-arm failure count as a
    non-event and let any feature correlated with the arm (requirement
    length, smell flags) score well without detecting constraint loss.
    Confirmatory analyses still require independent human labels.
    """

    passed = episode.get("oracle_passed")
    if type(passed) is not bool:
        raise ValueError("exploratory loss label requires a Boolean oracle_passed")
    return 0 if passed else 1
