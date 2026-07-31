#!/usr/bin/env python3
"""pres_15_embedding_ops: the two operations on a pair of AlphaEarth embeddings.

Teaching point is dimensionality. Two embeddings (2018, 2020), each a strip of 64 cells. Two
operations branch right:
  Delta        elementwise difference  -> a 64-cell strip   (all 64 dimensions preserved)
  Dot product  similarity between years -> a single cell     (the pair collapses to one number)

The 64-cell delta strip and the single dot-product cell are drawn at the SAME cell scale (identical
cell width and per-cell height), so the 64-vs-1 size difference is visible at a glance rather than
stated in a label. The single cell is NOT resized to fill space; that size gap is the argument.

Unit norm / cosine: confirmed from the AlphaEarth paper (presentation/assets/alphaearth.pdf, Fig 1E):
"A stack of 64 rasterized AEF layers forms an embedding field, and each individual vector maps to a
coordinate on the unit sphere S63." Each 64-D embedding is unit length, so the dot product of two
years is a cosine similarity in [-1, 1]; that range is labelled on the dot-product output.

Cell fills are an ARBITRARY illustrative gradient (sequential for the year strips, diverging for the
signed delta so direction reads as color). They are NOT real embedding values and must not be read
as such.

Styling matches pres_03 / pres_11 (rounded FancyBboxPatch nodes, #333333 arrows, DejaVu font).
Output (PNG only for the Google Slides deck): presentation/figures/pres_15_embedding_ops.png
"""

import os

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
from matplotlib.cm import ScalarMappable
from matplotlib.colors import Normalize, TwoSlopeNorm
from matplotlib.patches import FancyArrowPatch, FancyBboxPatch, Rectangle

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
OUT = os.path.join(ROOT, "presentation", "figures")

FIG_W, FIG_H = 12.0, 5.0
LABEL_FS, BODY_FS, SUB_FS = 20, 16, 16       # operation/year labels 20 pt; annotations/subs 16 pt
ARROW = "#333333"
NODE_FILL, NODE_EDGE = "white", "#333333"
FRAME = "#333333"                            # outer frame around a strip / the single cell
NCELL = 64

# geometry (data units = inches; axes span 0..12 x 0..5)
CW = 0.52                                     # cell width (also strip width)
SH = 2.35                                     # strip height for 64 cells
CH = SH / NCELL                               # single-cell height, shared by strip cells and dot cell
IN_CY = 2.9                                   # vertical center of the input strips and the delta lane
DOT_CY = 1.02                                 # vertical center of the dot-product lane
IN_X = [1.15, 2.25]                           # x-left of the 2018 / 2020 input strips (gap fits 20 pt labels)
NODE_CX, NODE_H = 4.8, 0.62
NODE_W = 1.95                                  # recomputed in main() to fit the widest label + padding
OUT_X = 7.99                                  # x-left of both outputs (same column: strip over cell)


def _cells(ax, x_left, cy, values, cmap, norm):
    """Draw a vertical strip of len(values) cells, bottom-to-top, plus an outer frame."""
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
    ax.text(cx, cy - NODE_H / 2 - 0.16, sub, ha="center", va="top", fontsize=SUB_FS,
            color="0.4", style="italic", zorder=6)


def _arrow(ax, p0, p1):
    ax.add_patch(FancyArrowPatch(p0, p1, arrowstyle="-|>", mutation_scale=20, color=ARROW,
                                 linewidth=2.6, shrinkA=3, shrinkB=3, zorder=2))


