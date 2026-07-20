from __future__ import annotations


def mann_whitney_auroc(scores: list[float], y: list[int]) -> float:
    """AUROC via Mann-Whitney U; handles ties; returns 0.5 if all labels equal."""
    if len(scores) != len(y) or not scores:
        return 0.5
    if len(set(y)) <= 1:
        return 0.5

    pos_scores = [score for score, label in zip(scores, y) if label == 1]
    neg_scores = [score for score, label in zip(scores, y) if label == 0]
    n_pos = len(pos_scores)
    n_neg = len(neg_scores)
    if n_pos == 0 or n_neg == 0:
        return 0.5

    wins = 0.0
    for pos in pos_scores:
        for neg in neg_scores:
            if pos > neg:
                wins += 1.0
            elif pos == neg:
                wins += 0.5
    return wins / (n_pos * n_neg)
