"""Planning simulation for the prospective QP4 study (H-a, H-b, H-c).

Offline. It resamples the 25 exploratory requirements of the shared-omission runs
(via scripts/verifier_coupling.py) to estimate how often the planned tests would
reject at a given number of requirements and projects. It is a planning aid, not
evidence: resampling observed requirements assumes effects as large as the ones
observed, which were selected post hoc, so an attenuated scenario is reported next
to the observed-effect scenario.

Per requirement, the observed quantities are:
  complete_score    mean over suites of killed / confirmed mutants, complete source, mean over
                    testers (the H-a estimand of the protocol)
  incomplete_score  the same for the incomplete source
  complete1         detection by the union of one tester's complete-source suites, mean over testers
  incomplete5       detection by the union of all testers' incomplete-source suites
  incomplete1       detection by the union of one tester's incomplete-source suites, mean over testers
  recovery          generator recovery in arm C

Hypotheses (one-sided directions are fixed in advance; tests are two-sided):
  H-a  complete_score - incomplete_score > 0   exact project sign-flip on per-requirement differences
  H-b  incomplete5 - complete1 < 0             exact project sign-flip
  H-c  rho(recovery, incomplete1) > 0   within-project permutation of Spearman rho

Each simulated study draws N requirements with replacement and assigns them in turn
to P projects (a project is a cluster of requirements). Effect model for H-a and H-b
(v2, after review by Codex on 28/10):

  d'_ij = d_ij - (1 - f) * mean(d) + u_j,   u_j ~ Normal(0, tau),   clipped to [-1, 1]

where d_ij is the observed per-requirement difference, f the effect factor and u_j a
project shift shared by the requirements of project j. The factor is a location shift
towards zero that keeps the requirement-level spread, so it reduces signal to noise;
multiplying the differences by f, as v1 did, leaves the exact sign-flip test unchanged
because the test is invariant to positive scaling. tau adds between-project
heterogeneity, which the resampled requirements do not contain. The decision rule is the
registered one: Holm over {H-a, H-b} at 0.05 with the predicted sign. Draws and project
shifts use common random numbers across factors, so scenarios differ only in the effect.

For H-c, attenuation replaces a share (1 - f) of the detection values with values from
other requirements; H-c is estimation only and its power is indicative.

Usage: python scripts/qp4_prospective_power.py [--reps 1000]
"""
from __future__ import annotations

import argparse
from itertools import product
import json
from pathlib import Path
import random
import statistics
import sys

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts import verifier_coupling as vc  # noqa: E402

SEED = 2026102802
OUT = ROOT / "data/confirmatory-planning/qp4-prospective-power.json"
DESIGNS = [(25, 8), (40, 8), (40, 10), (60, 12), (80, 12)]
ATTENUATION = (1.0, 0.5)
TAUS = (0.0, 0.10)
ALPHA = 0.05


def requirement_table() -> list[dict]:
    """Per-requirement quantities from the published coupling results."""
    res = json.loads((vc.OUT / "results.json").read_text())
    q1 = res["Q1_ensemble"]["per_requirement"]
    q3 = {r["case"]: r for r in res["Q3_coupling"]["per_requirement"]}
    k_all = str(len(res["Q1_ensemble"]["testers"]))
    rows = []
    for case, r in sorted(q1.items()):
        rows.append({
            "case": case,
            "complete_score": r["spec_complete"]["single_tester_published_score_mean"],
            "incomplete_score": r["spec_incomplete"]["single_tester_published_score_mean"],
            "complete1": r["spec_complete"]["single_tester_any_suite_detection_mean"],
            "incomplete1": r["spec_incomplete"]["single_tester_any_suite_detection_mean"],
            "incomplete5": r["spec_incomplete"]["union_detection_by_k_testers"][k_all],
            "recovery": q3[case]["generator_recovery"],
        })
    return rows


def sign_flip(groups: list[list[float]]) -> float:
    vals = [v for g in groups for v in g]
    obs = abs(sum(vals) / len(vals))
    if obs == 0:
        return 1.0
    sums = [sum(g) for g in groups]
    extreme = total = 0
    for signs in product((1, -1), repeat=len(groups)):
        extreme += abs(sum(s * x for s, x in zip(signs, sums)) / len(vals)) >= obs - 1e-12
        total += 1
    return extreme / total


def within_project_perm(x, y, proj, rng, n=400) -> tuple[float | None, float | None]:
    obs = vc.spearman(x, y)
    if obs is None:
        return None, None
    idx: dict[int, list[int]] = {}
    for i, p in enumerate(proj):
        idx.setdefault(p, []).append(i)
    hits = 0
    for _ in range(n):
        yy = list(y)
        for ii in idx.values():
            vals = [y[i] for i in ii]
            rng.shuffle(vals)
            for i, v in zip(ii, vals):
                yy[i] = v
        r = vc.spearman(x, yy)
        hits += r is not None and abs(r) >= abs(obs) - 1e-12
    return obs, (hits + 1) / (n + 1)


