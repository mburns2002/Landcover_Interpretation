#!/usr/bin/env python3
"""Manuscript figures for the Landsat 8 Tasseled Cap training set
(data/external/tc_training_points_l8_2018_2020.csv).

Produces four figures (Figure 1 in two versions) plus a printed summary:
  fig1a  single-date scatter, 2018 greenness vs brightness, small multiples
  fig1b  single-date scatter, 2018 wetness  vs brightness, small multiples
  fig2   2018 to 2020 delta-TC vector plot, small multiples
  fig3   Jeffries-Matusita separability heatmap in the 6-D TC space

Each figure is saved as vector PDF (for LaTeX) and 300 dpi PNG. No titles are drawn;
captions belong in the manuscript. Outputs go to figures/.

Requires: pandas, numpy, matplotlib
"""

import os

import matplotlib
matplotlib.use("Agg")
import matplotlib as mpl
import matplotlib.pyplot as plt
from matplotlib.collections import LineCollection
from matplotlib import patheffects as pe
import numpy as np
import pandas as pd

CSV = "data/external/tc_training_points_l8_2018_2020.csv"
OUT = "figures"

# class codes in the common scheme, kept in this order for every panel and axis
ORDER = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10]
NAMES = {1: "Harvest", 2: "Development", 3: "Forest", 4: "Urban", 5: "Water",
         6: "Agriculture", 7: "Grass/Shrub", 8: "Wetland", 9: "Beaver",
         10: "Insect/Disease"}
# the four GLKN-derived change classes (the rest are stable land cover)
CHANGE = {1, 2, 9, 10}

# explicitly chosen colourblind-safe palette (Paul Tol bright/muted + black), one per class.
# each colour is individually distinguishable under deuteranopia/protanopia; the lighter
# entries are avoided so points stay legible over the light-grey background layer.
PAL = {
    1: "#CC6677",   # rose
    2: "#882255",   # wine
    3: "#117733",   # green
    4: "#000000",   # black
    5: "#4477AA",   # blue
    6: "#999933",   # olive
    7: "#44AA99",   # teal
    8: "#88CCEE",   # cyan
    9: "#AA4499",   # purple
    10: "#332288",  # indigo
}
BG = "0.82"                                              # light-grey background reference

SIX = ["brightness_2018", "greenness_2018", "wetness_2018",
       "brightness_2020", "greenness_2020", "wetness_2020"]


def _style():
    # manuscript-ready defaults: no grid, keep left/bottom spines, embed editable PDF fonts
    mpl.rcParams.update({
        "figure.dpi": 300, "savefig.dpi": 300,
        "font.family": "sans-serif", "font.size": 8,
        "axes.labelsize": 8, "axes.titlesize": 8,
        "xtick.labelsize": 7, "ytick.labelsize": 7, "legend.fontsize": 7,
        "axes.grid": False,
        "axes.spines.top": False, "axes.spines.right": False,
        "pdf.fonttype": 42, "ps.fonttype": 42,
        "figure.autolayout": False,
    })


def _save(fig, stem):
    for ext in ("pdf", "png"):
        fig.savefig(os.path.join(OUT, f"{stem}.{ext}"), bbox_inches="tight")
    plt.close(fig)
    print(f"wrote {OUT}/{stem}.pdf and .png")


def load_and_dedup():
    df = pd.read_csv(CSV)
    before = df.label.value_counts().reindex(ORDER)
    # deduplicate on the six TC columns: training points were thinned at 10 m but Landsat is
    # 30 m, so several 10 m points fall on one 30 m pixel and carry identical TC values.
    ded = df.drop_duplicates(subset=SIX).reset_index(drop=True)
    after = ded.label.value_counts().reindex(ORDER)
    summary = pd.DataFrame({
        "code": ORDER,
        "class": [NAMES[c] for c in ORDER],
        "n_before": before.to_numpy(),
        "n_after": after.to_numpy(),
        "n_dropped": (before - after).to_numpy(),
        "type": ["change" if c in CHANGE else "stable" for c in ORDER],
    })
    print("\nper-class counts before and after dedup on the six TC columns:")
    print(summary.to_string(index=False))
    print(f"\ntotal rows {len(df)} -> {len(ded)} after dedup "
          f"({len(df) - len(ded)} exact duplicates removed)\n")
    summary.to_csv(os.path.join(OUT, "dedup_counts.csv"), index=False)
    return ded, summary


