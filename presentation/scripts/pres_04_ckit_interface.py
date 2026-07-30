#!/usr/bin/env python3
"""pres_04_ckit_interface: annotated CKIT-RF interface plus the resulting interpreted cell.

Two-panel figure. Left: the CKIT-RF interface screenshot (presentation/assets/interface.png) with
numbered callouts for the interpretation steps. Right: the interpreted reference raster for the same
location (sample id 11), rendered in the 10-class palette with a legend.

Edit the CALLOUTS list below to change the callout text or move a marker. Each marker's `xy` is a
fraction of the screenshot, measured from the TOP-LEFT corner (x right, y down), so it is easy to read
off the image. Data are local only, no Earth Engine.
"""

import glob
import os
import re

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.colors import to_rgb
from matplotlib.patches import Patch
import numpy as np
import pandas as pd
import rasterio

# ---- callouts: edit the text and the (x, y) marker positions here (x, y are fractions from top-left) ----
CALLOUTS = [
    {"num": 1, "text": "Compare the imagery panels (yearly NBR, optical, NAIP, difference, and the RF "
                       "classification) to read the land cover and any change.", "xy": (0.40, 0.27)},
    {"num": 2, "text": "Choose a label, either a stable class or a disturbance class.", "xy": (0.085, 0.90)},
    {"num": 3, "text": "Draw a polygon over the feature on the target imagery.", "xy": (0.44, 0.80)},
    {"num": 4, "text": "Convert the polygon to labeled pixel samples.", "xy": (0.125, 0.235)},
    {"num": 5, "text": "Advance to the next assigned sample.", "xy": (0.115, 0.635)},
]
SAMPLE_ID = "11"

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
IFACE = os.path.join(ROOT, "presentation", "assets", "interface.png")
RF_DIR = os.path.join(ROOT, "data", "raw", "rf_class_maps")
TRUTH = os.path.join(ROOT, "exports", "truth_selections.csv")
LEGEND = os.path.join(ROOT, "data", "reference", "model_maps_10class_legend.csv")
OUT = os.path.join(ROOT, "presentation", "figures")

CROSSWALK = {0: 4, 1: 6, 2: 7, 3: 3, 4: 5, 5: 8, 20: 1, 30: 2, 50: 10, 62: 9}
NAMES = {1: "Harvest", 2: "Development", 3: "Forest", 4: "Urban", 5: "Water", 6: "Agriculture",
         7: "Grass/Shrub", 8: "Wetland", 9: "Beaver", 10: "Insect/Disease"}
LUT = np.zeros(63, np.uint8)
for _k, _v in CROSSWALK.items():
    LUT[_k] = _v
MARKER_COLOR = "#D62728"


def _pad(g):
    return str(int(g)).zfill(5)


def _reference_for_sample(sample_id):
    # rasters for this sample id, keyed by (grid, reviewer); pick the adjudicated reviewer from truth
    rx = re.compile(r"reviewer_([A-Za-z]+)_grid_(\d+)_sample_(\d+)_", re.I)
    cands = []
    for p in sorted(glob.glob(os.path.join(RF_DIR, "**", "rf_class*.tif"), recursive=True)):
        m = rx.search(os.path.basename(p))
        if not m or m.group(3) != str(sample_id):
            continue
        with rasterio.open(p) as ds:
            if not (ds.transform.a == 10 and ds.transform.e == -10):
                continue
        cands.append((_pad(m.group(2)), m.group(1).lower(), p))
    if not cands:
        raise SystemExit(f"no 10 m reference raster found for sample {sample_id}")
    grid = cands[0][0]
    truth = pd.read_csv(TRUTH, dtype=str, keep_default_na=False)
    want = {_pad(r.grid_id): str(r.reviewer).strip().lower() for r in truth.itertuples()}.get(grid)
    for g, rev, p in cands:
        if rev == want:
            return g, rev, p
    return cands[0]   # fall back to the first if truth does not name a reviewer here


def _palette():
    leg = pd.read_csv(LEGEND)
    return {int(r.code): (r.display_name, to_rgb(r.color)) for r in leg.itertuples() if int(r.code) > 0}


