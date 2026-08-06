#!/usr/bin/env python3
"""pres_changecap_curves: change-class training-cap sensitivity, deck curve figures.

From reports/sensitivity_changecap_5class/sensitivity_metrics_long_5class.csv (five-class collapse,
common 180-cell set), three figures showing what raising the change-class training cap (50, 100, 150,
200 points; stable held at 200) does to the four change classes:

  changecap_predicted_pixels_vs_cap.png   predicted pixels vs cap, one panel per change class, with the
                                          interpreted-reference count (dashed) -> the commission flood
  changecap_precision_recall_vs_cap.png   precision (UA) and recall (PA) vs cap -> recall barely rises
                                          while precision stays near zero
  changecap_kappa_vs_cap.png              overall kappa and macro-F1 vs cap -> the map degrades overall

Output (PNG only), in presentation/figures/changecap/.
"""

import os

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

import slide_font
import numpy as np
import pandas as pd
slide_font.use_spectral()

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
CSV = os.path.join(ROOT, "reports", "sensitivity_changecap_5class", "sensitivity_metrics_long_5class.csv")
OUT_DIR = os.path.join(ROOT, "presentation", "figures", "changecap")

CAPS = [50, 100, 150, 200]
# change classes (5-class codes) with distinct line colors
CH = [(2, "Harvest", "#C9A227"), (3, "Development", "#d62728"),
      (4, "Insect/Disease", "#1f78b4"), (5, "Beaver", "#ff7f0e")]
AXIS_FS, TICK_FS, BODY_FS = 15, 12, 13


def _clean(ax, title):
    ax.grid(False)
    for sp in ("top", "right"):
        ax.spines[sp].set_visible(False)
    ax.set_xticks(CAPS)
    ax.tick_params(labelsize=TICK_FS)
    ax.set_title(title, fontsize=AXIS_FS, fontweight="bold")


def _series(df, code, col):
    s = df[df.class_code == code].set_index("cap")[col]
    return [float(s.loc[c]) for c in CAPS]


def predicted_pixels(df):
    fig, axes = plt.subplots(2, 2, figsize=(10, 7.8))
    for ax, (code, name, color) in zip(axes.ravel(), CH):
        pred = np.array(_series(df, code, "predicted_pixels")) / 1e3
        support = df[df.class_code == code]["support"].iloc[0] / 1e3
        ax.plot(CAPS, pred, "-o", color=color, lw=2.2, ms=6, zorder=3)
        ax.axhline(support, ls=(0, (5, 2)), color="0.35", lw=1.6)
        ax.set_ylim(0, max(pred.max(), support) * 1.15 + 1)
        _clean(ax, name)
        ax.set_ylabel("pixels (thousands)", fontsize=12)
    for ax in axes[1, :]:
        ax.set_xlabel("Change-class training cap (points)", fontsize=13)
    fig.suptitle("Predicted Change Pixels vs Training Cap (Five-Class)", fontsize=18,
                 fontweight="bold", y=0.965)
    fig.text(0.5, 0.035, "Solid: change pixels predicted at each cap. Dashed: interpreted-reference "
             "count. Higher caps flood the map with false change.",
             ha="center", va="bottom", fontsize=11, color="0.35")
    fig.subplots_adjust(left=0.08, right=0.98, top=0.88, bottom=0.16, hspace=0.36, wspace=0.24)
    fig.savefig(os.path.join(OUT_DIR, "changecap_predicted_pixels_vs_cap.png"), dpi=300)
    plt.close(fig)


def precision_recall(df):
    fig, (axp, axr) = plt.subplots(1, 2, figsize=(11, 5.8), sharey=True)
    for code, name, color in CH:
        axp.plot(CAPS, _series(df, code, "precision"), "-o", color=color, lw=2.2, ms=6, label=name)
        axr.plot(CAPS, _series(df, code, "recall"), "-o", color=color, lw=2.2, ms=6, label=name)
    _clean(axp, "Precision (user's accuracy)")
    _clean(axr, "Recall (producer's accuracy)")
    axp.set_ylim(0, 1.0)
    axp.set_ylabel("Score", fontsize=AXIS_FS)
    for ax in (axp, axr):
        ax.set_xlabel("Change-class training cap (points)", fontsize=13)
    axr.legend(fontsize=11, frameon=False, loc="upper left", title="Change class", title_fontsize=11)
    fig.suptitle("Change-Class Precision and Recall vs Training Cap", fontsize=18,
                 fontweight="bold", y=0.965)
    fig.text(0.5, 0.03, "Raising the cap lifts recall only modestly while precision stays near zero: the "
             "extra change predictions are almost all false positives.",
             ha="center", va="bottom", fontsize=11, color="0.35")
    fig.subplots_adjust(left=0.07, right=0.98, top=0.84, bottom=0.20, wspace=0.08)
    fig.savefig(os.path.join(OUT_DIR, "changecap_precision_recall_vs_cap.png"), dpi=300)
    plt.close(fig)


def kappa(df):
    agg = df.drop_duplicates("cap").set_index("cap")
    fig, ax = plt.subplots(figsize=(7.5, 5.0))
    ax.plot(CAPS, [agg.loc[c, "kappa"] for c in CAPS], "-o", color="#4e79a7", lw=2.4, ms=7, label="Kappa")
    ax.plot(CAPS, [agg.loc[c, "macro_F1"] for c in CAPS], "-s", color="#b07aa1", lw=2.4, ms=6,
            label="Macro-F1")
    _clean(ax, "")
    ax.set_ylim(0, max(agg["macro_F1"].max(), agg["kappa"].max()) * 1.25)
    ax.set_xlabel("Change-class training cap (points)", fontsize=14)
    ax.set_ylabel("Score", fontsize=AXIS_FS)
    ax.legend(fontsize=12, frameon=False, loc="upper right")
    ax.set_title("Overall Kappa and Macro-F1 vs Training Cap (Five-Class)", fontsize=16,
                 fontweight="bold", pad=10)
    fig.text(0.5, 0.035, "Chance-corrected agreement falls as the cap rises: the added false change "
             "outweighs the small recall gain.", ha="center", va="bottom", fontsize=11, color="0.35")
    fig.subplots_adjust(left=0.11, right=0.97, top=0.90, bottom=0.21)
    fig.savefig(os.path.join(OUT_DIR, "changecap_kappa_vs_cap.png"), dpi=300)
    plt.close(fig)


def main():
    df = pd.read_csv(CSV)
    os.makedirs(OUT_DIR, exist_ok=True)
    predicted_pixels(df)
    precision_recall(df)
    kappa(df)
    print("wrote changecap_predicted_pixels_vs_cap.png, changecap_precision_recall_vs_cap.png, "
          "changecap_kappa_vs_cap.png")


if __name__ == "__main__":
    main()
