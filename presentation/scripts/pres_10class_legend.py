#!/usr/bin/env python3
"""pres_10class_legend: standalone legend for the 10-class schema (no title).

A color-swatch legend for the 10 model classes, grouped into the six no-change (stable) classes and the
four change (disturbance) classes, in the canonical display order. Colors are pulled from the project
legend (compare_interpreted_vs_model.load_mappings), so they always match the maps and other figures.

Geometry: data units == inches (axes pinned to fill the figure), and swatch/column positions are sized
from renderer-measured label widths, so text never collides with a swatch or the next column.
Output (PNG only for the Google Slides deck): presentation/figures/pres_10class_legend.png
"""

import importlib.util
import os

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

import slide_font
from matplotlib.patches import Rectangle
slide_font.use_spectral()

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
OUT = os.path.join(ROOT, "presentation", "figures")


def _c10():
    spec = importlib.util.spec_from_file_location(
        "C", os.path.join(ROOT, "scripts", "compare_interpreted_vs_model.py"))
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod.load_mappings()[2]                              # canonical {code: color}


NAME10 = {1: "Harvest", 2: "Development", 3: "Forest", 4: "Urban", 5: "Water",
          6: "Agriculture", 7: "Grass/Shrub", 8: "Wetland", 9: "Beaver", 10: "Insect/Disease"}
STABLE = [3, 4, 5, 6, 7, 8]        # no-change classes, display order
CHANGE = [1, 2, 10, 9]             # disturbance classes, display order

LABEL_FS, HDR_FS = 15, 12
SW, SH, PAD = 0.34, 0.30, 0.16     # swatch width, height, swatch-to-label gap (in)
RP = 0.52                          # row pitch (in)
LM, RM, TOPM, BOTM = 0.3, 0.3, 0.28, 0.28
HDR_GAP, COLGAP = 0.34, 0.6        # header-to-first-row gap, gap between the two columns (in)
SWATCH_EDGE = "0.3"


def _measure(fig, r, s, fs):
    t = fig.text(0, 0, s, fontsize=fs)
    w = t.get_window_extent(r).width / fig.dpi
    t.remove()
    return w


def main():
    c10 = _c10()

    # measure label widths to size the columns
    tmp = plt.figure(figsize=(4, 4))
    tmp.canvas.draw()
    r = tmp.canvas.get_renderer()
    wa = max(_measure(tmp, r, NAME10[c], LABEL_FS) for c in STABLE)
    wb = max(_measure(tmp, r, NAME10[c], LABEL_FS) for c in CHANGE)
    wa = max(wa, _measure(tmp, r, "Stable", HDR_FS))
    wb = max(wb, _measure(tmp, r, "Change", HDR_FS))
    plt.close(tmp)

    colA_sw = LM
    colA_lbl = colA_sw + SW + PAD
    colB_sw = colA_lbl + wa + COLGAP
    colB_lbl = colB_sw + SW + PAD
    fig_w = colB_lbl + wb + RM
    fig_h = TOPM + 0.24 + HDR_GAP + len(STABLE) * RP + BOTM      # column A is the taller one

    fig = plt.figure(figsize=(fig_w, fig_h))
    ax = fig.add_axes([0, 0, 1, 1])
    ax.set_xlim(0, fig_w)
    ax.set_ylim(0, fig_h)
    ax.axis("off")

    hdr_y = fig_h - TOPM
    row0 = hdr_y - HDR_GAP - RP / 2                              # center y of the first row in each column

    def column(sw_x, lbl_x, header, codes):
        ax.text(sw_x, hdr_y, header, ha="left", va="top", fontsize=HDR_FS, fontweight="bold",
                color="#1a1a1a")
        for i, code in enumerate(codes):
            cy = row0 - i * RP
            ax.add_patch(Rectangle((sw_x, cy - SH / 2), SW, SH, facecolor=c10[code],
                                   edgecolor=SWATCH_EDGE, linewidth=0.8))
            ax.text(lbl_x, cy, NAME10[code], ha="left", va="center", fontsize=LABEL_FS, color="#1a1a1a")

    column(colA_sw, colA_lbl, "Stable", STABLE)
    column(colB_sw, colB_lbl, "Change", CHANGE)

    os.makedirs(OUT, exist_ok=True)
    fig.savefig(os.path.join(OUT, "pres_10class_legend.png"), dpi=300, transparent=True)
    plt.close(fig)
    print(f"canvas {fig_w:.2f} x {fig_h:.2f} in; 10 classes, no-change ({len(STABLE)}) + change ({len(CHANGE)})")
    print("wrote pres_10class_legend.png")


if __name__ == "__main__":
    main()
