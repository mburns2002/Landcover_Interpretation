#!/usr/bin/env python3
"""Combine the two Chapter 3 disagreement-geometry panels into one stacked figure 3.4:
panel A (most contested class pairs) on top, panel B (contested-patch area distribution) below,
each labeled in its top-left corner. This stacks the two already-rendered source images at a common
width; it does not recompute anything.

Run: python scripts/combine_figure_3_4.py
Requires: matplotlib
"""

import os

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.image as mpimg

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PANEL_A = os.path.join(ROOT, "reports/interpreter_agreement/class_disagreement_top.png")
PANEL_B = os.path.join(ROOT, "reports/interpreter_agreement/geometry/area_ecdf_focus.png")
OUT = os.path.join(ROOT, "manuscript_formatting/figures/figure_3_4_disagreement_geometry.png")


def main():
    ia = mpimg.imread(PANEL_A)
    ib = mpimg.imread(PANEL_B)
    w = 10.0                                                   # figure width in inches
    ha = w * ia.shape[0] / ia.shape[1]                         # panel heights from each image aspect
    hb = w * ib.shape[0] / ib.shape[1]
    fig = plt.figure(figsize=(w, ha + hb))
    gs = fig.add_gridspec(2, 1, height_ratios=[ha, hb], hspace=0.03)
    for cell, img, lab in [(gs[0], ia, "A."), (gs[1], ib, "B.")]:
        ax = fig.add_subplot(cell)
        ax.imshow(img)
        ax.axis("off")
        ax.text(0.005, 0.99, lab, transform=ax.transAxes, fontsize=20, fontweight="bold",
                va="top", ha="left")
    fig.savefig(OUT, dpi=200, bbox_inches="tight")
    plt.close(fig)
    print(f"wrote {OUT}")


if __name__ == "__main__":
    main()
