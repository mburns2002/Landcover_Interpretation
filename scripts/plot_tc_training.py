#!/usr/bin/env python3
"""Exploratory plots for the Tasseled Cap change-detection training set
(tc_training_points_l8_2018_2020.csv): Landsat 8 brightness/greenness/wetness for 2018 and
2020, their deltas, and a class label. 10 classes x 200 points (balanced).

Labels use the project's common 10-class scheme (1=Harvest ... 10=Insect/Disease); the mapping
is physically consistent with the per-class mean TC deltas (Development brightens most; harvest
loses wetness; insect/disease loses greenness without brightening = standing dead).

Outputs -> reports/TC_training/
Requires: pandas, numpy, matplotlib
"""

import os

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

CSV = "data/external/tc_training_points_l8_2018_2020.csv"
OUT = "reports/TC_training"

NAMES = {1: "Harvest", 2: "Development", 3: "Forest", 4: "Urban", 5: "Water",
         6: "Agriculture", 7: "Grass/Shrub", 8: "Wetland", 9: "Beaver", 10: "Insect/Disease"}
# the four disturbance/change classes vs the six stable land-cover classes
CHANGE = {1, 2, 9, 10}
# tab10 gives a distinct colour per label
PAL = {i: plt.get_cmap("tab10")(k) for k, i in enumerate(sorted(NAMES))}
DELTAS = ["d_brightness", "d_greenness", "d_wetness"]
DLAB = {"d_brightness": "Δ brightness", "d_greenness": "Δ greenness",
        "d_wetness": "Δ wetness"}


def _classic(ax):
    ax.grid(False)
    for s in ("top", "right"):
        ax.spines[s].set_visible(False)


def scatter_deltas(df):
    """Pairwise TC-delta scatter, change classes highlighted over a grey stable backdrop."""
    pairs = [("d_brightness", "d_greenness"), ("d_brightness", "d_wetness"),
             ("d_greenness", "d_wetness")]
    fig, axes = plt.subplots(1, 3, figsize=(16, 5.2))
    for ax, (xa, ya) in zip(axes, pairs):
        stable = df[~df.label.isin(CHANGE)]
        ax.scatter(stable[xa], stable[ya], s=8, c="0.8", edgecolors="none", label="_stable")
        for lab in sorted(CHANGE):
            s = df[df.label == lab]
            ax.scatter(s[xa], s[ya], s=14, color=PAL[lab], edgecolors="none",
                       alpha=0.8, label=NAMES[lab])
        ax.axhline(0, color="0.6", lw=0.7); ax.axvline(0, color="0.6", lw=0.7)
        ax.set_xlabel(DLAB[xa]); ax.set_ylabel(DLAB[ya]); _classic(ax)
    axes[0].legend(fontsize=8, frameon=False, title="change class", title_fontsize=8, loc="upper left")
    fig.suptitle("Tasseled Cap change space (2018→2020): where the disturbance classes live\n"
                 "grey = the six stable land-cover classes; harvest/development brighten and dry, "
                 "insect-disease loses greenness", fontsize=12)
    fig.tight_layout(rect=[0, 0, 1, 0.93])
    _save(fig, "tc_delta_scatter.png")


def boxplots_deltas(df):
    """Per-class distribution of each TC delta."""
    labs = sorted(NAMES)
    fig, axes = plt.subplots(3, 1, figsize=(12, 11), sharex=True)
    for ax, d in zip(axes, DELTAS):
        data = [df[df.label == l][d].to_numpy() for l in labs]
        bp = ax.boxplot(data, positions=range(len(labs)), widths=0.6, patch_artist=True,
                        showfliers=False, medianprops=dict(color="black"))
        for patch, l in zip(bp["boxes"], labs):
            patch.set_facecolor(PAL[l]); patch.set_alpha(0.55 if l in CHANGE else 0.25)
        ax.axhline(0, color="0.6", lw=0.7)
        ax.set_ylabel(DLAB[d]); _classic(ax)
    axes[-1].set_xticks(range(len(labs)))
    axes[-1].set_xticklabels([f"{l} {NAMES[l]}" for l in labs], rotation=30, ha="right")
    fig.suptitle("Per-class Tasseled Cap deltas (2018→2020) — spread, not just the mean\n"
                 "filled = the four change classes; faint = stable classes (deltas near zero)",
                 fontsize=12)
    fig.tight_layout(rect=[0, 0, 1, 0.95])
    _save(fig, "tc_delta_boxplots.png")


