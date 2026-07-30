#!/usr/bin/env python3
"""pres_01_agents_naip: 2 by 2 panel of NAIP before/after chips, one per change agent.

Compilation only. Each source screenshot in presentation/assets/examples_w_scale/ is already a
before/after NAIP pair (left before, right after) with a 50 m scale bar. This lays the four out in a
2 by 2 grid with the agent name as each panel label. No data processing.

Agent to file mapping (given): 1 harvest, 2 insect/disease, 3 beaver, 4 development.

output (png only):
  presentation/figures/pres_01_agents_naip.png
"""

import os

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
SRC = os.path.join(ROOT, "presentation", "assets", "examples_w_scale")
OUT = os.path.join(ROOT, "presentation", "figures")

# panel order (reading order), each: (label, filename). class palette color used only for a small tag
PANELS = [
    ("Harvest", "Thesis_Figures_-2-1_scalebar.png", "#C9A400"),        # yellow class, darkened for a tag
    ("Development", "Thesis_Figures_-2-4_scalebar.png", "#D62728"),
    ("Beaver", "Thesis_Figures_-2-3_scalebar.png", "#E69F00"),
    ("Insect/Disease Mortality", "Thesis_Figures_-2-2_scalebar.png", "#70A2DB"),
]


def main():
    for _lbl, fn, _c in PANELS:
        p = os.path.join(SRC, fn)
        if not os.path.isfile(p):
            raise SystemExit(f"missing source screenshot: {p}")

    plt.rcParams.update({"font.family": "sans-serif",
                         "font.sans-serif": ["Helvetica", "Arial", "DejaVu Sans"], "font.size": 16})
    fig, axes = plt.subplots(2, 2, figsize=(14, 8))
    fig.subplots_adjust(left=0.01, right=0.99, top=0.90, bottom=0.02, wspace=0.04, hspace=0.14)
    fig.suptitle("NAIP Chips by Change Agent (Before and After)", fontsize=21, fontweight="bold", y=0.98)

    for ax, (label, fn, color) in zip(axes.flat, PANELS):
        ax.imshow(plt.imread(os.path.join(SRC, fn)))
        ax.set_axis_off()
        # agent label with a small class-color tag square for consistency with the deck palette
        ax.set_title(label, fontsize=18, fontweight="bold", pad=8)
        ax.plot(0.012, 1.045, marker="s", markersize=13, markerfacecolor=color,
                markeredgecolor="black", markeredgewidth=0.6, transform=ax.transAxes, clip_on=False)

    print(f"compiled 4 NAIP before/after chips into a 2x2 grid from {SRC}")
    os.makedirs(OUT, exist_ok=True)
    fig.savefig(os.path.join(OUT, "pres_01_agents_naip.png"), dpi=300, bbox_inches="tight")
    plt.close(fig)
    print("wrote pres_01_agents_naip.png")


if __name__ == "__main__":
    main()
