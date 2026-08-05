#!/usr/bin/env python3
"""temporal_context.py: defense-slide panel — simplified version of the AEF paper's Figure 1B.

A time axis with three sensor rows of irregular observation ticks; a light "support period" band
(imagery the model reads) whose in-band observations converge into one embedding; and a separate copper
"valid period" bar (the interval the embedding describes) that only partially overlaps the support band.
No specific month offset, no dimensionality, no user-chosen window (all fixed model properties).
Flat style matching presentation/assets/gfm_figure_option2_band_stack.png. Transparent, ~5.5 x 4.5 in.
Output: presentation/figures/temporal_context.png
"""

import os

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import FancyArrowPatch, FancyBboxPatch, Rectangle

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
OUT = os.path.join(ROOT, "presentation", "figures")

TEXT, MUTED, BORDER, PANEL, COPPER = "#22282B", "#6B7378", "#C9CED2", "#F2F3F4", "#C1662F"
BAND = "#ECEEF0"
ARROW = "#9AA1A6"
plt.rcParams.update({"font.family": "sans-serif",
                     "font.sans-serif": ["Helvetica", "Arial", "DejaVu Sans"]})
FS_HEADER, FS_BODY, FS_MUTED, FS_SMALL = 17, 13.5, 12.5, 11.5

FIG_W, FIG_H = 5.5, 4.5
AX0, AX1 = 1.55, 5.30                            # time-axis x extent (leaves room for row labels)


def X(t):
    """Map a 'time' coordinate (0.75..5.15) to the panel's x, so it sits right of the labels."""
    return AX0 + (t - 0.75) * (AX1 - AX0) / (5.15 - 0.75)


AXIS_Y = 2.5
ROWS = [("Sentinel-2", 3.5, [0.95, 1.25, 1.62, 2.05, 2.5, 2.72, 3.05, 3.35, 3.9, 4.25, 4.8]),
        ("Sentinel-1", 3.16, [1.05, 1.5, 1.9, 2.2, 2.75, 3.1, 3.5, 4.0, 4.55, 4.9]),
        ("Landsat", 2.82, [0.9, 1.35, 1.8, 2.35, 2.9, 3.4, 3.85, 4.4, 4.95])]
YEARS = [(1.1, "2019"), (2.4, "2020"), (3.7, "2021"), (5.0, "2022")]
BAND_T = (1.7, 3.4)
VALID_T = (2.8, 4.4)
EMB_T, EMB_Y = 1.95, 1.32
BAND_TOP = 3.68


def main():
    fig = plt.figure(figsize=(FIG_W, FIG_H))
    ax = fig.add_axes([0, 0, 1, 1])
    ax.set_xlim(0, FIG_W)
    ax.set_ylim(0, FIG_H)
    ax.axis("off")

    ax.text(FIG_W / 2, 4.34, "Temporal context", ha="center", va="center", fontsize=FS_HEADER,
            fontweight="bold", color=TEXT)

    # support-period band (behind everything)
    bl, br = X(BAND_T[0]), X(BAND_T[1])
    ax.add_patch(Rectangle((bl, AXIS_Y), br - bl, BAND_TOP - AXIS_Y, facecolor=BAND,
                           edgecolor=BORDER, linewidth=0.8, zorder=0))
    bcx = (bl + br) / 2
    ax.text(bcx, 3.92, "support period", ha="center", va="bottom", fontsize=FS_BODY, color=TEXT)
    ax.text(bcx, 3.77, "imagery the model reads", ha="center", va="bottom", fontsize=FS_SMALL,
            color=MUTED)

    # sensor rows of irregular observation ticks
    for name, y, ticks in ROWS:
        ax.text(1.42, y, name, ha="right", va="center", fontsize=FS_SMALL, color=TEXT)
        for tx in ticks:
            ax.plot([X(tx), X(tx)], [y - 0.09, y + 0.09], color=TEXT, lw=1.1, zorder=2)

    # time axis; year labels sit above the line so the area below stays clear for the arrows
    ax.plot([X(0.75), X(5.15)], [AXIS_Y, AXIS_Y], color=TEXT, lw=1.3, zorder=2)
    for t, lab in YEARS:
        ax.plot([X(t), X(t)], [AXIS_Y, AXIS_Y + 0.05], color=TEXT, lw=1.1, zorder=2)
        ax.text(X(t), AXIS_Y + 0.07, lab, ha="center", va="bottom", fontsize=FS_SMALL, color=MUTED)

    # in-band observations converge into one embedding below the axis
    ex = X(EMB_T)
    for tt, ry in [(2.05, 3.5), (3.05, 3.5), (2.2, 3.16), (3.1, 3.16), (2.35, 2.82), (2.9, 2.82)]:
        ax.add_patch(FancyArrowPatch((X(tt), ry - 0.1), (ex, EMB_Y + 0.19), arrowstyle="-|>",
                                     mutation_scale=6, color=ARROW, lw=0.8, shrinkA=1, shrinkB=4,
                                     zorder=1))
    ax.add_patch(FancyBboxPatch((ex - 0.17, EMB_Y - 0.17), 0.34, 0.34,
                                boxstyle="round,pad=0.01,rounding_size=0.05", facecolor=PANEL,
                                edgecolor=BORDER, linewidth=1.4, zorder=3))
    ax.text(ex, EMB_Y - 0.32, "embedding", ha="center", va="top", fontsize=FS_SMALL, color=MUTED)

    # valid-period copper bar, offset so it only partially overlaps the support band
    vl, vr = X(VALID_T[0]), X(VALID_T[1])
    ax.add_patch(FancyBboxPatch((vl, 2.0), vr - vl, 0.16, boxstyle="round,pad=0.005,rounding_size=0.04",
                                facecolor=COPPER, edgecolor="none", zorder=3))
    vcx = (vl + vr) / 2
    ax.text(vcx, 1.83, "valid period", ha="center", va="top", fontsize=FS_BODY, color=COPPER,
            fontweight="bold")
    ax.text(vcx, 1.66, "the interval the embedding describes", ha="center", va="top",
            fontsize=FS_SMALL, color=MUTED)

    ax.text(FIG_W / 2, 0.4, "The valid period need not sit inside the support period.",
            ha="center", va="center", fontsize=FS_BODY, color=MUTED)

    os.makedirs(OUT, exist_ok=True)
    fig.savefig(os.path.join(OUT, "temporal_context.png"), dpi=300, transparent=True)
    plt.close(fig)
    print("wrote temporal_context.png")


if __name__ == "__main__":
    main()
