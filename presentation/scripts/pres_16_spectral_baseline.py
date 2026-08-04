#!/usr/bin/env python3
"""pres_16_spectral_baseline: how the spectral composite baseline is built.

Linear pipeline: three sensors (each a distinct color, showing the bands it contributes by type) feed
one spectral composite that a Random Forest classifies into a land-cover map.
Bands per sensor (user-supplied, from the AEF input table):
  Sentinel-2 L1C:   Blue, Green, Red, NIR, SWIR                 (B2, B3, B4, B8, B11)
  Landsat 8/9 L1C:  Blue, Green, Red, NIR, SWIR, Pan, Thermal   (B2, B3, B4, B5, B6, B8, B10)
  Sentinel-1 GRD:   VV, VH, HH, HV, angle                        (C-band SAR)
Raw bands plus derived indices total 50 (repo-stated). Growing-season compositing window (April to
October) is user-supplied; it is not recorded in the repo.

Geometry: data units == inches, because main() pins the axes to fill the figure (set_position([0,0,1,1])),
so point-sized fonts and data-unit boxes share one scale and text never overflows a box (see CLAUDE.md).
Output (PNG only for the Google Slides deck): presentation/figures/pres_16_spectral_baseline.png
"""

import os

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
from matplotlib.patches import FancyArrowPatch, FancyBboxPatch, Rectangle

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
OUT = os.path.join(ROOT, "presentation", "figures")

ARROW = "#333333"
SPEC_FILL, SPEC_EDGE = "#f5e6c8", "#c4941f"    # spectral composite: amber
RF_FILL, RF_EDGE = "#dcefe1", "#3f8f66"        # classifier: green
# one colorblind-safe color per sensor (Okabe-Ito), distinct from the amber composite and green RF
SENSORS = [
    ("Sentinel-2", ["Blue, Green, Red,", "NIR, SWIR"], "#d6e6f4", "#0072B2"),
    ("Landsat 8/9", ["Blue, Green, Red, NIR,", "SWIR, Pan, Thermal"], "#f7ddcf", "#D55E00"),
    ("Sentinel-1", ["VV, VH, HH, HV, angle"], "#e7ddf2", "#7A5DA8"),
]
WINDOW_LINE = "growing season: April to October"   # compositing window (user-supplied)
# illustrative land-cover classes for the classified-map icon (not real values); 10x10, fixed pattern
LC_COLORS = ["#2e7d32", "#e6c229", "#2f6fb0", "#8a8f98", "#8bc34a", "#4db6ac"]
LC_PATTERN = np.random.default_rng(5).integers(0, len(LC_COLORS), size=(10, 10)).tolist()

FIG_W, FIG_H = 12.0, 5.0
LABEL_FS, SUB_FS = 20, 13
LH = 0.32

# geometry (data units == inches; axes fills figure)
SX, SW = 0.35, 2.4
BUS_X = 2.9
SPX, SPW = 3.26, 3.4        # even ~0.51 in gaps: sensors|composite|RF|map
RFX, RFW = 7.17, 2.7
MAP_CX, MAP_SZ = 11.0, 1.25             # 10x10 grid, 0.125 in cells
MID = 2.5
GAP = 0.2


def _bh(n_lines):
    return n_lines * LH + 0.36


def _box(ax, x, cy, w, h, fill, edge, title_lines, sub_lines):
    ax.add_patch(FancyBboxPatch((x, cy - h / 2), w, h,
                                boxstyle="round,pad=0.015,rounding_size=0.07", facecolor=fill,
                                edgecolor=edge, linewidth=2.4, zorder=3))
    cx = x + w / 2
    lines = [(t, True) for t in title_lines] + [(s, False) for s in sub_lines]
    y_top = cy + (len(lines) - 1) * LH / 2
    for i, (text, is_title) in enumerate(lines):
        ax.text(cx, y_top - i * LH, text, ha="center", va="center",
                fontsize=LABEL_FS if is_title else SUB_FS,
                fontweight="bold" if is_title else "normal",
                color="#1a1a1a" if is_title else "0.25", zorder=4)


def _line(ax, xs, ys, lw=2.6):
    ax.plot(xs, ys, color=ARROW, lw=lw, zorder=2, solid_capstyle="round", solid_joinstyle="round")


