import math

import pytest

np = pytest.importorskip("numpy")
pytest.importorskip("scipy")
from scipy import integrate  # noqa: E402
from scipy.special import expit  # noqa: E402

from scripts import h1b_agq as a  # noqa: E402


def _sim(seed, k=30, m=4, beta=(0.5, -1.5), sd=2.0):
    rng = np.random.default_rng(seed)
    X, y, cl = [], [], []
    for c in range(k):
        x = int(rng.random() < 0.5)
        u = rng.normal(0, sd)
        for _ in range(m):
            X.append([1.0, x])
            y.append(int(rng.random() < expit(beta[0] + beta[1] * x + u)))
            cl.append(c)
    return np.array(X), np.array(y), np.array(cl)


def test_agq_matches_direct_numerical_integration():
    X, y, cl = _sim(1, sd=4.0)
    model = a.AGQLogit(X, y, cl, nodes=100)
    beta, ls = np.array([0.3, -1.0]), math.log(4.0)
    sigma = math.exp(ls)
    eta = X @ beta
    total = 0.0
    for c in range(cl.max() + 1):
        idx = np.where(cl == c)[0]

        def f(b, idx=idx):
            ll = sum(math.log(expit(eta[i] + b)) if y[i] else math.log(expit(-eta[i] - b)) for i in idx)
            return math.exp(ll - 0.5 * (b / sigma) ** 2) / (sigma * math.sqrt(2 * math.pi))
        total += math.log(integrate.quad(f, -80, 80, limit=1000, epsabs=1e-14, epsrel=1e-12)[0])
    assert model.loglik(beta, ls) == pytest.approx(total, abs=1e-4)
    assert abs(a.AGQLogit(X, y, cl, nodes=1).loglik(beta, ls) - total) > 1e-3  # Laplace is visibly off


def test_profile_interval_is_bracketed_and_covers_a_simulated_effect():
    X, y, cl = _sim(7, k=60, beta=(0.5, -2.0), sd=1.0)
    model = a.AGQLogit(X, y, cl, nodes=30)
    full = model.fit()
    lo = a.profile(model, full, 1, -1)
    hi = a.profile(model, full, 1, +1)
    assert lo["status"] == hi["status"] == "bracketed" and not lo["issues"] and not hi["issues"]
    assert lo["bound"] < -2.0 < hi["bound"]
    # the deviance at each bound is the chi-square cutoff
    for bound in (lo["bound"], hi["bound"]):
        ll = model.fit({1: bound}, starts=[np.delete(full["theta"], 1)])["loglik"]
        assert 2 * (full["loglik"] - ll) == pytest.approx(a.CHI2_1_95, abs=1e-3)


def test_separated_term_gets_only_a_lower_bound():
    rows = []
    rng = np.random.default_rng(3)
    for c in range(24):
        num = int(c < 4)
        u = rng.normal(0, 1.0)
        for model in ("m1", "m2"):
            for _ in range(2):
                y = 1 if num else int(rng.random() < expit(0.2 + u))
                rows.append({"case": f"c{c}", "project": "p", "model": model, "y": y, "numeric": num,
                             "context_cue": int(c % 3 == 0), "derived_state": int(c % 5 == 0),
                             "memorized": int(rng.random() < 0.5)})
    out = a.numeric_lower_bound(rows, nodes=20)
    assert out["upper"].startswith("unbounded") and out["lower_log_odds"] is not None
