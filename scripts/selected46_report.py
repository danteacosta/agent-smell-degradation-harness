"""Scoreboard and pre-registered estimands for the 46 selected A/B/C cases.

Reads every finished case packet under a results root (one folder per case
with results.json, as published in data/selection-abc-results/<date>/) and
the case configs in data/abc-cases/. It works on a partial collection: cases
without results are counted as not finished, never as passes.

Outcome per run (pre-registration section 4, target rule only):
  target held      pass, non_target_only_failure          -> severity 0
  target violated  target_only_failure, mixed_failure     -> severity 1
  unknown          anything else (invalid output, browser or interface
                   error, provider error, not attempted)  -> kept, see below

Estimands:
  H1a  paired probability that C is worse than A, pairs matched by
       requirement, model and repetition, repetitions averaged within the
       requirement, project-cluster bootstrap and sign-flip p-value
       (protocol.paired_stats). Reported on observed pairs and under the
       worst and best assignment of unknowns (section 5).
  B    the same estimand for B against A (wording control).
  H1b  descriptive only here: C target-violation rate by covariate level.
       context_cue is reported as not coded until the blind coding exists.

Everything here is exploratory while the packets carry
confirmatory_eligible: false.
"""
from __future__ import annotations

import argparse
from collections import Counter, defaultdict
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from protocol.paired_stats import paired_probability_of_superiority  # noqa: E402

HELD = {"pass", "non_target_only_failure"}
VIOLATED = {"target_only_failure", "mixed_failure"}
ARMS = ("A", "B", "C")
SCREENING = [ROOT / "data/llm-screening-20261002/results.json",
             ROOT / "data/llm-screening-round2-20261003/results.json"]
PROBES = [ROOT / "data/memorization-probe-20261002/results.json",
          ROOT / "data/memorization-probe-round2-20261003/results.json"]


def severity(category: str | None) -> int | None:
    if category in HELD:
        return 0
    if category in VIOLATED:
        return 1
    return None


def load_configs(cases_dir: Path) -> dict[str, dict]:
    configs = {}
    for path in sorted(cases_dir.glob("*.json")):
        config = json.loads(path.read_text())
        if config.get("candidate_id"):
            case = config.get("case")
            if not isinstance(case, str) or not case.strip():
                raise ValueError(f"{path}: selected case requires a nonempty text case id")
            if case in configs:
                raise ValueError(f"{case}: duplicate selected case config")
            expected_keys(config)
            configs[case] = config
    return configs


def expected_keys(config: dict) -> set[tuple[str, int, str]]:
    """Return the frozen model/replication/arm slots for one selected case."""
    models = config.get("models")
    repetitions = config.get("repetitions")
    if (not isinstance(models, list) or not models
            or any(not isinstance(model, str) or not model.strip() for model in models)
            or len(set(models)) != len(models)):
        raise ValueError(f"{config.get('case')}: models must be unique nonempty strings")
    if type(repetitions) is not int or repetitions < 1:
        raise ValueError(f"{config.get('case')}: repetitions must be a positive integer")
    return {(model, rep, arm) for model in models for rep in range(1, repetitions + 1) for arm in ARMS}


def load_results(results_root: Path, configs: dict[str, dict]) -> dict[str, list[dict]]:
    runs = {}
    for path in sorted(results_root.glob("*/results.json")):
        data = json.loads(path.read_text())
        case = data.get("case")
        if case not in configs:
            raise ValueError(f"{path}: case {case!r} is not a selected case")
        if case in runs:
            raise ValueError(f"{case}: two result packets")
        if path.parent.name != case:
            raise ValueError(f"{path}: packet folder does not match case {case!r}")
        rows = data.get("rows")
        if not isinstance(rows, list):
            raise ValueError(f"{path}: rows must be a list")
        expected = expected_keys(configs[case])
        seen: set[tuple[str, int, str]] = set()
        slot_ids: set[str] = set()
        for index, row in enumerate(rows):
            if not isinstance(row, dict):
                raise ValueError(f"{path}: row {index} must be an object")
            if row.get("intent_id") != configs[case].get("intent_id", case):
                raise ValueError(f"{path}: row {index} has the wrong intent_id")
            if row.get("project_id") != configs[case]["project_id"]:
                raise ValueError(f"{path}: row {index} has the wrong project_id")
            key = (row.get("model"), row.get("replication"), row.get("arm"))
            if key not in expected:
                raise ValueError(f"{path}: row {index} is outside the frozen design: {key!r}")
            if key in seen:
                raise ValueError(f"{path}: duplicate model/replication/arm slot: {key!r}")
            slot_id = row.get("slot_id")
            if not isinstance(slot_id, str) or not slot_id.strip() or slot_id in slot_ids:
                raise ValueError(f"{path}: row {index} has a missing or duplicate slot_id")
            seen.add(key)
            slot_ids.add(slot_id)
        if seen != expected:
            missing = sorted(expected - seen)
            raise ValueError(f"{path}: completed packet is missing frozen slots: {missing!r}")
        if data.get("planned_slots") not in (None, len(expected)):
            raise ValueError(f"{path}: planned_slots disagrees with the frozen case config")
        runs[case] = rows
    return runs


