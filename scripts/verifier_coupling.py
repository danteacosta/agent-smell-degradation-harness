"""Verifier coupling: what the published shared-omission runs say about the tests themselves.

Offline, descriptive and post hoc. It reads only the frozen, public results of the
five evaluated tester runs (data/shared-omission-e2e/testers.json) and the
context-cue panel; it makes no model call and changes no published number.

The shared-omission study gave every tester the same frozen implementations of 25
requirements. Each implementation has an oracle role fixed before any test was
written:

  correct    arm A, passed the frozen browser oracle
  mutant     arm C, failed only on the target rule (a confirmed loss)
  recovered  arm C, passed: the generator kept the rule although it was omitted

Each tester wrote suites from three sources: the complete requirement
(spec_complete), the incomplete request (spec_incomplete), and the incomplete
request plus the code of one seeded mutant (code_incomplete). Soundness and alarms
follow scripts/mutation_adequacy.py exactly: a suite is sound when it is quiet on
the reference implementation; assertion and error alarms both count.

Four questions, all on the same frozen rows:

  Q1 ensemble   Does pooling the suites of all five testers written from the
                incomplete request recover what one tester finds from the
                complete requirement?  (information versus model diversity)
  Q2 agreement  Do the five testers miss the same confirmed losses more often
                than independent testers with the same marginal rates would?
  Q3 coupling   Are the requirements whose omitted rule the generators recover
                also those whose loss the testers notice from the incomplete
                request?
  Q4 anchoring  Within arm C, do suites alarm on implementations that kept the
                rule (recovered) more or less often than on the ones that lost it
                (mutant)?  The difference is alarm(recovered) - alarm(mutant); a
                positive value would mean the suite rewards the loss.
  Q5 soundness  How often does a suite reject the correct reference itself?

Usage:
  python scripts/verifier_coupling.py            # writes data/verifier-coupling/v1/
  python scripts/verifier_coupling.py --check    # recompute and compare
"""
from __future__ import annotations

import argparse
from collections import defaultdict
from itertools import combinations
import json
from pathlib import Path
import random
import sys

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts.mutation_adequacy import ALARMS, SOURCES, project_bootstrap, project_sign_flip  # noqa: E402

SCHEMA = "verifier-coupling/v1"
SEED = 2026102801
TESTERS_FILE = ROOT / "data/shared-omission-e2e/testers.json"
MANIFEST = ROOT / "data/shared-omission-e2e/v1/frozen-manifest-public.json"
CONTEXT_CUE = ROOT / "data/context-cue/20261004-v2/results.json"
OUT = ROOT / "data/verifier-coupling/v1"
UNUSABLE = ("generation_failed", "suite_invalid", "runner_error")


# ---------------------------------------------------------------- loading

def load_runs(testers_file: Path = TESTERS_FILE) -> list[dict]:
    """Every evaluated run listed in testers.json, in listed order. Failed runs are skipped as listed."""
    spec = json.loads(testers_file.read_text())
    runs = []
    for run in spec["runs"]:
        if run["status"] != "evaluated":
            continue
        rows = json.loads((ROOT / run["results"]).read_text())["rows"]
        runs.append({"tester": run["tester"], "provider": run["provider"], "rows": rows})
    return runs


def suites(rows: list[dict]) -> list[dict]:
    """One record per suite with soundness and the set of implementations it alarms on."""
    by_call: dict[str, list[dict]] = defaultdict(list)
    for r in rows:
        by_call[r["call_id"]].append(r)
    out = []
    for call_id, rs in sorted(by_call.items()):
        ref = [r for r in rs if r["is_reference"]]
        unusable = any(r["verdict"] in UNUSABLE for r in rs)
        sound = not unusable and len(ref) == 1 and ref[0]["verdict"] == "quiet"
        out.append({
            "call_id": call_id, "case": rs[0]["case"], "project_id": rs[0]["project_id"], "source": rs[0]["source"],
            "sound": sound,
            "alarms": {r["slot_id"] for r in rs if r["verdict"] in ALARMS},
            "roles": {r["slot_id"]: ("reference" if r["is_reference"] else r["role"]) for r in rs},
        })
    return out


