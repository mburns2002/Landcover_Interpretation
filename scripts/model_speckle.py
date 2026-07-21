#!/usr/bin/env python3
"""Measure spatial speckle (neighbor-change) of the model maps over the FULL rasters.

`neighbor_change` = fraction of horizontally-adjacent, both-valid pixel pairs whose
class differs. Low (~0.08) = spatially smooth (coherent patches); high (~0.83) =
speckly / per-pixel (e.g. the v6 dot-product classifier). Background (0) pixels are
excluded so it characterizes the classified area, not the no-data padding.

Unlike the quick sample-window estimate in compare_interpreted_vs_model.py, this
streams every tile in row blocks and reports the exact whole-raster value.

Produces:
  - reports/model_comparison/model_speckle.csv
  - reports/model_comparison/model_speckle_bar.png          (neighbor-change per version)
  - reports/model_comparison/model_speckle_vs_accuracy.png  (speckle vs pooled OA)
  - reports/model_comparison/model_speckle_crops.png        (same-location crop per version)

Usage:
    python scripts/model_speckle.py
    python scripts/model_speckle.py --versions v2 v6

Requires: rasterio, numpy, pandas, matplotlib
"""

import argparse
import glob
import os
import warnings

import numpy as np
import pandas as pd
import rasterio
from rasterio.windows import Window, from_bounds

warnings.filterwarnings("ignore")

MODEL_DIR = "data/raw/model_maps"
LEGEND = "data/reference/model_maps_10class_legend.csv"
SUMMARY = "outputs/comparison_summary_by_version.csv"   # optional, for the scatter
OUT = "reports/model_comparison"
DEFAULT_VERSIONS = ["v2", "v3", "v4", "v5", "v6"]
# a central window with data in every version (bekka_grid_31320 footprint)
CROP_BOUNDS = (464760, 2593250, 468130, 2596620)


def tiles_for(version):
    return sorted(glob.glob(os.path.join(MODEL_DIR, f"classified_maps_10class_{version}", "*.tif")))


def full_neighbor_change(version, block=2048):
    """Stream every tile in row blocks; return exact whole-raster speckle stats."""
    diff = valid_pairs = valid_px = total_px = 0
    for t in tiles_for(version):
        with rasterio.open(t) as s:
            W, H = s.width, s.height
            for r0 in range(0, H, block):
                h = min(block, H - r0)
                a = s.read(1, window=Window(0, r0, W, h))
                total_px += a.size
                valid_px += int((a > 0).sum())
                left, right = a[:, :-1], a[:, 1:]
                both = (left > 0) & (right > 0)
                valid_pairs += int(both.sum())
                diff += int((both & (left != right)).sum())
    nc = diff / valid_pairs if valid_pairs else float("nan")
    return dict(version=version, neighbor_change_full=round(nc, 4),
                valid_pairs=valid_pairs, valid_px=valid_px, total_px=total_px,
                coverage=round(valid_px / total_px, 4) if total_px else float("nan"))


def read_crop(version, bounds):
    """Read the crop window from whichever tile covers it."""
    for t in tiles_for(version):
        with rasterio.open(t) as s:
            if (bounds[0] >= s.bounds.right or bounds[2] <= s.bounds.left or
                    bounds[1] >= s.bounds.top or bounds[3] <= s.bounds.bottom):
                continue
            win = from_bounds(*bounds, s.transform).round_offsets().round_lengths()
            arr = s.read(1, window=win, boundless=True, fill_value=0)
            if (arr > 0).any():
                return arr
    return None


def load_legend():
    df = pd.read_csv(LEGEND)
    codes = [int(c) for c in df.code if int(c) > 0]
    colors = {int(r.code): r.color for r in df.itertuples()}
    names = {int(r.code): r.display_name for r in df.itertuples()}
    return codes, colors, names


def _caption(fig, text, top=1.0, width=80):
    import textwrap
    wrapped = "\n".join(textwrap.wrap(text, width))
    nlines = wrapped.count("\n") + 1
    fig.tight_layout(rect=[0, 0.02 + 0.05 * nlines, 1, top])
    fig.text(0.5, 0.01, wrapped, ha="center", va="bottom", fontsize=8, color="0.35")


def plot_bar(df, out_path):
    import matplotlib.pyplot as plt
    fig, ax = plt.subplots(figsize=(7, 4))
    colors = ["#2ca02c" if v < 0.5 else "#d62728" for v in df.neighbor_change_full]
    ax.bar(df.version, df.neighbor_change_full, color=colors)
    ax.set_ylabel("neighbor-change (full raster)")
    ax.set_xlabel("model version")
    ax.set_title("Model-map spatial speckle by version\n(low = smooth patches, high = per-pixel)")
    ax.axhline(0.5, ls="--", lw=0.8, color="gray")
    for x, v in enumerate(df.neighbor_change_full):
        ax.text(x, v + 0.01, f"{v:.2f}", ha="center", fontsize=9)
    ax.set_ylim(0, 1)
    _caption(fig, "Each bar is one model version's whole-raster neighbor-change, the fraction of "
             "horizontally adjacent valid pixel pairs whose class differs. Low values near the green "
             "end mean spatially smooth maps with coherent patches, and high values near the red end "
             "mean speckly per-pixel maps such as the v6 dot-product classifier, with the dashed line "
             "at 0.5 separating the two regimes. Read the bar heights to rank the versions from "
             "smoothest to noisiest.")
    fig.savefig(out_path, dpi=140, bbox_inches="tight")
    plt.close(fig)


