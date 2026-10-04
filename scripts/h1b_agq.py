"""H1b intervals with adaptive Gauss-Hermite quadrature and checked profiles.

Why a second estimator. The pre-registered model (random intercepts for
project and requirement, Laplace) fits with the project variance on its
boundary (0, singular in lme4 and in scripts/h1b_mixed_logit.py), and lme4's
profile failed because the search found a lower deviance than the fit. With
about four runs per requirement and a requirement SD near 5, the Laplace
approximation is also known to be poor. This script therefore:

1. Drops the project intercept, whose estimate is exactly 0: at that boundary
   the reduced model has the same maximised likelihood.
2. Integrates the requirement intercept with adaptive Gauss-Hermite quadrature
   (default 100 nodes, where the log-likelihood agrees with direct numerical
   integration to 1e-5; lme4 allows at most nAGQ = 25, which is off by ~0.006 here).
3. Handles the numeric separation exactly. numeric is constant within each
   requirement and all its runs violated, so as beta_numeric -> +inf those
   four requirements contribute likelihood 1 whatever the other parameters
   are. The supremum over the full model is therefore the fit on the other
   42 requirements without the numeric term; profiles of the other terms are
   computed there, and numeric gets only a lower bound.
4. Profiles every term with explicit checks: each conditional fit must
   converge, the full fit is refitted from any better point a profile finds,
   a bound is reported only with a verified sign change of the profile
   deviance, and a missing bound is labelled either "not reached up to
   |log OR| = L" or, for numeric, "unbounded (separation)".

Reads the public design CSV of the lme4 validation so that both tools use the
same 178 rows.
"""
from __future__ import annotations

import argparse
import csv
import json
import math
from pathlib import Path

import numpy as np
from scipy.optimize import brentq, minimize
from scipy.special import expit, log_expit

CHI2_1_95 = 3.841458820694124
COVARIATES = ("context_cue", "numeric", "derived_state", "memorized")
LIMIT = 15.0
GRAD_TOL = 1e-3  # max |d(-loglik)/d theta| accepted as a converged optimum


def load(path: Path) -> list[dict]:
    rows = []
    for r in csv.DictReader(path.open()):
        rows.append({"case": r["case"], "project": r["project"], "model": r["model"], "y": int(r["y"]),
                     **{c: int(r[c]) for c in COVARIATES}})
    return rows