def _panel_axes(share_y=True):
    # 2 rows x 5 cols small-multiples grid, shared axes for direct comparison
    fig, axes = plt.subplots(2, 5, figsize=(7.2, 3.3), sharex=True, sharey=share_y)
    return fig, axes.ravel()


def scatter_single_date(df, ycol, xcol, ylabel, xlabel, stem):
    # single-date TC position: one class per panel in its colour over the full pooled cloud (grey)
    fig, axes = _panel_axes()
    bx, by = df[xcol].to_numpy(), df[ycol].to_numpy()      # identical background in every panel
    for ax, c in zip(axes, ORDER):
        ax.scatter(bx, by, s=3, c=BG, edgecolors="none", rasterized=True, zorder=1)
        s = df[df.label == c]
        ax.scatter(s[xcol], s[ycol], s=5, c=PAL[c], edgecolors="none",
                   rasterized=True, zorder=2)
        ax.text(0.05, 0.93, NAMES[c], transform=ax.transAxes, va="top", ha="left",
                fontsize=6.5, color=PAL[c],
                fontweight="bold" if c in CHANGE else "normal")
        ax.tick_params(length=2)
    for ax in axes[5:]:
        ax.set_xlabel(xlabel)
    for ax in axes[0::5]:
        ax.set_ylabel(ylabel)
    fig.tight_layout(pad=0.4, w_pad=0.3, h_pad=0.4)
    _save(fig, stem)


def delta_vectors(df, stem):
    # delta-TC vectors in greenness-brightness space.
    # with up to ~200 near-zero displacements per stable class, drawing an arrowhead per point is
    # unreadable, so each point is a faint headless segment (shows spread) and a single bold arrow
    # gives the class-mean displacement (shows coherent direction and magnitude).
    fig, axes = _panel_axes()
    bx = np.concatenate([df.brightness_2018, df.brightness_2020])
    by = np.concatenate([df.greenness_2018, df.greenness_2020])
    # robust limits: a few extreme 2020 points (harvest/development brighten strongly) would
    # otherwise compress the bulk, so clip to the 0.5-99.5 percentile range. segments running
    # past the edge are clipped by the axes.
    xlo, xhi = np.percentile(bx, [0.5, 99.5])
    ylo, yhi = np.percentile(by, [0.5, 99.5])
    xlim = (xlo - 0.03, xhi + 0.03)
    ylim = (ylo - 0.02, yhi + 0.02)
    bg_x, bg_y = df.brightness_2018.to_numpy(), df.greenness_2018.to_numpy()
    for ax, c in zip(axes, ORDER):
        ax.scatter(bg_x, bg_y, s=3, c=BG, edgecolors="none", rasterized=True, zorder=1)
        s = df[df.label == c]
        segs = np.stack([
            np.column_stack([s.brightness_2018, s.greenness_2018]),
            np.column_stack([s.brightness_2020, s.greenness_2020]),
        ], axis=1)
        lc = LineCollection(segs, colors=PAL[c], linewidths=0.4, alpha=0.25,
                            rasterized=True, zorder=2)
        ax.add_collection(lc)
        # bold class-mean displacement arrow on top, white-stroked so it reads over the fan
        m0 = (s.brightness_2018.mean(), s.greenness_2018.mean())
        m1 = (s.brightness_2020.mean(), s.greenness_2020.mean())
        ann = ax.annotate("", xy=m1, xytext=m0, zorder=4,
                          arrowprops=dict(arrowstyle="-|>", color=PAL[c], lw=1.8,
                                          mutation_scale=11))
        ann.arrow_patch.set_path_effects([pe.withStroke(linewidth=3.0, foreground="white")])
        ax.set_xlim(*xlim); ax.set_ylim(*ylim)
        ax.text(0.05, 0.93, NAMES[c], transform=ax.transAxes, va="top", ha="left",
                fontsize=6.5, color=PAL[c],
                fontweight="bold" if c in CHANGE else "normal")
        ax.tick_params(length=2)
    for ax in axes[5:]:
        ax.set_xlabel("TC brightness")
    for ax in axes[0::5]:
        ax.set_ylabel("TC greenness")
    fig.tight_layout(pad=0.4, w_pad=0.3, h_pad=0.4)
    _save(fig, stem)