def case_roles(runs: list[dict]) -> dict[str, dict]:
    """Implementation roles per case. They must be identical across runs (same frozen pages)."""
    found: dict[str, dict] = {}
    for run in runs:
        per: dict[str, dict] = {}
        for r in run["rows"]:
            c = per.setdefault(r["case"], {"project_id": r["project_id"], "slots": {}})
            role = "reference" if r["is_reference"] else r["role"]
            if c["slots"].setdefault(r["slot_id"], role) != role:
                raise ValueError(f"slot {r['slot_id']} has two roles in run {run['tester']}")
        if not found:
            found = per
        elif per != found:
            raise ValueError(f"implementation roles differ in run {run['tester']}")
    return found


# ---------------------------------------------------------------- statistics

def mean(xs):
    xs = [x for x in xs if x is not None]
    return sum(xs) / len(xs) if xs else None


def paired_by_project(values: dict[str, tuple[str, float]], seed: int = SEED) -> dict:
    """values: case -> (project, difference). Equal weight per requirement, inference by project."""
    diffs: dict[str, list[float]] = defaultdict(list)
    for project, d in values.values():
        diffs[project].append(d)
    flat = [d for _, d in values.values()]
    return {
        "requirements": len(flat), "projects": len(diffs),
        "mean_difference": mean(flat),
        "requirements_positive": sum(d > 0 for d in flat),
        "requirements_negative": sum(d < 0 for d in flat),
        "requirements_zero": sum(d == 0 for d in flat),
        "ci95_project_bootstrap": project_bootstrap(diffs, seed=seed),
        "p_exact_project_sign_flip": project_sign_flip(diffs),
    }


def spearman(x: list[float], y: list[float]) -> float | None:
    def ranks(v):
        order = sorted(range(len(v)), key=lambda i: v[i])
        r = [0.0] * len(v)
        i = 0
        while i < len(v):
            j = i
            while j + 1 < len(v) and v[order[j + 1]] == v[order[i]]:
                j += 1
            for k in range(i, j + 1):
                r[order[k]] = (i + j) / 2 + 1
            i = j + 1
        return r
    if len(x) < 3:
        return None
    rx, ry = ranks(x), ranks(y)
    mx, my = mean(rx), mean(ry)
    num = sum((a - mx) * (b - my) for a, b in zip(rx, ry))
    den = (sum((a - mx) ** 2 for a in rx) * sum((b - my) ** 2 for b in ry)) ** 0.5
    return num / den if den else None


def permutation_p(x: list[float], y: list[float], seed: int = SEED, n: int = 20000,
                  strata: list[str] | None = None) -> float | None:
    """Two-sided permutation p for Spearman rho.

    Without strata, y is permuted across all requirements. With strata (project ids), y is
    permuted only within each project, which keeps between-project differences fixed.
    """
    obs = spearman(x, y)
    if obs is None:
        return None
    rng = random.Random(seed)
    groups: dict[str, list[int]] = defaultdict(list)
    for i, g in enumerate(strata or ["all"] * len(y)):
        groups[g].append(i)
    hits = 0
    for _ in range(n):
        yy = list(y)
        for idx in groups.values():
            vals = [y[i] for i in idx]
            rng.shuffle(vals)
            for i, v in zip(idx, vals):
                yy[i] = v
        r = spearman(x, yy)
        hits += r is not None and abs(r) >= abs(obs) - 1e-12
    return (hits + 1) / (n + 1)


# ---------------------------------------------------------------- Q1 ensemble

def detection_sets(run_suites: list[dict], case: str, source: str, mutants: set[str]) -> set[str]:
    """Mutants of a case killed by at least one sound suite of this run and source."""
    hit: set[str] = set()
    for s in run_suites:
        if s["case"] == case and s["source"] == source and s["sound"]:
            hit |= s["alarms"] & mutants
    return hit


def single_score(run_suites: list[dict], case: str, source: str, mutants: set[str]) -> float | None:
    """The published per-requirement score: mean over suites of killed/mutants, unsound = 0."""
    ss = [s for s in run_suites if s["case"] == case and s["source"] == source]
    if not ss or not mutants:
        return None
    return mean([(len(s["alarms"] & mutants) / len(mutants)) if s["sound"] else 0.0 for s in ss])