class AGQLogit:
    """Logistic model with one scalar random intercept per cluster, AGQ likelihood."""

    def __init__(self, X: np.ndarray, y: np.ndarray, cluster: np.ndarray, nodes: int = 25):
        self.X, self.y = X.astype(float), y.astype(float)
        self.k = int(cluster.max()) + 1
        self.t, self.w = np.polynomial.hermite.hermgauss(nodes)
        counts = np.bincount(cluster, minlength=self.k)
        self.m = int(counts.max())
        # padded (cluster, slot) layout; mask marks real observations
        self.rows = np.full((self.k, self.m), -1)
        fill = np.zeros(self.k, dtype=int)
        for i, c in enumerate(cluster):
            self.rows[c, fill[c]] = i
            fill[c] += 1
        self.mask = self.rows >= 0
        self.Y = np.where(self.mask, self.y[np.maximum(self.rows, 0)], 0.0)

    def cluster_logliks(self, beta: np.ndarray, log_sigma: float) -> np.ndarray:
        sigma = math.exp(log_sigma)
        eta = np.where(self.mask, (self.X @ beta)[np.maximum(self.rows, 0)], 0.0)
        b = np.zeros(self.k)
        for _ in range(100):  # vectorised Newton for each cluster's mode
            mu = expit(eta + b[:, None]) * self.mask
            g = np.sum(self.Y - mu, axis=1) - b / sigma ** 2
            H = -np.sum(mu * (1 - mu), axis=1) - 1 / sigma ** 2
            step = np.clip(-g / H, -5.0, 5.0)
            b += step
            if np.max(np.abs(step)) < 1e-12:
                break
        mu = expit(eta + b[:, None]) * self.mask
        s = 1.0 / np.sqrt(np.sum(mu * (1 - mu), axis=1) + 1 / sigma ** 2)
        pts = b[:, None] + math.sqrt(2.0) * s[:, None] * self.t[None, :]          # (k, q)
        e = eta[:, :, None] + pts[:, None, :]                                      # (k, m, q)
        ll = (self.Y[:, :, None] * log_expit(e) + (1 - self.Y[:, :, None]) * log_expit(-e)) * self.mask[:, :, None]
        vals = (ll.sum(axis=1) - 0.5 * (pts / sigma) ** 2 - math.log(sigma) - 0.5 * math.log(2 * math.pi)
                + self.t[None, :] ** 2)
        top = vals.max(axis=1, keepdims=True)
        return (top[:, 0] + np.log(np.sum(self.w[None, :] * np.exp(vals - top), axis=1))
                + np.log(math.sqrt(2.0) * s))

    def loglik(self, beta: np.ndarray, log_sigma: float) -> float:
        return float(np.sum(self.cluster_logliks(beta, log_sigma)))

    def fit(self, fixed: dict[int, float] | None = None, starts: list[np.ndarray] | None = None) -> dict:
        fixed = fixed or {}
        p = self.X.shape[1]
        free = [j for j in range(p) if j not in fixed]

        def unpack(theta):
            beta = np.zeros(p)
            for j, v in fixed.items():
                beta[j] = v
            beta[free] = theta[:-1]
            return beta, theta[-1]

        def objective(theta):
            beta, ls = unpack(theta)
            if abs(ls) > 6 or np.any(np.abs(beta) > 60):
                return 1e12
            return -self.loglik(beta, ls)

        starts = starts or [np.r_[np.zeros(len(free)), 0.0], np.r_[np.zeros(len(free)), 1.5]]
        best = None
        for x0 in starts:
            res = minimize(objective, x0, method="BFGS", options={"gtol": 1e-7, "maxiter": 5000})
            res2 = minimize(objective, res.x, method="Nelder-Mead",
                            options={"xatol": 1e-9, "fatol": 1e-11, "maxiter": 20000, "maxfev": 40000})
            cand = res2 if res2.fun <= res.fun else res
            if best is None or cand.fun < best.fun:
                best = cand
        beta, ls = unpack(best.x)
        grad = _gradient(objective, best.x)
        grad_norm = float(np.max(np.abs(grad)))
        interior = abs(ls) < 5.9 and bool(np.all(np.abs(beta) < 59))
        return {"beta": beta, "log_sigma": float(ls), "loglik": float(-best.fun), "theta": best.x,
                "converged": bool(grad_norm < GRAD_TOL and interior), "grad_max_abs": grad_norm,
                "interior": interior, "free": free}


def _gradient(f, x: np.ndarray, h: float = 1e-5) -> np.ndarray:
    """Central-difference gradient; convergence is judged here, not by optimiser flags."""
    g = np.zeros_like(x)
    for i in range(len(x)):
        e = np.zeros_like(x)
        e[i] = h
        g[i] = (f(x + e) - f(x - e)) / (2 * h)
    return g