def _logdet(S):
    # slogdet is numerically stable where det underflows; sign should be +1 for an SPD matrix
    sign, ld = np.linalg.slogdet(S)
    return ld if sign > 0 else np.nan


def jm_matrix(df):
    # Jeffries-Matusita distance from the Bhattacharyya distance, in the full 6-D TC space.
    # this assumes each class is multivariate normal in TC space, which is only approximate.
    # a small ridge on each covariance guards against near-singular matrices left by the
    # duplicate collapse; the mean covariance is inverted with inv, or pinv if ill-conditioned.
    K = len(ORDER)
    mu, cov = {}, {}
    ridge = 1e-6 * np.eye(6)
    for c in ORDER:
        X = df[df.label == c][SIX].to_numpy()
        mu[c] = X.mean(axis=0)
        cov[c] = np.cov(X, rowvar=False) + ridge
    JM = np.zeros((K, K))
    for i, ci in enumerate(ORDER):
        for j, cj in enumerate(ORDER):
            if i == j:
                continue
            dmu = mu[ci] - mu[cj]
            Sig = 0.5 * (cov[ci] + cov[cj])
            SigInv = np.linalg.pinv(Sig) if np.linalg.cond(Sig) > 1e12 else np.linalg.inv(Sig)
            term1 = 0.125 * dmu @ SigInv @ dmu
            term2 = 0.5 * (_logdet(Sig) - 0.5 * (_logdet(cov[ci]) + _logdet(cov[cj])))
            B = term1 + term2
            JM[i, j] = 2.0 * (1.0 - np.exp(-B))
    return JM


def jm_heatmap(JM, stem):
    labels = [NAMES[c] for c in ORDER]
    fig, ax = plt.subplots(figsize=(6.3, 5.4))
    # cividis is a perceptually-uniform, colourblind-safe sequential map
    im = ax.imshow(JM, cmap="cividis", vmin=0, vmax=2, aspect="equal")
    ax.set_xticks(range(len(labels))); ax.set_yticks(range(len(labels)))
    ax.set_xticklabels(labels, rotation=45, ha="right")
    ax.set_yticklabels(labels)
    ax.tick_params(length=0)
    for i in range(len(labels)):
        for j in range(len(labels)):
            v = JM[i, j]
            ax.text(j, i, f"{v:.2f}", ha="center", va="center", fontsize=6,
                    color="white" if v < 1.3 else "black")
    cb = fig.colorbar(im, ax=ax, fraction=0.046, pad=0.04)
    cb.set_label("Jeffries-Matusita distance (0 = identical, 2 = separable)")
    cb.outline.set_visible(False)
    fig.tight_layout(pad=0.4)
    _save(fig, stem)


def main():
    os.makedirs(OUT, exist_ok=True)
    _style()
    df, _ = load_and_dedup()

    scatter_single_date(df, "greenness_2018", "brightness_2018",
                        "TC greenness (2018)", "TC brightness (2018)",
                        "fig1a_tc_scatter_greenness_brightness")
    scatter_single_date(df, "wetness_2018", "brightness_2018",
                        "TC wetness (2018)", "TC brightness (2018)",
                        "fig1b_tc_scatter_wetness_brightness")
    delta_vectors(df, "fig2_tc_delta_vectors")

    JM = jm_matrix(df)
    jm_heatmap(JM, "fig3_jm_distance_heatmap")
    jm_df = pd.DataFrame(JM, index=[NAMES[c] for c in ORDER],
                         columns=[NAMES[c] for c in ORDER])
    jm_df.to_csv(os.path.join(OUT, "jm_matrix.csv"))
    print("Jeffries-Matusita distance matrix (6-D TC space, both dates):")
    with pd.option_context("display.width", 200, "display.max_columns", 12):
        print(jm_df.round(3).to_string())


if __name__ == "__main__":
    main()
