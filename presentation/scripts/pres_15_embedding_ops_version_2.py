#!/usr/bin/env python3
"""pres_15_embedding_ops_version_2: real-map version of the embedding-ops figure.

Same flow as pres_15_embedding_ops, but using the actual AlphaEarth maps uploaded to
presentation/assets/ instead of the schematic drawings: the two input embeddings (2019, 2020), the
delta, and the dot product. Two operations branch off the embedding pair:
  Delta        elementwise difference   -> the delta map
  Dot product  similarity between years -> the dot-product map

Geometry: data units == inches for the background axes (set_position([0,0,1,1])); the four maps are
placed as their own axes in figure-fraction coordinates. Text never overlaps a box (see CLAUDE.md).
Output (PNG only): presentation/figures/pres_15_embedding_ops_version_2.png
"""

import os

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

import slide_font
from matplotlib.patches import FancyArrowPatch, FancyBboxPatch
slide_font.use_spectral()

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
ASSET = os.path.join(ROOT, "presentation", "assets")
OUT = os.path.join(ROOT, "presentation", "figures")

ARROW = "#333333"
NODE_FILL, NODE_EDGE = "white", "#333333"
IMG_EDGE = "#333333"

FIG_W, FIG_H = 12.0, 6.0
LABEL_FS, BODY_FS, SUB_FS = 20, 14, 12
MID, DELTA_CY, DOT_CY = 3.0, 4.0, 2.0
SQ_IN, SQ_OUT = 1.55, 1.4                        # input-map and output-map side (inches)
IN_X = [0.55, 2.35]                             # left-x of the 2019 / 2020 maps
BOX = (0.40, 2.00, 3.75, 2.00)                  # group box (x, y, w, h)
FORK_X = 4.4
NODE_CX, NODE_H = 5.95, 0.6
NODE_W = 2.3
OUT_X = 7.5                                     # left-x of both output maps


def _img(fig, x, y, w, h, im):
    ax = fig.add_axes([x / FIG_W, y / FIG_H, w / FIG_W, h / FIG_H])
    ax.imshow(im)
    ax.set_xticks([])
    ax.set_yticks([])
    for s in ax.spines.values():
        s.set_edgecolor(IMG_EDGE)
        s.set_linewidth(0.8)
    return ax


def _node(bg, cx, cy, name, sub):
    bg.add_patch(FancyBboxPatch((cx - NODE_W / 2, cy - NODE_H / 2), NODE_W, NODE_H,
                                boxstyle="round,pad=0.02,rounding_size=0.08", facecolor=NODE_FILL,
                                edgecolor=NODE_EDGE, linewidth=2.2, zorder=5))
    bg.text(cx, cy, name, ha="center", va="center", fontsize=LABEL_FS, fontweight="bold",
            color="#1a1a1a", zorder=6)
    bg.text(cx, cy - NODE_H / 2 - 0.13, sub, ha="center", va="top", fontsize=SUB_FS, color="0.4",
            style="italic", zorder=6)


def _line(bg, xs, ys):
    bg.plot(xs, ys, color=ARROW, lw=2.6, zorder=2, solid_capstyle="round", solid_joinstyle="round")


def _arrow(bg, p0, p1):
    bg.add_patch(FancyArrowPatch(p0, p1, arrowstyle="-|>", mutation_scale=20, color=ARROW,
                                 linewidth=2.6, shrinkA=0, shrinkB=2, zorder=2))


def main():
    imgs = {fn: plt.imread(os.path.join(ASSET, fn)) for fn in
            ("embeddings 2019.png", "embeddings 2020.png", "delta.png", "dot product.png")}

    fig = plt.figure(figsize=(FIG_W, FIG_H))
    bg = fig.add_axes([0, 0, 1, 1])
    bg.set_xlim(0, FIG_W)
    bg.set_ylim(0, FIG_H)
    bg.axis("off")

    global NODE_W
    fig.canvas.draw()
    r = fig.canvas.get_renderer()
    widest = 0.0
    for s in ("Delta", "Dot product"):                 # size boxes to the widest label (inches)
        t = fig.text(0, 0, s, fontsize=LABEL_FS, fontweight="bold")
        widest = max(widest, t.get_window_extent(r).width / fig.dpi)
        t.remove()
    NODE_W = widest + 0.6

    # group box behind the input maps
    bg.add_patch(FancyBboxPatch((BOX[0], BOX[1]), BOX[2], BOX[3],
                                boxstyle="round,pad=0.02,rounding_size=0.08", facecolor="#f4f7fb",
                                edgecolor="#b6c5d4", linewidth=1.4, zorder=1))

    # input embeddings
    for x, fn, yr in zip(IN_X, ("embeddings 2019.png", "embeddings 2020.png"), ("2019", "2020")):
        _img(fig, x, MID - SQ_IN / 2, SQ_IN, SQ_IN, imgs[fn])
        bg.text(x + SQ_IN / 2, MID + SQ_IN / 2 + 0.14, yr, ha="center", va="bottom",
                fontsize=LABEL_FS, fontweight="bold", color="#1a1a1a", zorder=6)
    box_cx = (IN_X[0] + IN_X[1] + SQ_IN) / 2
    bg.text(box_cx, BOX[1] + BOX[3] + 0.5, "AlphaEarth Embeddings", ha="center", va="bottom",
            fontsize=16, fontweight="bold", color="#1a1a1a", zorder=6)

    # fork off the group box to the two operations
    node_l = NODE_CX - NODE_W / 2
    box_r = BOX[0] + BOX[2]
    _line(bg, [box_r, FORK_X], [MID, MID])
    _line(bg, [FORK_X, FORK_X], [DOT_CY, DELTA_CY])
    _arrow(bg, (FORK_X, DELTA_CY), (node_l, DELTA_CY))
    _arrow(bg, (FORK_X, DOT_CY), (node_l, DOT_CY))
    _node(bg, NODE_CX, DELTA_CY, "Delta", "elementwise difference")
    _node(bg, NODE_CX, DOT_CY, "Dot product", "similarity between the years")

    # operation -> output map
    node_r = NODE_CX + NODE_W / 2
    _arrow(bg, (node_r, DELTA_CY), (OUT_X - 0.05, DELTA_CY))
    _arrow(bg, (node_r, DOT_CY), (OUT_X - 0.05, DOT_CY))
    _img(fig, OUT_X, DELTA_CY - SQ_OUT / 2, SQ_OUT, SQ_OUT, imgs["delta.png"])
    _img(fig, OUT_X, DOT_CY - SQ_OUT / 2, SQ_OUT, SQ_OUT, imgs["dot product.png"])

    ann_x = OUT_X + SQ_OUT + 0.25
    bg.text(ann_x, DELTA_CY, "which dimensions changed,\nand in which direction", ha="left",
            va="center", fontsize=BODY_FS, color="0.2", linespacing=1.4, zorder=6)
    bg.text(ann_x, DOT_CY + 0.12, "how much changed overall", ha="left", va="bottom",
            fontsize=BODY_FS, color="0.2", zorder=6)
    bg.text(ann_x, DOT_CY - 0.12, "cosine similarity (−1 to 1)", ha="left", va="top", fontsize=SUB_FS,
            color="0.45", style="italic", zorder=6)

    os.makedirs(OUT, exist_ok=True)
    fig.savefig(os.path.join(OUT, "pres_15_embedding_ops_version_2.png"), dpi=300)
    plt.close(fig)
    print("wrote pres_15_embedding_ops_version_2.png")


if __name__ == "__main__":
    main()
