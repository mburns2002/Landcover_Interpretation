#!/usr/bin/env python3
"""pres_15_embedding_ops: the two operations on a pair of AlphaEarth embeddings.

Teaching point is dimensionality. Each embedding is a stack of 64 band layers (A00..A63), drawn as
stacked squares with an ellipsis for the omitted middle bands, the standard "feature/channel stack"
glyph. Two operations branch right:
  Delta        elementwise difference   -> a 64-cell strip   (all 64 dimensions preserved)
  Dot product  similarity between years -> a single cell     (the pair collapses to one number)

The 64-cell delta strip and the single dot-product cell are drawn at the SAME cell scale, so the
64-vs-1 size difference is visible at a glance. The single cell is NOT resized to fill space.

Unit norm / cosine: confirmed from the AlphaEarth paper (presentation/assets/alphaearth.pdf, Fig 1E):
"A stack of 64 rasterized AEF layers forms an embedding field, and each individual vector maps to a
coordinate on the unit sphere S63." Each 64-D embedding is unit length, so the dot product of two
years is a cosine similarity in [-1, 1]; that range is labelled on the dot-product output.

Colors: the embedding band layers use a single flat channel tint (illustrative structure, not values);
the signed delta uses a colorblind-safe diverging map so direction reads as color. Neither is a real
embedding value.

Styling matches pres_03 / pres_11 (rounded FancyBboxPatch nodes, #333333 arrows, DejaVu font).
Output (PNG only for the Google Slides deck): presentation/figures/pres_15_embedding_ops.png
"""

import os

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
from matplotlib.cm import ScalarMappable
from matplotlib.colors import TwoSlopeNorm
from matplotlib.patches import FancyArrowPatch, FancyBboxPatch, Rectangle

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
OUT = os.path.join(ROOT, "presentation", "figures")

FIG_W, FIG_H = 12.0, 5.0
LABEL_FS, BODY_FS, SUB_FS = 20, 15, 12        # year/op labels 20; right annotations 15; node subs 12
ARROW = "#333333"
NODE_FILL, NODE_EDGE = "white", "#333333"
FRAME = "#333333"
EMB_FILL, EMB_EDGE = "#cfe3f2", "#0072B2"     # embedding-family blue (pres_11/pres_16)
NCELL = 64

# geometry (data units = inches; axes span 0..12 x 0..5)
SQ = 0.5                                       # embedding band-square side
ELL = 0.40                                     # ellipsis gap in the band stack
STACK_CX = [1.4, 2.9]                          # x-centers of the 2018 / 2020 stacks (well separated)
STACK_CY = 2.6
CW = 0.52                                      # delta-strip / dot-cell width
SH = 2.0                                       # delta-strip height (64 cells)
CH = SH / NCELL                                # single-cell height, shared by strip cells and dot cell
DELTA_CY, DOT_CY = 3.15, 1.30                  # upper (delta) and lower (dot) lane centers
NODE_CX, NODE_H = 5.3, 0.55
NODE_W = 2.0                                    # recomputed in main() to fit the widest label
FORK_X = 4.0
OUT_X = 8.3                                     # x-left of both outputs (same column: strip over cell)


def _stack(ax, cx, cy):
    """Draw an embedding as a stack of band squares: A00, A01, A02, ellipsis, A63."""
    top_labels = ["A00", "A01", "A02"]
    total = len(top_labels) * SQ + ELL + SQ
    y = cy + total / 2
    for lab in top_labels:
        ax.add_patch(Rectangle((cx - SQ / 2, y - SQ), SQ, SQ, facecolor=EMB_FILL,
                               edgecolor=EMB_EDGE, linewidth=1.6, zorder=3))
        ax.text(cx, y - SQ / 2, lab, ha="center", va="center", fontsize=12, color="#12405e", zorder=4)
        y -= SQ
    for k in (-1, 0, 1):                        # vertical ellipsis for the omitted bands
        ax.plot([cx], [y - ELL / 2 + k * 0.10], marker="o", ms=3.0, color="#3a6f92", zorder=4)
    y -= ELL
    ax.add_patch(Rectangle((cx - SQ / 2, y - SQ), SQ, SQ, facecolor=EMB_FILL, edgecolor=EMB_EDGE,
                           linewidth=1.6, zorder=3))
    ax.text(cx, y - SQ / 2, "A63", ha="center", va="center", fontsize=12, color="#12405e", zorder=4)
    return cy + total / 2                       # top y


def _cells(ax, x_left, cy, values, cmap, norm):
    n = len(values)
    y0 = cy - n * CH / 2
    sm = ScalarMappable(norm=norm, cmap=cmap)
    for i, v in enumerate(values):
        ax.add_patch(Rectangle((x_left, y0 + i * CH), CW, CH, facecolor=sm.to_rgba(v),
                               edgecolor="0.55", linewidth=0.15, zorder=3))
    ax.add_patch(Rectangle((x_left, y0), CW, n * CH, fill=False, edgecolor=FRAME,
                           linewidth=1.6, zorder=4))