def q1_ensemble(runs, all_suites, roles) -> dict:
    testers = [r["tester"] for r in runs]
    per_case = {}
    for case, info in sorted(roles.items()):
        mutants = {s for s, role in info["slots"].items() if role == "mutant"}
        if not mutants:
            continue
        rec = {"project_id": info["project_id"], "mutants": len(mutants)}
        for source in SOURCES:
            sets = {t: detection_sets(all_suites[t], case, source, mutants) for t in testers}
            curve = {}
            for k in range(1, len(testers) + 1):
                curve[str(k)] = mean([len(set().union(*(sets[t] for t in combo))) / len(mutants)
                                      for combo in combinations(testers, k)])
            rec[source] = {
                "single_tester_published_score_mean": mean([single_score(all_suites[t], case, source, mutants)
                                                            for t in testers]),
                "single_tester_any_suite_detection_mean": curve["1"],
                "union_detection_by_k_testers": curve,
            }
        per_case[case] = rec
    k_all = str(len(testers))
    contrast = {c: (r["project_id"], r["spec_incomplete"]["union_detection_by_k_testers"][k_all]
                    - r["spec_complete"]["single_tester_any_suite_detection_mean"])
                for c, r in per_case.items()}
    summary = {}
    for source in SOURCES:
        summary[source] = {k: mean([r[source]["union_detection_by_k_testers"][k] for r in per_case.values()])
                           for k in map(str, range(1, len(testers) + 1))}
    return {
        "question": "Does pooling all testers' incomplete-source suites match one tester's complete-source suites?",
        "unit": "requirement, equal weight; detection = share of confirmed mutants killed by >=1 sound suite",
        "testers": testers,
        "mean_union_detection_by_k": summary,
        "contrast_union_all_incomplete_minus_single_complete": paired_by_project(contrast),
        "requirements_where_union_incomplete_reaches_single_complete": sum(v >= -1e-12 for _, v in contrast.values()),
        "per_requirement": per_case,
    }


# ---------------------------------------------------------------- Q2 agreement

def q2_agreement(runs, all_suites, roles) -> dict:
    testers = [r["tester"] for r in runs]
    out = {}
    for source in SOURCES:
        counts: dict[str, int] = {}
        flags: dict[str, dict[str, bool]] = {}
        for case, info in roles.items():
            mutants = {s for s, role in info["slots"].items() if role == "mutant"}
            sets = {t: detection_sets(all_suites[t], case, source, mutants) for t in testers}
            for m in mutants:
                flags[m] = {t: m in sets[t] for t in testers}
                counts[m] = sum(flags[m].values())
        n = len(counts)
        rate = {t: sum(f[t] for f in flags.values()) / n for t in testers}
        expected_all_miss = 1.0
        for t in testers:
            expected_all_miss *= 1 - rate[t]
        observed_all_miss = sum(c == 0 for c in counts.values()) / n
        # Within-requirement independence: each tester's rate inside the requirement.
        within_expected = 0.0
        case_of = {m: case for case, info in roles.items() for m, role in info["slots"].items() if role == "mutant"}
        by_case: dict[str, list[str]] = defaultdict(list)
        for m in flags:
            by_case[case_of[m]].append(m)
        for case, ms in by_case.items():
            p_all_miss = 1.0
            for t in testers:
                p_all_miss *= 1 - sum(flags[m][t] for m in ms) / len(ms)
            within_expected += p_all_miss * len(ms)
        within_expected /= n
        # Project-cluster bootstrap of the excess over the pooled-independence expectation.
        project_of = {case: info["project_id"] for case, info in roles.items()}
        projects = sorted({project_of[c] for c in by_case})
        rng = random.Random(SEED)
        draws = []
        for _ in range(4000):
            ms = [m for p in (rng.choice(projects) for _ in projects)
                  for c in by_case if project_of[c] == p for m in by_case[c]]
            if not ms:
                continue
            r_t = {t: sum(flags[m][t] for m in ms) / len(ms) for t in testers}
            exp = 1.0
            for t in testers:
                exp *= 1 - r_t[t]
            draws.append(sum(counts[m] == 0 for m in ms) / len(ms) - exp)
        draws.sort()
        out[source] = {
            "mutants": n,
            "excess_missed_by_all_over_independence": observed_all_miss - expected_all_miss,
            "excess_ci95_project_bootstrap": [draws[int(0.025 * (len(draws) - 1))],
                                              draws[int(0.975 * (len(draws) - 1))]],
            "expected_missed_by_all_if_independent_within_requirement": within_expected,
            "tester_detection_rate": rate,
            "distribution_testers_detecting": {str(k): sum(c == k for c in counts.values())
                                               for k in range(len(testers) + 1)},
            "observed_missed_by_all": observed_all_miss,
            "expected_missed_by_all_if_independent": expected_all_miss,
            "observed_detected_by_all": sum(c == len(testers) for c in counts.values()) / n,
        }
    return {"question": "Do testers miss the same confirmed losses?",
            "unit": "confirmed mutant (pooled across requirements); independence uses each tester's marginal rate",
            "caveat": "Mutants of one requirement are not independent; the pooled comparison is descriptive.",
            "by_source": out}


