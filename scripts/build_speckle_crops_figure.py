#!/usr/bin/env python3
"""Figure 2.9, the classified-map speckle crop, regenerated from the current 180-cell pipeline.

One panel per embedding configuration (v2 to v6) showing the same ground location classified by each,
to illustrate the neighbor-change speckle metric visually. This replaces the earlier crop drawn from
the 154-location model_comparison snapshot; it now uses the current temporally-matched per-bracket
predictions (data/raw/transfer_predictions, bands 1 to 5 = v2 to v6), the same classifications behind
the current spatial-structure diagnostics. The neighbor-change value annotated on each panel is
computed over all 180 current cells, not the snapshot.

Crop location: cell 31320 (bracket 2018_2020), whose footprint equals the earlier crop bounds
(464760, 2593250, 468130, 2596620 in EPSG:5070), so the location is reused for continuity. It contains
a water body where the v6 salt-and-pepper speckle is visually obvious.

Run: python scripts/build_speckle_crops_figure.py
Requires: rasterio, numpy, matplotlib
"""

import glob
import importlib.util
import os
import textwrap

import matplotlib.pyplot as plt
import numpy as np
import rasterio
from matplotlib.colors import ListedColormap, to_rgb
from matplotlib.patches import Patch, Rectangle

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PRED_DIR = f"{ROOT}/data/raw/transfer_predictions"
OUT = f"{ROOT}/manuscript_formatting/figures"
CROP_CELL = "31320"                                        # footprint matches the earlier crop bounds
VBAND = {"v2": 1, "v3": 2, "v4": 3, "v5": 4, "v6": 5}      # transfer_predictions band order
NAME10 = {1: "Harvest", 2: "Development", 3: "Forest", 4: "Urban", 5: "Water",
          6: "Agriculture", 7: "Grass/Shrub", 8: "Wetland", 9: "Beaver", 10: "Insect/Disease"}


def _load(name, path):
    spec = importlib.util.spec_from_file_location(name, os.path.join(ROOT, "scripts", path))
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


C = _load("C", "compare_interpreted_vs_model.py")
C10 = C.load_mappings()[2]                                  # canonical 10-class palette {code: color}
# color lookup: index 0 = nodata (white), 1..10 = class colors
CLUT = np.ones((11, 4))
for code, col in C10.items():
    CLUT[code] = to_rgb(col) + (1.0,)
CMAP = ListedColormap([CLUT[i] for i in range(11)])


def neighbor_change_all():
    """Current neighbor-change per variant: fraction of horizontally-adjacent, both-valid pixel pairs
    whose class differs, pooled over all 180 current cells."""
    cells = sorted(glob.glob(f"{PRED_DIR}/*/pred_*.tif"))
    diff = {v: 0 for v in VBAND}
    tot = {v: 0 for v in VBAND}
    for f in cells:
        with rasterio.open(f) as s:
            for v, b in VBAND.items():
                a = s.read(b)
                left, right = a[:, :-1], a[:, 1:]           # horizontally-adjacent pairs
                valid = (left > 0) & (right > 0)
                tot[v] += int(valid.sum())
                diff[v] += int((valid & (left != right)).sum())
    return {v: diff[v] / tot[v] for v in VBAND}, len(cells)


def main():
    os.makedirs(OUT, exist_ok=True)
    nc, n_cells = neighbor_change_all()
    print(f"current neighbor-change over {n_cells} cells:")
    for v in VBAND:
        print(f"  {v}: {nc[v]:.4f}")

    crop_f = glob.glob(f"{PRED_DIR}/*/pred_*_cell{CROP_CELL}.tif")
    if not crop_f:
        raise SystemExit(f"STOP: crop cell {CROP_CELL} not found in current predictions.")
    with rasterio.open(crop_f[0]) as s:
        bands = {v: s.read(b) for v, b in VBAND.items()}
        res = s.res[0]                                       # metres per pixel (10 m)

    fig, axes = plt.subplots(1, 5, figsize=(13.5, 5.4))
    for ax, v in zip(axes, VBAND):
        ax.imshow(bands[v], cmap=CMAP, vmin=0, vmax=10, interpolation="nearest")
        ax.set_title(v, fontsize=14, fontweight="bold")
        # neighbor-change value below the panel, clear of the legend
        ax.text(0.5, -0.05, f"neighbor-change {nc[v]:.3f}", transform=ax.transAxes,
                ha="center", va="top", fontsize=12)
        ax.set_xticks([]); ax.set_yticks([])
    # scale bar on the first panel: 1 km = 100 px at 10 m
    h, w = bands["v2"].shape
    km_px = 1000 / res
    y0 = h - 22
    axes[0].add_patch(Rectangle((12, y0), km_px, 6, facecolor="black", edgecolor="white", lw=0.6))
    axes[0].text(12 + km_px / 2, y0 - 6, "1 km", ha="center", va="bottom", fontsize=8, color="black")

    # class legend for classes present in the crop, using the standard palette
    present = sorted({int(c) for v in VBAND for c in np.unique(bands[v]) if c > 0})
    handles = [Patch(facecolor=CLUT[c], edgecolor="0.4", label=NAME10[c]) for c in present]
    # panels occupy the top band; legend and caption sit below without overlap
    fig.subplots_adjust(left=0.02, right=0.98, top=0.88, bottom=0.34, wspace=0.05)
    fig.legend(handles=handles, loc="lower center", ncol=5, fontsize=12,
               frameon=False, bbox_to_anchor=(0.5, 0.18))

    fig.suptitle(f"Same Location Classified by Each Embedding Configuration (Cell {CROP_CELL})",
                 fontsize=15, fontweight="bold", y=0.97)

    # descriptive caption band below the class legend
    caption = (
        f"The same NAIP grid cell (cell {CROP_CELL}) classified by each embedding configuration, v2 "
        "through v6, with the standard land-cover class colors. Each panel is annotated with its "
        "neighbor-change fraction, the share of horizontally adjacent pixel pairs assigned differing "
        "classes pooled over all 180 cells, a per-pixel speckle measure. The scale bar is 1 km. The "
        "dot-product configuration v6 fragments into salt-and-pepper speckle, while the "
        "baseline-preserving configurations stay spatially coherent."
    )
    wrapped = "\n".join(textwrap.wrap(caption, 115))
    fig.text(0.5, 0.015, wrapped, ha="center", va="bottom", fontsize=9, color="0.3")

    png = f"{OUT}/figure_2_9_speckle_crops.png"
    pdf = f"{OUT}/figure_2_9_speckle_crops.pdf"
    fig.savefig(png, dpi=300, bbox_inches="tight")
    fig.savefig(pdf, bbox_inches="tight")
    plt.close(fig)
    print(f"wrote {png} and {pdf}")


if __name__ == "__main__":
    main()
