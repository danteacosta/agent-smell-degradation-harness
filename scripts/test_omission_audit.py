"""Blind audit of how generated E2E suites missed a confirmed rule loss (#184).

The shared-omission collection (data/shared-omission-e2e/v1) shows that suites
written from the incomplete request, with or without the mutant's own code,
rarely detect the confirmed loss. This audit asks *how* they missed it, without
touching the frozen results.

Two groups, fixed from the public results before any suite is opened:

  P  passes despite the defect: the suite is sound (quiet on the correct
     reference) and quiet on the mutant that was shown to the code arm.
     Sources: spec_incomplete and code_incomplete (spec_complete has none).
  R  rejects the correct reference: the suite alarms (assertion or error) on
     the correct reference page. All three sources.

The source arm is hidden from the coders: items are mixed, renamed T001...,
and the sheet shows only the complete requirement, the omitted rule, the suite
code and (group R) the failing tests on the correct reference. It never shows
the prompt the tester received or the code it saw.

Modes
  frame   public data only; writes the audit frame (call ids and groups) and
          checks the counts. Run once, committed before any suite is opened.
  sheet   on the Mac, over the private study directory; writes the blind
          workbook, one .cjs file per item and the private key.
  score   reads the two coders' workbooks (and the adjudicated one), checks
          labels and quotes, computes agreement and kappa per group and the
          descriptive table by source; writes the public result.

Exploratory and descriptive. No hypothesis test, no change to #184.
"""
from __future__ import annotations

import argparse
from collections import Counter, defaultdict
import hashlib
import json
from pathlib import Path
import random
import sys

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

PUBLIC = ROOT / "data/shared-omission-e2e/v1"
AUDIT = PUBLIC / "test-audit"
CASES_DIR = ROOT / "data/abc-cases"
SEED = 2026100609
SOURCES = ("spec_complete", "spec_incomplete", "code_incomplete")
ALARMS = ("assertion_alarm", "error_alarm")
EXPECTED = {"P": {"spec_incomplete": 35, "code_incomplete": 17},
            "R": {"spec_complete": 11, "spec_incomplete": 11, "code_incomplete": 30}}
EXCEL_CELL = 32000

CODES = {
    "P": {
        "nao_testa_regra": "Nenhum teste tenta exercitar a situação a que a regra omitida se aplica.",
        "nao_cria_condicao": "Algum teste vai na direção da regra, mas não cria a condição em que ela se aplica "
                             "(dados iniciais, estado ou passos que a disparam).",
        "assercao_insuficiente": "Um teste cria a condição da regra, mas nenhuma asserção distingue cumprir de "
                                 "violar a regra (ex.: só verifica que a página carregou ou que algo foi salvo).",
        "espera_violacao": "Uma asserção sobre a situação da regra espera o comportamento que a viola.",
        "indeterminado": "Não é possível decidir com o material mostrado.",
    },
    "R": {
        "exige_violacao_da_regra": "A asserção que falha espera, na situação da regra omitida, um comportamento "
                                   "que viola a regra (o que o requisito completo proíbe ou não permite).",
        "contradiz_outra_parte": "A asserção que falha espera algo contrário a outra parte do requisito completo, "
                                 "não à regra omitida.",
        "exige_detalhe_nao_especificado": "A asserção que falha exige um detalhe que o requisito completo não "
                                          "determina (texto exato, rótulo, id, ordem, formato, momento) e não "
                                          "trata da regra.",
        "teste_quebrado": "A falha vem da construção do teste: seletor inexistente, espera esgotada, exceção, "
                          "preparação inválida, sem relação com o comportamento exigido.",
        "indeterminado": "Não é possível decidir com o material mostrado.",
    },
}
# Precedence when several tests qualify (first match wins).
PRECEDENCE = {
    "P": ["espera_violacao", "assercao_insuficiente", "nao_cria_condicao", "nao_testa_regra", "indeterminado"],
    "R": ["exige_violacao_da_regra", "contradiz_outra_parte", "exige_detalhe_nao_especificado",
          "teste_quebrado", "indeterminado"],
}
SOURCE_GUESS = ["completa", "incompleta", "com_codigo", "nao_sei"]
YES_NO = ["sim", "não"]
CODERS = ("codificador_a", "codificador_b")
SHEETS = {"P": "grupo_P", "R": "grupo_R"}