def holm_two(pa: float, pb: float, alpha: float = ALPHA) -> tuple[bool, bool]:
    """Holm step-down over two p-values."""
    lo, hi = sorted([("a", pa), ("b", pb)], key=lambda t: t[1])
    rej = {"a": False, "b": False}
    if lo[1] <= alpha / 2:
        rej[lo[0]] = True
        if hi[1] <= alpha:
            rej[hi[0]] = True
    return rej["a"], rej["b"]


def simulate(rows, n_req, n_proj, factor, reps, tau=0.0, seed=SEED) -> dict:
    # common random numbers: the stream does not depend on factor
    rng = random.Random(f"{seed}-{n_req}-{n_proj}-{tau}")
    da_all = [r["complete_score"] - r["incomplete_score"] for r in rows]
    db_all = [r["incomplete5"] - r["complete1"] for r in rows]
    shift_a = (1 - factor) * statistics.fmean(da_all)
    shift_b = (1 - factor) * statistics.fmean(db_all)
    clip = lambda v: max(-1.0, min(1.0, v))  # noqa: E731
    rej = {"H-a": 0, "H-b": 0, "H-c": 0, "H-a_unadjusted": 0, "H-b_unadjusted": 0}
    rhos, dirs = [], {"H-a": 0, "H-b": 0, "H-c": 0}
    for _ in range(reps):
        draw = [rng.choice(rows) for _ in range(n_req)]
        proj = [i % n_proj for i in range(n_req)]
        ua = [rng.gauss(0, tau) if tau else 0.0 for _ in range(n_proj)]
        ub = [rng.gauss(0, tau) if tau else 0.0 for _ in range(n_proj)]
        a = [[] for _ in range(n_proj)]
        b = [[] for _ in range(n_proj)]
        for r, p in zip(draw, proj):
            a[p].append(clip(r["complete_score"] - r["incomplete_score"] - shift_a + ua[p]))
            b[p].append(clip(r["incomplete5"] - r["complete1"] - shift_b + ub[p]))
        pa, pb = sign_flip(a), sign_flip(b)
        da = sum(sum(g) for g in a) > 0
        db = sum(sum(g) for g in b) < 0
        ha, hb = holm_two(pa, pb)
        rej["H-a"] += ha and da
        rej["H-b"] += hb and db
        rej["H-a_unadjusted"] += pa <= ALPHA and da
        rej["H-b_unadjusted"] += pb <= ALPHA and db
        dirs["H-a"] += da
        dirs["H-b"] += db
        x = [r["recovery"] for r in draw]
        y = [r["incomplete1"] for r in draw]
        u = [rng.random() for _ in range(n_req)]
        alt = [rng.choice(rows)["incomplete1"] for _ in range(n_req)]
        y = [alt[i] if u[i] > factor else y[i] for i in range(n_req)]
        rho, pc = within_project_perm(x, y, proj, rng)
        if rho is not None:
            rhos.append(rho)
            rej["H-c"] += pc <= ALPHA and rho > 0
            dirs["H-c"] += rho > 0
    rhos.sort()
    return {
        "requirements": n_req, "projects": n_proj, "effect_factor": factor, "tau": tau,
        "replications": reps,
        "mean_effect": {"H-a": statistics.fmean(da_all) - shift_a, "H-b": statistics.fmean(db_all) - shift_b},
        "power": {k: v / reps for k, v in rej.items()},
        "correct_direction": {k: v / reps for k, v in dirs.items()},
        "rho_median": rhos[len(rhos) // 2] if rhos else None,
    }


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--reps", type=int, default=1000)
    args = ap.parse_args(argv)
    rows = requirement_table()
    results = [simulate(rows, n, p, f, args.reps, tau=t) for n, p in DESIGNS for t in TAUS for f in ATTENUATION]
    out = {
        "schema_version": "qp4-prospective-power/v2",
        "planning_only": True,
        "confirmatory_eligible": False,
        "source": str((vc.OUT / "results.json").relative_to(ROOT)),
        "alpha_two_sided": ALPHA,
        "note": ("Resamples 25 post hoc requirements; observed-effect power is optimistic. "
                 "Projects are clusters of resampled requirements; between-project heterogeneity enters only "
                 "through the assumed tau. Effect factor = location shift of the mean difference towards zero; "
                 "H-a and H-b power uses Holm over the two tests. v1 scaled differences, which the sign-flip "
                 "test ignores; v1 numbers are withdrawn."),
        "assumptions": {"effect_model": "d' = d - (1-f)*mean(d) + u_project, u ~ N(0, tau), clipped to [-1,1]",
                        "taus": list(TAUS), "factors": list(ATTENUATION), "decision_rule": "Holm {H-a, H-b}, alpha 0.05, predicted sign"},
        "seed": SEED,
        "results": results,
    }
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(out, indent=2) + "\n")
    for r in results:
        print(r["requirements"], r["projects"], r["tau"], r["effect_factor"], {k: round(v, 2) for k, v in r["power"].items()})


if __name__ == "__main__":
    main()
