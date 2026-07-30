#!/usr/bin/env python3
"""pres_08_synthesis_loop: two-box loop for the closing argument.

Two boxes, a forward arrow and a return arrow forming a loop, and one consequence line. Meant to be
spoken over and read in about two seconds, so the text is large and there is nothing else. Drawn with
matplotlib patches, text kept as text (not paths), no icons and no gradients.

output (png only):
  presentation/figures/pres_08_synthesis_loop.png
"""

import os

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch, FancyArrowPatch

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
OUT = os.path.join(ROOT, "presentation", "figures")


def _box(ax, cx, cy, w, h, face, edge):
    ax.add_patch(FancyBboxPatch((cx - w / 2, cy - h / 2), w, h,
                                boxstyle="round,pad=0.008,rounding_size=0.03",
                                linewidth=2.6, edgecolor=edge, facecolor=face, zorder=3))


def main():
    plt.rcParams.update({"font.family": "sans-serif",
                         "font.sans-serif": ["Helvetica", "Arial", "DejaVu Sans"],
                         "font.size": 18, "pdf.fonttype": 42, "ps.fonttype": 42})
    fig, ax = plt.subplots(figsize=(13.33, 7.5))
    ax.set_xlim(0, 1)
    ax.set_ylim(0, 1)
    ax.axis("off")

    lcx, rcx, cy, bw, bh = 0.235, 0.765, 0.56, 0.34, 0.26
    _box(ax, lcx, cy, bw, bh, "#E8EEF6", "#34618E")
    _box(ax, rcx, cy, bw, bh, "#F5EAE0", "#8C5A2B")

    ax.text(lcx, cy + 0.055, "Chapter 2", ha="center", va="center", fontsize=25, fontweight="bold",
            color="#34618E")
    ax.text(lcx, cy - 0.045, "representation determines\nspatial structure", ha="center", va="center",
            fontsize=20, color="0.1")
    ax.text(rcx, cy + 0.055, "Chapter 3", ha="center", va="center", fontsize=25, fontweight="bold",
            color="#8C5A2B")
    ax.text(rcx, cy - 0.045, "conventional assessment cannot\nsee spatial structure", ha="center",
            va="center", fontsize=20, color="0.1")

    # forward arrow (left -> right), bowing up, and return arrow (right -> left), bowing down
    xl, xr = lcx + bw / 2, rcx - bw / 2
    ax.add_patch(FancyArrowPatch((xl, cy + 0.05), (xr, cy + 0.05), connectionstyle="arc3,rad=-0.55",
                                 arrowstyle="-|>", mutation_scale=28, lw=2.8, color="0.2", zorder=2))
    ax.add_patch(FancyArrowPatch((xr, cy - 0.05), (xl, cy - 0.05), connectionstyle="arc3,rad=-0.55",
                                 arrowstyle="-|>", mutation_scale=28, lw=2.8, color="0.2", zorder=2))
    ax.text(0.5, cy + 0.22, "the property that distinguishes maps", ha="center", va="center",
            fontsize=18, color="0.2")
    ax.text(0.5, cy - 0.22, "the property that inflates variance", ha="center", va="center",
            fontsize=18, color="0.2")

    # one line of consequence
    ax.text(0.5, 0.12,
            "A study designed on aggregate accuracy from a point sample\n"
            "would have found these configurations equivalent.",
            ha="center", va="center", fontsize=19, color="0.1")

    os.makedirs(OUT, exist_ok=True)
    fig.savefig(os.path.join(OUT, "pres_08_synthesis_loop.png"), dpi=300, bbox_inches="tight")
    plt.close(fig)
    print("wrote pres_08_synthesis_loop.png")


if __name__ == "__main__":
    main()
