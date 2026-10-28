"""Figures for the verifier-coupling report (static, for the paper draft).

Reads data/verifier-coupling/v1/results.json and writes two figures to
docs/figures/: the detection of confirmed losses by number of pooled testers and
source (F1), and generator recovery against incomplete-source detection per
requirement (F3). Colors are the validated categorical slots 1-3 of the dataviz
reference palette; every series is direct-labeled and has its own marker.
"""
from __future__ import annotations

import json
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]
RES = ROOT / "data/verifier-coupling/v1/results.json"
OUT = ROOT / "docs/figures"
INK, INK2, GRID, SURFACE = "#0b0b0b", "#52514e", "#e4e3df", "#fcfcfb"
SERIES = [("spec_complete", "Complete requirement", "#2a78d6", "o"),
          ("spec_incomplete", "Incomplete request", "#eb6834", "s"),
          ("code_incomplete", "Incomplete request + mutant code", "#1baf7a", "^")]


def style(ax):
    ax.set_facecolor(SURFACE)
    for s in ("top", "right"):
        ax.spines[s].set_visible(False)
    for s in ("left", "bottom"):
        ax.spines[s].set_color(GRID)
    ax.tick_params(colors=INK2, labelsize=9)
    ax.grid(axis="y", color=GRID, linewidth=0.8)
    ax.set_axisbelow(True)


def fig_ensemble(res):
    q = res["Q1_ensemble"]["mean_union_detection_by_k"]
    fig, ax = plt.subplots(figsize=(7.2, 3.8), facecolor=SURFACE)
    style(ax)
    for key, label, color, marker in SERIES:
        ks = sorted(q[key], key=int)
        xs, ys = [int(k) for k in ks], [q[key][k] for k in ks]
        ax.plot(xs, ys, color=color, linewidth=2, marker=marker, markersize=8,
                markeredgecolor=SURFACE, markeredgewidth=2)
        ax.annotate(f"{label}  {ys[-1]:.2f}", (xs[-1], ys[-1]), xytext=(8, 0), textcoords="offset points",
                    va="center", fontsize=9, color=INK)
    ax.set_xticks([1, 2, 3, 4, 5])
    ax.set_xlim(0.8, 5.2)
    ax.set_ylim(0, 1.05)
    ax.set_xlabel("Testers pooled (k)", color=INK2, fontsize=9)
    ax.set_ylabel("Confirmed losses detected\n(mean per requirement)", color=INK2, fontsize=9)
    ax.set_title("Pooled testers vs. the information they receive", loc="left", fontsize=11, color=INK)
    fig.text(0.01, 0.01, "25 requirements, 8 projects; detection by at least one sound suite. Exploratory, post hoc.",
             fontsize=7.5, color=INK2)
    fig.tight_layout(rect=(0, 0.04, 0.70, 1))
    return fig


def fig_coupling(res):
    rows = res["Q3_coupling"]["per_requirement"]
    fig, ax = plt.subplots(figsize=(5.2, 4.2), facecolor=SURFACE)
    style(ax)
    ax.grid(axis="x", color=GRID, linewidth=0.8)
    counts: dict[tuple, int] = {}
    for r in rows:
        key = (round(r["generator_recovery"], 3), round(r["tester_detection_incomplete"], 3))
        counts[key] = counts.get(key, 0) + 1
    for (x, y), n in counts.items():
        ax.scatter(x, y, s=48 * n, color="#eb6834", edgecolor=SURFACE, linewidth=2, zorder=3)
        if n > 1:
            ax.annotate(f"{n} requirements", (x, y), xytext=(10, 6), textcoords="offset points", fontsize=8, color=INK2)
    q3 = res["Q3_coupling"]
    ax.text(0.02, 0.97, f"Spearman ρ = {q3['spearman_rho']:.2f}\n"
                        f"within-project permutation p = {q3['within_project_permutation_p_two_sided']:.3f}",
            transform=ax.transAxes, va="top", fontsize=9, color=INK)
    ax.set_xlim(-0.05, 0.85)
    ax.set_ylim(-0.03, 0.7)
    ax.set_xlabel("Generator recovery of the omitted rule", color=INK2, fontsize=9)
    ax.set_ylabel("Detection from the incomplete request\n(mean over 5 testers)", color=INK2, fontsize=9)
    ax.set_title("Generator recovery vs. tester detection, per requirement", loc="left", fontsize=11, color=INK)
    fig.tight_layout()
    return fig


def main():
    res = json.loads(RES.read_text())
    OUT.mkdir(parents=True, exist_ok=True)
    for name, fig in (("verifier-coupling-ensemble", fig_ensemble(res)),
                      ("verifier-coupling-recovery-detection", fig_coupling(res))):
        fig.savefig(OUT / f"{name}.png", dpi=200, facecolor=SURFACE)
        fig.savefig(OUT / f"{name}.svg", facecolor=SURFACE)
        print(f"wrote docs/figures/{name}.png")


if __name__ == "__main__":
    main()