def profile(model: AGQLogit, full: dict, j: int, direction: int) -> dict:
    """One side of the 95% profile interval for coefficient j.

    A bound is returned only if every conditional fit used to bracket and
    locate it converged and none exceeded the full fit. If a conditional fit
    beats the full fit, the best such point is returned in `better` so that
    the caller can refit and recompute every interval against the new maximum.
    """
    sup = full["loglik"]
    target = sup - CHI2_1_95 / 2
    center = float(full["beta"][j])
    warm = [np.delete(full["theta"], full["free"].index(j))]
    state = {"nonconverged": [], "better": None}

    def value(c):
        res = model.fit({j: c}, starts=warm)
        if not res["converged"]:
            state["nonconverged"].append(round(float(c), 4))
        if res["loglik"] > sup + 1e-7 and (state["better"] is None or res["loglik"] > state["better"]["loglik"]):
            state["better"] = {"loglik": res["loglik"], "theta": np.insert(res["theta"], j, c)}
        warm[0] = res["theta"]
        return res["loglik"] - target

    def result(bound, status):
        if state["better"] is not None:
            return {"bound": None, "status": "a conditional fit exceeded the full fit; refit required",
                    "better": state["better"]}
        if state["nonconverged"]:
            return {"bound": None, "status": "refused: conditional fit(s) did not converge at "
                    + ", ".join(map(str, state["nonconverged"][:5]))}
        return {"bound": bound, "status": status}

    prev, f_prev, step = center, CHI2_1_95 / 2, 0.25
    while abs(prev - center) < LIMIT:
        cur = prev + direction * step
        f_cur = value(cur)
        if state["better"] is not None:
            return result(None, "")
        if f_cur < 0 < f_prev:
            lo, hi = sorted((prev, cur))
            root = brentq(value, lo, hi, xtol=1e-5)
            if not (value(root - direction * 1e-3) > 0 > value(root + direction * 1e-3)):
                return {"bound": None, "status": "refused: sign change not confirmed around the root"}
            return result(float(root), "bracketed")
        prev, f_prev, step = cur, f_cur, min(step * 1.5, 2.0)
    return result(None, f"not reached within |log OR - estimate| <= {LIMIT} (search exhausted, not shown infinite)")


def build(rows: list[dict], covariates: tuple[str, ...], nodes: int) -> tuple[AGQLogit, dict]:
    cases = sorted({r["case"] for r in rows})
    X = np.array([[1.0] + [r[c] for c in covariates] for r in rows])
    y = np.array([r["y"] for r in rows])
    cl = np.array([cases.index(r["case"]) for r in rows])
    model = AGQLogit(X, y, cl, nodes)
    return model, model.fit()


def analyse(rows: list[dict], covariates: tuple[str, ...], nodes: int, label: str, max_refits: int = 3) -> dict:
    model, full = build(rows, covariates, nodes)
    refits = 0
    while True:
        sides, better = {}, None
        for j, name in enumerate(covariates, start=1):
            for direction in (-1, +1):
                side = profile(model, full, j, direction)
                sides[(name, direction)] = side
                if side.get("better") and (better is None or side["better"]["loglik"] > better["loglik"]):
                    better = side["better"]
        if better is None:
            break
        if refits == max_refits:
            for key in sides:
                sides[key] = {"bound": None, "status": f"refused: maximum still moving after {max_refits} refits"}
            break
        refit = model.fit(starts=[better["theta"], full["theta"]])
        refits += 1
        full = refit  # every interval is recomputed against the new maximum
    terms = {}
    for j, name in enumerate(covariates, start=1):
        lo, hi = sides[(name, -1)], sides[(name, +1)]
        b = float(full["beta"][j])
        terms[name] = {"log_odds": b, "odds_ratio": math.exp(b),
                       "ci95_log_odds": [lo["bound"], hi["bound"]],
                       "ci95_odds_ratio": [None if lo["bound"] is None else math.exp(lo["bound"]),
                                           None if hi["bound"] is None else math.exp(hi["bound"])],
                       "lower": lo["status"], "upper": hi["status"]}
    return {"label": label, "n_runs": len(rows), "n_requirements": len({r['case'] for r in rows}),
            "nodes": nodes, "loglik": full["loglik"], "sd_requirement": math.exp(full["log_sigma"]),
            "intercept_log_odds": float(full["beta"][0]), "converged": full["converged"],
            "grad_max_abs": full["grad_max_abs"], "refits_after_profiling": refits, "terms": terms}


