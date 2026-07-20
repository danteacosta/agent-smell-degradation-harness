from __future__ import annotations

import random
from typing import Any


def synthetic_agreement_demo(*, seed: int = 0, n_items: int = 10) -> dict[str, Any]:
    """Placeholder inter-rater agreement — not derived from human annotation."""
    rng = random.Random(seed)
    agreements = [rng.random() > 0.15 for _ in range(n_items)]
    agreement_rate = sum(agreements) / len(agreements) if agreements else 0.0
    return {
        "agreement_rate": round(agreement_rate, 4),
        "n_raters": 2,
        "n_items": n_items,
        "synthetic": True,
        "limitation": (
            "Synthetic demo only; agreement_rate is not derived from human dual "
            "annotation and must not be cited as empirical IRR."
        ),
    }
