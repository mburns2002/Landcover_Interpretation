"""Model-map speckle (neighbor-change) on the CURRENT pipeline, replacing the 154-location snapshot.

Recomputes the neighbor-change metric per embedding variant (v2 to v6) over the current 180 adjudicated
cells, using the temporally-matched per-bracket predictions (data/raw/transfer_predictions, bands 1 to
5), and pairs it with the current pooled overall accuracy to redraw the speckle-versus-accuracy
relationship. This is the current-basis counterpart of reports/model_comparison/model_speckle.csv,
which was drawn from the earlier static mosaic. Dedup-selection sensitivity is not reproduced, since it
is moot under adjudication (each cell has exactly one chosen reviewer).

Run: python scripts/model_speckle_current.py
Requires: rasterio, numpy, pandas, matplotlib
"""

import glob
import os

import numpy as np
import pandas as pd
import rasterio

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PRED_DIR = f"{ROOT}/data/raw/transfer_predictions"
OVERALL = f"{ROOT}/reports/spectral_composite_classified_maps/comparison/overall_comparison.csv"
OUT = f"{ROOT}/reports/model_comparison_current"
VBAND = {"v2": 1, "v3": 2, "v4": 3, "v5": 4, "v6": 5}       # transfer_predictions band order
# canonical variant palette (v2 blue, v3 green, v4 purple, v5 orange, v6 red)
VPAL = {"v2": "#1f77b4", "v3": "#2ca02c", "v4": "#9467bd", "v5": "#ff7f0e", "v6": "#d62728"}


def neighbor_change():
    """Per variant: horizontally-adjacent both-valid pixel pairs that differ, pooled over 180 cells."""
    cells = sorted(glob.glob(f"{PRED_DIR}/*/pred_*.tif"))
    diff = {v: 0 for v in VBAND}; valid = {v: 0 for v in VBAND}; total = {v: 0 for v in VBAND}
    for f in cells:
        with rasterio.open(f) as s:
            for v, b in VBAND.items():
                a = s.read(b)
                left, right = a[:, :-1], a[:, 1:]           # horizontal pairs
                both = (left > 0) & (right > 0)
                total[v] += left.size
                valid[v] += int(both.sum())
                diff[v] += int((both & (left != right)).sum())
    rows = []
    for v in VBAND:
        rows.append(dict(version=v, neighbor_change=round(diff[v] / valid[v], 4),
                         valid_pairs=valid[v], differing_pairs=diff[v], total_pairs=total[v],
                         coverage=round(valid[v] / total[v], 4)))
    return pd.DataFrame(rows), len(cells)


def main():
    os.makedirs(OUT, exist_ok=True)
    df, n = neighbor_change()
    df.to_csv(f"{OUT}/model_speckle.csv", index=False)
    print(f"neighbor-change over {n} current per-bracket cells:")
    print(df[["version", "neighbor_change", "coverage"]].to_string(index=False))

    # pair with current pooled overall accuracy
    ov = pd.read_csv(OVERALL)
    ov = ov[ov.bracket == "pooled"].copy()
    ov["version"] = ov.source.str.replace("embedding_", "", regex=False)
    acc = ov.set_index("version").OA
    df["pooled_OA"] = df.version.map(acc).round(4)
    df.to_csv(f"{OUT}/model_speckle.csv", index=False)

    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    fig, ax = plt.subplots(figsize=(6.2, 5))
    for _, r in df.iterrows():
        ax.scatter(r.neighbor_change, r.pooled_OA, color=VPAL[r.version], s=90, zorder=3,
                   edgecolor="white")
        ax.annotate(r.version, (r.neighbor_change, r.pooled_OA), xytext=(6, 4),
                    textcoords="offset points", fontsize=10, fontweight="bold")
    ax.set_xlabel("neighbor-change (per-pixel speckle)")
    ax.set_ylabel("pooled overall accuracy vs adjudicated reference")
    ax.set_title("Speckle versus accuracy, current 180-cell pipeline", fontsize=11)
    ax.grid(False)
    for sp in ("top", "right"):
        ax.spines[sp].set_visible(False)
    cap = ("Neighbor-change (fraction of horizontally-adjacent, both-valid pixel pairs whose class "
           "differs, over the current 180 per-bracket cells) against pooled overall accuracy for each "
           "embedding variant. The smooth variants (v2, v3, v5) sit at low speckle and higher "
           "accuracy, and the speckly v6 sits at high speckle and low accuracy.")
    import textwrap
    fig.tight_layout(rect=[0, 0.12, 1, 1])
    fig.text(0.5, 0.01, "\n".join(textwrap.wrap(cap, 92)), ha="center", va="bottom", fontsize=8,
             color="0.35")
    fig.savefig(f"{OUT}/speckle_vs_accuracy.png", dpi=150, bbox_inches="tight")
    plt.close(fig)
    print(f"\nwrote {OUT}/model_speckle.csv and speckle_vs_accuracy.png")


if __name__ == "__main__":
    main()
