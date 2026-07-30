#!/usr/bin/env python3
"""pres_06_speckle_vs_oa: pooled overall accuracy against map speckle, one point per source.

Defense-slide scatter of pooled overall accuracy (y) against neighbor-change (x, a map-speckle
diagnostic) for the five embedding variants, each point labeled directly with its source name and
colored by the shared variant palette. No legend, and no trend line by request.

Data source: manuscript_formatting/tables/S3.csv (the table behind Table S3). That CSV, and the
source model_speckle.csv it derives from, carry neighbor-change for v2 through v6 only. spec_all
neighbor-change was not found anywhere in manuscript_formatting or reports, so spec_all is omitted
here (it would also sit on a different, 168-cell basis). What it would take to add it is described in
the console output and the accompanying message.

The Spearman rank correlation is printed to the console rather than drawn, so the presenter can quote
it verbally.

sizing: 10 x 5.6 in, the content area of a 16:9 slide.

output (png only):
  presentation/figures/pres_06_speckle_vs_oa.png
"""

import os

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import pandas as pd
from scipy.stats import spearmanr

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
CSV = os.path.join(ROOT, "manuscript_formatting", "tables", "S3.csv")
OUT = os.path.join(ROOT, "presentation", "figures")

# shared variant palette, matching the rest of the repo
VPAL = {"v2": "#1f77b4", "v3": "#2ca02c", "v4": "#9467bd", "v5": "#ff7f0e", "v6": "#d62728"}

# per-point label offsets in points (dx, dy, horizontal-align), to keep the close cluster readable
LABEL_OFFSET = {
    "v2": (12, 6, "left"),
    "v3": (-12, 0, "right"),
    "v5": (13, -2, "left"),
    "v4": (13, 2, "left"),
    "v6": (-15, 6, "right"),
}


def _style():
    plt.rcParams.update({
        "font.family": "sans-serif",
        "font.sans-serif": ["Helvetica", "Arial", "DejaVu Sans"],
        "font.size": 16,
        "axes.linewidth": 1.0,
    })


def main():
    df = pd.read_csv(CSV)
    df = df.rename(columns={"Neighbor-change": "nc", "Pooled OA": "oa", "Source": "source"})

    # diagnostics before plotting
    print("Table S3 data (source, neighbor-change, pooled OA):")
    for r in df.itertuples():
        print(f"  {r.source:<4} neighbor-change={r.nc:.3f}  pooled OA={r.oa:.3f}")
    x = df["nc"].to_numpy()
    y = df["oa"].to_numpy()
    rho, p = spearmanr(x, y)
    print(f"\nSpearman rank correlation (neighbor-change vs pooled OA), n={len(df)}: "
          f"rho={rho:.3f}, p={p:.3f}")
    print("note: spec_all neighbor-change is not present in manuscript_formatting or reports, so only")
    print("      the five embedding variants are plotted. To add spec_all, run the neighbor-change")
    print("      routine on the spec_all classified maps over its 168 usable cells and mark it with a")
    print("      distinct symbol (its basis differs from the 180-cell embedding runs).")

    _style()
    fig, ax = plt.subplots(figsize=(10, 5.6))
    fig.subplots_adjust(left=0.11, right=0.97, top=0.87, bottom=0.15)
    # in-plot title, title case, no subtitle
    ax.set_title("Map Speckle Versus Overall Accuracy by Variant", fontsize=20,
                 fontweight="bold", pad=14)

    for r in df.itertuples():
        src = r.source
        ax.scatter(r.nc, r.oa, s=240, color=VPAL[src], edgecolor="black", linewidth=1.0, zorder=3)
        dx, dy, ha = LABEL_OFFSET[src]
        ax.annotate(src, (r.nc, r.oa), textcoords="offset points",
                    xytext=(dx, dy), ha=ha, va="center", fontsize=16, fontweight="bold",
                    color=VPAL[src])

    ax.set_xlim(0, 0.85)
    ax.set_ylim(0, 0.72)
    ax.set_xlabel("Neighbor-change (map speckle)", fontsize=18)
    ax.set_ylabel("Pooled overall accuracy", fontsize=18)
    ax.tick_params(labelsize=15)
    ax.grid(False)
    for s in ("top", "right"):
        ax.spines[s].set_visible(False)

    os.makedirs(OUT, exist_ok=True)
    fig.savefig(os.path.join(OUT, "pres_06_speckle_vs_oa.png"), dpi=300, bbox_inches="tight")
    plt.close(fig)
    print("\nwrote pres_06_speckle_vs_oa.png")


if __name__ == "__main__":
    main()
