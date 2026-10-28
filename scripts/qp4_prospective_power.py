"""Planning simulation for the prospective QP4 study (H-a, H-b, H-c).

Offline. It resamples the 25 exploratory requirements of the shared-omission runs
(via scripts/verifier_coupling.py) to estimate how often the planned tests would
reject at a given number of requirements and projects. It is a planning aid, not
evidence: resampling observed requirements assumes effects as large as the ones
observed, which were selected post hoc, so an attenuated scenario is reported next
to the observed-effect scenario.

Per requirement, the observed quantities are:
  complete1   detection by one tester from the complete requirement (mean over testers)
  incomplete5 detection by the union of all testers from the incomplete request
  incomplete1 detection by one tester from the incomplete request (mean over testers)
  recovery    generator recovery in arm C

Hypotheses (one-sided directions are fixed in advance; tests are two-sided):
  H-a  complete1 - incomplete1 > 0      exact project sign-flip on per-requirement differences
  H-b  incomplete5 - complete1 < 0      exact project sign-flip
  H-c  rho(recovery, incomplete1) > 0   within-project permutation of Spearman rho

Each simulated study draws N requirements with replacement and assigns them in turn
to P projects (a project is a cluster of requirements). Attenuation multiplies
the H-a and H-b differences by a factor and, for H-c, replaces a share of the
detection values with values drawn from other requirements.

Usage: python scripts/qp4_prospective_power.py [--reps 1000]
"""
from __future__ import annotations

import argparse
from itertools import product
import json
from pathlib import Path
import random
import sys

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts import verifier_coupling as vc  # noqa: E402

SEED = 2026102802
OUT = ROOT / "data/confirmatory-planning/qp4-prospective-power.json"
DESIGNS = [(25, 8), (40, 8), (40, 10), (60, 12), (80, 12)]
ATTENUATION = (1.0, 0.5)
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


def simulate(rows, n_req, n_proj, factor, reps, seed=SEED) -> dict:
    rng = random.Random(f"{seed}-{n_req}-{n_proj}-{factor}")
    rej = {"H-a": 0, "H-b": 0, "H-c": 0}
    rhos, dirs = [], {"H-a": 0, "H-b": 0, "H-c": 0}
    for _ in range(reps):
        draw = [rng.choice(rows) for _ in range(n_req)]
        proj = [i % n_proj for i in range(n_req)]
        a = [[] for _ in range(n_proj)]
        b = [[] for _ in range(n_proj)]
        for r, p in zip(draw, proj):
            a[p].append(factor * (r["complete1"] - r["incomplete1"]))
            b[p].append(factor * (r["incomplete5"] - r["complete1"]))
        pa, pb = sign_flip(a), sign_flip(b)
        da = sum(sum(g) for g in a) > 0
        db = sum(sum(g) for g in b) < 0
        rej["H-a"] += pa <= ALPHA and da
        rej["H-b"] += pb <= ALPHA and db
        dirs["H-a"] += da
        dirs["H-b"] += db
        x = [r["recovery"] for r in draw]
        y = [r["incomplete1"] for r in draw]
        if factor < 1:
            # replace a share (1 - factor) of detections with values from other requirements
            for i in range(n_req):
                if rng.random() > factor:
                    y[i] = rng.choice(rows)["incomplete1"]
        rho, pc = within_project_perm(x, y, proj, rng)
        if rho is not None:
            rhos.append(rho)
            rej["H-c"] += pc <= ALPHA and rho > 0
            dirs["H-c"] += rho > 0
    rhos.sort()
    return {
        "requirements": n_req, "projects": n_proj, "effect_factor": factor, "replications": reps,
        "power": {k: v / reps for k, v in rej.items()},
        "correct_direction": {k: v / reps for k, v in dirs.items()},
        "rho_median": rhos[len(rhos) // 2] if rhos else None,
    }


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--reps", type=int, default=1000)
    args = ap.parse_args(argv)
    rows = requirement_table()
    results = [simulate(rows, n, p, f, args.reps) for n, p in DESIGNS for f in ATTENUATION]
    out = {
        "schema_version": "qp4-prospective-power/v1",
        "planning_only": True,
        "confirmatory_eligible": False,
        "source": str((vc.OUT / "results.json").relative_to(ROOT)),
        "alpha_two_sided": ALPHA,
        "note": ("Resamples 25 post hoc requirements; observed-effect power is optimistic. "
                 "Projects are clusters of resampled requirements, not real projects, so between-project "
                 "heterogeneity is not modelled."),
        "seed": SEED,
        "results": results,
    }
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(out, indent=2) + "\n")
    for r in results:
        print(r["requirements"], r["projects"], r["effect_factor"], r["power"], round(r["rho_median"], 2))


if __name__ == "__main__":
    main()