# ---------------------------------------------------------------- Q3 coupling

def q3_coupling(runs, all_suites, roles, context_cue_file: Path = CONTEXT_CUE) -> dict:
    testers = [r["tester"] for r in runs]
    cue = {r["case"]: r["context_cue"] for r in json.loads(context_cue_file.read_text())["rows"]}
    rows = []
    for case, info in sorted(roles.items()):
        mutants = {s for s, role in info["slots"].items() if role == "mutant"}
        recovered = [s for s, role in info["slots"].items() if role == "recovered"]
        evaluable_c = len(mutants) + len(recovered)
        det = mean([single_score(all_suites[t], case, "spec_incomplete", mutants) for t in testers])
        rows.append({"case": case, "project_id": info["project_id"],
                     "generator_recovery": len(recovered) / evaluable_c if evaluable_c else None,
                     "recovered": len(recovered), "mutants": len(mutants),
                     "tester_detection_incomplete": det, "context_cue": cue.get(case)})
    usable = [r for r in rows if r["generator_recovery"] is not None and r["tester_detection_incomplete"] is not None]
    xs = [r["generator_recovery"] for r in usable]
    ys = [r["tester_detection_incomplete"] for r in usable]
    zs = [r["project_id"] for r in usable]
    by_cue = {}
    for v in (0, 1):
        sel = [r for r in rows if r["context_cue"] == v]
        by_cue[str(v)] = {"requirements": len(sel),
                          "generator_recovery_mean": mean([r["generator_recovery"] for r in sel]),
                          "tester_detection_incomplete_mean": mean([r["tester_detection_incomplete"] for r in sel])}
    return {"question": "Are rules the generators recover also the ones testers notice from the incomplete request?",
            "unit": "requirement; generator recovery = recovered / (recovered + confirmed mutants) in arm C of the 46-case "
                    "collection, restricted to these 25 eligible requirements (each has >=1 mutant by construction)",
            "spearman_rho": spearman(xs, ys), "permutation_p_two_sided": permutation_p(xs, ys),
            "within_project_permutation_p_two_sided": permutation_p(xs, ys, strata=zs),
            "requirements": len(xs),
            "by_context_cue": by_cue,
            "caveat": "Eligibility requires at least one confirmed mutant, so fully recovered rules are absent: "
                      "the range of generator recovery is truncated.",
            "per_requirement": rows}


# ---------------------------------------------------------------- Q4 anchoring