INSTRUCTIONS = [
    "Auditoria cega dos testes E2E gerados (omissão compartilhada, #184)",
    "",
    "Não abra data/shared-omission-e2e/v1 nem o relatório do #184 antes de terminar.",
    "Cada linha é uma suíte de testes gerada por um modelo. A pasta itens/ tem o código completo (Txxx.cjs).",
    "Você vê o requisito completo, com o trecho omitido entre [[ ]], e esse trecho isolado (regra_omitida).",
    "A regra é o que o trecho acrescenta ao requisito; leia-o no contexto da frase.",
    "Você não sabe o que o modelo recebeu; não tente adivinhar antes",
    "de codificar (há uma coluna para o palpite no fim).",
    "Preencha só as colunas amarelas, com as listas suspensas. 'citacao' é um trecho literal do código da suíte",
    "que justifica a categoria (obrigatório, exceto em nao_testa_regra e indeterminado).",
    "",
    "GRUPO P: a suíte aprovou uma implementação correta E aprovou uma implementação que perdeu a regra omitida.",
    "Pergunta: por que a suíte não pegou a perda da regra? Escolha uma categoria. Se várias se aplicam a testes",
    "diferentes, use a primeira desta ordem: " + " > ".join(PRECEDENCE["P"]) + ".",
    *[f"  {k}: {v}" for k, v in CODES["P"].items()],
    "",
    "GRUPO R: a suíte reprovou uma implementação correta (que cumpre o requisito completo).",
    "As colunas falhas_na_referencia mostram os testes que falharam e a mensagem. Pergunta: o que a asserção que",
    "falha exige? Se vários testes falham, use a primeira desta ordem: " + " > ".join(PRECEDENCE["R"]) + ".",
    *[f"  {k}: {v}" for k, v in CODES["R"].items()],
    "",
    "Campos nos dois grupos:",
    "  menciona_regra: algum teste se refere à condição da regra omitida (nome, comentário, dados ou asserção)?",
    "  palpite_fonte: só depois de codificar, que material você acha que o modelo recebeu? "
    "completa = requisito completo; incompleta = pedido sem a regra; com_codigo = pedido sem a regra + código.",
    "Codificadores trabalham separados. Divergências são resolvidas depois, na aba de adjudicação.",
]


# ---------------------------------------------------------------- frame (public)

def frame(results: dict, manifest: dict) -> dict:
    """Audit population from public outcomes only; deterministic, no suite opened."""
    selected = manifest["selected_mutants"]
    suites: dict[str, dict] = defaultdict(dict)
    for row in results["rows"]:
        s = suites[row["call_id"]]
        s.update(call_id=row["call_id"], case=row["case"], project_id=row["project_id"], source=row["source"])
        if row["is_reference"]:
            s["reference"] = row["verdict"]
        if row["slot_id"] == selected[row["case"]]:
            s["shown_mutant"] = row["verdict"]
            s["shown_mutant_slot"] = row["slot_id"]
        if row["is_reference"]:
            s["reference_slot"] = row["slot_id"]
    items = []
    for s in sorted(suites.values(), key=lambda x: x["call_id"]):
        if s["reference"] in ALARMS:
            group = "R"
        elif s["reference"] == "quiet" and s["shown_mutant"] == "quiet" and s["source"] != "spec_complete":
            group = "P"
        else:
            continue
        items.append({"call_id": s["call_id"], "case": s["case"], "project_id": s["project_id"],
                      "source": s["source"], "group": group, "reference_verdict": s["reference"],
                      "shown_mutant_verdict": s["shown_mutant"], "reference_slot": s["reference_slot"],
                      "shown_mutant_slot": s["shown_mutant_slot"]})
    counts = {g: dict(Counter(i["source"] for i in items if i["group"] == g)) for g in ("P", "R")}
    if counts != EXPECTED:
        raise ValueError(f"audit frame drift: {counts}")
    return {"schema_version": "shared-omission-test-audit-frame/v1", "seed": SEED,
            "results_sha256": sha256_text(json.dumps(results["rows"], sort_keys=True)),
            "counts": counts, "items": items, "confirmatory_eligible": False}


def sha256_text(text: str) -> str:
    return hashlib.sha256(text.encode()).hexdigest()


def omitted_span(a: str, c: str) -> str:
    from scripts.context_cue_panel import omitted_span as span
    return span(a, c)


