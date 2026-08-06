#!/usr/bin/env python3
"""pres_changecap_maps: same location classified under each change-class training cap.

The change-cap sensitivity analysis raises the training cap for the four change classes (50, 100, 150,
200 points; stable held at 200) on the v2 embedding classifier. This renders, for a cell, the interpreted
reference plus the classification at each cap, so the commission flood is visible: raising the cap fills
the map with (mostly false) change. Each panel is annotated with the share of pixels it labels as change.

Per-cap rasters (10-class codes 1..10):
  cap 50/100/150: data/raw/sensitivity_changecap_10class_percell/<bracket>/sens_<bracket>_cell<id>.tif
                  bands 1/2/3 = cap50/cap100/cap150
  cap 200:        data/raw/transfer_predictions/<bracket>/pred_<bracket>_cell<id>.tif, band 1 (v2)
  reference:      data/raw/rf_class_maps (CKIT ids crosswalked to the 10-class schema)

Output (PNG only), in presentation/figures/changecap/.
"""

import glob
import importlib.util
import os
import sys

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import rasterio
from matplotlib.patches import Patch, Rectangle

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
sys.path.insert(0, HERE)                              # slide_font
sys.path.insert(0, os.path.join(ROOT, "scripts"))    # pres_07's helpers (compare_interpreters)
import slide_font

_spec = importlib.util.spec_from_file_location("P7", os.path.join(HERE, "pres_07_speckle_with_ref.py"))
P7 = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(P7)

SENS_DIR = os.path.join(ROOT, "data", "raw", "sensitivity_changecap_10class_percell")
TRANSFER_DIR = os.path.join(ROOT, "data", "raw", "transfer_predictions")
OUT_DIR = os.path.join(ROOT, "presentation", "figures", "changecap")
CAPS = [50, 100, 150, 200]
CAP_BAND = {50: 1, 100: 2, 150: 3}                    # bands of the sens raster
CHANGE_CODES = {1, 2, 9, 10}                          # Harvest, Development, Beaver, Insect/Disease
LOCATIONS = [("04602", "2017_2019"), ("50721", "2020_2022")]


def _change_frac(img):
    valid = img > 0
    return float(np.isin(img, list(CHANGE_CODES))[valid].mean()) if valid.any() else float("nan")


def build_for_cell(cell, bracket, ref_paths, out_path):
    ref_f = glob.glob(f"{P7.RF_DIR}/**/rf_class_reviewer_*grid_{cell}_*.tif", recursive=True)[0]
    with rasterio.open(ref_f) as s:
        ref_img = P7.LUT[np.clip(s.read(1), 0, 62)]
        res = s.res[0]
    with rasterio.open(glob.glob(f"{SENS_DIR}/{bracket}/sens_{bracket}_cell{cell}.tif")[0]) as s:
        sens = {c: s.read(CAP_BAND[c]) for c in (50, 100, 150)}
    with rasterio.open(glob.glob(f"{TRANSFER_DIR}/{bracket}/pred_{bracket}_cell{cell}.tif")[0]) as s:
        cap200 = s.read(1)                            # band 1 = v2 = cap 200

    panels = [("interpreted reference", ref_img)]
    panels += [(f"cap {c}", sens[c]) for c in (50, 100, 150)]
    panels += [("cap 200", cap200)]

    plt.rcParams.update({"font.family": "sans-serif",
                         "font.sans-serif": ["Helvetica", "Arial", "DejaVu Sans"], "font.size": 14})
    slide_font.use_spectral()
    fig, axes = plt.subplots(1, len(panels), figsize=(2.55 * len(panels), 5.6))
    for ax, (name, img) in zip(axes, panels):
        ax.imshow(img, cmap=P7.CMAP, vmin=0, vmax=10, interpolation="nearest")
        ax.set_title(name, fontsize=15, fontweight="bold")
        ax.text(0.5, -0.05, f"change: {_change_frac(img):.1%}", transform=ax.transAxes,
                ha="center", va="top", fontsize=12)
        ax.set_xticks([]); ax.set_yticks([])

    h, w = ref_img.shape                              # 1 km scale bar on the reference panel
    km_px = 1000 / res
    y0 = h - 22
    axes[0].add_patch(Rectangle((12, y0), km_px, 6, facecolor="black", edgecolor="white", lw=0.6))
    axes[0].text(12 + km_px / 2, y0 - 6, "1 km", ha="center", va="bottom", fontsize=9, color="black")

    present = sorted({int(c) for _n, img in panels for c in np.unique(img) if c > 0})
    handles = [Patch(facecolor=P7.CLUT[c], edgecolor="0.4", label=P7.NAME10[c]) for c in present]
    fig.subplots_adjust(left=0.015, right=0.985, top=0.86, bottom=0.20, wspace=0.05)
    fig.legend(handles=handles, loc="lower center", ncol=min(len(present), 8), fontsize=12,
               frameon=False, bbox_to_anchor=(0.5, 0.02))
    fig.suptitle(f"Same Location Under Each Change-Class Training Cap (Cell {cell})",
                 fontsize=17, fontweight="bold", y=0.96)

    os.makedirs(os.path.dirname(out_path), exist_ok=True)
    fig.savefig(out_path, dpi=300, bbox_inches="tight")
    plt.close(fig)
    print(f"wrote {out_path}")


def main():
    ref_paths = P7._adjudicated_reference_paths()
    for cell, bracket in LOCATIONS:
        build_for_cell(cell, bracket, ref_paths,
                       os.path.join(OUT_DIR, f"changecap_maps_cell{cell}_{bracket}.png"))


if __name__ == "__main__":
    main()