def main():
    print("unit-norm check (AlphaEarth paper, presentation/assets/alphaearth.pdf, Fig 1E):")
    print('  "... each individual vector maps to a coordinate on the unit sphere S63."')
    print("  -> embeddings are unit length; dot product = cosine similarity in [-1, 1]. Range labelled.")

    # illustrative-only values (NOT real embeddings). fixed seed for reproducibility.
    rng = np.random.default_rng(7)
    a = rng.uniform(-1.0, 1.0, NCELL)
    b = a + rng.normal(0.0, 0.45, NCELL)                 # 2020 resembles 2018 (correlated), illustrative
    delta = b - a                                        # signed elementwise difference

    seq = plt.get_cmap("cividis")                        # colorblind-safe sequential, for year strips
    div = plt.get_cmap("RdBu_r")                         # colorblind-safe diverging, for signed delta
    n_a = Normalize(a.min(), a.max())
    n_b = Normalize(b.min(), b.max())
    dmax = float(np.max(np.abs(delta)))
    n_d = TwoSlopeNorm(vmin=-dmax, vcenter=0.0, vmax=dmax)

    fig, ax = plt.subplots(figsize=(FIG_W, FIG_H))
    ax.set_xlim(0, FIG_W)
    ax.set_ylim(0, FIG_H)
    ax.axis("off")

    # size the operation boxes to the widest label so 20 pt text never touches the border
    global NODE_W
    fig.canvas.draw()
    r = fig.canvas.get_renderer()
    widest = 0.0
    for name in ("Delta", "Dot product"):
        t = fig.text(0, 0, name, fontsize=LABEL_FS, fontweight="bold")
        widest = max(widest, t.get_window_extent(r).width / fig.dpi)
        t.remove()
    NODE_W = widest + 0.5                                 # 0.25 in padding each side

    # title (Title Case) + caption, per the presentation-figure convention
    ax.text(FIG_W / 2, 4.82, "Two Operations on a Pair of Embeddings", ha="center", va="center",
            fontsize=LABEL_FS + 1, fontweight="bold", color="#1a1a1a")

    # inputs: two 64-cell strips
    _cells(ax, IN_X[0], IN_CY, a, seq, n_a)
    _cells(ax, IN_X[1], IN_CY, b, seq, n_b)
    top = IN_CY + SH / 2
    ax.text(IN_X[0] + CW / 2, top + 0.16, "2018", ha="center", va="bottom", fontsize=LABEL_FS,
            fontweight="bold", color="#1a1a1a")
    ax.text(IN_X[1] + CW / 2, top + 0.16, "2020", ha="center", va="bottom", fontsize=LABEL_FS,
            fontweight="bold", color="#1a1a1a")

    # operation nodes
    _node(ax, NODE_CX, IN_CY, "Delta", "elementwise difference")
    _node(ax, NODE_CX, DOT_CY, "Dot product", "similarity between the years")

    # arrows: the input pair feeds both operations
    src_x = IN_X[1] + CW + 0.12
    _arrow(ax, (src_x, IN_CY), (NODE_CX - NODE_W / 2, IN_CY))
    _arrow(ax, (src_x, IN_CY - 0.15), (NODE_CX - NODE_W / 2, DOT_CY))
    # arrows: operation -> output
    _arrow(ax, (NODE_CX + NODE_W / 2, IN_CY), (OUT_X - 0.08, IN_CY))
    _arrow(ax, (NODE_CX + NODE_W / 2, DOT_CY), (OUT_X - 0.08, DOT_CY))

    # outputs, drawn at the SAME cell scale: 64-cell delta strip over a single dot-product cell
    _cells(ax, OUT_X, IN_CY, delta, div, n_d)
    ax.add_patch(Rectangle((OUT_X, DOT_CY - CH / 2), CW, CH, facecolor=div(0.82),
                           edgecolor=FRAME, linewidth=1.6, zorder=4))

    # per-operation annotations, to the right of each output
    ax.text(OUT_X + CW + 0.28, IN_CY, "which dimensions changed,\nand in which direction",
            ha="left", va="center", fontsize=BODY_FS, color="0.2", linespacing=1.4)
    ax.text(OUT_X + CW + 0.28, DOT_CY + 0.10, "how much changed overall", ha="left", va="bottom",
            fontsize=BODY_FS, color="0.2")
    ax.text(OUT_X + CW + 0.28, DOT_CY - 0.10, "cosine similarity (−1 to 1)", ha="left", va="top",
            fontsize=SUB_FS, color="0.45", style="italic")

    ax.text(FIG_W / 2, 0.16, "Delta preserves all 64 dimensions; the dot product collapses the pair "
            "to a single number.", ha="center", va="center", fontsize=BODY_FS - 2, color="0.3")

    os.makedirs(OUT, exist_ok=True)
    fig.savefig(f"{OUT}/pres_15_embedding_ops.png", dpi=300)
    plt.close(fig)
    print("wrote pres_15_embedding_ops.png")


if __name__ == "__main__":
    main()
