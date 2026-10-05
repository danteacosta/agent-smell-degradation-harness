"""t1/tn evidence for the historical arm: who changed the rule, what each model did, screenshots.

For each of the 17 admitted requirements: t1 is the requirement as documented
before the commit that wrote the rule (arm H), tn the documentation at the
frame end (arm A). This script assembles, without new model calls:

  table        commit, author, date and link of the change; t1 and tn texts;
               the outcome of every A/H run by model and repetition
  screenshots  (on the Mac) copy the oracle screenshots of every pair where
               t1 and tn differ from the private packets into the repository,
               each verified against the sha256 recorded in results.json
  gallery      one self-contained HTML page: per requirement, the change, then
               the t1 and tn screenshots side by side for each differing pair

Outcomes come from the frozen collection (data/historical-arm-results/v1);
nothing is re-run or re-judged here.
"""
from __future__ import annotations

import argparse
import base64
import hashlib
import html
import json
from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

RESULTS = ROOT / "data/historical-arm-results/v1"
CASES = ROOT / "data/historical-arm/cases"
OUT = RESULTS / "t1-tn"
REPOS = {"grist": "gristlabs/grist-help", "immich": "immich-app/immich", "mattermost": "mattermost/docs",
         "mealie": "mealie-recipes/mealie", "nextcloud": "nextcloud/documentation", "openproject": "opf/openproject",
         "paperless-ngx": "paperless-ngx/paperless-ngx", "wekan": "wekan/wekan", "zulip": "zulip/zulip"}
CLONE = {"paperless-ngx": "paperless"}


def severity(category):
    from scripts.selected46_report import severity as s
    return s(category)


def commit_meta(repos: Path | None, project: str, sha: str) -> dict:
    meta = {"commit": sha, "url": f"https://github.com/{REPOS[project]}/commit/{sha}"}
    if repos is not None:
        out = subprocess.run(["git", "-C", str(repos / CLONE.get(project, project)), "show", "-s",
                              "--format=%an%x1f%as%x1f%s", sha], capture_output=True, text=True, check=True).stdout
        author, date, subject = out.strip().split("\x1f", 2)
        meta.update(author=author, date=date, subject=subject)
    return meta


def pairs(case: str, config: dict) -> list[dict]:
    rows = json.loads((RESULTS / case / "results.json").read_text())["rows"]
    by = {(r["model"], r["replication"], r["arm"]): r for r in rows}
    out = []
    for model in config["models"]:
        for rep in range(1, config["repetitions"] + 1):
            a, h = by[(model, rep, "A")], by[(model, rep, "H")]
            sa, sh = severity(a.get("category")), severity(h.get("category"))
            verdict = ("unknown" if sa is None or sh is None else
                       "t1_worse" if (sa, sh) == (0, 1) else "t1_better" if (sa, sh) == (1, 0) else
                       "both_held" if sa == 0 else "both_violated")
            out.append({"model": model, "replication": rep, "verdict": verdict,
                        "tn": {"slot_id": a["slot_id"], "category": a.get("category"),
                               "screenshots": a.get("execution", {}).get("screenshots", {})},
                        "t1": {"slot_id": h["slot_id"], "category": h.get("category"),
                               "screenshots": h.get("execution", {}).get("screenshots", {})}})
    return out


def table(repos: Path | None) -> dict:
    rows = []
    for path in sorted(CASES.glob("*.json")):
        config = json.loads(path.read_text())
        hist = config["historical"]
        ps = pairs(config["case"], config)
        rows.append({
            "case": config["case"], "project": config["project_id"],
            "change": commit_meta(repos, config["project_id"], hist["commit"]), "file": hist["file"],
            "t1_kind": "rule absent before the commit" if hist["construction"] == "absent_h_equals_c"
                       else "vaguer passage before the commit",
            "t1_old_passage": hist.get("old_quote"),
            "omitted_rule": None, "t1": config["arms"]["H"], "tn": config["arms"]["A"],
            "pairs": ps, "differs": any(p["verdict"] in ("t1_worse", "t1_better") for p in ps)})
    for r in rows:
        from scripts.historical_arm import omitted_span
        config = json.loads((CASES / f"{r['case']}.json").read_text())
        s, e = omitted_span(config["arms"]["A"], config["arms"]["C"])
        r["omitted_rule"] = config["arms"]["A"][s:e].strip()
    return {"schema_version": "historical-t1-tn/v1", "confirmatory_eligible": False,
            "requirements": len(rows), "requirements_where_t1_and_tn_differ": sum(r["differs"] for r in rows),
            "rows": rows}