def mark_rule(a: str, c: str) -> str:
    """The complete requirement with the omitted span wrapped in [[ ]]."""
    prefix = 0
    while prefix < len(c) and a[prefix] == c[prefix]:
        prefix += 1
    suffix = 0
    while suffix < len(c) - prefix and a[-1 - suffix] == c[-1 - suffix]:
        suffix += 1
    if prefix + suffix != len(c):
        raise ValueError("arm C is not arm A with one contiguous span removed")
    return a[:prefix] + "[[" + a[prefix:len(a) - suffix] + "]]" + a[len(a) - suffix:]


def blind_order(items: list[dict], seed: int = SEED) -> list[dict]:
    """Mix sources, then number T001...; the key maps ids back to call ids."""
    order = sorted(items, key=lambda i: i["call_id"])
    random.Random(seed).shuffle(order)
    return [{**item, "item_id": f"T{n:03d}"} for n, item in enumerate(order, start=1)]


# ---------------------------------------------------------------- sheet (private)

def failing_tests(report: dict) -> str:
    lines = []
    for t in report.get("tests", []):
        if t.get("outcome") != "pass":
            lines.append(f"[{t.get('outcome')}] {t.get('name', '')}\n  {t.get('message', '')}".rstrip())
    if report.get("status") != "complete":
        lines.append(f"[{report.get('status')}] {report.get('error', '')}")
    return "\n".join(lines)


def test_names(report: dict) -> str:
    return "\n".join(f"[{t.get('outcome')}] {t.get('name', '')}" for t in report.get("tests", []))


def load_material(study: Path, item: dict) -> dict:
    config = json.loads((CASES_DIR / f"{item['case']}.json").read_text())
    suite = (study / "calls" / item["call_id"] / "suite.cjs").read_text()
    ref = json.loads((study / "execution" / item["call_id"] / item["reference_slot"] / "report.json").read_text())
    shown = json.loads((study / "execution" / item["call_id"] / item["shown_mutant_slot"] / "report.json").read_text())
    return {"requisito_completo": mark_rule(config["arms"]["A"], config["arms"]["C"]),
            "regra_omitida": omitted_span(config["arms"]["A"], config["arms"]["C"]),
            "suite": suite,
            "testes_na_referencia": test_names(ref),
            "falhas_na_referencia": failing_tests(ref),
            "testes_no_defeituoso": test_names(shown)}


def check_private(study: Path, audit_frame: dict) -> None:
    private = json.loads((study / "results.json").read_text())
    if sha256_text(json.dumps(private["rows"], sort_keys=True)) != audit_frame["results_sha256"]:
        raise ValueError("private results differ from the published rows the frame was built from")


def build_sheet(study: Path, out: Path, audit_frame: dict) -> dict:
    from openpyxl import Workbook
    from openpyxl.styles import Alignment, Font, PatternFill
    from openpyxl.worksheet.datavalidation import DataValidation
    if out.exists():
        raise FileExistsError(f"{out} exists; the audit sheet is built once")
    check_private(study, audit_frame)
    items = blind_order(audit_frame["items"])
    out.mkdir(mode=0o700, parents=True)
    (out / "itens").mkdir()
    materials = {}
    for item in items:
        m = load_material(study, item)
        (out / "itens" / f"{item['item_id']}.cjs").write_text(m["suite"])
        materials[item["item_id"]] = m

    yellow = PatternFill("solid", fgColor="FFF2CC")
    wrap = Alignment(wrap_text=True, vertical="top")
    text_cols = {"P": ["requisito_completo", "regra_omitida", "testes_na_referencia", "testes_no_defeituoso", "suite"],
                 "R": ["requisito_completo", "regra_omitida", "falhas_na_referencia", "suite"]}
    answer_cols = lambda g: [("categoria", list(CODES[g])), ("menciona_regra", YES_NO), ("citacao", None),  # noqa: E731
                             ("palpite_fonte", SOURCE_GUESS), ("comentario", None)]

    def workbook(title: str) -> "Workbook":
        wb = Workbook()
        ws = wb.active
        ws.title = "instrucoes"
        for i, line in enumerate(INSTRUCTIONS + ["", f"Codificador: {title}"], start=1):
            ws.cell(i, 1, line).font = Font(bold=i == 1)
        ws.column_dimensions["A"].width = 140
        for group in ("P", "R"):
            s = wb.create_sheet(SHEETS[group])
            cols = text_cols[group]
            answers = answer_cols(group)
            s.append(["item", *cols, *[a for a, _ in answers]])
            for c in s[1]:
                c.font = Font(bold=True)
            rows = [i for i in items if i["group"] == group]
            for item in rows:
                m = materials[item["item_id"]]
                values = [m[c] if c != "suite" else
                          (m[c] if len(m[c]) <= EXCEL_CELL else m[c][:EXCEL_CELL] + "\n... (ver itens/)")
                          for c in cols]
                s.append([item["item_id"], *values, *[None] * len(answers)])
            first = 2 + len(cols)
            for j, (_, choices) in enumerate(answers):
                if choices:
                    col = s.cell(1, first + j).column_letter
                    dv = DataValidation(type="list", formula1='"' + ",".join(choices) + '"', allow_blank=True)
                    s.add_data_validation(dv)
                    dv.add(f"{col}2:{col}{len(rows) + 1}")
            for row in s.iter_rows(min_row=2):
                for c in row:
                    c.alignment = wrap
                for c in row[first - 1:]:
                    c.fill = yellow
            for i, w in enumerate([8, 60, 40, *[40] * (len(cols) - 3), 80, 26, 14, 50, 14, 40], start=1):
                s.column_dimensions[s.cell(1, i).column_letter].width = w
            s.freeze_panes = "B2"
        return wb

    for coder in CODERS:
        workbook(coder).save(out / f"auditoria-testes-{coder}.xlsx")
    key = {"schema_version": "shared-omission-test-audit-key/v1", "seed": SEED,
           "items": [{k: item[k] for k in ("item_id", "call_id", "case", "project_id", "source", "group")}
                     for item in items],
           "quotes_source_sha256": {i: sha256_text(m["suite"]) for i, m in materials.items()}}
    (out / "chave-privada.json").write_text(json.dumps(key, indent=2) + "\n")
    return {"dir": str(out), "items": len(items),
            "groups": dict(Counter(i["group"] for i in items)),
            "key_sha256": hashlib.sha256((out / "chave-privada.json").read_bytes()).hexdigest()}


