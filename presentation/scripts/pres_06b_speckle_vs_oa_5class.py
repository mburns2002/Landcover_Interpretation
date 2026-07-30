#!/usr/bin/env python3
"""pres_06b_speckle_vs_oa_5class: design-based five-class overall accuracy against map speckle.

Defense-slide scatter of design-based five-class overall accuracy (y) against neighbor-change (x, a
map-speckle diagnostic) for the five embedding configurations, one point per configuration, each
labeled directly and colored by the shared variant palette. A dashed line marks the overall accuracy
of the trivial all-Stable prediction. No trend line by request.

Data sources:
  y and baseline: manuscript_formatting/tables/S4.csv (design-based pooled 5-class OA and the
                  all-Stable baseline_OA)
  x:              manuscript_formatting/tables/S3.csv (neighbor-change)
spec_all is not shown, since neighbor-change was not computed on the current basis; its spatial
diagnostics appear in Table 2.6.

The Spearman rank correlation is printed to the console rather than drawn.

sizing: 10 x 5.6 in, the content area of a 16:9 slide.

output (png only):
  presentation/figures/pres_06b_speckle_vs_oa_5class.png
"""

import os

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.lines import Line2D
import pandas as pd
from scipy.stats import spearmanr

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
S3 = os.path.join(ROOT, "manuscript_formatting", "tables", "S3.csv")
S4 = os.path.join(ROOT, "manuscript_formatting", "tables", "S4.csv")
OUT = os.path.join(ROOT, "presentation", "figures")

VPAL = {"v2": "#1f77b4", "v3": "#2ca02c", "v4": "#9467bd", "v5": "#ff7f0e", "v6": "#d62728"}

# embedding configuration per variant, worded in reference to the base year (2018), paired with 2020
VDESC = {
    "v2": "v2: base (2018) embedding + delta",
    "v3": "v3: base (2018) + 2020 embeddings",
    "v4": "v4: delta only (2020 - 2018)",
    "v5": "v5: base (2018) embedding + dot product",
    "v6": "v6: dot product only",
}
VORDER = ["v2", "v3", "v4", "v5", "v6"]

# per-point label offsets in points (dx, dy, horizontal-align)
LABEL_OFFSET = {
    "v2": (12, 9, "left"),
    "v3": (-12, 0, "right"),
    "v5": (13, -8, "left"),
    "v4": (13, 4, "left"),
    "v6": (-15, 7, "right"),
}


def _style():
    plt.rcParams.update({
        "font.family": "sans-serif",
        "font.sans-serif": ["Helvetica", "Arial", "DejaVu Sans"],
        "font.size": 16,
        "axes.linewidth": 1.0,
    })


def main():
    nc = pd.read_csv(S3).rename(columns={"Neighbor-change": "nc", "Source": "source"})[["source", "nc"]]
    acc = pd.read_csv(S4).rename(columns={"Source": "source", "OA": "oa"})
    df = acc.merge(nc, on="source")

    baselines = df["baseline_OA"].unique()
    baseline = float(baselines[0])
    assert len(baselines) == 1, f"expected a single all-Stable baseline, found {baselines}"

    # diagnostics before plotting
    print("design-based 5-class OA vs neighbor-change (source, nc, OA):")
    for r in df.itertuples():
        print(f"  {r.source:<4} neighbor-change={r.nc:.3f}  5-class OA={r.oa:.3f}")
    print(f"all-Stable baseline OA: {baseline:.3f}")
    rho, p = spearmanr(df["nc"], df["oa"])
    print(f"Spearman (neighbor-change vs 5-class OA), n={len(df)}: rho={rho:.3f}, p={p:.3f}")
    print("note: spec_all omitted (neighbor-change not computed on the current basis); its spatial")
    print("      diagnostics are in Table 2.6.")

    _style()
    fig, ax = plt.subplots(figsize=(10, 5.6))
    fig.subplots_adjust(left=0.12, right=0.97, top=0.87, bottom=0.15)
    ax.set_title("Map Speckle Versus Five-Class Overall Accuracy by Variant", fontsize=19,
                 fontweight="bold", pad=14)

    # all-Stable baseline
    ax.axhline(baseline, linestyle="--", color="0.35", linewidth=1.6, zorder=2)
    ax.text(0.97, baseline + 0.006, f"Predict Stable everywhere (OA = {baseline:.2f})",
            ha="right", va="bottom", fontsize=14, color="0.35")

    for r in df.itertuples():
        src = r.source
        ax.scatter(r.nc, r.oa, s=240, color=VPAL[src], edgecolor="black", linewidth=1.0, zorder=3)
        dx, dy, ha = LABEL_OFFSET[src]
        ax.annotate(src, (r.nc, r.oa), textcoords="offset points", xytext=(dx, dy),
                    ha=ha, va="center", fontsize=16, fontweight="bold", color=VPAL[src])

    ax.set_xlim(0, 0.85)
    ax.set_ylim(0.5, 1.05)
    ax.set_xlabel("Neighbor-change (map speckle)", fontsize=18)
    ax.set_ylabel("Design-based 5-class overall accuracy", fontsize=17)
    ax.tick_params(labelsize=15)
    ax.grid(False)
    for s in ("top", "right"):
        ax.spines[s].set_visible(False)

    # legend reminding what each variant is, placed in the open lower-centre of the panel
    handles = [Line2D([0], [0], marker="o", linestyle="none", markersize=11,
                      markerfacecolor=VPAL[v], markeredgecolor="black", markeredgewidth=0.8,
                      label=VDESC[v]) for v in VORDER]
    ax.legend(handles=handles, loc="upper left", bbox_to_anchor=(0.33, 0.62), frameon=False,
              fontsize=14, handletextpad=0.5, labelspacing=0.55,
              title="Embedding configuration", title_fontsize=14)

    os.makedirs(OUT, exist_ok=True)
    fig.savefig(os.path.join(OUT, "pres_06b_speckle_vs_oa_5class.png"), dpi=300, bbox_inches="tight")
    plt.close(fig)
    print("\nwrote pres_06b_speckle_vs_oa_5class.png")


if __name__ == "__main__":
    main()
