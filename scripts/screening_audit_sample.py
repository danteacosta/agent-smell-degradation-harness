"""Blind human audit of a random 20% of the confirmatory screening decisions.

Pre-registration section 3 (reviewers): "a human audit of a random 20% of
panel decisions is planned before any confirmatory claim". This covers the two
confirmatory screening panels of 2026-10-05 (reserve and 2024 window).

  build  draw the sample and write a blind .xlsx: the auditor sees exactly
         what the panel saw (project, file, removed and added sentences) and
         the same three criteria; never the panel's decision, reason, target
         rule or route. Only the drawn candidate ids and the seed are written
         to the manifest, so the stratum (which encodes the decision) is not
         revealed; score recomputes it.
  score  compare the filled sheet with the panel's consensus: agreement,
         Cohen's kappa overall and by stratum, and every disagreement.

Sampling: the 365 decided candidates (2 unresolved are not decisions and
are left out) are stratified by option x project x panel decision; the
ceil(20%) = 73 draws are allocated proportionally by largest remainder, at
least one per non-empty stratum when the total allows, and drawn with a
fixed seed inside each stratum.
"""
from __future__ import annotations

import argparse
from collections import Counter
import json
import math
from pathlib import Path
import random
import sys

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

OPTIONS = {
    "reserve": (ROOT / "data/llm-screening-confirmatory-reserve-20261005/results.json",
                ROOT / "data/requirement-sampling/screening-confirmatory-reserve-20261005.json"),
    "w2024": (ROOT / "data/llm-screening-confirmatory-w2024-20261005/results.json",
              ROOT / "data/requirement-sampling/screening-confirmatory-w2024-20261005.json"),
}
SEED = 2026100505
FRACTION = 0.20
OUT_DIR = ROOT / "data/human-audit"
SHEET = OUT_DIR / "screening-audit-sheet-20261005.xlsx"
MANIFEST = OUT_DIR / "screening-audit-sample-20261005.json"
REASONS = ("admit", "operations_or_configuration", "not_web_interface", "no_rule_change",
           "no_single_testable_rule", "needs_multiple_systems")

INSTRUCTIONS = [
    "Auditoria humana cega de 20% da triagem confirmatória (05/10)",
    "",
    "Não abra data/llm-screening-confirmatory-*/ antes de terminar: as decisões do painel não estão nesta planilha.",
    "Cada linha é uma mudança na documentação de usuário de um projeto: frases removidas (-) e acrescentadas (+).",
    "Decida se a mudança contém uma regra de comportamento que atende aos TRÊS critérios:",
    "1. Um usuário consegue observá-la na interface WEB do produto. Não contam instalação, configuração de",
    "   servidor ou autenticação, linha de comando, só API, recursos só mobile ou desktop, nem cenários com vários servidores.",
    "2. Pode ser escrita como UMA obrigação testável, com uma observação que passa e uma que falha.",
    "3. Uma página web pequena e autocontida, imitando aquela tela, conseguiria exercitá-la sem o produto inteiro.",
    "",
    "decisao: admit ou exclude. motivo: 'admit' exatamente quando decisao = admit; senão o critério que falhou:",
    "  operations_or_configuration, not_web_interface, no_rule_change, no_single_testable_rule, needs_multiple_systems.",
    "regra_alvo: se admit, a regra em uma frase. Comentário: dúvidas ou casos de fronteira.",
]


def load_options() -> list[dict]:
    items = []
    for option, (results, sample) in OPTIONS.items():
        texts = {c["candidate_id"]: c for c in json.loads(sample.read_text())["candidates"]}
        for r in json.loads(results.read_text())["rows"]:
            if r["consensus"] not in ("admit", "exclude"):
                continue
            c = texts[r["candidate_id"]]
            items.append({"option": option, "candidate_id": r["candidate_id"], "project": c["project"],
                          "file": c["file"], "removed": c["removed"], "added": c["added"],
                          "panel": r["consensus"], "panel_rule": r.get("target_rule")})
    return items


def allocate(sizes: dict, total: int) -> dict:
    n = sum(sizes.values())
    quota = {k: total * v / n for k, v in sizes.items()}
    alloc = {k: math.floor(q) for k, q in quota.items()}
    for k in sorted(quota, key=lambda k: (-(quota[k] - alloc[k]), k))[:total - sum(alloc.values())]:
        alloc[k] += 1
    # at least one per stratum when possible, taken from the largest allocations
    for k in sorted(sizes):
        if alloc[k] == 0 and sizes[k] > 0:
            donor = max((d for d in alloc if alloc[d] > 1), key=lambda d: (alloc[d], d), default=None)
            if donor is None:
                break
            alloc[donor] -= 1
            alloc[k] = 1
    return alloc


def draw(items: list[dict]) -> list[dict]:
    strata: dict[tuple, list[dict]] = {}
    for it in items:
        strata.setdefault((it["option"], it["project"], it["panel"]), []).append(it)
    total = math.ceil(FRACTION * len(items))
    alloc = allocate({k: len(v) for k, v in strata.items()}, total)
    rng = random.Random(SEED)
    chosen = []
    for key in sorted(strata):
        pool = sorted(strata[key], key=lambda i: i["candidate_id"])
        chosen.extend(rng.sample(pool, alloc[key]))
    return chosen


