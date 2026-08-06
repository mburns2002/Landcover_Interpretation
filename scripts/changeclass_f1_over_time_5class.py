#!/usr/bin/env python3
"""changeclass_f1_over_time_5class: five-class change-class F1 over the bracket years.

For the 5-class collapse, plot the per-class F1 of the four change classes (Harvest, Development, Beaver,
Insect/Disease) as a function of the temporal bracket (2017-2019 ... 2021-2023). One small-multiple panel
per source (v2..v6 and the spectral baseline spec_all), since the trajectory depends on the model; the
four change classes are lines, colored by the change-class palette.

F1 is recomputed per (source, bracket) by reusing pres_14's computation on the common cell set, so the
numbers match Figure 14 / pres_18 exactly.

Outputs:
  reports/changeclass_f1_over_time/changeclass_f1_over_time_5class.png
  reports/changeclass_f1_over_time/changeclass_f1_over_time_5class.csv   (tidy: source, bracket, class, f1)
"""

import importlib.util
import os
import sys

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ROOT, "reports", "changeclass_f1_over_time")

# reuse pres_14's five-class computation (per-bracket F1 per source per change class)
sys.path.insert(0, os.path.join(ROOT, "presentation", "scripts"))     # pres_14 imports slide_font
_p = os.path.join(ROOT, "presentation", "scripts", "pres_14_changeclass_f1_5class.py")
_spec = importlib.util.spec_from_file_location("P14", _p)
P14 = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(P14)
# keep this a plain reports figure (pres_14 sets the Spectral deck font on import)
plt.rcParams.update({"font.family": "sans-serif",
                     "font.sans-serif": ["Helvetica", "Arial", "DejaVu Sans"]})

BRACKETS = P14.BRACKETS                      # 2017_2019 ... 2021_2023
SOURCES = P14.SOURCES                        # v2..v6, spec_all
CHANGE = P14.CHANGE                          # [(2,Harvest),(3,Development),(5,Beaver),(4,Insect/Disease)]
# change palette, with a darker gold for Harvest so the line reads on white
LINE_COLOR = {"Harvest": "#C9A227", "Development": "red", "Beaver": "orange", "Insect/Disease": "#70A2DB"}
# per-model palette (matches pres_17/pres_18): embeddings + brown spec_all
MODEL_COLOR = {"v2": "#1f77b4", "v3": "#2ca02c", "v4": "#9467bd", "v5": "#ff7f0e", "v6": "#d62728",
               "spec_all": "#8c564b"}