def pairs(runs: dict[str, list[dict]], configs: dict[str, dict], clean: str, defective: str,
          unknown: str) -> list[dict]:
    """unknown: 'drop' (observed pairs), 'worst' or 'best'."""
    out = []
    for case, config in configs.items():
        rows = runs.get(case, [])
        by_key = {(r["model"], r["replication"], r["arm"]): r for r in rows}
        model_reps = sorted({(model, rep) for model, rep, _ in expected_keys(config)})
        for model, rep in model_reps:
            c = severity(by_key.get((model, rep, clean), {}).get("category"))
            d = severity(by_key.get((model, rep, defective), {}).get("category"))
            if c is None or d is None:
                if unknown == "drop":
                    continue
                if c is None:
                    c = 0 if unknown == "worst" else 1
                if d is None:
                    d = 1 if unknown == "worst" else 0
            out.append({"intent_id": case, "project_id": configs[case]["project_id"], "model": model,
                        "replication": rep, "clean_severity": c, "defective_severity": d})
    return out


def estimand(rows: list[dict], seed: int, assignment: str | None = None) -> dict:
    if not rows:
        return {"estimate": None, "n_pairs": 0, "n_intents": 0, "n_projects": 0}
    result = paired_probability_of_superiority(rows, seed=seed)
    if assignment is not None:
        result.update({
            "analysis_scope": "deterministic_sensitivity_bound",
            "unknown_assignment": assignment,
            "ci95_project_cluster": {"low": None, "high": None},
            "paired_randomization_pvalue": None,
            "valid_for_inference": False,
        })
    return result


def covariates(configs: dict[str, dict]) -> dict[str, dict]:
    screening = {r["candidate_id"]: r for p in SCREENING for r in json.loads(p.read_text())["rows"]}
    probe = defaultdict(dict)
    for p in PROBES:
        for r in json.loads(p.read_text())["rows"]:
            probe[r["candidate_id"]][r["coder"]] = r["memorized"]
    out = {}
    for case, config in configs.items():
        s = screening.get(config["candidate_id"], {})
        out[case] = {"numeric": s.get("numeric"), "derived_state": s.get("derived_state"),
                     "memorized": dict(probe.get(config["candidate_id"], {})),
                     "context_cue": config.get("context_cue")}
    return out


def c_violation_by(runs: dict[str, list[dict]], covs: dict[str, dict]) -> dict:
    table = {}
    for name in ("numeric", "derived_state", "memorized", "context_cue"):
        cells = defaultdict(Counter)
        for case, rows in runs.items():
            for r in rows:
                if r["arm"] != "C":
                    continue
                value = covs[case][name]
                if name == "memorized":
                    value = value.get(r["model"])
                level = "not coded" if value is None else str(int(bool(value)))
                sev = severity(r.get("category"))
                cells[level]["violated" if sev == 1 else "held" if sev == 0 else "unknown"] += 1
        table[name] = {level: dict(c) for level, c in sorted(cells.items())}
    return table


def build(results_root: Path, cases_dir: Path = ROOT / "data/abc-cases", seed: int = 2026100401) -> dict:
    configs = load_configs(cases_dir)
    runs = load_results(results_root, configs)
    counts = defaultdict(lambda: defaultdict(Counter))
    per_case = {}
    for case, rows in sorted(runs.items()):
        cell = defaultdict(Counter)
        for r in rows:
            sev = severity(r.get("category"))
            label = "held" if sev == 0 else "violated" if sev == 1 else "unknown"
            counts[r["model"]][r["arm"]][label] += 1
            cell[r["arm"]][label] += 1
        per_case[case] = {"project": configs[case]["project_id"], "candidate_id": configs[case]["candidate_id"],
                          "arms": {a: dict(cell[a]) for a in ARMS}}
    h1 = {mode: estimand(pairs(runs, configs, "A", "C", mode), seed,
                         None if mode == "drop" else mode) for mode in ("drop", "worst", "best")}
    b_control = {mode: estimand(pairs(runs, configs, "A", "B", mode), seed,
                                None if mode == "drop" else mode) for mode in ("drop", "worst", "best")}
    planned_runs = sum(len(expected_keys(config)) for config in configs.values())
    return {
        "schema_version": "selected46-report/v1",
        "confirmatory_eligible": False,
        "progress": {"selected_cases": len(configs), "finished_cases": len(runs),
                     "runs": sum(len(r) for r in runs.values()), "planned_runs": planned_runs,
                     "projects_finished": sorted({configs[c]["project_id"] for c in runs})},
        "counts_by_model_and_arm": {m: {a: dict(counts[m][a]) for a in ARMS} for m in sorted(counts)},
        "per_case": per_case,
        "h1a_c_vs_a": h1,
        "wording_control_b_vs_a": b_control,
        "h1b_c_violation_by_covariate": c_violation_by(runs, covariates(configs)),
    }