def q4_anchoring(runs, all_suites, roles, shown: dict[str, str]) -> dict:
    """Within arm C: alarm rate on recovered minus alarm rate on mutants, sound suites only."""
    out = {}
    for run in runs:
        t = run["tester"]
        per_source = {}
        for source in SOURCES:
            values = {}
            detail = {}
            for case, info in roles.items():
                rec = {s for s, role in info["slots"].items() if role == "recovered"}
                mut = {s for s, role in info["slots"].items() if role == "mutant"}
                if source == "code_incomplete":
                    mut = mut - {shown.get(case)}
                if not rec or not mut:
                    continue
                ss = [s for s in all_suites[t] if s["case"] == case and s["source"] == source and s["sound"]]
                if not ss:
                    continue
                a_rec = mean([len(s["alarms"] & rec) / len(rec) for s in ss])
                a_mut = mean([len(s["alarms"] & mut) / len(mut) for s in ss])
                values[case] = (info["project_id"], a_rec - a_mut)
                detail[case] = {"alarm_recovered": a_rec, "alarm_mutant": a_mut, "sound_suites": len(ss)}
            res = paired_by_project(values) if values else {"requirements": 0}
            res["mean_alarm_recovered"] = mean([d["alarm_recovered"] for d in detail.values()])
            res["mean_alarm_mutant"] = mean([d["alarm_mutant"] for d in detail.values()])
            res["per_requirement"] = detail
            per_source[source] = res
        out[t] = per_source
    pooled = {}
    for source in SOURCES:
        diffs = {}
        for case in roles:
            ds = [out[t][source]["per_requirement"][case] for t in out if case in out[t][source]["per_requirement"]]
            if ds:
                diffs[case] = (roles[case]["project_id"],
                               mean([d["alarm_recovered"] - d["alarm_mutant"] for d in ds]))
        pooled[source] = paired_by_project(diffs) if diffs else {"requirements": 0}
    return {"question": "Within arm C, do suites alarm more on implementations that kept the rule than on those that lost it?",
            "unit": "requirement with >=1 recovered and >=1 mutant; sound suites; code_incomplete excludes the mutant "
                    "whose code the tester saw",
            "difference": "alarm(recovered) - alarm(mutant); positive = the suite rewards the loss",
            "by_tester": out, "testers_averaged_per_requirement": pooled}


# ---------------------------------------------------------------- Q5 soundness

def q5_soundness(runs, all_suites) -> dict:
    """Share of suites that reject the correct reference implementation, by tester and source."""
    out = {}
    for run in runs:
        t = run["tester"]
        out[t] = {}
        for source in SOURCES:
            ss = [s for s in all_suites[t] if s["source"] == source]
            rejects_ref = [s for s in ss if any(s["roles"].get(slot) == "reference" for slot in s["alarms"])]
            out[t][source] = {"suites": len(ss), "sound": sum(s["sound"] for s in ss),
                              "alarm_on_reference": len(rejects_ref)}
    return {"question": "How often does a suite reject the correct reference implementation?",
            "note": "A suite that alarms on the reference is unsound and cannot kill any mutant under the published rule.",
            "by_tester": out}


# ---------------------------------------------------------------- driver

def analyse() -> dict:
    runs = load_runs()
    all_suites = {r["tester"]: suites(r["rows"]) for r in runs}
    roles = case_roles(runs)
    shown = json.loads(MANIFEST.read_text())["selected_mutants"]
    return {
        "schema_version": SCHEMA,
        "exploratory": True,
        "post_hoc": True,
        "confirmatory_eligible": False,
        "inputs": {"testers": str(TESTERS_FILE.relative_to(ROOT)), "manifest": str(MANIFEST.relative_to(ROOT)),
                   "context_cue": str(CONTEXT_CUE.relative_to(ROOT))},
        "requirements": len(roles),
        "projects": len({v["project_id"] for v in roles.values()}),
        "Q1_ensemble": q1_ensemble(runs, all_suites, roles),
        "Q2_agreement": q2_agreement(runs, all_suites, roles),
        "Q3_coupling": q3_coupling(runs, all_suites, roles),
        "Q4_anchoring": q4_anchoring(runs, all_suites, roles, shown),
        "Q5_soundness": q5_soundness(runs, all_suites),
    }


def main(argv: list[str] | None = None) -> None:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--check", action="store_true", help="recompute and compare with the published file")
    args = ap.parse_args(argv)
    result = analyse()
    text = json.dumps(result, indent=2, sort_keys=True) + "\n"
    target = OUT / "results.json"
    if args.check:
        if target.read_text() != text:
            raise SystemExit("verifier-coupling results differ from recomputation")
        print("verifier-coupling: results reproduce")
        return
    OUT.mkdir(parents=True, exist_ok=True)
    target.write_text(text)
    print(f"wrote {target.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
