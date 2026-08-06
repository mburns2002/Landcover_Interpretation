#!/usr/bin/env python3
"""pres_17_model_metrics: grouped bar chart of accuracy metrics by model.

Four metric groups on the x-axis (OA, F1, IoU, Kappa), with one bar per model inside each group, colored
by model. Two versions:
  pres_17_model_metrics.png            the five embedding models (v2 to v6)
  pres_17_model_metrics_with_spec.png  the same, plus the spectral baseline (spec_all)

Values are the 10-class headline metrics from manuscript_formatting/tables/table_2_3.csv: OA, Macro-F1,
Mean IoU, and Kappa. Embedding models are scored on the 180-cell reference; spec_all is on the common
168-cell set (noted in the caption of the second version).

Output (PNG only for the Google Slides deck).
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
T23 = os.path.join(ROOT, "manuscript_formatting", "tables", "table_2_3.csv")
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
    ax.legend(ncol=n, fontsize=12, loc="upper right", frameon=False, columnspacing=1.1,
              handletextpad=0.5)
    ax.set_title(title, fontsize=17, fontweight="bold", pad=12)

    fig.text(0.5, 0.25, caption, ha="center", va="top", fontsize=11, color="0.35", linespacing=1.4)
    fig.text(0.5, 0.15, note, ha="center", va="top", fontsize=9.5, color="0.45", linespacing=1.35)

    os.makedirs(OUT, exist_ok=True)
    fig.savefig(os.path.join(OUT, f"{stem}.png"), dpi=300)
    plt.close(fig)
    print(f"wrote {stem}.png")


NOTE = ("Metrics: OA = fraction of pixels correct; F1 = macro-average of per-class F1; IoU = mean per-class IoU;\n"
        "Kappa = chance-corrected agreement. OA is much higher because it is dominated by the abundant common\n"
        "classes (Forest, Water, Agriculture) that every model gets right, whereas F1 and IoU weight all classes\n"
        "equally (the rare change classes pull them down) and Kappa discounts chance agreement under the class skew.")


def main():
    df = pd.read_csv(T23).set_index("Source")

    _draw(df, ["v2", "v3", "v4", "v5", "v6"], "pres_17_model_metrics",
          "Accuracy Metrics by Embedding Model",
          "10-class metrics on the 180-cell reference (Table 2.3).", NOTE)

    _draw(df, ["v2", "v3", "v4", "v5", "v6", "spec_all"], "pres_17_model_metrics_with_spec",
          "Accuracy Metrics by Model, with Spectral Baseline",
          "10-class metrics (Table 2.3). Embedding models on 180 cells; spec_all on the common 168-cell set.",
          NOTE)


if __name__ == "__main__":
    main()