def _fmt(est: dict) -> str:
    if est.get("estimate") is None:
        return "no pairs"
    ci = est.get("ci95_project_cluster") or {}
    interval = (f"[{ci['low']:.2f}, {ci['high']:.2f}]" if ci.get("low") is not None
                else "no interval (<2 projects)")
    p = est.get("paired_randomization_pvalue")
    pair_word = "pair" if est["n_pairs"] == 1 else "pairs"
    requirement_word = "requirement" if est["n_intents"] == 1 else "requirements"
    project_word = "project" if est["n_projects"] == 1 else "projects"
    return (f"{est['estimate']:.3f} {interval}, p={p:.3f}, {est['n_pairs']} {pair_word}, "
            f"{est['n_intents']} {requirement_word}, {est['n_projects']} {project_word}")


def _fmt_bound(est: dict) -> str:
    if est.get("estimate") is None:
        return "no pairs"
    pair_word = "pair" if est["n_pairs"] == 1 else "pairs"
    requirement_word = "requirement" if est["n_intents"] == 1 else "requirements"
    project_word = "project" if est["n_projects"] == 1 else "projects"
    return (f"{est['estimate']:.3f}, {est['n_pairs']} planned {pair_word}, "
            f"{est['n_intents']} {requirement_word}, {est['n_projects']} {project_word}; no inference")


def markdown(report: dict) -> str:
    pr = report["progress"]
    lines = ["# Selected 46 requirements scoreboard", "",
             "Generated by `scripts/selected46_report.py`. Exploratory "
             "(`confirmatory_eligible: false`).", "",
             f"Cases completed: {pr['finished_cases']} of {pr['selected_cases']}; "
             f"{pr['runs']} of {pr['planned_runs']} runs; projects with any completed case: "
             f"{', '.join(pr['projects_finished']) or '—'}.", "",
             "## Target-rule outcome by model and arm", "",
             "| Model | Arm | Held | Violated | Unknown |", "| --- | --- | ---: | ---: | ---: |"]
    for model, arms in report["counts_by_model_and_arm"].items():
        for arm in ARMS:
            c = arms.get(arm, {})
            lines.append(f"| {model} | {arm} | {c.get('held', 0)} | {c.get('violated', 0)} | {c.get('unknown', 0)} |")
    lines += ["", "## Paired estimands", "",
              "Probability that the defective arm is worse than A, matched by requirement, model, and replication; "
              "0.5 means no effect. Unknowns are excluded from the observed estimate, assigned to maximize harm "
              "in the defective arm for the worst-behavior bound, and assigned to minimize harm for the "
              "best-behavior bound.", "",
              "| Comparison | Observed | Worst behavior (maximum harm) | Best behavior (minimum harm) |",
              "| --- | --- | --- | --- |"]
    for label, key in (("H1a: C vs A", "h1a_c_vs_a"), ("Control: B vs A", "wording_control_b_vs_a")):
        e = report[key]
        lines.append(f"| {label} | {_fmt(e['drop'])} | {_fmt_bound(e['worst'])} | {_fmt_bound(e['best'])} |")
    lines += ["", "## By requirement", "", "| Case | Project | A held/violated/unknown | B | C |", "| --- | --- | --- | --- | --- |"]
    for case, info in report["per_case"].items():
        cells = [f"{info['arms'][a].get('held', 0)}/{info['arms'][a].get('violated', 0)}/{info['arms'][a].get('unknown', 0)}"
                 for a in ARMS]
        lines.append(f"| {case} | {info['project']} | {cells[0]} | {cells[1]} | {cells[2]} |")
    lines += ["", "## H1b, descriptive: C violations by covariate", ""]
    for name, levels in report["h1b_c_violation_by_covariate"].items():
        parts = [f"{lvl}: {c.get('violated', 0)} violated / {c.get('held', 0)} held / {c.get('unknown', 0)} unknown"
                 for lvl, c in levels.items()]
        lines.append(f"- `{name}` — " + ("; ".join(parts) if parts else "no data"))
    lines += ["", "Repeated runs of the same requirement are not independent; the interval resamples projects. "
              "Worst/best scenarios include every frozen slot not yet collected and are deterministic bounds, not "
              "inferential tests or intervals. `context_cue` remains not coded until blind coding exists."]
    return "\n".join(lines) + "\n"


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--results", type=Path, required=True, help="folder with one sub-folder per finished case")
    parser.add_argument("--json", type=Path)
    parser.add_argument("--markdown", type=Path)
    args = parser.parse_args(argv)
    report = build(args.results)
    if args.json:
        args.json.write_text(json.dumps(report, indent=2, ensure_ascii=False) + "\n")
    text = markdown(report)
    if args.markdown:
        args.markdown.write_text(text)
    print(text)


if __name__ == "__main__":
    main()
