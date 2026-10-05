import random

from scripts import confirmatory_power as cp


def test_pool_matches_the_published_estimate():
    pool = cp.observed_pool(cp.ROOT / "data/selection-abc-results/20261003", cp.ROOT / "data/abc-cases")
    assert len(pool) == 9 and sum(len(v) for v in pool.values()) == 44
    assert abs(cp.pool_estimate(pool) - 0.7254) < 1e-3
    assert all(s in (0.5, 1.0) for reqs in pool.values() for r in reqs for s in r)  # no reversal observed


def test_attenuation_and_noise():
    rng = random.Random(0)
    assert cp.attenuate([1.0, 0.5, 1.0], 1.0, rng) == [0.5, 0.5, 0.5]
    assert cp.attenuate([1.0, 0.5], 0.0, rng) == [1.0, 0.5]
    redrawn = [s for _ in range(2000) for s in cp.attenuate([0.5], 0.0, rng, noise=1.0)]
    assert set(redrawn) == {0.0, 1.0} and 0.4 < redrawn.count(1.0) / len(redrawn) < 0.6


def test_null_grid_rejects_rarely():
    pool = {"a": [[0.5] * 4, [1.0] * 4], "b": [[0.5] * 4, [1.0, 0.5, 0.5, 0.5]], "c": [[1.0] * 4]}
    row = cp.power_grid(pool, [(6, 3)], [1.0], [0.05], simulations=60, seed=1, n_boot=200, n_perm=400)[0]
    assert abs(row["mean_estimate"] - 0.5) < 0.02 and row["power_p_below_05"] <= 0.1
