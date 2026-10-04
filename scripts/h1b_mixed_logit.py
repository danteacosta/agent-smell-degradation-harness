"""H1b: mixed-effects logistic regression of target violation in arm C.

Pre-registration section 5: the target-failure indicator of every arm-C run
is regressed on context_cue, numeric, derived_state and memorized, with a
random intercept per project and per requirement (requirement nested in
project). Odds ratios get 95% profile-likelihood intervals; no multiplicity
correction for these four terms.

The likelihood is the Laplace approximation of the GLMM marginal likelihood
(as glmer's default nAGQ=1), maximised over the fixed effects and the two
log standard deviations. A profile interval bound is reported as null when the
profile deviance never reaches the chi-square(1) cutoff, which is what
happens under quasi-complete separation (e.g. a covariate level in which every
run violated the rule): the estimate then lies on the boundary and only one
side of the interval is finite.

Runs with an unknown outcome are left out, as in the observed H1a estimate.
`memorized` is taken for the model that produced the run.

Requires numpy and scipy (not in the base lock):
  python3 scripts/h1b_mixed_logit.py --results data/selection-abc-results/20261003 \
      --context-cue data/context-cue/20261004-v2/results.json --out h1b.json
"""
from __future__ import annotations

import argparse
import json
import math
from pathlib import Path
import sys

import numpy as np
from scipy.optimize import brentq, minimize
from scipy.special import expit

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

COVARIATES = ("context_cue", "numeric", "derived_state", "memorized")
CHI2_1_95 = 3.841458820694124
LOG_TAU_BOUNDS = (-6.0, 3.0)


def design(results_root: Path, context_cue: Path, cases_dir: Path = ROOT / "data/abc-cases"):
    from scripts import selected46_report as rep
    configs = rep.load_configs(cases_dir)
    runs = rep.load_results(results_root, configs)
    covs = rep.covariates(configs)
    cues = rep.load_context_cue(context_cue)
    rows = []
    for case, case_rows in sorted(runs.items()):
        for r in case_rows:
            if r["arm"] != "C":
                continue
            sev = rep.severity(r.get("category"))
            if sev is None:
                continue
            values = {"context_cue": cues.get(case), "numeric": covs[case]["numeric"],
                      "derived_state": covs[case]["derived_state"],
                      "memorized": covs[case]["memorized"].get(r["model"])}
            if any(v is None for v in values.values()):
                raise ValueError(f"{case}/{r['model']}: missing covariate {values}")
            rows.append({"case": case, "project": configs[case]["project_id"], "model": r["model"],
                         "y": sev, **{k: int(bool(v)) for k, v in values.items()}})
    return rows


class LaplaceGLMM:
    """Logistic GLMM with random intercepts for groups A (outer) and B (inner)."""

    def __init__(self, X: np.ndarray, y: np.ndarray, ga: np.ndarray, gb: np.ndarray):
        self.X, self.y = X.astype(float), y.astype(float)
        self.na, self.nb = int(ga.max()) + 1, int(gb.max()) + 1
        self.Z = np.zeros((len(y), self.na + self.nb))
        self.Z[np.arange(len(y)), ga] = 1.0
        self.Z[np.arange(len(y)), self.na + gb] = 1.0
        self._b = np.zeros(self.na + self.nb)

    def loglik(self, beta: np.ndarray, log_ta: float, log_tb: float) -> float:
        d = np.concatenate([np.full(self.na, math.exp(2 * log_ta)), np.full(self.nb, math.exp(2 * log_tb))])
        b = self._b.copy()
        offset = self.X @ beta
        for _ in range(200):
            eta = offset + self.Z @ b
            mu = expit(eta)
            grad = self.Z.T @ (self.y - mu) - b / d
            H = (self.Z.T * (mu * (1 - mu))) @ self.Z + np.diag(1.0 / d)
            step = np.linalg.solve(H, grad)
            biggest = np.max(np.abs(step))
            if biggest > 5.0:  # damp early Newton steps
                step *= 5.0 / biggest
            b = b + step
            if biggest < 1e-10:
                break
        eta = offset + self.Z @ b
        mu = expit(eta)
        H = (self.Z.T * (mu * (1 - mu))) @ self.Z + np.diag(1.0 / d)
        self._b = b
        cond = float(np.sum(self.y * eta - np.logaddexp(0.0, eta)))
        sign, logdet = np.linalg.slogdet(H)
        return cond - 0.5 * float(np.sum(b * b / d)) - 0.5 * float(np.sum(np.log(d))) - 0.5 * logdet

    def fit(self, fixed: dict[int, float] | None = None, start: np.ndarray | None = None) -> dict:
        fixed = fixed or {}
        p = self.X.shape[1]
        free = [j for j in range(p) if j not in fixed]

        def unpack(theta):
            beta = np.zeros(p)
            for j, v in fixed.items():
                beta[j] = v
            beta[free] = theta[:len(free)]
            return beta, theta[len(free)], theta[len(free) + 1]

        def objective(theta):
            beta, la, lb = unpack(theta)
            return -self.loglik(beta, la, lb)

        x0 = np.zeros(len(free) + 2) if start is None else start
        bounds = [(-30.0, 30.0)] * len(free) + [LOG_TAU_BOUNDS, LOG_TAU_BOUNDS]
        best = None
        for init in ([x0] if start is not None else [x0, np.r_[np.zeros(len(free)), -1.0, -1.0]]):
            self._b = np.zeros(self.na + self.nb)
            res = minimize(objective, init, method="L-BFGS-B", bounds=bounds,
                           options={"ftol": 1e-12, "gtol": 1e-8, "maxiter": 2000})
            if best is None or res.fun < best.fun:
                best = res
        beta, la, lb = unpack(best.x)
        return {"beta": beta, "log_tau_a": la, "log_tau_b": lb, "loglik": -best.fun,
                "converged": bool(best.success), "theta": best.x}

    def profile_bound(self, j: int, full: dict, direction: int, limit: float = 25.0) -> float | None:
        """Where the profile deviance crosses the chi-square(1) cutoff on one side, or None."""
        target = full["loglik"] - CHI2_1_95 / 2
        start = np.delete(full["theta"], j)

        def g(value):
            return self.fit({j: value}, start=start)["loglik"] - target

        center = float(full["beta"][j])
        prev, step = center, 0.5
        while abs(prev - center) < limit:
            cur = prev + direction * step
            if g(cur) < 0:
                lo, hi = sorted((prev, cur))
                if g(lo if direction < 0 else hi) * g(hi if direction < 0 else lo) > 0:
                    return float(cur)  # crossing within one optimiser tolerance of cur
                return float(brentq(g, lo, hi, xtol=1e-4))
            prev, step = cur, step * 1.6
        return None