def numeric_lower_bound(rows: list[dict], nodes: int) -> dict:
    """Profile lower bound for numeric against its supremum (beta_numeric -> +inf)."""
    others = tuple(c for c in COVARIATES if c != "numeric")
    reduced = [r for r in rows if r["numeric"] == 0]
    _, sup_fit = build(reduced, others, nodes)
    if not sup_fit["converged"]:
        return {"lower_log_odds": None, "status": "refused: supremum fit did not converge"}
    sup = sup_fit["loglik"]  # numeric requirements contribute log(1) = 0 in the limit
    model, _ = build(rows, COVARIATES, nodes)
    j = 1 + COVARIATES.index("numeric")
    target = sup - CHI2_1_95 / 2
    warm, problems = [None], []

    def value(c):
        res = model.fit({j: c}, starts=None if warm[0] is None else [warm[0]])
        if not res["converged"]:
            problems.append(f"non-converged conditional fit at {c:.3f}")
        if res["loglik"] > sup + 1e-7:
            problems.append(f"conditional fit at {c:.3f} exceeds the supremum")
        warm[0] = res["theta"]
        return res["loglik"] - target

    grid = [-6.0, -3.0, 0.0, 2.0, 4.0, 6.0, 9.0, 13.0, 20.0]
    vals = [value(c) for c in grid]
    out = {"upper": "unbounded (quasi-complete separation)", "supremum_loglik": sup,
           "grid": dict(zip(map(str, grid), vals))}
    for (a, fa), (b, fb) in zip(zip(grid, vals), zip(grid[1:], vals[1:])):
        if fa < 0 < fb:
            root = brentq(value, a, b, xtol=1e-5)
            if problems:
                return {**out, "lower_log_odds": None, "status": "refused: " + "; ".join(problems[:5])}
            return {**out, "lower_log_odds": float(root), "lower_odds_ratio": math.exp(root), "status": "bracketed"}
    return {**out, "lower_log_odds": None, "status": "profile did not cross the cutoff on the grid"}


def _laplace_check(rows: list[dict], covariates: tuple[str, ...]) -> dict:
    """Same reduced model with one node (= Laplace), to show how much quadrature moves the fit."""
    _, fit = build(rows, covariates, 1)
    return {"nodes": 1, "loglik": fit["loglik"], "sd_requirement": math.exp(fit["log_sigma"]),
            "log_odds": dict(zip(covariates, map(float, fit["beta"][1:])))}


def _nodes_check(rows: list[dict], covariates: tuple[str, ...], nodes: int) -> dict:
    """Fit with lme4's maximum nAGQ, for a direct comparison with glmer(..., nAGQ = 25)."""
    _, fit = build(rows, covariates, nodes)
    return {"nodes": nodes, "loglik": fit["loglik"], "sd_requirement": math.exp(fit["log_sigma"]),
            "intercept": float(fit["beta"][0]), "log_odds": dict(zip(covariates, map(float, fit["beta"][1:])))}


def report(rows: list[dict], nodes: int = 100) -> dict:
    others = tuple(c for c in COVARIATES if c != "numeric")
    return {
        "schema_version": "h1b-agq/v1",
        "confirmatory_eligible": False,
        "role": ("sensitivity analysis: the project random intercept is fixed at 0 (its estimate in the "
                 "pre-registered two-intercept fit is on the boundary). This does not validate the "
                 "pre-registered model; it is the reduced model with an accurate likelihood."),
        "model": "logit P(violated) = b0 + covariates + u_requirement, u ~ N(0, sd^2); AGQ",
        "full_model_other_terms": analyse([r for r in rows if r["numeric"] == 0], others, nodes,
                                          "full model: supremum over beta_numeric (42 requirements without numeric runs)"),
        "full_model_numeric": numeric_lower_bound(rows, nodes),
        "sensitivity_without_numeric": analyse(rows, others, nodes, "all 46 requirements, numeric term removed"),
        "laplace_check": _laplace_check([r for r in rows if r["numeric"] == 0], others),
        "agq25_check": _nodes_check([r for r in rows if r["numeric"] == 0], others, 25),
    }


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--design", type=Path, required=True, help="design.csv of the lme4 validation")
    parser.add_argument("--nodes", type=int, default=100)
    parser.add_argument("--out", type=Path)
    args = parser.parse_args(argv)
    result = report(load(args.design), args.nodes)
    text = json.dumps(result, indent=2)
    if args.out:
        args.out.write_text(text + "\n")
    print(text)


if __name__ == "__main__":
    main()
