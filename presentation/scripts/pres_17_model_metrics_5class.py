#!/usr/bin/env python3
"""pres_17_model_metrics_5class: grouped bar chart of five-class accuracy metrics by model.

Five-class (collapsed) counterpart of pres_17. Four metric groups on the x-axis (OA, F1, IoU, Kappa),
one bar per model inside each group, colored by model. Two versions:
  pres_17_model_metrics_5class.png            the five embedding models (v2 to v6)
  pres_17_model_metrics_5class_with_spec.png  the same, plus the spectral baseline (spec_all)

Values are the five-class metrics from manuscript_formatting/tables/T4.csv: OA, Macro-F1, Mean IoU, and
Kappa, all on the common 168-cell set. Note the all-Stable baseline OA is 0.985, so every model's OA
sits below the trivial baseline even though it looks high (Stable dominates the 5-class scheme).

Output (PNG only for the Google Slides deck).
"""

import os

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

import slide_font
import numpy as np
import pandas as pd
from matplotlib.lines import Line2D
slide_font.use_spectral()

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
T4 = os.path.join(ROOT, "manuscript_formatting", "tables", "T4.csv")
OUT = os.path.join(ROOT, "presentation", "figures")

# per-model colors: embeddings from the transfer-OA palette, spec_all brown (the tab10 next color)
COLOR = {"v2": "#1f77b4", "v3": "#2ca02c", "v4": "#9467bd", "v5": "#ff7f0e", "v6": "#d62728",
         "spec_all": "#8c564b"}
# (x-axis group label, table column)
STATS = [("OA", "OA"), ("F1", "Macro-F1"), ("IoU", "Mean IoU"), ("Kappa", "Kappa")]


def _draw(df, models, stem, title, caption, note):
    x = np.arange(len(STATS))
    n = len(models)
    bar_w = 0.8 / n

    fig, ax = plt.subplots(figsize=(10, 7.2))
    fig.subplots_adjust(left=0.08, right=0.98, top=0.92, bottom=0.33)

    for i, m in enumerate(models):
        offs = (i - (n - 1) / 2) * bar_w
        vals = [df.loc[m, col] for _, col in STATS]
        ax.bar(x + offs, vals, bar_w, color=COLOR[m], edgecolor="black", linewidth=0.5, label=m,
               zorder=3)
        for xi, v in zip(x + offs, vals):
            ax.text(xi, v + 0.012, f"{v:.2f}", ha="center", va="bottom", fontsize=8, color="0.2")

    ax.set_xticks(x)
    ax.set_xticklabels([lab for lab, _ in STATS], fontsize=15)
    ax.set_ylim(0, 1.0)
    ax.set_ylabel("Score", fontsize=14)
    ax.tick_params(axis="y", labelsize=12)
    ax.grid(False)
    for s in ("top", "right"):
        ax.spines[s].set_visible(False)

    # all-Stable baseline OA: OA you would get by predicting Stable everywhere (dashed reference line)
    baseline = float(df["All-Stable baseline OA"].iloc[0])
    ax.axhline(baseline, ls=(0, (6, 3)), color="#333333", lw=1.7, zorder=4)
    handles, labels = ax.get_legend_handles_labels()
    handles.append(Line2D([0], [0], color="#333333", ls=(0, (6, 3)), lw=1.7))
    labels.append(f"all-Stable baseline (OA = {baseline:.3f})")
    ax.legend(handles, labels, ncol=4, fontsize=11, loc="upper right", bbox_to_anchor=(0.995, 0.94),
              frameon=False, columnspacing=1.2, handletextpad=0.5)
    ax.set_title(title, fontsize=17, fontweight="bold", pad=12)

    fig.text(0.5, 0.25, caption, ha="center", va="top", fontsize=11, color="0.35", linespacing=1.4)
    fig.text(0.5, 0.15, note, ha="center", va="top", fontsize=9.5, color="0.45", linespacing=1.35)

    os.makedirs(OUT, exist_ok=True)
    fig.savefig(os.path.join(OUT, f"{stem}.png"), dpi=300)
    plt.close(fig)
    print(f"wrote {stem}.png")


NOTE = ("Metrics: OA = fraction of pixels correct; F1 = macro-average of per-class F1; IoU = mean per-class IoU;\n"
        "Kappa = chance-corrected agreement. OA is much higher because it is dominated by the abundant Stable\n"
        "class (~98% of pixels) that every model gets right, whereas F1 and IoU weight all classes equally (the\n"
        "rare change classes pull them down) and Kappa discounts chance agreement under the class skew.")


def main():
    df = pd.read_csv(T4).set_index("Source")

    cap = ("Five-class metrics on the common 168-cell set (Table T4). OA is dominated by Stable, so every\n"
           "model sits below the all-Stable baseline OA of 0.985.")
    _draw(df, ["v2", "v3", "v4", "v5", "v6"], "pres_17_model_metrics_5class",
          "Accuracy Metrics by Embedding Model (Five-Class)", cap, NOTE)

    _draw(df, ["v2", "v3", "v4", "v5", "v6", "spec_all"], "pres_17_model_metrics_5class_with_spec",
          "Accuracy Metrics by Model, with Spectral Baseline (Five-Class)", cap, NOTE)


if __name__ == "__main__":
    main()