def separation(rows: list[dict]) -> dict[str, str | None]:
    out = {}
    for name in COVARIATES:
        flag = None
        for level in (0, 1):
            ys = [r["y"] for r in rows if r[name] == level]
            if ys and (all(ys) or not any(ys)):
                flag = f"level {level}: all {len(ys)} runs {'violated' if all(ys) else 'held'}"
        out[name] = flag
    return out


def analyse(rows: list[dict], covariates: tuple[str, ...] = COVARIATES, with_intervals: bool = True) -> dict:
    projects = sorted({r["project"] for r in rows})
    cases = sorted({r["case"] for r in rows})
    X = np.array([[1.0] + [r[c] for c in covariates] for r in rows])
    y = np.array([r["y"] for r in rows])
    ga = np.array([projects.index(r["project"]) for r in rows])
    gb = np.array([cases.index(r["case"]) for r in rows])
    model = LaplaceGLMM(X, y, ga, gb)
    full = model.fit()
    separated = separation(rows)
    terms = {}
    for j, name in enumerate(covariates, start=1):
        beta = float(full["beta"][j])
        finite = separated.get(name) is None and abs(beta) < 29.0
        entry = {"log_odds": beta if finite else None, "odds_ratio": math.exp(beta) if finite else None,
                 "estimable": finite,
                 "note": None if finite else f"no finite maximum-likelihood estimate ({separated.get(name) or 'at optimiser bound'})"}
        if with_intervals:
            lo = model.profile_bound(j, full, -1)
            hi = model.profile_bound(j, full, +1)
            entry["ci95_profile_log_odds"] = [lo, hi]
            entry["ci95_profile_odds_ratio"] = [None if lo is None else math.exp(lo), None if hi is None else math.exp(hi)]
        terms[name] = entry
    return {"n_runs": int(len(y)), "n_violated": int(y.sum()), "n_requirements": len(cases),
            "n_projects": len(projects), "intercept_log_odds": float(full["beta"][0]),
            "sd_project": math.exp(full["log_tau_a"]), "sd_requirement": math.exp(full["log_tau_b"]),
            "loglik_laplace": full["loglik"], "converged": full["converged"], "terms": terms}


def requirement_level(rows: list[dict]) -> dict:
    """Diagnostic: share of C runs violated per requirement, averaged within covariate level.

    `memorized` varies by model within a requirement, so it is summarised per
    (requirement, model) cell instead.
    """
    from collections import defaultdict
    out = {}
    for name in COVARIATES:
        unit = (lambda r: (r["case"], r["model"])) if name == "memorized" else (lambda r: r["case"])
        cells = defaultdict(list)
        for r in rows:
            cells[(unit(r), r[name])].append(r["y"])
        by_level = defaultdict(list)
        for (_, level), ys in cells.items():
            by_level[level].append(sum(ys) / len(ys))
        out[name] = {str(level): {"units": len(v), "mean_violation_share": round(sum(v) / len(v), 3),
                                  "units_all_violated": sum(1 for x in v if x == 1.0),
                                  "units_none_violated": sum(1 for x in v if x == 0.0)}
                     for level, v in sorted(by_level.items())}
    return out


def report(rows: list[dict]) -> dict:
    return {
        "schema_version": "h1b-mixed-logit/v1",
        "confirmatory_eligible": False,
        "model": "logit P(violated) = b0 + context_cue + numeric + derived_state + memorized + u_project + u_requirement; Laplace",
        "separation": separation(rows),
        "level_counts": {c: {str(l): {"violated": sum(r["y"] for r in rows if r[c] == l),
                                      "held": sum(1 - r["y"] for r in rows if r[c] == l)} for l in (0, 1)}
                         for c in COVARIATES},
        "requirement_level": requirement_level(rows),
        "prespecified": analyse(rows),
        "sensitivity_without_numeric": analyse(rows, tuple(c for c in COVARIATES if c != "numeric")),
    }


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--results", type=Path, required=True)
    parser.add_argument("--context-cue", type=Path, required=True)
    parser.add_argument("--out", type=Path)
    args = parser.parse_args(argv)
    result = report(design(args.results, args.context_cue))
    text = json.dumps(result, indent=2)
    if args.out:
        args.out.write_text(text + "\n")
    print(text)


if __name__ == "__main__":
    main()