# ---------------------------------------------------------------- score

def read_labels(path: Path, suites: dict[str, str]) -> dict[str, dict]:
    from openpyxl import load_workbook
    wb = load_workbook(path, read_only=True)
    out = {}
    for group, title in SHEETS.items():
        rows = list(wb[title].iter_rows(values_only=True))
        header = list(rows[0])
        for r in rows[1:]:
            row = dict(zip(header, r))
            item = row.get("item")
            if not item:
                continue
            if item in out:
                raise ValueError(f"{path.name}: duplicate item {item}")
            label = str(row.get("categoria") or "").strip()
            if label and label not in CODES[group]:
                raise ValueError(f"{path.name} {item}: invalid category {label!r}")
            mention = str(row.get("menciona_regra") or "").strip().lower()
            if mention and mention not in ("sim", "não", "nao"):
                raise ValueError(f"{path.name} {item}: invalid menciona_regra {mention!r}")
            guess = str(row.get("palpite_fonte") or "").strip()
            if guess and guess not in SOURCE_GUESS:
                raise ValueError(f"{path.name} {item}: invalid palpite_fonte {guess!r}")
            quote = " ".join(str(row.get("citacao") or "").split())
            if label and label not in ("nao_testa_regra", "indeterminado"):
                if not quote or quote not in " ".join(suites[item].split()):
                    raise ValueError(f"{path.name} {item}: {label} requires a literal quote from the suite")
            out[item] = {"group": group, "label": label or None,
                         "mentions_rule": {"sim": True, "não": False, "nao": False}.get(mention),
                         "source_guess": guess or None}
    return out


