#!/usr/bin/env python3
"""pres_change_disagreement: where interpreters disagreed about change (summary bar chart).

The dominant form of change-class disagreement is change-vs-stable: one interpreter called a pixel
change, the other called it stable. This ranks the largest contested class pairs (symmetrized, in
hectares) from reports/interpreter_agreement/change_stable_conflicts/ordered_pairs.csv, colored by the
change class in each pair. The headline is that change-vs-stable is ~56% of all change-labeled pixels,
while both-called-change-but-disagreed-on-type is tiny (~1.3%).

Output (PNG only), in presentation/figures/change_disagreement/.
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
CS = os.path.join(ROOT, "reports", "interpreter_agreement", "change_stable_conflicts", "ordered_pairs.csv")
OUT_DIR = os.path.join(ROOT, "presentation", "figures", "change_disagreement")

CHANGE_COLOR = {"Harvest": "#C9A227", "Development": "#d62728",
                "Insect/Disease": "#70A2DB", "Beaver": "#ff7f0e"}
N_TOP = 10


def _change_of(pair):
    a, b = pair.split("<->")
    return b if b in CHANGE_COLOR else a


def main():
    df = pd.read_csv(CS)
    sym = df[df.class_pair.str.contains("symmetrized")].copy()
    sym["pair"] = sym.class_pair.str.replace(r"\s*\(symmetrized\)", "", regex=True).str.replace("<->", " vs ")
    sym["raw"] = sym.class_pair.str.replace(r"\s*\(symmetrized\)", "", regex=True)
    sym = sym.sort_values("area_ha", ascending=False).head(N_TOP).iloc[::-1]   # largest at top

    colors = [CHANGE_COLOR[_change_of(r.raw)] for r in sym.itertuples()]
    y = range(len(sym))

    fig, ax = plt.subplots(figsize=(10, 6.2))
    fig.subplots_adjust(left=0.30, right=0.97, top=0.89, bottom=0.26)
    ax.barh(list(y), sym.area_ha, color=colors, edgecolor="black", linewidth=0.7, zorder=3)
    ax.set_yticks(list(y))
    ax.set_yticklabels(sym.pair, fontsize=13)
    ax.set_xlim(0, sym.area_ha.max() * 1.16)
    for i, a in enumerate(sym.area_ha):
        ax.text(a + sym.area_ha.max() * 0.012, i, f"{a:,.0f} ha", va="center", ha="left", fontsize=11,
                color="0.2")
    ax.set_xlabel("Disagreed area (hectares)", fontsize=14)
    ax.tick_params(axis="x", labelsize=12)
    ax.grid(False)
    for sp in ("top", "right"):
        ax.spines[sp].set_visible(False)
    ax.set_title("Where Interpreters Disagreed About Change", fontsize=19, fontweight="bold", pad=12)

    handles = [Patch(facecolor=c, edgecolor="black", label=n) for n, c in CHANGE_COLOR.items()]
    ax.legend(handles=handles, title="Change class in the pair", fontsize=11, title_fontsize=11,
              loc="lower right", frameon=False)

    fig.text(0.5, 0.02, "Change vs stable: one interpreter called it change, the other stable. Top contested "
             "pairs, symmetrized.\n~56% of all change-labeled pixels (1,103 ha). Disagreeing on change type "
             "is tiny: ~1.3%, 26 ha.",
             ha="center", va="bottom", fontsize=11, color="0.35", linespacing=1.4)

    os.makedirs(OUT_DIR, exist_ok=True)
    fig.savefig(os.path.join(OUT_DIR, "change_disagreement_summary.png"), dpi=300)
    plt.close(fig)
    print("wrote change_disagreement_summary.png")


if __name__ == "__main__":
    main()