def build() -> dict:
    from openpyxl import Workbook
    from openpyxl.styles import Alignment, Font, PatternFill
    from openpyxl.worksheet.datavalidation import DataValidation
    if SHEET.exists() or MANIFEST.exists():
        raise FileExistsError("the screening audit sample is drawn once")
    items = load_options()
    chosen = draw(items)
    order = chosen[:]
    random.Random(f"{SEED}-order").shuffle(order)
    wb = Workbook()
    ws = wb.active
    ws.title = "instrucoes"
    for i, line in enumerate(INSTRUCTIONS, start=1):
        ws.cell(i, 1, line).font = Font(bold=i == 1)
    ws.column_dimensions["A"].width = 140
    s = wb.create_sheet("triagem")
    s.append(["ordem", "id", "projeto", "arquivo", "removidas (-)", "acrescentadas (+)",
              "decisao", "motivo", "regra_alvo", "comentario"])
    for c in s[1]:
        c.font = Font(bold=True)
    for n, it in enumerate(order, start=1):
        s.append([n, it["candidate_id"], it["project"], it["file"], "\n".join(f"- {x}" for x in it["removed"]),
                  "\n".join(f"+ {x}" for x in it["added"]), None, None, None, None])
    for col, choices in (("G", ("admit", "exclude")), ("H", REASONS)):
        dv = DataValidation(type="list", formula1='"' + ",".join(choices) + '"', allow_blank=True)
        s.add_data_validation(dv)
        dv.add(f"{col}2:{col}{len(order) + 1}")
    yellow, wrap = PatternFill("solid", fgColor="FFF2CC"), Alignment(wrap_text=True, vertical="top")
    for row in s.iter_rows(min_row=2):
        for c in row:
            c.alignment = wrap
        for c in row[6:]:
            c.fill = yellow
    for col, w in zip("ABCDEFGHIJ", (7, 18, 13, 40, 60, 60, 12, 26, 50, 40)):
        s.column_dimensions[col].width = w
    s.freeze_panes = "C2"
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    wb.save(SHEET)
    manifest = {"schema_version": "screening-human-audit-sample/v1", "seed": SEED, "fraction": FRACTION,
                "population": len(items), "sample": len(chosen),
                "stratification": "option x project x panel decision; largest remainder; >=1 per stratum",
                "candidate_ids": sorted(it["candidate_id"] for it in chosen),
                "sources": {o: [str(p.relative_to(ROOT)) for p in paths] for o, paths in OPTIONS.items()}}
    MANIFEST.write_text(json.dumps(manifest, indent=2) + "\n")
    return {"sheet": str(SHEET.relative_to(ROOT)), "population": len(items), "sample": len(chosen),
            "by_option": dict(Counter(it["option"] for it in chosen))}


def score(sheet_path: Path) -> dict:
    from openpyxl import load_workbook
    from scripts.llm_screening_panel import cohen_kappa
    panel = {it["candidate_id"]: it for it in load_options()}
    rows = list(load_workbook(sheet_path, read_only=True)["triagem"].iter_rows(values_only=True))
    header = list(rows[0])
    answered, bad = [], []
    for r in rows[1:]:
        rec = dict(zip(header, r))
        if not rec.get("id"):
            continue
        decision = str(rec.get("decisao") or "").strip().lower()
        reason = str(rec.get("motivo") or "").strip()
        if not decision:
            continue
        if decision not in ("admit", "exclude") or reason not in REASONS or (decision == "admit") != (reason == "admit"):
            bad.append(rec["id"])
            continue
        answered.append((rec["id"], decision, reason, rec.get("regra_alvo")))
    pairs = [(h, panel[i]["panel"]) for i, h, _, _ in answered]
    by_decision = {d: {"n": sum(1 for _, p in pairs if p == d),
                       "agree": sum(1 for h, p in pairs if p == d and h == p)} for d in ("admit", "exclude")}
    return {
        "answered": len(answered), "of": len(json.loads(MANIFEST.read_text())["candidate_ids"]),
        "malformed": bad,
        "agreement": round(sum(h == p for h, p in pairs) / len(pairs), 3) if pairs else None,
        "kappa": cohen_kappa([h for h, _ in pairs], [p for _, p in pairs]) if pairs else None,
        "by_panel_decision": by_decision,
        "disagreements": [{"candidate_id": i, "project": panel[i]["project"], "option": panel[i]["option"],
                           "human": h, "human_reason": reason, "panel": panel[i]["panel"]}
                          for i, h, reason, _ in answered if h != panel[i]["panel"]],
        "both_admit_rules": [{"candidate_id": i, "human_rule": rule, "panel_rule": panel[i]["panel_rule"]}
                             for i, h, _, rule in answered if h == "admit" == panel[i]["panel"]],
    }


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    sub = parser.add_subparsers(dest="mode", required=True)
    sub.add_parser("build")
    sub.add_parser("score").add_argument("sheet", type=Path)
    args = parser.parse_args(argv)
    print(json.dumps(build() if args.mode == "build" else score(args.sheet), indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
