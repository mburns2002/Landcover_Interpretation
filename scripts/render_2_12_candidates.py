"""Render the Figure 2.12 candidate confusion matrices for the manuscript with a clean title, no wide
subtitle (details go in the caption), larger publication-size fonts, and American spelling. The v2
panel is pooled over all grid cells (the five per-bracket matrices summed, 180 cells), not the single
2018_2020 control bracket. Outputs go to manuscript_formatting/figures/figure_2_12_candidates/.

Run: python scripts/render_2_12_candidates.py
"""

import os

import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = f"{ROOT}/manuscript_formatting/figures/figure_2_12_candidates"
LABELS = ["Harvest", "Development", "Forest", "Urban", "Water", "Agriculture", "Grass/Shrub",
          "Wetland", "Beaver", "Insect/Disease"]                # 10-class order 1..10


def render_cm(M, title, path):
    """count heatmap colored by row proportion, with a PA column, a UA row, and OA and kappa in the
    corner. reference on rows, prediction on columns. larger fonts for print legibility."""
    M = M.astype(float)
    tp = np.diag(M); row = M.sum(1); col = M.sum(0); tot = M.sum()
    with np.errstate(invalid="ignore", divide="ignore"):
        rn = M / np.where(row[:, None] > 0, row[:, None], np.nan)     # row proportion
        pa = np.where(row > 0, tp / row, np.nan)                      # producer's (recall)
        ua = np.where(col > 0, tp / col, np.nan)                      # user's (precision)
    oa = tp.sum() / tot if tot else np.nan
    pe = (row * col).sum() / (tot * tot) if tot else np.nan
    kappa = (oa - pe) / (1 - pe) if tot and (1 - pe) else np.nan
    blues, greens = plt.get_cmap("Blues"), plt.get_cmap("Greens")

    img = np.ones((11, 11, 4))
    for i in range(10):
        for j in range(10):
            img[i, j] = blues(rn[i, j] if np.isfinite(rn[i, j]) else 0.0)
        img[i, 10] = greens(pa[i] if np.isfinite(pa[i]) else 0.0)
    for j in range(10):
        img[10, j] = greens(ua[j] if np.isfinite(ua[j]) else 0.0)
    img[10, 10] = greens(oa if np.isfinite(oa) else 0.0)

    fig, ax = plt.subplots(figsize=(11, 10))
    ax.imshow(img, aspect="auto")

    def tc(v):
        return "white" if (np.isfinite(v) and v > 0.5) else "black"

    for i in range(10):
        for j in range(10):
            c = int(M[i, j])
            if c:
                ax.text(j, i, f"{c:,}", ha="center", va="center", fontsize=8.5, color=tc(rn[i, j]))
    for i in range(10):                                    # PA column + reference support
        t = f"{pa[i]*100:.0f}%" if np.isfinite(pa[i]) else "-"
        ax.text(10, i, f"{t}\nn={int(row[i]):,}", ha="center", va="center", fontsize=8, color=tc(pa[i]))
    for j in range(10):                                    # UA row + predicted support
        t = f"{ua[j]*100:.0f}%" if np.isfinite(ua[j]) else "-"
        ax.text(j, 10, f"{t}\nn={int(col[j]):,}", ha="center", va="center", fontsize=8, color=tc(ua[j]))
    ax.text(10, 10, f"OA {oa*100:.0f}%\nκ {kappa:.2f}", ha="center", va="center", fontsize=9,
            color=tc(oa))

    ax.set_xticks(range(11)); ax.set_xticklabels(LABELS + ["PA"], rotation=45, ha="left", fontsize=11)
    ax.set_yticks(range(11)); ax.set_yticklabels(LABELS + ["UA"], fontsize=11)
    ax.xaxis.tick_top(); ax.xaxis.set_label_position("top")
    ax.set_xlabel("prediction (columns)", fontsize=12)
    ax.set_ylabel("reference (rows)", fontsize=12)
    ax.axhline(9.5, color="0.4", lw=1.0); ax.axvline(9.5, color="0.4", lw=1.0)
    ax.set_xticks(np.arange(-0.5, 11, 1), minor=True)
    ax.set_yticks(np.arange(-0.5, 11, 1), minor=True)
    ax.grid(which="minor", color="white", lw=0.6); ax.tick_params(which="minor", length=0)
    ax.set_title(title, fontsize=15, fontweight="bold", pad=30)
    fig.savefig(path, dpi=300, bbox_inches="tight")
    plt.close(fig)


def main():
    os.makedirs(OUT, exist_ok=True)

    # v2 pooled over all grid cells: sum the five per-bracket count matrices (180 cells)
    brackets = ["2017_2019", "2018_2020", "2019_2021", "2020_2022", "2021_2023"]
    mats = [pd.read_csv(f"{ROOT}/reports/transfer_confusion_adjudicated/cm_v2_{b}.csv", index_col=0)
            for b in brackets]
    v2 = sum(m.values for m in mats)
    render_cm(v2, "AlphaEarth Embedding v2, baseline + delta",
              f"{OUT}/cm_v2_allcells.png")
    print(f"v2 pooled over all cells: {int(v2.sum()):,} reference pixels")

    # spec_all pooled (already 168 cells)
    sp = pd.read_csv(f"{ROOT}/reports/spectral_composite_classified_maps/cm_specall_pooled.csv",
                     index_col=0).values
    render_cm(sp, "Spectral Composite, all sensors all indices",
              f"{OUT}/cm_specall_pooled.png")
    print(f"spec_all pooled: {int(sp.sum()):,} reference pixels")

    # remove the superseded single-bracket v2 candidate
    old = f"{OUT}/cm_v2_2018_2020.png"
    if os.path.exists(old):
        os.remove(old); print(f"removed {os.path.basename(old)} (replaced by cm_v2_allcells.png)")
    print(f"wrote cm_v2_allcells.png and cm_specall_pooled.png -> {OUT}/")


if __name__ == "__main__":
    main()
