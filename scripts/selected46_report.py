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
            configs[config["case"]] = config
    return configs


def load_results(results_root: Path, configs: dict[str, dict]) -> dict[str, list[dict]]:
    runs = {}
    for path in sorted(results_root.glob("*/results.json")):
        data = json.loads(path.read_text())
        case = data.get("case")
        if case not in configs:
            raise ValueError(f"{path}: case {case!r} is not a selected case")
        if case in runs:
            raise ValueError(f"{case}: two result packets")
        runs[case] = data["rows"]
    return runs


def pairs(runs: dict[str, list[dict]], configs: dict[str, dict], clean: str, defective: str,
          unknown: str) -> list[dict]:
    """unknown: 'drop' (observed pairs), 'worst' or 'best'."""
    out = []
    for case, rows in runs.items():
        by_key = {(r["model"], r["replication"], r["arm"]): r for r in rows}
        for model, rep in sorted({(r["model"], r["replication"]) for r in rows}):
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


def estimand(rows: list[dict], seed: int) -> dict:
    if not rows:
        return {"estimate": None, "n_pairs": 0, "n_intents": 0, "n_projects": 0}
    return paired_probability_of_superiority(rows, seed=seed)


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
                level = "não codificado" if value is None else str(int(bool(value)))
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
    h1 = {mode: estimand(pairs(runs, configs, "A", "C", mode), seed) for mode in ("drop", "worst", "best")}
    b_control = {mode: estimand(pairs(runs, configs, "A", "B", mode), seed) for mode in ("drop", "worst", "best")}
    return {
        "schema_version": "selected46-report/v1",
        "confirmatory_eligible": False,
        "progress": {"selected_cases": len(configs), "finished_cases": len(runs),
                     "runs": sum(len(r) for r in runs.values()),
                     "projects_finished": sorted({configs[c]["project_id"] for c in runs})},
        "counts_by_model_and_arm": {m: {a: dict(counts[m][a]) for a in ARMS} for m in sorted(counts)},
        "per_case": per_case,
        "h1a_c_vs_a": h1,
        "wording_control_b_vs_a": b_control,
        "h1b_c_violation_by_covariate": c_violation_by(runs, covariates(configs)),
    }


def _fmt(est: dict) -> str:
    if est.get("estimate") is None:
        return "sem pares"
    ci = est.get("ci95_project_cluster") or {}
    interval = (f"[{ci['low']:.2f}, {ci['high']:.2f}]" if ci.get("low") is not None
                else "sem intervalo (menos de 2 projetos)")
    p = est.get("paired_randomization_pvalue")
    return (f"{est['estimate']:.3f} {interval}, p={p:.3f}, {est['n_pairs']} pares, "
            f"{est['n_intents']} requisitos, {est['n_projects']} projetos")


def markdown(report: dict) -> str:
    pr = report["progress"]
    lines = ["# Placar dos 46 requisitos selecionados", "",
             f"Gerado por `scripts/selected46_report.py`. Exploratório (`confirmatory_eligible: false`).", "",
             f"Requisitos concluídos: {pr['finished_cases']} de {pr['selected_cases']}; "
             f"{pr['runs']} execuções; projetos com algum caso concluído: {', '.join(pr['projects_finished']) or '—'}.", "",
             "## Regra-alvo por modelo e braço", "",
             "| Modelo | Braço | Mantida | Violada | Desconhecido |", "| --- | --- | ---: | ---: | ---: |"]
    for model, arms in report["counts_by_model_and_arm"].items():
        for arm in ARMS:
            c = arms.get(arm, {})
            lines.append(f"| {model} | {arm} | {c.get('held', 0)} | {c.get('violated', 0)} | {c.get('unknown', 0)} |")
    lines += ["", "## Estimandos pareados", "",
              "Probabilidade de o braço com defeito ser pior que A, por requisito, modelo e repetição; "
              "0,5 = sem efeito. Desconhecidos: excluídos (observado), atribuídos contra (pior caso) ou a favor (melhor caso) da hipótese.", "",
              "| Comparação | Observado | Pior caso | Melhor caso |", "| --- | --- | --- | --- |"]
    for label, key in (("H1a: C vs A", "h1a_c_vs_a"), ("Controle: B vs A", "wording_control_b_vs_a")):
        e = report[key]
        lines.append(f"| {label} | {_fmt(e['drop'])} | {_fmt(e['worst'])} | {_fmt(e['best'])} |")
    lines += ["", "## Por requisito", "", "| Caso | Projeto | A mantida/violada/desc. | B | C |", "| --- | --- | --- | --- | --- |"]
    for case, info in report["per_case"].items():
        cells = [f"{info['arms'][a].get('held', 0)}/{info['arms'][a].get('violated', 0)}/{info['arms'][a].get('unknown', 0)}"
                 for a in ARMS]
        lines.append(f"| {case} | {info['project']} | {cells[0]} | {cells[1]} | {cells[2]} |")
    lines += ["", "## H1b, descritivo: violação em C por covariável", ""]
    for name, levels in report["h1b_c_violation_by_covariate"].items():
        parts = [f"{lvl}: {c.get('violated', 0)} violadas / {c.get('held', 0)} mantidas / {c.get('unknown', 0)} desc."
                 for lvl, c in levels.items()]
        lines.append(f"- `{name}` — " + ("; ".join(parts) if parts else "sem dados"))
    lines += ["", "Execuções repetidas do mesmo requisito não são independentes; o intervalo reamostra projetos. "
              "`context_cue` aparece como não codificado até existir a codificação cega."]
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
