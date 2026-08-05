#!/usr/bin/env python3
"""pres_05_census_vs_points: one interpreted cell as a full census versus 50 sample points.

Two panels of the same real interpreted cell (cell 42180, chosen from the printed candidate list).
Left: the full interpreted reference raster, every pixel labeled, 10-class palette. Right: the identical
cell in light grey, overlaid with 50 points drawn by stratified random sampling from the reference,
colored by their reference class in the same palette. The point is that the 50 points cannot support
any statement about the spatial structure the left panel makes plain. Annotation is limited to the two
panel labels and a shared legend.

Data (local only, no Earth Engine): the adjudicated interpreted reference raster for the cell, from
data/raw/rf_class_maps/ (the reviewer named in exports/truth_selections.csv), remapped from CKIT label
codes to the 10-class schema. Palette from data/reference/model_maps_10class_legend.csv.

Sampling: stratified random, strata = reference classes, proportional (area) allocation summed to 50 by
largest remainder, drawn without replacement. Random seed is 42 (set below).

sizing: 12 x 7 in, near a 16:9 slide.

output (png only):
  presentation/figures/pres_05_census_vs_points.png
"""

import glob
import os
import re

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

import slide_font
from matplotlib.colors import to_rgb
from matplotlib.patches import Patch
import numpy as np
import pandas as pd
import rasterio

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
RF_DIR = os.path.join(ROOT, "data", "raw", "rf_class_maps")
TRUTH = os.path.join(ROOT, "exports", "truth_selections.csv")
LEGEND = os.path.join(ROOT, "data", "reference", "model_maps_10class_legend.csv")
OUT = os.path.join(ROOT, "presentation", "figures")

CELL = "42180"
SEED = 42
N_POINTS = 50

# CKIT label_id -> 10-class schema code (reference only); 10 and 13 are excluded (unknown, other)
CROSSWALK = {0: 4, 1: 6, 2: 7, 3: 3, 4: 5, 5: 8, 20: 1, 30: 2, 50: 10, 62: 9}
NAMES = {1: "Harvest", 2: "Development", 3: "Forest", 4: "Urban", 5: "Water", 6: "Agriculture",
         7: "Grass/Shrub", 8: "Wetland", 9: "Beaver", 10: "Insect/Disease"}
LUT = np.zeros(63, np.uint8)
for _k, _v in CROSSWALK.items():
    LUT[_k] = _v


def _pad(g):
    return str(int(g)).zfill(5)


def _reference_path(cell):
    # adjudicated reviewer's 10 m reference raster for the cell
    rx = re.compile(r"reviewer_([A-Za-z]+)_grid_(\d+)_sample_", re.I)
    idx = {}
    for p in sorted(glob.glob(os.path.join(RF_DIR, "**", "rf_class*.tif"), recursive=True)):
        m = rx.search(os.path.basename(p))
        if not m:
            continue
        with rasterio.open(p) as ds:
            if not (ds.transform.a == 10 and ds.transform.e == -10):
                continue
        idx.setdefault(_pad(m.group(2)), []).append((m.group(1).lower(), p))
    truth = {_pad(r.grid_id): str(r.reviewer).strip().lower()
             for r in pd.read_csv(TRUTH, dtype=str, keep_default_na=False).itertuples()}
    want = truth[cell]
    match = [p for r, p in idx[cell] if r == want]
    return match[0], want


def _palette():
    leg = pd.read_csv(LEGEND)
    return {int(r.code): (r.display_name, to_rgb(r.color)) for r in leg.itertuples() if int(r.code) > 0}


def _allocate(counts, n):
    # proportional (largest-remainder) allocation of n points to the present classes
    total = sum(counts.values())
    raw = {c: n * counts[c] / total for c in counts}
    alloc = {c: int(np.floor(v)) for c, v in raw.items()}
    rem = n - sum(alloc.values())
    for c in sorted(counts, key=lambda k: raw[k] - alloc[k], reverse=True)[:rem]:
        alloc[c] += 1
    return alloc


def main():
    path, reviewer = _reference_path(CELL)
    with rasterio.open(path) as ds:
        ref = LUT[np.clip(ds.read(1), 0, 62)]
    H, W = ref.shape
    valid = ref > 0
    n_valid = int(valid.sum())
    present = [c for c in range(1, 11) if (ref == c).any()]
    counts = {c: int((ref == c).sum()) for c in present}
    pal = _palette()

    rng = np.random.default_rng(SEED)
    alloc = _allocate(counts, N_POINTS)

    # diagnostics
    print(f"cell {CELL}, adjudicated reviewer '{reviewer}', raster {W}x{H} px, {n_valid:,} labeled px")
    print("class composition and stratified proportional allocation (seed 42):")
    for c in present:
        print(f"  {NAMES[c]:<16} {counts[c]:>8,} px  {100*counts[c]/n_valid:5.1f}%   -> {alloc[c]} points")
    print(f"  total points: {sum(alloc.values())}")

    # sample points: within each class, pick alloc[c] pixels without replacement
    pts_rc, pts_c = [], []
    for c in present:
        if alloc[c] == 0:
            continue
        rows, cols = np.where(ref == c)
        sel = rng.choice(rows.size, alloc[c], replace=False)
        for i in sel:
            pts_rc.append((rows[i], cols[i]))
            pts_c.append(c)

    plt.rcParams.update({"font.family": "sans-serif",
                         "font.sans-serif": ["Helvetica", "Arial", "DejaVu Sans"], "font.size": 16})
    slide_font.use_spectral()
    fig, (axL, axR) = plt.subplots(1, 2, figsize=(12, 7))
    fig.subplots_adjust(left=0.02, right=0.98, top=0.98, bottom=0.18, wspace=0.06)

    # left: full census, every pixel colored by class
    rgb = np.ones((H, W, 3))
    for c in present:
        rgb[ref == c] = pal[c][1]
    axL.imshow(rgb, interpolation="nearest")
    axL.set_axis_off()
    axL.text(0.5, -0.04, f"every pixel labeled\n({n_valid:,} px)", transform=axL.transAxes,
             ha="center", va="top", fontsize=17)

    # right: same cell in light grey, 50 sampled points colored by reference class
    grey = np.ones((H, W, 3))
    grey[valid] = (0.85, 0.85, 0.85)
    axR.imshow(grey, interpolation="nearest")
    axR.set_axis_off()
    for (r, cc), c in zip(pts_rc, pts_c):
        axR.plot(cc, r, marker="o", markersize=9, markerfacecolor=pal[c][1],
                 markeredgecolor="black", markeredgewidth=0.8, linestyle="none")
    axR.text(0.5, -0.04, f"{N_POINTS} sampled points", transform=axR.transAxes,
             ha="center", va="top", fontsize=17)

    # shared legend, classes present in the cell
    handles = [Patch(facecolor=pal[c][1], edgecolor="black", linewidth=0.6, label=NAMES[c])
               for c in present]
    fig.legend(handles=handles, loc="lower center", ncol=len(present), frameon=False,
               fontsize=14, handletextpad=0.5, columnspacing=1.4, bbox_to_anchor=(0.5, 0.02))

    os.makedirs(OUT, exist_ok=True)
    fig.savefig(os.path.join(OUT, "pres_05_census_vs_points.png"), dpi=300, bbox_inches="tight")
    plt.close(fig)
    print("\nwrote pres_05_census_vs_points.png")


if __name__ == "__main__":
    main()
