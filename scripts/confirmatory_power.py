"""How many requirements and projects does a confirmatory H1a run need?

Simulation, not a closed-form calculation. Each simulated study draws
projects and requirements from the observed 46-case collection (two-stage
bootstrap: projects with replacement, then requirements with replacement
within each drawn project, each requirement keeping all of its observed
A/C pair scores) and analyses them with the pre-registered estimator
(protocol.paired_stats.paired_probability_of_superiority).

Effect scenarios: the observed effect, and attenuated effects obtained by
turning each "C worse" pair into a tie with probability q. Attenuation is the
conservative case for a confirmatory run on new requirements, whose effect
may be smaller than in the exploratory sample (winner's curse).

Noise: the exploratory A/C pairs contain no "C better" pair at all, so
resampling them alone can never produce a reversal and makes any design look
fully powered. Each simulated pair is therefore redrawn as worse or better
(50/50) with probability `noise`: 0.047 is the discordance between two
wordings of the same complete requirement (B vs A: 4 worse, 4 better in 172
pairs), and three times that is a stress case.

Three decision rules are reported, because they can disagree:
  ci   lower bound of the 95% project-cluster bootstrap interval > 0.5
  p_intent  sign-flip p-value < 0.05 after aggregating repetitions within
            requirements; exchangeability across requirements is not
            established, so this is retained only as an optimistic diagnostic
  p_project exact sign-flip p-value that flips every requirement in a project
            together; this preserves the declared independence unit

Exploratory: the resampled pool is the exploratory sample itself, so the
projected power inherits its quirks (9 projects; per-requirement outcomes that
are nearly all-or-nothing).
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path
import random
import sys

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from protocol.paired_stats import paired_probability_of_superiority  # noqa: E402

SCORE = {(0, 1): 1.0, (0, 0): 0.5, (1, 1): 0.5, (1, 0): 0.0}


def observed_pool(results: Path, cases: Path) -> dict[str, list[list[float]]]:
    """project -> list of requirements, each a list of A/C pair scores (unknowns dropped)."""
    from scripts import selected46_report as rep
    configs = rep.load_configs(cases)
    rows = rep.pairs(rep.load_results(results, configs), configs, "A", "C", "drop")
    by_req: dict[str, list[float]] = {}
    project_of: dict[str, str] = {}
    for r in rows:
        by_req.setdefault(r["intent_id"], []).append(SCORE[(r["clean_severity"], r["defective_severity"])])
        project_of[r["intent_id"]] = r["project_id"]
    pool: dict[str, list[list[float]]] = {}
    for req in sorted(by_req):
        pool.setdefault(project_of[req], []).append(by_req[req])
    return pool


def pool_estimate(pool: dict[str, list[list[float]]]) -> float:
    reqs = [sum(s) / len(s) for reqs in pool.values() for s in reqs]
    return sum(reqs) / len(reqs)


def attenuate(scores: list[float], q: float, rng: random.Random, noise: float = 0.0) -> list[float]:
    """Worse -> tie with probability q; then each pair is redrawn as worse or better
    (50/50) with probability `noise`, the discordance seen between wordings (B vs A)."""
    out = [0.5 if s == 1.0 and rng.random() < q else s for s in scores]
    return [rng.choice((0.0, 1.0)) if rng.random() < noise else s for s in out]


def project_sign_flip_pvalue(rows: list[dict]) -> float:
    """Exact two-sided sign-flip test at the declared project unit.

    Repetitions are first averaged within requirements. A permutation then
    flips all centered requirement scores from one project together. The test
    retains equal requirement weighting in the statistic while avoiding the
    unsupported assumption that requirements from one project are independently
    exchangeable. With at most 12 planned projects, all 2**G assignments are
    enumerated.
    """
    scores_by_intent: dict[str, list[float]] = {}
    project_of: dict[str, str] = {}
    for row in rows:
        intent = row["intent_id"]
        project = row["project_id"]
        if project_of.setdefault(intent, project) != project:
            raise ValueError(f"intent {intent} appears in more than one project")
        clean, defective = row["clean_severity"], row["defective_severity"]
        score = 1.0 if defective > clean else 0.5 if defective == clean else 0.0
        scores_by_intent.setdefault(intent, []).append(score)
    centered_by_project: dict[str, list[float]] = {}
    for intent, scores in scores_by_intent.items():
        centered_by_project.setdefault(project_of[intent], []).append(sum(scores) / len(scores) - 0.5)
    projects = sorted(centered_by_project)
    if not projects:
        return 1.0
    observed = abs(sum(value for values in centered_by_project.values() for value in values))
    if observed == 0.0:
        return 1.0
    extreme = 0
    assignments = 1 << len(projects)
    for mask in range(assignments):
        randomized = 0.0
        for index, project in enumerate(projects):
            sign = 1.0 if mask & (1 << index) else -1.0
            randomized += sign * sum(centered_by_project[project])
        if abs(randomized) >= observed - 1e-12:
            extreme += 1
    return extreme / assignments


def simulate_study(pool, n_projects: int, per_project: int, q: float, rng: random.Random,
                   n_boot: int, n_perm: int, noise: float = 0.0) -> dict:
    names = sorted(pool)
    rows = []
    for p in range(n_projects):
        source = rng.choice(names)
        for k in range(per_project):
            scores = attenuate(rng.choice(pool[source]), q, rng, noise)
            for i, s in enumerate(scores):
                clean, defective = {1.0: (0, 1), 0.5: (0, 0), 0.0: (1, 0)}[s]
                rows.append({"intent_id": f"p{p}-r{k}", "project_id": f"p{p}", "model": "m",
                             "replication": i, "clean_severity": clean, "defective_severity": defective})
    est = paired_probability_of_superiority(rows, n_boot=n_boot, n_perm=n_perm, seed=rng.randrange(2**31))
    return {"estimate": est["estimate"], "ci_low": est["ci95_project_cluster"]["low"],
            "p_intent": est["paired_randomization_pvalue"],
            "p_project": project_sign_flip_pvalue(rows)}


def power_grid(pool, designs, attenuations, noises, simulations: int, seed: int, n_boot: int, n_perm: int) -> list[dict]:
    out = []
    for noise in noises:
      for q in attenuations:
        for n_projects, per_project in designs:
            rng = random.Random(f"{seed}-{noise}-{q}-{n_projects}-{per_project}")
            sims = [simulate_study(pool, n_projects, per_project, q, rng, n_boot, n_perm, noise)
                    for _ in range(simulations)]
            out.append({
                "noise": noise, "attenuation_q": q, "projects": n_projects, "requirements_per_project": per_project,
                "requirements": n_projects * per_project, "generation_calls": n_projects * per_project * 12,
                "mean_estimate": round(sum(s["estimate"] for s in sims) / len(sims), 3),
                "power_ci_lower_above_half": round(sum(s["ci_low"] is not None and s["ci_low"] > 0.5 for s in sims) / len(sims), 3),
                "power_intent_p_below_05_optimistic": round(sum(s["p_intent"] < 0.05 for s in sims) / len(sims), 3),
                "power_project_p_below_05": round(sum(s["p_project"] < 0.05 for s in sims) / len(sims), 3),
                "power_both_project": round(sum(s["ci_low"] is not None and s["ci_low"] > 0.5
                                                  and s["p_project"] < 0.05 for s in sims) / len(sims), 3),
                "simulations": simulations,
            })
            print(json.dumps(out[-1]), flush=True)
    return out


DESIGNS = [(4, 4), (6, 4), (8, 3), (8, 4), (8, 5), (8, 6), (9, 4), (12, 4)]
ATTENUATIONS = [0.0, 5 / 9, 0.8, 1.0]  # worse->tie: observed, about 0.60, about 0.55, null (type I error)
NOISES = [0.047, 0.14]  # B vs A discordance (8 of 172 pairs), and three times that


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--results", type=Path, default=ROOT / "data/selection-abc-results/20261003")
    parser.add_argument("--cases", type=Path, default=ROOT / "data/abc-cases")
    parser.add_argument("--simulations", type=int, default=1000)
    parser.add_argument("--seed", type=int, default=2026100501)
    parser.add_argument("--n-boot", type=int, default=1000)
    parser.add_argument("--n-perm", type=int, default=2000)
    parser.add_argument("--out", type=Path)
    args = parser.parse_args(argv)
    pool = observed_pool(args.results, args.cases)
    result = {
        "schema_version": "confirmatory-power/v2", "exploratory": True,
        "pool": {"projects": len(pool), "requirements": sum(len(v) for v in pool.values()),
                 "estimate": round(pool_estimate(pool), 4)},
        "pairs_per_requirement": "as observed (2 models x 2 repetitions, unknowns dropped)",
        "seed": args.seed, "n_boot": args.n_boot, "n_perm": args.n_perm,
        "noise_model": "each pair redrawn worse/better 50/50 with the given probability",
        "decision_rule": "project-level exact sign flip AND project-cluster bootstrap lower bound above 0.5",
        "intent_sign_flip_status": "optimistic diagnostic only; within-project exchangeability not established",
        "grid": power_grid(pool, DESIGNS, ATTENUATIONS, NOISES, args.simulations, args.seed, args.n_boot, args.n_perm),
    }
    text = json.dumps(result, indent=2)
    if args.out:
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_text(text + "\n")


if __name__ == "__main__":
    main()