def _arrow(ax, p0, p1, lw=2.6):
    ax.add_patch(FancyArrowPatch(p0, p1, arrowstyle="-|>", mutation_scale=18, color=ARROW,
                                 linewidth=lw, zorder=2, shrinkA=0, shrinkB=1))


def _map(ax, cx, cy, size):
    """Classified land-cover map icon: a grid of illustrative class colors, plus a caption."""
    n = len(LC_PATTERN)
    cs = size / n
    x0, y0 = cx - size / 2, cy - size / 2
    for i in range(n):
        for j in range(n):
            ax.add_patch(Rectangle((x0 + j * cs, y0 + (n - 1 - i) * cs), cs, cs,
                                   facecolor=LC_COLORS[LC_PATTERN[i][j]], edgecolor="none",
                                   zorder=3))
    ax.add_patch(Rectangle((x0, y0), size, size, fill=False, edgecolor="#333333", linewidth=1.8,
                           zorder=4))
    ax.text(cx, y0 - 0.16, "classified\nland-cover map", ha="center", va="top", fontsize=SUB_FS,
            fontweight="bold", color="#1a1a1a", linespacing=1.3)


def _fit_check(fig, entries):
    fig.canvas.draw()
    r = fig.canvas.get_renderer()
    over = []
    for text, w, fs, bold in entries:
        t = fig.text(0, 0, text, fontsize=fs, fontweight="bold" if bold else "normal")
        tw = t.get_window_extent(r).width / fig.dpi
        t.remove()
        if tw > w - 0.3:
            over.append((text, round(tw, 2), round(w - 0.3, 2)))
    return over


def main():
    fig, ax = plt.subplots(figsize=(FIG_W, FIG_H))
    ax.set_xlim(0, FIG_W)
    ax.set_ylim(0, FIG_H)
    ax.axis("off")
    ax.set_position([0, 0, 1, 1])                 # axes fills the figure: 1 data unit == 1 inch

    spec_sub = ["50 bands (with indices)", WINDOW_LINE]
    checks = [("Spectral", SPW, LABEL_FS, True), ("composites", SPW, LABEL_FS, True),
              ("Random Forest", RFW, LABEL_FS, True)]
    checks += [(s, SPW, SUB_FS, False) for s in spec_sub]
    for name, bands, _f, _e in SENSORS:
        checks += [(name, SW, LABEL_FS, True)] + [(b, SW, SUB_FS, False) for b in bands]
    over = _fit_check(fig, checks)
    if over:
        print("WARN line wider than box interior:", over)

    # sensor column, one color per sensor, stacked and centered on MID with a shared bus
    heights = [_bh(1 + len(bands)) for _, bands, _f, _e in SENSORS]
    total = sum(heights) + GAP * (len(heights) - 1)
    y = MID + total / 2
    centers = []
    for h in heights:
        centers.append(y - h / 2)
        y -= h + GAP
    for (name, bands, fill, edge), cy, h in zip(SENSORS, centers, heights):
        _box(ax, SX, cy, SW, h, fill, edge, [name], bands)
        _line(ax, [SX + SW, BUS_X], [cy, cy])
    _line(ax, [BUS_X, BUS_X], [centers[-1], centers[0]])
    _arrow(ax, (BUS_X, MID), (SPX, MID))

    # spectral composite -> random forest -> classified land-cover map
    _box(ax, SPX, MID, SPW, _bh(4), SPEC_FILL, SPEC_EDGE, ["Spectral", "composites"], spec_sub)
    _arrow(ax, (SPX + SPW, MID), (RFX, MID))
    _box(ax, RFX, MID, RFW, _bh(2), RF_FILL, RF_EDGE, ["Random Forest"], ["300 trees"])
    _arrow(ax, (RFX + RFW, MID), (MAP_CX - MAP_SZ / 2, MID))
    _map(ax, MAP_CX, MID, MAP_SZ)

    os.makedirs(OUT, exist_ok=True)
    fig.savefig(f"{OUT}/pres_16_spectral_baseline.png", dpi=300)
    plt.close(fig)
    print("bands shown by type per sensor; 50 bands total (raw + indices, repo-stated)")
    print(f"growing-season window (user-supplied): {WINDOW_LINE!r}")
    print("wrote pres_16_spectral_baseline.png")


if __name__ == "__main__":
    main()
