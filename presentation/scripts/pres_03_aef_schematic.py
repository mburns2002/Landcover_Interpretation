#!/usr/bin/env python3
"""pres_03_aef_schematic: what goes into an AlphaEarth Foundations embedding and what comes out.

A left-to-right schematic: the inference input sensor streams on the left, the AlphaEarth
Foundations model in the middle, and one 64-dimensional annual embedding per pixel on the right. The
output is annotated with the fact that one embedding covers a single year, which motivates the
two-date configurations on the next slide.

The input list is taken from the AlphaEarth Foundations paper (Brown et al. 2025), Table S1, which is
in presentation/assets/alphaearth.pdf. That table tags each data source as "input, target" or
"target", and its caption states that only the input sources are required at inference time. So only
the three input sources appear on the left. The many target-only sources (ALOS PALSAR, Copernicus
DEM, GEDI, ERA5-Land, GRACE, NLCD, Wikipedia, GBIF) are training reconstruction targets, not inputs,
and are deliberately excluded. The 64-dimension unit-sphere output, the 10 m resolution, and the
annual cadence are all stated in the paper (pages 3, 19, and 33).

vector, not raster mockup: drawn with matplotlib patches, exported to png at 300 dpi so text is crisp.

sizing: 10 x 5.6 in, the content area of a 16:9 slide, leaving room for a caption as separate slide
text below the image.

output (png only):
  presentation/figures/pres_03_aef_schematic.png
"""

import os

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch, FancyArrowPatch

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
OUT = os.path.join(ROOT, "presentation", "figures")

# inference inputs, from Brown et al. 2025 Table S1 (rows tagged "input, target")
INPUTS = [
    ("Sentinel-2", "Optical: B2, B3, B4, B8, B11", "#0072B2"),
    ("Landsat 8/9", "Optical + thermal: B2-B6, B8, B10", "#D55E00"),
    ("Sentinel-1", "C-band SAR: VV, VH, HH, HV, angle", "#009E73"),
]
# target-only sources from Table S1, excluded from the inputs (printed for the record)
TARGET_ONLY = ["ALOS PALSAR (L-band SAR)", "Copernicus DEM", "GEDI (LiDAR)", "ERA5-Land (climate)",
               "GRACE (gravity)", "NLCD (land cover)", "Wikipedia (text)", "GBIF (text)"]


def _style():
    plt.rcParams.update({
        "font.family": "sans-serif",
        "font.sans-serif": ["Helvetica", "Arial", "DejaVu Sans"],
        "font.size": 16,
    })


def _box(ax, x, y, w, h, edge, lw=2.0, face="white"):
    ax.add_patch(FancyBboxPatch((x, y), w, h, boxstyle="round,pad=0.006,rounding_size=0.02",
                                linewidth=lw, edgecolor=edge, facecolor=face, zorder=3))


def _arrow(ax, x0, y0, x1, y1):
    ax.add_patch(FancyArrowPatch((x0, y0), (x1, y1), arrowstyle="-|>", mutation_scale=18,
                                 lw=2.0, color="0.35", shrinkA=2, shrinkB=2, zorder=2))


def main():
    # diagnostics before plotting
    print("AlphaEarth Foundations inference inputs (Brown et al. 2025, Table S1, 'input, target'):")
    for name, bands, _ in INPUTS:
        print(f"  {name:<12} {bands}")
    print("excluded (Table S1 target-only sources, not used at inference):")
    print("  " + "; ".join(TARGET_ONLY))
    print("output: 64-D embedding on unit sphere S63, 10 m pixel, one embedding per one-year period")

    _style()
    fig, ax = plt.subplots(figsize=(10, 5.6))
    ax.set_xlim(0, 1)
    ax.set_ylim(0, 1)
    ax.axis("off")

    # title inside the plot, title case, no subtitle
    ax.text(0.5, 0.965, "What Goes Into an AlphaEarth Embedding", ha="center", va="top",
            fontsize=23, fontweight="bold")

    # geometry: input boxes on the left, model in the middle, output column on the right
    bx, bw, bh = 0.03, 0.38, 0.15
    y_centers = [0.72, 0.505, 0.29]
    mx, mw, mh = 0.52, 0.17, 0.32
    ox, ow, oy0, oy1 = 0.75, 0.045, 0.35, 0.67

    # column headers
    ax.text(bx + bw / 2, 0.86, "Inputs (at inference)", ha="center", va="center", fontsize=15, color="0.3")
    ax.text(mx + mw / 2, 0.86, "Model", ha="center", va="center", fontsize=15, color="0.3")
    ax.text(ox + ow / 2, 0.86, "Output", ha="center", va="center", fontsize=15, color="0.3")

    # input boxes, arrows fan into the left edge of the model at matched heights so they miss the text
    entry_y = [0.60, 0.505, 0.41]
    for (name, bands, color), yc, ey in zip(INPUTS, y_centers, entry_y):
        _box(ax, bx, yc - bh / 2, bw, bh, edge=color)
        ax.text(bx + 0.018, yc + 0.028, name, ha="left", va="center", fontsize=17,
                fontweight="bold", color=color)
        ax.text(bx + 0.018, yc - 0.032, bands, ha="left", va="center", fontsize=14, color="0.15")
        _arrow(ax, bx + bw, yc, mx, ey)

    # model box
    _box(ax, mx, 0.505 - mh / 2, mw, mh, edge="0.2", lw=2.4, face="#f2f2f2")
    ax.text(mx + mw / 2, 0.505, "AlphaEarth\nFoundations\nmodel", ha="center", va="center",
            fontsize=18, fontweight="bold", color="0.1")
    _arrow(ax, mx + mw, 0.505, ox, (oy0 + oy1) / 2)

    # output: a tall vector column subdivided to suggest components, with a 64 dimension marker
    _box(ax, ox, oy0, ow, oy1 - oy0, edge="#7B3294", lw=2.2, face="#f3eef6")
    n_ticks = 12
    for k in range(1, n_ticks):
        yy = oy0 + (oy1 - oy0) * k / n_ticks
        ax.plot([ox, ox + ow], [yy, yy], color="#7B3294", lw=0.5, alpha=0.5, zorder=4)
    ax.annotate("", xy=(ox + ow + 0.02, oy1), xytext=(ox + ow + 0.02, oy0),
                arrowprops=dict(arrowstyle="<->", color="0.3", lw=1.4))
    ax.text(ox + ow + 0.035, (oy0 + oy1) / 2, "64\ndims", ha="left", va="center", fontsize=15,
            color="0.2")
    ax.text(ox + ow / 2, oy0 - 0.03, "Embedding vector\nper 10 m pixel", ha="center", va="top",
            fontsize=15, color="0.1")

    # the annual-cadence annotation that motivates the two-date configurations next slide,
    # placed as a takeaway band across the open bottom, clear of the other elements
    ax.add_patch(FancyBboxPatch((0.19, 0.03), 0.78, 0.15,
                                boxstyle="round,pad=0.008,rounding_size=0.02",
                                linewidth=1.6, edgecolor="0.45", facecolor="white", zorder=3))
    ax.text(0.58, 0.105,
            "One embedding covers one full year, so comparing two dates\n"
            "needs two embeddings (the two-date configurations, next slide).",
            ha="center", va="center", fontsize=15, color="0.1")

    os.makedirs(OUT, exist_ok=True)
    fig.savefig(os.path.join(OUT, "pres_03_aef_schematic.png"), dpi=300, bbox_inches="tight")
    plt.close(fig)
    print("wrote pres_03_aef_schematic.png")


if __name__ == "__main__":
    main()