def mean_delta_heatmap(df):
    """10x3 heatmap of mean delta per class — the compact class signature."""
    labs = sorted(NAMES)
    M = np.array([[df[df.label == l][d].mean() for d in DELTAS] for l in labs])
    vmax = np.abs(M).max()
    fig, ax = plt.subplots(figsize=(6.2, 8))
    im = ax.imshow(M, cmap="RdBu_r", vmin=-vmax, vmax=vmax, aspect="auto")
    ax.set_xticks(range(3)); ax.set_xticklabels([DLAB[d] for d in DELTAS], rotation=20, ha="right")
    ax.set_yticks(range(len(labs))); ax.set_yticklabels([f"{l} {NAMES[l]}" for l in labs])
    for i in range(len(labs)):
        for j in range(3):
            ax.text(j, i, f"{M[i, j]:.3f}", ha="center", va="center", fontsize=8,
                    color="black" if abs(M[i, j]) < vmax * 0.6 else "white")
    ax.set_title("Mean TC delta per class (2018→2020)\nthe spectral-change signature the "
                 "classifier keys on", fontsize=11)
    fig.colorbar(im, ax=ax, fraction=0.046, pad=0.04, label="mean Δ (reflectance units)")
    fig.tight_layout()
    _save(fig, "tc_mean_delta_heatmap.png")


def trajectory(df):
    """2018->2020 movement of each class centroid in brightness-greenness space."""
    fig, ax = plt.subplots(figsize=(9, 7.5))
    for lab in sorted(NAMES):
        s = df[df.label == lab]
        b0, g0 = s.brightness_2018.mean(), s.greenness_2018.mean()
        b1, g1 = s.brightness_2020.mean(), s.greenness_2020.mean()
        lw = 2.4 if lab in CHANGE else 1.0
        ax.annotate("", xy=(b1, g1), xytext=(b0, g0),
                    arrowprops=dict(arrowstyle="->", color=PAL[lab], lw=lw))
        ax.scatter([b0], [g0], s=30, color=PAL[lab], edgecolors="k", zorder=3)
        ax.annotate(NAMES[lab], (b1, g1), textcoords="offset points", xytext=(6, 3),
                    fontsize=9, color=PAL[lab],
                    fontweight="bold" if lab in CHANGE else "normal")
    ax.set_xlabel("brightness"); ax.set_ylabel("greenness")
    ax.set_title("Class centroids move in brightness–greenness space, 2018→2020\n"
                 "dot = 2018, arrowhead = 2020; bold arrows = the four change classes", fontsize=12)
    _classic(ax)
    fig.tight_layout()
    _save(fig, "tc_trajectory.png")


def lda_projection(df):
    """Two-component LDA via whitening (symmetric eigenproblem) — best linear class separation.

    Uses the 6 independent TC features only; the three deltas are exact linear combinations
    (Δ = 2020 − 2018), which would make the within-class scatter singular.
    """
    feats = ["brightness_2018", "greenness_2018", "wetness_2018",
             "brightness_2020", "greenness_2020", "wetness_2020"]
    X = df[feats].to_numpy()
    y = df.label.to_numpy()
    X = (X - X.mean(0)) / X.std(0)
    mu = X.mean(0)
    p = X.shape[1]
    Sw = np.zeros((p, p)); Sb = np.zeros((p, p))
    for l in np.unique(y):
        Xl = X[y == l]; mul = Xl.mean(0)
        Sw += (Xl - mul).T @ (Xl - mul)
        d = (mul - mu).reshape(-1, 1)
        Sb += len(Xl) * (d @ d.T)
    Sw /= len(X); Sb /= len(X)
    Sw += 1e-6 * np.eye(p)                                   # ridge for stability
    # whiten by Sw (symmetric), then diagonalise Sb in the whitened space
    s, U = np.linalg.eigh(Sw)
    white = U @ np.diag(1.0 / np.sqrt(s)) @ U.T
    Sb_w = white @ Sb @ white
    evals, evecs = np.linalg.eigh(Sb_w)                      # ascending
    A = white @ evecs[:, [-1, -2]]                           # top-2 discriminants
    Z = X @ A

    fig, ax = plt.subplots(figsize=(10, 8))
    for lab in sorted(NAMES):
        s = Z[y == lab]
        big = lab in CHANGE
        ax.scatter(s[:, 0], s[:, 1], s=18 if big else 10, color=PAL[lab],
                   edgecolors="none", alpha=0.85 if big else 0.4,
                   label=f"{lab} {NAMES[lab]}")
    ax.set_xlabel("LD1"); ax.set_ylabel("LD2")
    ax.set_title("Linear discriminant projection of the training points (6 TC features)\n"
                 "how separable the 10 classes are in the space the classifier sees", fontsize=12)
    ax.legend(fontsize=8, frameon=False, ncol=2, markerscale=1.5)
    _classic(ax)
    fig.tight_layout()
    _save(fig, "tc_lda_projection.png")


def _save(fig, name):
    fig.savefig(os.path.join(OUT, name), dpi=140, bbox_inches="tight")
    plt.close(fig)
    print(f"wrote {OUT}/{name}")


def main():
    os.makedirs(OUT, exist_ok=True)
    df = pd.read_csv(CSV)
    scatter_deltas(df)
    boxplots_deltas(df)
    mean_delta_heatmap(df)
    trajectory(df)
    lda_projection(df)


if __name__ == "__main__":
    main()