def _blab(b):
    a, c = b.split("_")
    return str((int(a) + int(c)) // 2)   # 2017_2019 -> center year 2018


def main():
    _mat, per_bracket, n_cells, per_bracket_n = P14.compute()
    print(f"common cell set N = {n_cells}  (per bracket: {per_bracket_n})")

    os.makedirs(OUT, exist_ok=True)
    # tidy CSV
    rows = ["source,bracket,class,f1"]
    for s in SOURCES:
        for b in BRACKETS:
            for j, (_c, name) in enumerate(CHANGE):
                rows.append(f"{s},{b},{name},{per_bracket[b][s][j]:.6f}")
    with open(os.path.join(OUT, "changeclass_f1_over_time_5class.csv"), "w") as f:
        f.write("\n".join(rows) + "\n")

    xs = np.arange(len(BRACKETS))
    peak = np.nanmax([per_bracket[b][s][j] for b in BRACKETS for s in SOURCES
                      for j in range(len(CHANGE))])
    ymax = float(np.ceil(peak * 20)) / 20 + 0.02      # round up to a clean tick, small headroom

    fig, axes = plt.subplots(2, 3, figsize=(13, 7), sharex=True, sharey=True)
    for ax, s in zip(axes.ravel(), SOURCES):
        for j, (_c, name) in enumerate(CHANGE):
            vals = [per_bracket[b][s][j] for b in BRACKETS]
            ax.plot(xs, vals, "-o", color=LINE_COLOR[name], lw=2, ms=6, label=name, zorder=3)
        ax.set_title(s, fontsize=14, fontweight="bold")
        ax.set_ylim(0, ymax)
        ax.set_xticks(xs)
        ax.set_xticklabels([_blab(b) for b in BRACKETS], fontsize=11)
        ax.tick_params(axis="y", labelsize=11)
        ax.grid(False)
        for sp in ("top", "right"):
            ax.spines[sp].set_visible(False)
    for ax in axes[:, 0]:
        ax.set_ylabel("Per-class F1 (5-class)", fontsize=12)

    handles, labels = axes.ravel()[0].get_legend_handles_labels()
    fig.legend(handles, labels, ncol=4, fontsize=12, frameon=False, loc="lower center",
               bbox_to_anchor=(0.5, 0.0))
    fig.suptitle("Change-Class F1 Over Time by Model (Five-Class Collapse)", fontsize=17,
                 fontweight="bold", y=0.98)
    fig.text(0.5, 0.055, f"Per-class F1 for the four change classes across temporal brackets, "
             f"common cell set (N = {n_cells} cell-brackets). Bracket cell counts: "
             + ", ".join(f"{_blab(b)}: {per_bracket_n[b]}" for b in BRACKETS) + ".",
             ha="center", va="bottom", fontsize=9, color="0.35")
    fig.subplots_adjust(left=0.06, right=0.98, top=0.9, bottom=0.16, hspace=0.35, wspace=0.12)

    fig.savefig(os.path.join(OUT, "changeclass_f1_over_time_5class.png"), dpi=200)
    plt.close(fig)

    # ---- version faceted by change type: one panel per change class, lines colored by model ----
    fig2, axes2 = plt.subplots(2, 2, figsize=(11, 7.5))
    for ax, (j, (_c, name)) in zip(axes2.ravel(), enumerate(CHANGE)):
        for s in SOURCES:
            vals = [per_bracket[b][s][j] for b in BRACKETS]
            ax.plot(xs, vals, "-o", color=MODEL_COLOR[s], lw=2, ms=6, label=s, zorder=3)
        cmax = np.nanmax([per_bracket[b][s][j] for b in BRACKETS for s in SOURCES])
        ax.set_ylim(0, cmax * 1.18 + 1e-3)                  # per-panel scale (classes differ ~10x)
        ax.set_title(name, fontsize=14, fontweight="bold")
        ax.set_xticks(xs)
        ax.set_xticklabels([_blab(b) for b in BRACKETS], fontsize=11)
        ax.tick_params(axis="y", labelsize=11)
        ax.grid(False)
        for sp in ("top", "right"):
            ax.spines[sp].set_visible(False)
    for ax in axes2[:, 0]:
        ax.set_ylabel("Per-class F1 (5-class)", fontsize=12)

    handles, labels = axes2.ravel()[0].get_legend_handles_labels()
    fig2.legend(handles, labels, ncol=6, fontsize=12, frameon=False, loc="lower center",
                bbox_to_anchor=(0.5, 0.0))
    fig2.suptitle("Change-Class F1 Over Time by Change Type (Five-Class Collapse)", fontsize=17,
                  fontweight="bold", y=0.98)
    fig2.text(0.5, 0.05, f"Per-class F1 over time, one panel per change class, lines colored by model. "
              f"y-axes are scaled per panel (change classes differ by ~10x). "
              f"Common cell set (N = {n_cells} cell-brackets).", ha="center", va="bottom",
              fontsize=9, color="0.35")
    fig2.subplots_adjust(left=0.08, right=0.98, top=0.9, bottom=0.14, hspace=0.35, wspace=0.18)
    fig2.savefig(os.path.join(OUT, "changeclass_f1_over_time_5class_by_class.png"), dpi=200)
    plt.close(fig2)

    print("wrote changeclass_f1_over_time_5class.png, _by_class.png, and .csv")


if __name__ == "__main__":
    main()
