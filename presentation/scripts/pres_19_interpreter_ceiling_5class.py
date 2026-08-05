#!/usr/bin/env python3
"""pres_19_interpreter_ceiling_5class: per-class inter-interpreter agreement (the human ceiling).

Deck version of manuscript Figure 3.3: inter-interpreter F1 with 95% CI for the five collapsed classes,
colored by reliability (High green, Low red). This is the ceiling on any classifier's F1: even two human
interpreters disagree badly on the change classes, so no model can be expected to beat these values.

Data: reports/interpreter_agreement/per_class_agreement_ci_5class.csv.
Output (PNG only for the Google Slides deck): presentation/figures/pres_19_interpreter_ceiling_5class.png
"""

import os

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

import slide_font
import pandas as pd
from matplotlib.patches import Patch
slide_font.use_spectral()

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
OUT = os.path.join(ROOT, "presentation", "figures")
CI_CSV = os.path.join(ROOT, "reports", "interpreter_agreement", "per_class_agreement_ci_5class.csv")

ORDER = ["Stable", "Harvest", "Development", "Insect/Disease", "Beaver"]   # top to bottom
REL_COLOR = {"High": "#2e7d32", "Moderate": "#e6902e", "Low": "#c0392b"}


def main():
    df = pd.read_csv(CI_CSV).set_index("cls")
    fig, ax = plt.subplots(figsize=(10, 5.2))
    fig.subplots_adjust(left=0.22, right=0.9, top=0.86, bottom=0.28)

    ys = list(range(len(ORDER)))[::-1]                     # first class on top
    for y, cls in zip(ys, ORDER):
        r = df.loc[cls]
        color = REL_COLOR[r["reliability"]]
        ax.errorbar(r["f1"], y, xerr=[[r["f1"] - r["f1_lo"]], [r["f1_hi"] - r["f1"]]], fmt="o",
                    color=color, ecolor=color, elinewidth=3, capsize=5, markersize=11, zorder=3)
        ax.text(r["f1_hi"] + 0.02, y, f"{r['f1']:.2f}", va="center", ha="left", fontsize=13,
                color="0.2")

    ax.set_yticks(ys)
    ax.set_yticklabels([f"{c}  (n={int(df.loc[c, 'n_pairs'])})" for c in ORDER], fontsize=15)
    ax.set_ylim(-0.6, len(ORDER) - 0.4)
    ax.set_xlim(0, 1.0)
    ax.set_xlabel("Inter-interpreter F1 (95% CI)", fontsize=16)
    ax.tick_params(axis="x", labelsize=13)
    ax.grid(False)
    for sp in ("top", "right"):
        ax.spines[sp].set_visible(False)
    ax.set_title("Per-Class Inter-Interpreter Agreement (Five-Class)", fontsize=19,
                 fontweight="bold", pad=12)
    handles = [Patch(facecolor=REL_COLOR[k], label=k) for k in ("High", "Low")]
    ax.legend(handles=handles, fontsize=13, frameon=False, loc="lower right", title="Reliability",
              title_fontsize=13)
    fig.text(0.5, 0.02,
             "Inter-interpreter F1 on the 5-class collapse: the ceiling on any classifier's F1. Stable and\n"
             "Harvest are reliable; Development, Insect/Disease, and Beaver are not.",
             ha="center", va="bottom", fontsize=12, color="0.35", linespacing=1.4)

    os.makedirs(OUT, exist_ok=True)
    fig.savefig(os.path.join(OUT, "pres_19_interpreter_ceiling_5class.png"), dpi=300)
    plt.close(fig)
    print("wrote pres_19_interpreter_ceiling_5class.png")


if __name__ == "__main__":
    main()
