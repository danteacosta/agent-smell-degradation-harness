import math

import pytest

np = pytest.importorskip("numpy")
pytest.importorskip("scipy")

from scripts import h1b_mixed_logit as h  # noqa: E402


def _plain_logit(X, y, iters=50):
    beta = np.zeros(X.shape[1])
    for _ in range(iters):
        mu = 1 / (1 + np.exp(-X @ beta))
        beta += np.linalg.solve((X.T * (mu * (1 - mu))) @ X, X.T @ (y - mu))
    return beta


def _simulate(seed, n_proj=6, n_req=8, reps=4, beta=(0.3, -1.5), tau_req=0.5):
    rng = np.random.default_rng(seed)
    rows = []
    for p in range(n_proj):
        for r in range(n_req):
            x = int(rng.random() < 0.5)
            u = rng.normal(0, tau_req)
            for _ in range(reps):
                eta = beta[0] + beta[1] * x + u
                rows.append({"project": f"p{p}", "case": f"p{p}-r{r}", "x": x,
                             "y": int(rng.random() < 1 / (1 + math.exp(-eta)))})
    return rows


def test_tiny_random_effects_reduce_to_ordinary_logistic_regression():
    rows = _simulate(1)
    X = np.array([[1.0, r["x"]] for r in rows])
    y = np.array([r["y"] for r in rows])
    ga = np.array([int(r["project"][1:]) for r in rows])
    gb = np.array([sorted({r["case"] for r in rows}).index(r["case"]) for r in rows])
    model = h.LaplaceGLMM(X, y, ga, gb)
    fit = model.fit({}, start=None)
    plain = _plain_logit(X, y)
    # with both variances pinned near zero the Laplace likelihood is the ordinary one
    ll_tiny = model.loglik(plain, -6.0, -6.0)
    mu = 1 / (1 + np.exp(-X @ plain))
    ll_plain = float(np.sum(y * np.log(mu) + (1 - y) * np.log(1 - mu)))
    assert ll_tiny == pytest.approx(ll_plain, abs=1e-3)
    assert fit["loglik"] >= ll_tiny - 1e-6


def test_simulated_effect_is_recovered_with_a_covering_profile_interval():
    rows = _simulate(7, n_proj=8, n_req=10, beta=(0.5, -2.0))
    for r in rows:
        r.update(context_cue=r["x"], numeric=0, derived_state=0, memorized=0)
    result = h.analyse(rows, covariates=("context_cue",))
    term = result["terms"]["context_cue"]
    assert term["estimable"] and term["log_odds"] < 0
    lo, hi = term["ci95_profile_log_odds"]
    assert lo is not None and hi is not None and lo < -2.0 < hi


def test_separation_is_reported_not_estimated():
    rows = _simulate(3)
    for r in rows:
        r.update(context_cue=r["x"], numeric=r["x"], derived_state=0, memorized=0)
        if r["numeric"] == 1:
            r["y"] = 1
    assert h.separation(rows)["numeric"].startswith("level 1: all")
    term = h.analyse(rows, covariates=("numeric",), with_intervals=False)["terms"]["numeric"]
    assert term["estimable"] is False and term["odds_ratio"] is None
