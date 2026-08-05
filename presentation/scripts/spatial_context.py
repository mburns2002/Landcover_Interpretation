#!/usr/bin/env python3
"""spatial_context.py: defense-slide panel — each embedding carries neighborhood context.

A 1.28 km x 1.28 km window (128 x 128 pixels at 10 m); one 10 m pixel highlighted in copper near the
centre and magnified via a leader-line callout (too small to draw to scale). Flat style matching
presentation/assets/gfm_figure_option2_band_stack.png. Transparent background, ~5.5 x 4.5 in.
Output: presentation/figures/spatial_context.png
"""

import os

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

import slide_font
from matplotlib.patches import FancyArrowPatch, FancyBboxPatch, Rectangle

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
OUT = os.path.join(ROOT, "presentation", "figures")

TEXT, MUTED, BORDER, PANEL, COPPER = "#22282B", "#6B7378", "#C9CED2", "#F2F3F4", "#C1662F"
ARROW = "#AEB4B9"
plt.rcParams.update({"font.family": "sans-serif",
                     "font.sans-serif": ["Helvetica", "Arial", "DejaVu Sans"]})
slide_font.use_spectral()
FS_HEADER, FS_BODY, FS_MUTED, FS_SMALL = 17, 13.5, 12.5, 11.5

FIG_W, FIG_H = 5.5, 4.5


def main():
    fig = plt.figure(figsize=(FIG_W, FIG_H))
    ax = fig.add_axes([0, 0, 1, 1])
    ax.set_xlim(0, FIG_W)
    ax.set_ylim(0, FIG_H)
    ax.axis("off")

    ax.text(FIG_W / 2, 4.2, "Spatial context", ha="center", va="center", fontsize=FS_HEADER,
            fontweight="bold", color=TEXT)

    # 1.28 km window
    wx, wy, ws = 0.45, 1.1, 2.5
    ax.add_patch(Rectangle((wx, wy), ws, ws, facecolor=PANEL, edgecolor=BORDER, linewidth=1.5))
    ty = wy + ws + 0.12
    ax.plot([wx, wx + ws], [ty, ty], color=MUTED, lw=1.0)
    for xx in (wx, wx + ws):
        ax.plot([xx, xx], [ty - 0.05, ty + 0.05], color=MUTED, lw=1.0)
    ax.text(wx + ws / 2, ty + 0.1, "1.28 km", ha="center", va="bottom", fontsize=FS_SMALL, color=MUTED)

    # one 10 m pixel (near centre, offset), too small to read at true scale
    px, py, ps = wx + ws * 0.56, wy + ws * 0.58, 0.06
    ax.add_patch(Rectangle((px - ps / 2, py - ps / 2), ps, ps, facecolor="none", edgecolor=COPPER,
                           linewidth=1.4, zorder=6))

    # the whole neighborhood informs that pixel
    for sx, sy in [(0.9, 3.25), (2.5, 3.3), (0.95, 1.55), (2.35, 1.55), (1.5, 3.4), (1.05, 2.45)]:
        ax.add_patch(FancyArrowPatch((sx, sy), (px, py), arrowstyle="-|>", mutation_scale=7,
                                     color=ARROW, lw=0.9, shrinkA=2, shrinkB=7, zorder=3))

    # magnified callout of the single pixel
    cx, cy, cs = 3.6, 1.85, 1.1
    ax.plot([px, cx], [py, cy + cs], color=COPPER, lw=0.9, zorder=4)
    ax.plot([px, cx], [py, cy], color=COPPER, lw=0.9, zorder=4)
    ax.add_patch(Rectangle((cx, cy), cs, cs, facecolor="#F6E9DF", edgecolor=COPPER, linewidth=2.4,
                           zorder=5))
    ax.text(cx + cs / 2, cy - 0.16, "one 10 m pixel", ha="center", va="top", fontsize=FS_BODY,
            color=TEXT)

    ax.text(FIG_W / 2, 0.42, "Every pixel's vector is informed by its whole neighborhood.",
            ha="center", va="center", fontsize=FS_BODY, color=MUTED)

    os.makedirs(OUT, exist_ok=True)
    fig.savefig(os.path.join(OUT, "spatial_context.png"), dpi=300, transparent=True)
    plt.close(fig)
    print("wrote spatial_context.png")


if __name__ == "__main__":
    main()
