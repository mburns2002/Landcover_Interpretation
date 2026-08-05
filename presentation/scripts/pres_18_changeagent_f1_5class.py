#!/usr/bin/env python3
"""pres_18_changeagent_f1_5class: five-class change F1 grouped by change agent, colored by model.

Transpose of pres_14: x = change agent (Harvest, Development, Beaver, Insect/Disease), one bar per model
inside each group (v2..v6 and the spectral baseline spec_all), colored by model. This shows, per change
agent, how the models compare. Values are the exact five-class per-class F1 from pres_14's computation on
the common 168-cell reference set (imported, not recomputed by hand), so the two figures always agree.

Outputs (presentation/figures/, PNG only for the Google Slides deck):
  pres_18_changeagent_f1_5class.png        y auto-zoomed just above the tallest bar
  pres_18_changeagent_f1_5class_full.png   y 0..1 (drives the "all change F1 is at the floor" message)
"""

import importlib.util
import os

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

import slide_font
import numpy as np
slide_font.use_spectral()

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
OUT = os.path.join(ROOT, "presentation", "figures")

# reuse pres_14's five-class computation so the numbers match exactly
_spec = importlib.util.spec_from_file_location("P14", os.path.join(HERE, "pres_14_changeclass_f1_5class.py"))
P14 = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(P14)

SOURCES = P14.SOURCES                              # ["v2","v3","v4","v5","v6","spec_all"]
AGENTS = [name for _, name in P14.CHANGE]          # Harvest, Development, Beaver, Insect/Disease
# per-model colors (match pres_17): embeddings from the transfer-OA palette, spec_all brown (tab10 next)
COLOR = {"v2": "#1f77b4", "v3": "#2ca02c", "v4": "#9467bd", "v5": "#ff7f0e", "v6": "#d62728",
         "spec_all": "#8c564b"}

FIG_W, FIG_H = 12.0, 5.8
BODY_FS, AXIS_FS, TICK_FS = 16, 18, 16


def draw(mat, stem, title, caption, y_full):
    x = np.arange(len(AGENTS))
    n = len(SOURCES)
    bar_w = 0.85 / n
    peak = np.nanmax([mat[s][j] for s in SOURCES for j in range(len(AGENTS))])
    ymax = 1.0 if y_full else float(np.ceil(peak * 100 + 1.0)) / 100

    fig, ax = plt.subplots(figsize=(FIG_W, FIG_H))
    for i, s in enumerate(SOURCES):
        offs = (i - (n - 1) / 2) * bar_w
        vals = [mat[s][j] for j in range(len(AGENTS))]
        ax.bar(x + offs, vals, bar_w, color=COLOR[s], edgecolor="0.25", linewidth=0.6, label=s,
               zorder=3)
        for xi, v in zip(x + offs, vals):
            if not np.isnan(v):
                ax.text(xi, v + ymax * 0.012, f"{v:.2f}", ha="center", va="bottom", fontsize=7.5,
                        color="0.2")

    ax.set_xticks(x)
    ax.set_xticklabels(AGENTS, fontsize=TICK_FS)
    ax.set_ylabel("Per-class F1 (five-class)", fontsize=AXIS_FS)
    ax.tick_params(axis="y", labelsize=TICK_FS)
    ax.set_ylim(0, ymax)
    ax.set_xlim(-0.6, len(AGENTS) - 0.4)
    ax.grid(False)
    for sp in ("top", "right"):
        ax.spines[sp].set_visible(False)
    ax.set_title(title, fontsize=AXIS_FS + 2, fontweight="bold", pad=14)
    # legend inside the empty upper-right (only Harvest has tall bars)
    ax.legend(ncol=3, fontsize=BODY_FS - 3, frameon=False, loc="upper right",
              handlelength=1.2, columnspacing=1.3, labelspacing=0.4)
    fig.text(0.5, 0.03, caption, ha="center", va="bottom", fontsize=BODY_FS - 4, color="0.3",
             linespacing=1.4)
    fig.subplots_adjust(left=0.085, right=0.985, top=0.88, bottom=0.25)
    return fig


def main():
    mat, _per_bracket, n_cells, _pbn = P14.compute()
    print(f"common cell set N = {n_cells}")
    print("F1 (rows=source, cols=" + ", ".join(AGENTS) + "):")
    for s in SOURCES:
        print(f"  {s:<9}" + "".join(f"{v:>12.4f}" for v in mat[s]))

    cap = ("Five-class F1 for each change agent across the embedding configurations (v2–v6)\n"
           "and the spectral baseline (spec_all), on the common 168-cell reference set.")
    os.makedirs(OUT, exist_ok=True)
    fig = draw(mat, "pres_18_changeagent_f1_5class",
               "Change-Agent F1 by Model (Five-Class)", cap, y_full=False)
    fig.savefig(f"{OUT}/pres_18_changeagent_f1_5class.png", dpi=300)
    plt.close(fig)
    fig = draw(mat, "pres_18_changeagent_f1_5class_full",
               "Change-Agent F1 by Model (Five-Class)", cap, y_full=True)
    fig.savefig(f"{OUT}/pres_18_changeagent_f1_5class_full.png", dpi=300)
    plt.close(fig)
    print("wrote pres_18_changeagent_f1_5class.png and _full.png")


if __name__ == "__main__":
    main()