def score(key: dict, suites: dict[str, str], coder_a: Path, coder_b: Path, adjudicated: Path | None) -> dict:
    from scripts.llm_screening_panel import cohen_kappa
    expected = {i["item_id"]: i for i in key["items"]}
    a, b = read_labels(coder_a, suites), read_labels(coder_b, suites)
    for name, labels in (("codificador_a", a), ("codificador_b", b)):
        if set(labels) != set(expected):
            raise ValueError(f"{name}: items differ from the key")
        if any(labels[i]["group"] != expected[i]["group"] for i in labels):
            raise ValueError(f"{name}: item placed in the wrong group")
    agreement = {}
    for group in ("P", "R"):
        ids = sorted(i for i in expected if expected[i]["group"] == group and a[i]["label"] and b[i]["label"])
        la, lb = [a[i]["label"] for i in ids], [b[i]["label"] for i in ids]
        agreement[group] = {
            "coded_by_both": len(ids), "of": sum(e["group"] == group for e in expected.values()),
            "agreement": round(sum(x == y for x, y in zip(la, lb)) / len(ids), 3) if ids else None,
            "kappa": None if not ids or cohen_kappa(la, lb) is None else round(cohen_kappa(la, lb), 3),
            "disagreements": [i for i, x, y in zip(ids, la, lb) if x != y]}
    # source-guess blinding check: how often a coder guessed the true source
    guesses = Counter()
    truth = {"spec_complete": "completa", "spec_incomplete": "incompleta", "code_incomplete": "com_codigo"}
    for labels in (a, b):
        for i, v in labels.items():
            g = v["source_guess"]
            if g and g != "nao_sei":
                guesses["correct" if g == truth[expected[i]["source"]] else "wrong"] += 1
            else:
                guesses["unknown"] += 1
    result = {"schema_version": "shared-omission-test-audit/v1", "confirmatory_eligible": False,
              "agreement": agreement, "blinding_source_guesses": dict(guesses)}
    if adjudicated:
        final = read_labels(adjudicated, suites)
        if set(final) != set(expected) or any(final[i]["label"] is None for i in final):
            raise ValueError("adjudicated workbook must label every item")
        table: dict[str, dict] = {}
        for group in ("P", "R"):
            for source in SOURCES:
                ids = [i for i in expected if expected[i]["group"] == group and expected[i]["source"] == source]
                if not ids:
                    continue
                by_label = Counter(final[i]["label"] for i in ids)
                reqs = defaultdict(set)
                for i in ids:
                    reqs[final[i]["label"]].add(expected[i]["case"])
                table.setdefault(group, {})[source] = {
                    "items": len(ids),
                    "labels": {k: by_label.get(k, 0) for k in CODES[group]},
                    "requirements_per_label": {k: len(reqs.get(k, ())) for k in CODES[group]},
                    "projects": len({expected[i]["project_id"] for i in ids}),
                    "mentions_rule": sum(bool(final[i]["mentions_rule"]) for i in ids)}
        result["final"] = table
        result["items"] = [{**{k: expected[i][k] for k in ("item_id", "call_id", "case", "project_id", "source",
                                                            "group")},
                            "coder_a": a[i]["label"], "coder_b": b[i]["label"], "final": final[i]["label"],
                            "mentions_rule": final[i]["mentions_rule"]} for i in sorted(expected)]
    return result


def suites_from_dir(audit_dir: Path, key: dict) -> dict[str, str]:
    out = {}
    for item in key["items"]:
        text = (audit_dir / "itens" / f"{item['item_id']}.cjs").read_text()
        if sha256_text(text) != key["quotes_source_sha256"][item["item_id"]]:
            raise ValueError(f"suite file changed since the sheet was built: {item['item_id']}")
        out[item["item_id"]] = text
    return out


# ---------------------------------------------------------------- cli

def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    sub = parser.add_subparsers(dest="mode", required=True)
    f = sub.add_parser("frame")
    f.add_argument("--out", type=Path, default=AUDIT / "audit-frame.json")
    s = sub.add_parser("sheet")
    s.add_argument("--study", type=Path, required=True, help="private study directory (…/shared-omission-e2e-v1/study)")
    s.add_argument("--out", type=Path, required=True, help="new private directory for the workbooks")
    s.add_argument("--frame", type=Path, default=AUDIT / "audit-frame.json")
    c = sub.add_parser("score")
    c.add_argument("--audit-dir", type=Path, required=True)
    c.add_argument("--coder-a", type=Path, required=True)
    c.add_argument("--coder-b", type=Path, required=True)
    c.add_argument("--adjudicated", type=Path)
    c.add_argument("--out", type=Path)
    args = parser.parse_args(argv)
    if args.mode == "frame":
        result = frame(json.loads((PUBLIC / "results.json").read_text()),
                       json.loads((PUBLIC / "frozen-manifest-public.json").read_text()))
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_text(json.dumps(result, indent=2) + "\n")
        print(json.dumps(result["counts"]))
    elif args.mode == "sheet":
        print(json.dumps(build_sheet(args.study, args.out, json.loads(args.frame.read_text())), indent=2))
    else:
        key = json.loads((args.audit_dir / "chave-privada.json").read_text())
        result = score(key, suites_from_dir(args.audit_dir, key), args.coder_a, args.coder_b, args.adjudicated)
        text = json.dumps(result, indent=2, ensure_ascii=False)
        if args.out:
            args.out.parent.mkdir(parents=True, exist_ok=True)
            args.out.write_text(text + "\n")
        print(text)


if __name__ == "__main__":
    main()