def markdown(data: dict) -> str:
    lines = ["# Reconstrução histórica H (t1) vs referência A (tn)", "",
             "t1 é o braço H reconstruído: C nos casos de regra ausente, ou C mais uma citação antiga nos casos mais vagos. Não é a documentação antiga integral. tn é A no corte de 30/09/2026, não necessariamente a versão imediatamente posterior ao commit. A comparação é exploratória.", "",
             f"{data['requirements_where_t1_and_tn_differ']} de {data['requirements']} requisitos deram resultado "
             "diferente entre t1 e tn em pelo menos um par modelo × repetição. Fonte: coleta congelada "
             "`data/historical-arm-results/v1`; sem novas chamadas.", "",
             "| Requisito | Mudança (autor, data) | t1 | luna r1/r2 | sol r1/r2 |", "| --- | --- | --- | --- | --- |"]
    short = {"t1_worse": "t1 pior", "t1_better": "t1 melhor", "both_held": "ambos ok", "both_violated": "ambos falham",
             "unknown": "desconhecido"}
    for r in data["rows"]:
        c = r["change"]
        who = f"[{c['commit'][:10]}]({c['url']})" + (f", {c['author']}, {c['date']}" if "author" in c else "")
        cells = {m: " / ".join(short[p["verdict"]] for p in r["pairs"] if p["model"] == m)
                 for m in ("gpt-5.6-luna", "gpt-5.6-sol")}
        kind = "regra ausente" if r["t1_kind"].startswith("rule absent") else "passagem mais vaga"
        lines.append(f"| {r['case']} | {who} | {kind} | {cells['gpt-5.6-luna']} | {cells['gpt-5.6-sol']} |")
    lines += ["", "t1 pior = a regra foi seguida com o texto tn e violada com o texto t1, no mesmo modelo e repetição.",
              "Prints: `data/historical-arm-results/v1/t1-tn/screenshots/` (copiados dos pacotes privados com hash "
              "conferido) e a galeria `gallery.html`."]
    return "\n".join(lines) + "\n"


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def collect_screenshots(data: dict, packets: Path) -> dict:
    """Copy screenshots of every differing pair from the private packets, verifying each hash."""
    copied, missing = 0, []
    for r in data["rows"]:
        for p in r["pairs"]:
            if p["verdict"] not in ("t1_worse", "t1_better"):
                continue
            for arm in ("t1", "tn"):
                for name, digest in p[arm]["screenshots"].items():
                    dest = OUT / "screenshots" / r["case"] / f"{p['model']}-r{p['replication']}-{arm}-{name}"
                    if dest.exists() and sha256(dest) == digest:
                        continue
                    found = [f for f in (packets / r["case"] / "execution" / p[arm]["slot_id"]).rglob(name)
                             if sha256(f) == digest]
                    if not found:
                        missing.append(str(dest.relative_to(OUT)))
                        continue
                    dest.parent.mkdir(parents=True, exist_ok=True)
                    dest.write_bytes(found[0].read_bytes())
                    copied += 1
    return {"copied": copied, "missing": missing}


