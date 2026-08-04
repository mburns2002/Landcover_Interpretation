#!/usr/bin/env python3
"""pres_16_spectral_baseline: how the spectral composite baseline is built.

Linear pipeline: three sensors, each with the bands it contributes, feed one spectral composite that a
Random Forest classifies. Bands per sensor (user-supplied, from the AEF input table):
  Sentinel-2 L1C:   B2, B3, B4, B8, B11   (Blue, Green, Red, NIR, SWIR)
  Landsat 8/9 L1C:  B2, B3, B4, B5, B6, B8, B10   (Blue, Green, Red, NIR, SWIR, Pan, Thermal)
  Sentinel-1 GRD:   VV, VH, HH, HV, angle
Raw bands plus derived indices total 50 (repo-stated count). The growing-season compositing window
(April to October) is user-supplied; it is not recorded in the repo.

Geometry: data units == inches, because main() pins the axes to fill the figure (set_position([0,0,1,1])),
so point-sized fonts and data-unit boxes share one scale and text never overflows a box (see CLAUDE.md).
Output (PNG only for the Google Slides deck): presentation/figures/pres_16_spectral_baseline.png
"""

import os

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import FancyArrowPatch, FancyBboxPatch

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
OUT = os.path.join(ROOT, "presentation", "figures")

SENS_FILL, SENS_EDGE = "#e7edf3", "#5b7085"    # sensors: light steel
SPEC_FILL, SPEC_EDGE = "#f5e6c8", "#c4941f"    # spectral composite: amber
RF_FILL, RF_EDGE = "#dcefe1", "#3f8f66"        # classifier: green
ARROW = "#333333"

FIG_W, FIG_H = 12.0, 5.0
LABEL_FS, SUB_FS = 20, 14
LH = 0.32
WINDOW_LINE = "growing season: April to October"   # compositing window (user-supplied)

SENSORS = [("Sentinel-2", "B2, B3, B4, B8, B11"),
           ("Landsat 8/9", "B2, B3, B4, B5, B6, B8, B10"),
           ("Sentinel-1", "VV, VH, HH, HV, angle")]

# geometry (data units == inches; axes fills figure)
SX, SW, SENS_BH, SGAP = 0.4, 3.15, 1.0, 0.22
BUS_X = 3.75
SPX, SPW, SP_BH = 4.45, 3.5, 1.7
RFX, RFW, RF_BH = 8.55, 2.8, 1.06
MID = 2.5
SENSOR_CY = [MID + (SENS_BH + SGAP), MID, MID - (SENS_BH + SGAP)]


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


def _fit_check(fig, entries):
    """Warn if any line is wider than its box interior (text-must-fit-in-boxes rule)."""
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

    checks = [("Spectral", SPW, LABEL_FS, True), ("composites", SPW, LABEL_FS, True),
              ("Random Forest", RFW, LABEL_FS, True), ("50 bands (with indices)", SPW, SUB_FS, False),
              (WINDOW_LINE, SPW, SUB_FS, False)]
    for name, codes in SENSORS:
        checks += [(name, SW, LABEL_FS, True), (codes, SW, SUB_FS, False)]
    over = _fit_check(fig, checks)
    if over:
        print("WARN line wider than box interior:", over)

    # sensor column on a shared bus, each box carrying its bands
    for (name, codes), cy in zip(SENSORS, SENSOR_CY):
        _box(ax, SX, cy, SW, SENS_BH, SENS_FILL, SENS_EDGE, [name], [codes])
        _line(ax, [SX + SW, BUS_X], [cy, cy])
    _line(ax, [BUS_X, BUS_X], [SENSOR_CY[2], SENSOR_CY[0]])
    _arrow(ax, (BUS_X, MID), (SPX, MID))

    # spectral composite -> random forest
    _box(ax, SPX, MID, SPW, SP_BH, SPEC_FILL, SPEC_EDGE, ["Spectral", "composites"],
         ["50 bands (with indices)", WINDOW_LINE])
    _arrow(ax, (SPX + SPW, MID), (RFX, MID))
    _box(ax, RFX, MID, RFW, RF_BH, RF_FILL, RF_EDGE, ["Random Forest"], ["300 trees"])

    os.makedirs(OUT, exist_ok=True)
    fig.savefig(f"{OUT}/pres_16_spectral_baseline.png", dpi=300)
    plt.close(fig)
    print("bands per sensor set from user table; 50 bands total (raw + indices, repo-stated)")
    print(f"growing-season window (user-supplied): {WINDOW_LINE!r}")
    print("wrote pres_16_spectral_baseline.png")


if __name__ == "__main__":
    main()
