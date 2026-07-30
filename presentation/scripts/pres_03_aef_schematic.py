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
from matplotlib.patches import FancyBboxPatch, FancyArrowPatch, Rectangle

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
OUT = os.path.join(ROOT, "presentation", "figures")

# inference inputs, from Brown et al. 2025 Table S1 (rows tagged "input, target").
# muted, colorblind-safe box colors (brown/teal from ColorBrewer BrBG); the top blue is kept
INPUTS = [
    ("Sentinel-2", "Optical: B2, B3, B4, B8, B11", "#0072B2"),
    ("Landsat 8/9", "Optical + thermal: B2-B6, B8, B10", "#8C5A2B"),
    ("Sentinel-1", "C-band SAR: VV, VH, HH, HV, angle", "#2C7A73"),
]
OUT_EDGE = "#5A5A5A"   # neutral grey for the output vector, muted rather than cartoonish
OUT_FILL = "#EDEDED"
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


def _vector_stack(ax, cx, cy):
    # stacked squares standing in for the 64-D embedding vector: three cells, a vertical
    # ellipsis, then two cells, so it reads as a long vector without drawing all 64 cells.
    # the axes span 10 x 5.6 in over 0..1, so square cells need a wider x than y extent.
    # one cell sits at cy so the feed arrow points straight at a square
    side = 0.30
    w, h = side / 10.0, side / 5.6
    s = 0.062
    offsets = [2, 1, 0, -2, -3]        # gap at -1 holds the ellipsis
    for off in offsets:
        yc = cy + off * s
        ax.add_patch(Rectangle((cx - w / 2, yc - h / 2), w, h, linewidth=1.6,
                               edgecolor=OUT_EDGE, facecolor=OUT_FILL, zorder=4))
    ey = cy - s
    for dy in (-0.016, 0.0, 0.016):
        ax.plot(cx, ey + dy, marker="o", ms=3, color=OUT_EDGE, zorder=4)
    top = cy + 2 * s + h / 2
    bot = cy - 3 * s - h / 2
    ax.annotate("", xy=(cx + w / 2 + 0.03, top), xytext=(cx + w / 2 + 0.03, bot),
                arrowprops=dict(arrowstyle="<->", color="0.3", lw=1.4))
    ax.text(cx + w / 2 + 0.05, cy, "64\ndims", ha="left", va="center", fontsize=15, color="0.2")
    return cx - w / 2, bot


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
    ax.text(0.5, 0.965, "What Goes Into an AlphaEarth Embedding?", ha="center", va="top",
            fontsize=23, fontweight="bold")

    # geometry: input boxes on the left, model in the middle, output vector on the right.
    # the model and output sit below the input mid-line so they read closer to the lower boxes
    bx, bw, bh = 0.03, 0.38, 0.15
    y_centers = [0.72, 0.505, 0.29]
    mx, mw, mh, mc = 0.52, 0.17, 0.32, 0.45
    ocx = 0.80

    # column headers
    ax.text(bx + bw / 2, 0.86, "Inputs (at inference)", ha="center", va="center", fontsize=15, color="0.3")
    ax.text(mx + mw / 2, 0.86, "Model", ha="center", va="center", fontsize=15, color="0.3")
    ax.text(ocx, 0.86, "Output", ha="center", va="center", fontsize=15, color="0.3")

    # input boxes, arrows fan into the left edge of the model at matched heights so they miss the text
    entry_y = [mc + 0.10, mc, mc - 0.10]
    for (name, bands, color), yc, ey in zip(INPUTS, y_centers, entry_y):
        _box(ax, bx, yc - bh / 2, bw, bh, edge=color)
        ax.text(bx + 0.018, yc + 0.028, name, ha="left", va="center", fontsize=17,
                fontweight="bold", color=color)
        ax.text(bx + 0.018, yc - 0.032, bands, ha="left", va="center", fontsize=14, color="0.15")
        _arrow(ax, bx + bw, yc, mx, ey)

    # model box
    _box(ax, mx, mc - mh / 2, mw, mh, edge="0.2", lw=2.4, face="#f2f2f2")
    ax.text(mx + mw / 2, mc, "AlphaEarth\nFoundations\nmodel", ha="center", va="center",
            fontsize=18, fontweight="bold", color="0.1")

    # output: stacked squares for the 64-D embedding vector
    left_edge, bot = _vector_stack(ax, ocx, mc)
    _arrow(ax, mx + mw, mc, left_edge - 0.012, mc)
    ax.text(ocx, bot - 0.03, "Embedding vector per 10 m pixel", ha="center", va="top",
            fontsize=15, color="0.1")

    # the annual-cadence annotation that motivates the two-date configurations next slide,
    # placed as a takeaway band across the open bottom, clear of the other elements
    ax.add_patch(FancyBboxPatch((0.19, 0.02), 0.78, 0.135,
                                boxstyle="round,pad=0.008,rounding_size=0.02",
                                linewidth=1.6, edgecolor="0.45", facecolor="white", zorder=3))
    ax.text(0.58, 0.088,
            "One embedding covers one full year, so comparing two dates\n"
            "needs two embeddings (the two-date configurations, next slide).",
            ha="center", va="center", fontsize=15, color="0.1")

    os.makedirs(OUT, exist_ok=True)
    fig.savefig(os.path.join(OUT, "pres_03_aef_schematic.png"), dpi=300, bbox_inches="tight")
    plt.close(fig)
    print("wrote pres_03_aef_schematic.png")


if __name__ == "__main__":
    main()
