#!/usr/bin/env python3
"""Figure 2.9, the classified-map speckle crop, regenerated from the current 180-cell pipeline.

One panel per classification of the same ground location (cell 31320): the spectral baseline (Sentinel-2
Random Forest) followed by each embedding configuration (v2 to v6), to show how map coherence differs
across feature sets. The embedding panels use the current temporally-matched per-bracket predictions
(data/raw/transfer_predictions, bands 1 to 5 = v2 to v6); the spectral panel uses the matching Sentinel-2
RF classification under data/raw/rf_class_maps (its CKIT class ids are remapped to the model's 10 codes).

Crop location: cell 31320 (bracket 2018_2020), footprint (464760, 2593250, 468130, 2596620) in
EPSG:5070. The spectral and prediction rasters share this exact footprint (both 337 x 337 at 10 m), so
all six panels are pixel-aligned. The cell contains a water body where the v6 salt-and-pepper speckle is
visually obvious.

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
RF_MAP_DIR = f"{ROOT}/data/raw/rf_class_maps"
OUT = f"{ROOT}/manuscript_formatting/figures"
CROP_CELL = "31320"                                        # footprint matches the earlier crop bounds
VBAND = {"v2": 1, "v3": 2, "v4": 3, "v5": 4, "v6": 5}      # transfer_predictions band order
NAME10 = {1: "Harvest", 2: "Development", 3: "Forest", 4: "Urban", 5: "Water",
          6: "Agriculture", 7: "Grass/Shrub", 8: "Wetland", 9: "Beaver", 10: "Insect/Disease"}
# model code -> CKIT label id (the spectral RF rasters are stored as CKIT ids)
CKIT = {1: 20, 2: 30, 3: 3, 4: 0, 5: 4, 6: 1, 7: 2, 8: 5, 9: 62, 10: 50}
CKIT2CODE = {v: k for k, v in CKIT.items()}


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


def _spectral_crop():
    """Sentinel-2 RF classification of the crop cell, remapped from CKIT ids to the model's 10 codes."""
    files = glob.glob(f"{RF_MAP_DIR}/*_s2_{CROP_CELL}/*.tif")
    if not files:
        raise SystemExit(f"STOP: spectral RF map for cell {CROP_CELL} not found under {RF_MAP_DIR}.")
    with rasterio.open(files[0]) as s:
        raw = s.read(1)
    out = np.zeros_like(raw)
    for ckit_val, code in CKIT2CODE.items():
        out[raw == ckit_val] = code                        # CKIT id -> model code (unmapped stays 0)
    return out


def main():
    os.makedirs(OUT, exist_ok=True)

    crop_f = glob.glob(f"{PRED_DIR}/*/pred_*_cell{CROP_CELL}.tif")
    if not crop_f:
        raise SystemExit(f"STOP: crop cell {CROP_CELL} not found in current predictions.")
    with rasterio.open(crop_f[0]) as s:
        bands = {v: s.read(b) for v, b in VBAND.items()}
        res = s.res[0]                                       # metres per pixel (10 m)

    panels = [("spectral", _spectral_crop())] + [(v, bands[v]) for v in VBAND]

    fig, axes = plt.subplots(1, len(panels), figsize=(16.2, 5.4))
    for ax, (name, arr) in zip(axes, panels):
        ax.imshow(arr, cmap=CMAP, vmin=0, vmax=10, interpolation="nearest")
        ax.set_title(name, fontsize=14, fontweight="bold")
        ax.set_xticks([]); ax.set_yticks([])
    # scale bar on the first panel: 1 km = 100 px at 10 m
    h, w = panels[0][1].shape
    km_px = 1000 / res
    y0 = h - 22
    axes[0].add_patch(Rectangle((12, y0), km_px, 6, facecolor="black", edgecolor="white", lw=0.6))
    axes[0].text(12 + km_px / 2, y0 - 6, "1 km", ha="center", va="bottom", fontsize=8, color="black")

    # class legend for classes present in any panel, using the standard palette
    present = sorted({int(c) for _, arr in panels for c in np.unique(arr) if c > 0})
    handles = [Patch(facecolor=CLUT[c], edgecolor="0.4", label=NAME10[c]) for c in present]
    # panels occupy the top band; legend and caption sit below without overlap
    fig.subplots_adjust(left=0.02, right=0.98, top=0.88, bottom=0.32, wspace=0.05)
    fig.legend(handles=handles, loc="lower center", ncol=5, fontsize=12,
               frameon=False, bbox_to_anchor=(0.5, 0.16))

    fig.suptitle(f"Same Location Classified by the Spectral Baseline and Embedding Configurations "
                 f"(Cell {CROP_CELL})", fontsize=15, fontweight="bold", y=0.97)

    # descriptive caption band below the class legend
    caption = (
        f"The same NAIP grid cell (cell {CROP_CELL}) classified by the spectral baseline (Sentinel-2 "
        "Random Forest) and by each embedding configuration, v2 through v6, with the standard land-cover "
        "class colors. The scale bar is 1 km. The dot-product configuration v6 fragments into "
        "salt-and-pepper speckle, while the spectral baseline and the baseline-preserving embedding "
        "configurations stay spatially coherent."
    )
    wrapped = "\n".join(textwrap.wrap(caption, 130))
    fig.text(0.5, 0.015, wrapped, ha="center", va="bottom", fontsize=9, color="0.3")

    png = f"{OUT}/figure_2_9_speckle_crops.png"
    pdf = f"{OUT}/figure_2_9_speckle_crops.pdf"
    fig.savefig(png, dpi=300, bbox_inches="tight")
    fig.savefig(pdf, bbox_inches="tight")
    plt.close(fig)
    print(f"wrote {png} and {pdf}")


if __name__ == "__main__":
    main()