def gallery(data: dict) -> str:
    def img(path: Path) -> str:
        if not path.exists():
            return "<div class='missing'>print não publicado</div>"
        return f"<img alt='' src='data:image/png;base64,{base64.b64encode(path.read_bytes()).decode()}'>"

    parts = []
    for r in data["rows"]:
        if not r["differs"]:
            continue
        c = r["change"]
        who = html.escape(f"{c.get('author', '')}, {c.get('date', '')}".strip(", "))
        parts.append(f"<section><h2>{html.escape(r['case'])}</h2>"
                     f"<p class='meta'>Mudança: <a href='{c['url']}'>{c['commit'][:10]}</a> {who}"
                     f"{(' · ' + html.escape(c['subject'])) if 'subject' in c else ''}</p>"
                     f"<p><b>Regra (tn):</b> {html.escape(r['omitted_rule'])}</p>"
                     f"<p><b>t1:</b> {html.escape(r['t1_kind'])}"
                     f"{(': ' + html.escape(r['t1_old_passage'])) if r['t1_old_passage'] else ''}</p>")
        for p in r["pairs"]:
            if p["verdict"] not in ("t1_worse", "t1_better"):
                continue
            parts.append(f"<h3>{p['model']} · repetição {p['replication']} · "
                         f"{'t1 violou, tn seguiu' if p['verdict'] == 't1_worse' else 't1 seguiu, tn violou'}</h3>"
                         "<div class='pair'>")
            for arm, label in (("t1", "t1 (antes)"), ("tn", "tn (depois)")):
                shots = "".join(img(OUT / "screenshots" / r["case"] / f"{p['model']}-r{p['replication']}-{arm}-{n}")
                                for n in sorted(p[arm]["screenshots"]))
                parts.append(f"<figure><figcaption>{label}: {html.escape(str(p[arm].get('category')))}</figcaption>"
                             f"{shots}</figure>")
            parts.append("</div>")
        parts.append("</section>")
    return ("<!doctype html><html lang='pt-BR'><head><meta charset='utf-8'><meta name='viewport' "
            "content='width=device-width,initial-scale=1'><title>t1 vs tn</title><style>"
            ":root{--bg:#fff;--fg:#1b1b1b;--muted:#666;--line:#ddd}"
            "@media (prefers-color-scheme:dark){:root{--bg:#161616;--fg:#eee;--muted:#aaa;--line:#333}}"
            "body{background:var(--bg);color:var(--fg);font:15px/1.5 system-ui,sans-serif;margin:0 auto;"
            "max-width:1100px;padding:16px}a{color:inherit}.meta{color:var(--muted)}section{border-top:1px solid "
            "var(--line);padding-top:8px;margin-top:24px}.pair{display:grid;grid-template-columns:1fr 1fr;gap:12px}"
            "@media (max-width:700px){.pair{grid-template-columns:1fr}}figure{margin:0}img{width:100%;border:1px "
            "solid var(--line);margin-bottom:6px}figcaption{font-weight:600;margin-bottom:4px}"
            ".missing{border:1px dashed var(--line);padding:24px;color:var(--muted);text-align:center}</style>"
            "</head><body><h1>Reconstrução histórica H (t1) vs referência A (tn)</h1>"
            "<p>t1 é H: C quando a regra estava ausente, ou C mais a citação antiga quando era mais vaga. "
            "Não é a documentação antiga integral. tn é A no corte de 30/09/2026, não necessariamente "
            "a versão imediatamente posterior ao commit. A comparação é exploratória.</p>"
            f"<p class='meta'>{data['requirements_where_t1_and_tn_differ']} de {data['requirements']} requisitos "
            "com resultado diferente. Coleta congelada, sem novas chamadas; exploratório.</p>"
            + "".join(parts) + "</body></html>")


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    sub = parser.add_subparsers(dest="mode", required=True)
    t = sub.add_parser("table")
    t.add_argument("--repos", type=Path, help="clones of the nine projects (adds author, date and subject)")
    s = sub.add_parser("screenshots")
    s.add_argument("--packets", type=Path, required=True, help="private historical-arm-v1 packet folder")
    sub.add_parser("gallery")
    args = parser.parse_args(argv)
    OUT.mkdir(parents=True, exist_ok=True)
    if args.mode == "table":
        data = table(args.repos)
        (OUT / "table.json").write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n")
        (OUT / "table.md").write_text(markdown(data))
        print(markdown(data))
        return
    data = json.loads((OUT / "table.json").read_text())
    if args.mode == "screenshots":
        print(json.dumps(collect_screenshots(data, args.packets), indent=2))
    else:
        (OUT / "gallery.html").write_text(gallery(data))
        print(OUT / "gallery.html")


if __name__ == "__main__":
    main()
