#!/usr/bin/env python3
"""Cross-variant view of the sampling experiment: how the embedding classifier variants
(v2-v6 over the AlphaEarth embeddings; v6 = dot-product) differ under the sampling strategies.

Reads the CSVs written by sampling_experiment_ABCD.py (no re-running) and renders one figure
contrasting the variants on the design properties that discriminate them. Draws from designs,
not accuracy estimates.

Output: reports/Case_ABCD_sampling/variant_comparison.png

Requires: pandas, numpy, matplotlib
"""

import os

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

D = "reports/Case_ABCD_sampling"
VERS = ["v2", "v3", "v4", "v5", "v6"]
VPAL = {"v2": "#1f77b4", "v3": "#2ca02c", "v4": "#9467bd", "v5": "#ff7f0e", "v6": "#d62728"}


def _classic(ax):
    ax.grid(False)
    for s in ("top", "right"):
        ax.spines[s].set_visible(False)


def main():
    de = pd.read_csv(os.path.join(D, "design_effect.csv"))
    dc = pd.read_csv(os.path.join(D, "d_correlation.csv"))
    ab = pd.read_csv(os.path.join(D, "class_absence.csv"))

    fig = plt.figure(figsize=(16, 5.2))
    gs = fig.add_gridspec(1, 3, width_ratios=[1.1, 1.3, 1.1])

    # panel 1: design effect vs W, per variant (autocorrelation -> v6 stands apart)
    ax = fig.add_subplot(gs[0, 0])
    g = de.groupby(["version", "W"]).design_effect.mean().reset_index()
    for v in VERS:
        s = g[g.version == v]
        ax.plot(s.W, s.design_effect, "o-", color=VPAL[v], label=v)
    ax.axhline(1, ls="--", color="k", lw=0.8)
    ax.set_xticks([1, 3, 5, 7, 9]); ax.set_xlabel("window size W")
    ax.set_ylabel("design effect  Var_obs / Var_binomial")
    ax.set_title("Autocorrelation cost by variant\n(v6 dot-product ~4x lower)")
    ax.legend(fontsize=8, frameon=False); _classic(ax)

    # panel 2: Approach D census correlation heatmap (class x variant) at W=5
    ax = fig.add_subplot(gs[0, 1])
    piv = dc[(dc.design == "simple") & (dc.W == 5) & (dc.n == 5000)].pivot(
        index="cls", columns="version", values="census_corr")
    order = piv.mean(axis=1).sort_values(ascending=False).index
    piv = piv.loc[order, VERS]
    im = ax.imshow(piv.to_numpy(), cmap="RdBu_r", vmin=-1, vmax=1, aspect="auto")
    ax.set_xticks(range(len(VERS))); ax.set_xticklabels(VERS)
    ax.set_yticks(range(len(order))); ax.set_yticklabels(order, fontsize=8)
    for i in range(len(order)):
        for j in range(len(VERS)):
            val = piv.to_numpy()[i, j]
            ax.text(j, i, f"{val:.2f}", ha="center", va="center", fontsize=7,
                    color="black" if abs(val) < 0.6 else "white")
    ax.set_title("Approach D: proportion correlation to reference\n"
                 "(abundance tracking; v2/v3/v5 > v4 > v6)")
    fig.colorbar(im, ax=ax, fraction=0.046, pad=0.04, label="corr(prop_map, prop_ref)")

    # panel 3: class absence at n=20, W=1, simple, rare classes per variant
    ax = fig.add_subplot(gs[0, 2])
    rare = ["Development", "Insect/Disease", "Harvest", "Beaver"]
    s = ab[(ab.design == "simple") & (ab.W == 1) & (ab.n == 20)]
    x = np.arange(len(rare)); w = 0.16
    for i, v in enumerate(VERS):
        vals = [float(s[(s.version == v) & (s.cls == c)].frac_absent.iloc[0]) for c in rare]
        ax.bar(x + i * w, vals, w, color=VPAL[v], label=v)
    ax.set_xticks(x + 2 * w); ax.set_xticklabels(rare, rotation=30, ha="right", fontsize=8)
    ax.set_ylabel("fraction absent (simple, n=20, W=1)")
    ax.set_title("Rare-class absence by variant\n(v6 speckle scatters classes -> less absent)")
    ax.legend(fontsize=8, frameon=False, ncol=2); _classic(ax)

    fig.suptitle("Embedding classifier variants under the sampling strategies: what the designs reveal",
                 fontsize=13)
    fig.tight_layout(rect=[0, 0, 1, 0.93])
    fig.savefig(os.path.join(D, "variant_comparison.png"), dpi=140, bbox_inches="tight")
    plt.close(fig)
    print(f"wrote {D}/variant_comparison.png")

    separation_scatter(de, dc)


def separation_scatter(de, dc):
    """One point per variant: abundance-weighted Approach D correlation vs design effect."""
    ceil = pd.read_csv(os.path.join(D, "stratum_ceiling.csv"))
    wt = ceil[ceil.W == 1].set_index("cls").proportion            # true pixel abundance per class
    corr = dc[(dc.design == "simple") & (dc.W == 5) & (dc.n == 5000)].pivot(
        index="cls", columns="version", values="census_corr")
    w = wt.reindex(corr.index).to_numpy()
    x = {v: float(np.nansum(corr[v].to_numpy() * w) / w.sum()) for v in VERS}   # abundance-weighted
    y = {v: float(de[(de.version == v) & (de.W == 9)].design_effect.mean()) for v in VERS}

    fig, ax = plt.subplots(figsize=(8, 6))
    for v in VERS:
        ax.scatter(x[v], y[v], s=160, color=VPAL[v], edgecolors="k", zorder=3)
        ax.annotate(v, (x[v], y[v]), textcoords="offset points", xytext=(9, 4), fontsize=11)
    ax.set_xlabel("abundance-weighted proportion correlation to reference  (Approach D) →  better")
    ax.set_ylabel("design effect at W=9  →  more spatial autocorrelation")
    ax.set_title("How the embedding variants separate\n"
                 "smooth & faithful (v2/v3/v5) — intermediate (v4) — dot-product (v6)")
    ax.annotate("v2/v3/v5: coherent, tracks abundance", (x["v2"], y["v2"]),
                textcoords="offset points", xytext=(-6, -22), fontsize=8, color="0.3", ha="right")
    ax.annotate("v6: per-pixel, no abundance signal", (x["v6"], y["v6"]),
                textcoords="offset points", xytext=(12, 10), fontsize=8, color="0.3")
    _classic(ax)
    fig.tight_layout()
    fig.savefig(os.path.join(D, "variant_separation_scatter.png"), dpi=140, bbox_inches="tight")
    plt.close(fig)
    print(f"wrote {D}/variant_separation_scatter.png")
    print("  abundance-weighted D-corr:", {v: round(x[v], 3) for v in VERS})
    print("  design effect (W=9):      ", {v: round(y[v], 1) for v in VERS})


if __name__ == "__main__":
    main()