def plot_vs_accuracy(df, out_path):
    import matplotlib.pyplot as plt
    if not os.path.exists(SUMMARY):
        print("  (skip scatter: comparison summary not found)")
        return
    s = pd.read_csv(SUMMARY)[["version", "overall_accuracy"]]
    m = df.merge(s, on="version", how="inner")
    if m.empty:
        print("  (skip scatter: no overlapping versions)")
        return
    fig, ax = plt.subplots(figsize=(6.5, 5))
    ax.scatter(m.neighbor_change_full, m.overall_accuracy, s=70, color="#1f77b4")
    for r in m.itertuples():
        ax.annotate(r.version, (r.neighbor_change_full, r.overall_accuracy),
                    textcoords="offset points", xytext=(6, 4), fontsize=9)
    ax.set_xlabel("neighbor-change (full raster speckle)")
    ax.set_ylabel("pooled overall accuracy vs. interpreted")
    ax.set_title("Speckle vs. agreement with interpretations")
    ax.grid(alpha=0.3)
    _caption(fig, "Each point is one model version, plotting its whole-raster neighbor-change "
             "(speckle) on the x-axis against its pooled overall accuracy versus the interpreted "
             "reference on the y-axis, labelled by version. This shows whether spatially noisier maps "
             "agree more or less with the human interpretations. Read left to right to see how "
             "accuracy changes as speckle increases across the versions.")
    fig.savefig(out_path, dpi=140, bbox_inches="tight")
    plt.close(fig)


def plot_crops(versions, out_path):
    import matplotlib.pyplot as plt
    from matplotlib.colors import ListedColormap, BoundaryNorm
    codes, colors, _ = load_legend()
    order = sorted(codes)
    cmap = ListedColormap(["#ffffff"] + [colors[c] for c in order])
    norm = BoundaryNorm(np.arange(-0.5, len(order) + 1.5), cmap.N)
    lut = {c: i + 1 for i, c in enumerate(order)}

    crops = [(v, read_crop(v, CROP_BOUNDS)) for v in versions]
    crops = [(v, a) for v, a in crops if a is not None]
    n = len(crops)
    fig, axes = plt.subplots(1, n, figsize=(3 * n, 3.4))
    axes = np.atleast_1d(axes)
    for ax, (v, a) in zip(axes, crops):
        remap = np.zeros_like(a, dtype=np.int16)
        for c, i in lut.items():
            remap[a == c] = i
        ax.imshow(remap, cmap=cmap, norm=norm, interpolation="nearest")
        both = (a[:, :-1] > 0) & (a[:, 1:] > 0)
        nc = ((a[:, :-1] != a[:, 1:]) & both).sum() / both.sum() if both.sum() else float("nan")
        ax.set_title(f"{v}\nneighbor-change {nc:.2f}", fontsize=9)
        ax.set_xticks([]); ax.set_yticks([])
    fig.suptitle("Same location across model versions (smooth vs. speckly)", fontsize=11)
    _caption(fig, "Each panel is the same ground location classified by a different model version, "
             "drawn in the 10-class land-cover colour scheme, with its local neighbor-change value "
             "printed above. Smooth versions render the scene as coherent patches, while speckly "
             "versions such as v6 break it into per-pixel noise. Compare the panels side by side to "
             "see the same landscape grow noisier as neighbor-change rises.", top=0.95, width=110)
    fig.savefig(out_path, dpi=140, bbox_inches="tight")
    plt.close(fig)


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--versions", nargs="+", default=DEFAULT_VERSIONS)
    ap.add_argument("--block", type=int, default=2048, help="row-block height for streaming")
    args = ap.parse_args()

    os.makedirs(OUT, exist_ok=True)
    rows = []
    for v in args.versions:
        if not tiles_for(v):
            print(f"  {v}: no tiles, skipping")
            continue
        print(f"  scanning {v} (full raster) ...", flush=True)
        r = full_neighbor_change(v, args.block)
        rows.append(r)
        print(f"    neighbor_change={r['neighbor_change_full']:.4f}  coverage={r['coverage']:.2f}")

    df = pd.DataFrame(rows)
    df.to_csv(os.path.join(OUT, "model_speckle.csv"), index=False)
    plot_bar(df, os.path.join(OUT, "model_speckle_bar.png"))
    plot_vs_accuracy(df, os.path.join(OUT, "model_speckle_vs_accuracy.png"))
    plot_crops(args.versions, os.path.join(OUT, "model_speckle_crops.png"))

    print("\n" + "=" * 50)
    print(df.to_string(index=False))
    print(f"\nwrote {OUT}/model_speckle.csv + 3 plots")


if __name__ == "__main__":
    main()