def main():
    if not os.path.isfile(IFACE):
        raise SystemExit(f"interface screenshot not found: {IFACE}\n"
                         f"add it, then re-run this script.")

    grid, reviewer, ref_path = _reference_for_sample(SAMPLE_ID)
    with rasterio.open(ref_path) as ds:
        ref = LUT[np.clip(ds.read(1), 0, 62)]
    H, W = ref.shape
    n_valid = int((ref > 0).sum())
    present = [c for c in range(1, 11) if (ref == c).any()]
    pal = _palette()
    iface = plt.imread(IFACE)
    ih, iw = iface.shape[:2]

    print(f"sample {SAMPLE_ID}: grid {grid}, adjudicated reviewer '{reviewer}', "
          f"reference {W}x{H} px, {n_valid:,} labeled px")
    print(f"interface screenshot {iw}x{ih}px; {len(CALLOUTS)} callouts")
    print("classes present:", ", ".join(NAMES[c] for c in present))

    plt.rcParams.update({"font.family": "sans-serif",
                         "font.sans-serif": ["Helvetica", "Arial", "DejaVu Sans"], "font.size": 15})
    fig = plt.figure(figsize=(16, 8))
    fig.text(0.5, 0.99, "CKIT-RF Interpretation: Interface and Resulting Reference",
             ha="center", va="top", fontsize=21, fontweight="bold")

    # ---- left panel: annotated interface ----
    iface_aspect = iw / ih
    ax_w = 0.60
    ax_h = ax_w * 16 / 8 / iface_aspect     # match the image aspect so markers map exactly
    top = 0.90
    axIF = fig.add_axes([0.015, top - ax_h, ax_w, ax_h])
    axIF.imshow(iface, aspect="auto")
    axIF.set_axis_off()
    axIF.set_title("Annotated interface (sample 11)", fontsize=16, pad=6)
    for co in CALLOUTS:
        x, y = co["xy"]
        axIF.text(x, 1 - y, str(co["num"]), transform=axIF.transAxes, ha="center", va="center",
                  fontsize=15, fontweight="bold", color="white", zorder=5,
                  bbox=dict(boxstyle="circle,pad=0.32", facecolor=MARKER_COLOR, edgecolor="white", lw=2))

    # ---- numbered step list below the interface ----
    import textwrap
    y = top - ax_h - 0.05
    for co in CALLOUTS:
        wrapped = textwrap.fill(co["text"], 78)
        axIF.figure.text(0.03, y, f"{co['num']}", fontsize=14, fontweight="bold", color=MARKER_COLOR,
                         ha="left", va="top")
        fig.text(0.055, y, wrapped, fontsize=13.5, ha="left", va="top", color="0.1")
        y -= 0.038 * (wrapped.count("\n") + 1) + 0.012

    # ---- right panel: interpreted reference raster ----
    axR = fig.add_axes([0.66, 0.28, 0.325, 0.58])
    rgb = np.ones((H, W, 3))
    for c in present:
        rgb[ref == c] = pal[c][1]
    axR.imshow(rgb, interpolation="nearest")
    axR.set_axis_off()
    axR.set_title(f"Interpreted reference cell (grid {grid})", fontsize=16, pad=6)
    axR.text(0.5, -0.03, f"every pixel labeled ({n_valid:,} px)", transform=axR.transAxes,
             ha="center", va="top", fontsize=14)
    handles = [Patch(facecolor=pal[c][1], edgecolor="black", linewidth=0.6, label=NAMES[c]) for c in present]
    ncol = 2 if len(present) > 5 else 1
    axR.legend(handles=handles, loc="upper center", bbox_to_anchor=(0.5, -0.09), frameon=False,
               fontsize=13, ncol=ncol, handletextpad=0.5, columnspacing=1.2)

    os.makedirs(OUT, exist_ok=True)
    fig.savefig(os.path.join(OUT, "pres_04_ckit_interface.png"), dpi=300, bbox_inches="tight")
    plt.close(fig)
    print("\nwrote pres_04_ckit_interface.png")


if __name__ == "__main__":
    main()
