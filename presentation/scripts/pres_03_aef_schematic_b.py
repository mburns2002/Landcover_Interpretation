#!/usr/bin/env python3
"""pres_03_aef_schematic_b: what goes into an AlphaEarth embedding (restyled).

New version of pres_03_aef_schematic_a in the flat pres_16 style: shaded per-sensor input boxes
(Inputs at inference), a simplified "training targets" step (Climate, LiDAR, Land cover, Text; used in
training only), the AlphaEarth Foundations model, and the output embedding drawn as an overlapping
stack of layers (pres_15 v3 style) instead of a labelled column. No title, no Model/Output headers, no
bottom caption.

Geometry: data units == inches (axes fills the figure), so fonts and boxes share one scale (CLAUDE.md).
Output (PNG only): presentation/figures/pres_03_aef_schematic_b.png
"""

import os

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import FancyArrowPatch, FancyBboxPatch, Rectangle

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
OUT = os.path.join(ROOT, "presentation", "figures")

TEXT, MUTED, ARROW = "#22282B", "#6B7378", "#333333"
MODEL_FILL, MODEL_EDGE = "#F2F3F4", "#333333"
TGT_FILL, TGT_EDGE = "#F5F6F7", "#9AA1A6"
EMB_FILL, EMB_EDGE = "#d9ecdb", "#3f8f66"        # green output, distinct from Sentinel-2 blue
EMB_S, EMB_OFF, EMB_N = 1.0, 0.2, 4
EMB_BBOX = EMB_S + (EMB_N - 1) * EMB_OFF
plt.rcParams.update({"font.family": "sans-serif",
                     "font.sans-serif": ["Helvetica", "Arial", "DejaVu Sans"]})
FS_SECTION, FS_TITLE, FS_SUB, FS_MODEL = 17, 17, 13, 18
FS_TGT, FS_TGT_EX, FS_EMB = 14.5, 11.5, 13.5

FIG_W, FIG_H = 13.0, 7.0
SENSORS = [  # (title, sub, fill, edge, y_center)
    ("Sentinel-2", "Spectral:  B2, B3, B4, B8, B11", "#d6e6f4", "#0072B2", 5.6),
    ("Landsat 8/9", "Spectral + thermal:  B2–B6, B8, B10", "#f7ddcf", "#D55E00", 4.15),
    ("Sentinel-1", "C-band SAR:  VV, VH, HH, HV, angle", "#e7ddf2", "#7A5DA8", 2.7)]
SX, SW, SH = 0.35, 3.35, 1.25                    # input box x-left, width, height
TARGETS = [("Climate", "ERA5-Land"), ("LiDAR", "GEDI"), ("Land cover", "NLCD"), ("Text", "Wikipedia")]
MODEL_BOX = (5.75, 3.35, 2.55, 1.7)              # x, y, w, h
EMB_CX, EMB_CY = 9.75, 4.2


def _box(ax, x, y, w, h, fill, edge, title, sub, lw=2.2):
    ax.add_patch(FancyBboxPatch((x, y), w, h, boxstyle="round,pad=0.02,rounding_size=0.09",
                                facecolor=fill, edgecolor=edge, linewidth=lw, zorder=3))
    cx = x + w / 2
    ax.text(cx, y + h / 2 + 0.18, title, ha="center", va="center", fontsize=FS_TITLE,
            fontweight="bold", color=TEXT, zorder=4)
    ax.text(cx, y + h / 2 - 0.22, sub, ha="center", va="center", fontsize=FS_SUB, color=TEXT,
            zorder=4)


def _arrow(ax, p0, p1, dashed=False):
    ax.add_patch(FancyArrowPatch(p0, p1, arrowstyle="-|>", mutation_scale=18, color=ARROW,
                                 linewidth=2.2, shrinkA=2, shrinkB=3, zorder=2,
                                 linestyle="--" if dashed else "-"))


def _stack(ax, cx, cy):
    bl = (cx - EMB_BBOX / 2, cy - EMB_BBOX / 2)
    for i in range(EMB_N - 1, -1, -1):
        ax.add_patch(Rectangle((bl[0] + i * EMB_OFF, bl[1] + i * EMB_OFF), EMB_S, EMB_S,
                               facecolor=EMB_FILL, edgecolor=EMB_EDGE, linewidth=2.0,
                               zorder=3 + (EMB_N - 1 - i)))


def main():
    fig = plt.figure(figsize=(FIG_W, FIG_H))
    ax = fig.add_axes([0, 0, 1, 1])
    ax.set_xlim(0, FIG_W)
    ax.set_ylim(0, FIG_H)
    ax.axis("off")

    # inputs (at inference)
    ax.text(SX + SW / 2, 6.68, "Inputs (at inference)", ha="center", va="center", fontsize=FS_SECTION,
            fontweight="bold", color=TEXT)
    mx, my, mw, mh = MODEL_BOX
    for title, sub, fill, edge, cy in SENSORS:
        _box(ax, SX, cy - SH / 2, SW, SH, fill, edge, title, sub)
        _arrow(ax, (SX + SW, cy), (mx, my + mh * (0.5 + (cy - 4.15) * 0.16)))

    # model
    ax.add_patch(FancyBboxPatch((mx, my), mw, mh, boxstyle="round,pad=0.02,rounding_size=0.09",
                                facecolor=MODEL_FILL, edgecolor=MODEL_EDGE, linewidth=2.6, zorder=3))
    ax.text(mx + mw / 2, my + mh / 2, "AlphaEarth\nFoundations\nmodel", ha="center", va="center",
            fontsize=FS_MODEL, fontweight="bold", color=TEXT, linespacing=1.25, zorder=4)

    # output embedding as an overlapping stack of layers
    _arrow(ax, (mx + mw, my + mh / 2), (EMB_CX - EMB_BBOX / 2 - 0.05, EMB_CY))
    _stack(ax, EMB_CX, EMB_CY)
    ebot = EMB_CY - EMB_BBOX / 2
    ax.text(EMB_CX, ebot - 0.22, "64-D embedding", ha="center", va="top", fontsize=FS_EMB,
            fontweight="bold", color=TEXT)
    ax.text(EMB_CX, ebot - 0.5, "per 10 m pixel", ha="center", va="top", fontsize=FS_EMB, color=MUTED)

    # training targets: an additional step feeding the model
    tx, ty, tw, th = 4.55, 1.1, 4.35, 1.05
    ax.add_patch(FancyBboxPatch((tx, ty), tw, th, boxstyle="round,pad=0.02,rounding_size=0.08",
                                facecolor=TGT_FILL, edgecolor=TGT_EDGE, linewidth=1.8, linestyle="--",
                                zorder=1))
    ax.text(tx + tw / 2, ty + th - 0.28, "Training targets", ha="center", va="center",
            fontsize=FS_SECTION - 1, fontweight="bold", color=TEXT, zorder=4)
    cxs = [tx + tw * f for f in (0.13, 0.38, 0.63, 0.88)]
    for (cat, _ex), cxx in zip(TARGETS, cxs):
        ax.text(cxx, ty + 0.34, cat, ha="center", va="center", fontsize=FS_TGT, fontweight="bold",
                color=TEXT, zorder=4)
    _arrow(ax, (tx + tw / 2, ty + th), (mx + mw / 2, my), dashed=True)

    os.makedirs(OUT, exist_ok=True)
    fig.savefig(os.path.join(OUT, "pres_03_aef_schematic_b.png"), dpi=300)
    plt.close(fig)
    print("wrote pres_03_aef_schematic_b.png")


if __name__ == "__main__":
    main()
