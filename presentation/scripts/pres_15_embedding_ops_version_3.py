#!/usr/bin/env python3
"""pres_15_embedding_ops_version_3: symbolic version of the embedding-ops figure.

Similar to pres_15_embedding_ops, but the two embeddings (2018, 2020) are drawn as overlapping squares
(a stack of layers), and the two operations are shown symbolically:
  Delta        a subtraction between the two embeddings   (square - square)
  Dot product  a single dot                                (the dot-product operator)

Geometry: data units == inches; the axes fills the figure (set_position([0,0,1,1])) so point fonts and
data-unit shapes share one scale and text never overflows (see CLAUDE.md).
Output (PNG only): presentation/figures/pres_15_embedding_ops_version_3.png
"""

import os

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import Circle, FancyArrowPatch, FancyBboxPatch, Rectangle

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
OUT = os.path.join(ROOT, "presentation", "figures")

ARROW = "#333333"
EMB_FILL, EMB_EDGE = "#cfe3f2", "#0072B2"
DARK = "#1a1a1a"

FIG_W, FIG_H = 12.0, 5.2
LABEL_FS, BODY_FS, SUB_FS = 20, 14, 12

# geometry (data units == inches)
MID, DELTA_CY, DOT_CY = 2.6, 3.7, 1.55
IN_CX = [1.6, 3.25]                      # centers of the 2018 / 2020 stacks
S_IN, N_IN, OFF_IN = 0.74, 4, 0.15       # input stack: square side, count, per-layer offset
S_SM, N_SM, OFF_SM = 0.44, 3, 0.11       # small stacks used in the delta subtraction
FORK_X = 4.55
SYM_CX = 6.15                            # x-center of the delta glyph and the dot
DOT_R = 0.27
ANN_X = 7.55


def _ostack(ax, cx, cy, n, s, off, fill=EMB_FILL, edge=EMB_EDGE, lw=1.6):
    """Overlapping squares offset up-right, so they read as a stack of layers. Returns the bbox side."""
    bbox = s + (n - 1) * off
    bl = (cx - bbox / 2, cy - bbox / 2)                 # front square bottom-left
    for i in range(n - 1, -1, -1):                      # back to front, front on top
        ax.add_patch(Rectangle((bl[0] + i * off, bl[1] + i * off), s, s, facecolor=fill,
                               edgecolor=edge, linewidth=lw, zorder=3 + (n - 1 - i)))
    return bbox


def _line(ax, xs, ys):
    ax.plot(xs, ys, color=ARROW, lw=2.6, zorder=2, solid_capstyle="round", solid_joinstyle="round")


def _arrow(ax, p0, p1):
    ax.add_patch(FancyArrowPatch(p0, p1, arrowstyle="-|>", mutation_scale=20, color=ARROW,
                                 linewidth=2.6, shrinkA=0, shrinkB=2, zorder=2))


def _oplabel(ax, cx, cy, name, sub):
    ax.text(cx, cy, name, ha="center", va="top", fontsize=LABEL_FS, fontweight="bold", color=DARK,
            zorder=6)
    ax.text(cx, cy - 0.32, sub, ha="center", va="top", fontsize=SUB_FS, color="0.4", style="italic",
            zorder=6)


def main():
    fig, ax = plt.subplots(figsize=(FIG_W, FIG_H))
    ax.set_xlim(0, FIG_W)
    ax.set_ylim(0, FIG_H)
    ax.axis("off")
    ax.set_position([0, 0, 1, 1])

    # group box around the two embeddings
    stack_bbox = S_IN + (N_IN - 1) * OFF_IN
    box_l = IN_CX[0] - stack_bbox / 2 - 0.22
    box_r = IN_CX[1] + stack_bbox / 2 + 0.22
    box_b, box_t = MID - stack_bbox / 2 - 0.22, MID + stack_bbox / 2 + 0.22
    ax.add_patch(FancyBboxPatch((box_l, box_b), box_r - box_l, box_t - box_b,
                                boxstyle="round,pad=0.02,rounding_size=0.08", facecolor="#f4f7fb",
                                edgecolor="#b6c5d4", linewidth=1.4, zorder=1))

    # input embeddings as overlapping stacks
    for cx, yr in zip(IN_CX, ("2018", "2020")):
        _ostack(ax, cx, MID, N_IN, S_IN, OFF_IN)
        ax.text(cx, box_t + 0.12, yr, ha="center", va="bottom", fontsize=LABEL_FS, fontweight="bold",
                color=DARK, zorder=6)
    ax.text((box_l + box_r) / 2, box_t + 0.5, "AlphaEarth Embeddings", ha="center", va="bottom",
            fontsize=16, fontweight="bold", color=DARK, zorder=6)

    # fork off the group box
    _line(ax, [box_r, FORK_X], [MID, MID])
    _line(ax, [FORK_X, FORK_X], [DOT_CY, DELTA_CY])

    # delta branch: a subtraction between two embeddings (small stack - small stack)
    sm_bbox = S_SM + (N_SM - 1) * OFF_SM
    dxoff = sm_bbox / 2 + 0.34                          # half-spacing between each small stack and the sign
    glyph_l = SYM_CX - dxoff - sm_bbox / 2
    _arrow(ax, (FORK_X, DELTA_CY), (glyph_l, DELTA_CY))
    _ostack(ax, SYM_CX - dxoff, DELTA_CY, N_SM, S_SM, OFF_SM)
    _ostack(ax, SYM_CX + dxoff, DELTA_CY, N_SM, S_SM, OFF_SM)
    ax.text(SYM_CX, DELTA_CY, "−", ha="center", va="center", fontsize=40, fontweight="bold",
            color=DARK, zorder=6)
    _oplabel(ax, SYM_CX, DELTA_CY - sm_bbox / 2 - 0.22, "Delta", "elementwise difference")

    # dot-product branch: a single dot
    _arrow(ax, (FORK_X, DOT_CY), (SYM_CX - DOT_R, DOT_CY))
    ax.add_patch(Circle((SYM_CX, DOT_CY), DOT_R, facecolor=DARK, edgecolor="none", zorder=4))
    _oplabel(ax, SYM_CX, DOT_CY - DOT_R - 0.16, "Dot product", "similarity between the years")

    # annotations
    ax.text(ANN_X, DELTA_CY, "which dimensions changed,\nand in which direction", ha="left",
            va="center", fontsize=BODY_FS, color="0.2", linespacing=1.4, zorder=6)
    ax.text(ANN_X, DOT_CY + 0.12, "how much changed overall", ha="left", va="bottom",
            fontsize=BODY_FS, color="0.2", zorder=6)
    ax.text(ANN_X, DOT_CY - 0.12, "cosine similarity (−1 to 1)", ha="left", va="top",
            fontsize=SUB_FS, color="0.45", style="italic", zorder=6)

    os.makedirs(OUT, exist_ok=True)
    fig.savefig(os.path.join(OUT, "pres_15_embedding_ops_version_3.png"), dpi=300)
    plt.close(fig)
    print("wrote pres_15_embedding_ops_version_3.png")


if __name__ == "__main__":
    main()