def _node(ax, cx, cy, name, sub):
    ax.add_patch(FancyBboxPatch((cx - NODE_W / 2, cy - NODE_H / 2), NODE_W, NODE_H,
                                boxstyle="round,pad=0.02,rounding_size=0.08", facecolor=NODE_FILL,
                                edgecolor=NODE_EDGE, linewidth=2.2, zorder=5))
    ax.text(cx, cy, name, ha="center", va="center", fontsize=LABEL_FS, fontweight="bold",
            color="#1a1a1a", zorder=6)
    ax.text(cx, cy - NODE_H / 2 - 0.13, sub, ha="center", va="top", fontsize=SUB_FS,
            color="0.4", style="italic", zorder=6)


def _line(ax, xs, ys):
    ax.plot(xs, ys, color=ARROW, lw=2.6, zorder=2, solid_capstyle="round", solid_joinstyle="round")


def _arrow(ax, p0, p1):
    ax.add_patch(FancyArrowPatch(p0, p1, arrowstyle="-|>", mutation_scale=20, color=ARROW,
                                 linewidth=2.6, shrinkA=0, shrinkB=2, zorder=2))


def main():
    print("unit-norm check (AlphaEarth paper, presentation/assets/alphaearth.pdf, Fig 1E):")
    print('  "... each individual vector maps to a coordinate on the unit sphere S63."')
    print("  -> embeddings are unit length; dot product = cosine similarity in [-1, 1]. Range labelled.")

    rng = np.random.default_rng(7)
    a = rng.uniform(-1.0, 1.0, NCELL)
    b = a + rng.normal(0.0, 0.45, NCELL)
    delta = b - a                                        # signed elementwise difference, illustrative
    div = plt.get_cmap("RdBu_r")
    dmax = float(np.max(np.abs(delta)))
    n_d = TwoSlopeNorm(vmin=-dmax, vcenter=0.0, vmax=dmax)

    fig, ax = plt.subplots(figsize=(FIG_W, FIG_H))
    ax.set_xlim(0, FIG_W)
    ax.set_ylim(0, FIG_H)
    ax.axis("off")

    global NODE_W
    fig.canvas.draw()
    r = fig.canvas.get_renderer()
    widest = 0.0
    for name in ("Delta", "Dot product"):
        t = fig.text(0, 0, name, fontsize=LABEL_FS, fontweight="bold")
        widest = max(widest, t.get_window_extent(r).width / fig.dpi)
        t.remove()
    NODE_W = widest + 0.5

    ax.text(FIG_W / 2, 4.72, "Two Operations on a Pair of Embeddings", ha="center", va="center",
            fontsize=LABEL_FS + 1, fontweight="bold", color="#1a1a1a")

    # inputs: two embeddings as band-layer stacks
    top = _stack(ax, STACK_CX[0], STACK_CY)
    _stack(ax, STACK_CX[1], STACK_CY)
    for cx, yr in zip(STACK_CX, ("2018", "2020")):
        ax.text(cx, top + 0.14, yr, ha="center", va="bottom", fontsize=LABEL_FS, fontweight="bold",
                color="#1a1a1a")

    # operation nodes
    _node(ax, NODE_CX, DELTA_CY, "Delta", "elementwise difference")
    _node(ax, NODE_CX, DOT_CY, "Dot product", "similarity between the years")

    # orthogonal fork: the pair feeds both operations
    node_l = NODE_CX - NODE_W / 2
    _line(ax, [STACK_CX[1] + SQ / 2, FORK_X], [STACK_CY, STACK_CY])   # trunk from the pair
    _line(ax, [FORK_X, FORK_X], [DOT_CY, DELTA_CY])                   # fork riser
    _arrow(ax, (FORK_X, DELTA_CY), (node_l, DELTA_CY))
    _arrow(ax, (FORK_X, DOT_CY), (node_l, DOT_CY))
    # operation -> output
    node_r = NODE_CX + NODE_W / 2
    _arrow(ax, (node_r, DELTA_CY), (OUT_X - 0.08, DELTA_CY))
    _arrow(ax, (node_r, DOT_CY), (OUT_X - 0.08, DOT_CY))

    # outputs at the same cell scale: 64-cell delta strip over a single dot-product cell
    _cells(ax, OUT_X, DELTA_CY, delta, div, n_d)
    ax.add_patch(Rectangle((OUT_X, DOT_CY - CH / 2), CW, CH, facecolor=div(0.82),
                           edgecolor=FRAME, linewidth=1.6, zorder=4))

    # per-operation annotations, right of each output
    ax_x = OUT_X + CW + 0.3
    ax.text(ax_x, DELTA_CY, "which dimensions changed,\nand in which direction", ha="left",
            va="center", fontsize=BODY_FS, color="0.2", linespacing=1.4)
    ax.text(ax_x, DOT_CY + 0.10, "how much changed overall", ha="left", va="bottom",
            fontsize=BODY_FS, color="0.2")
    ax.text(ax_x, DOT_CY - 0.10, "cosine similarity (−1 to 1)", ha="left", va="top",
            fontsize=SUB_FS, color="0.45", style="italic")

    os.makedirs(OUT, exist_ok=True)
    fig.savefig(f"{OUT}/pres_15_embedding_ops.png", dpi=300)
    plt.close(fig)
    print("wrote pres_15_embedding_ops.png")


if __name__ == "__main__":
    main()
