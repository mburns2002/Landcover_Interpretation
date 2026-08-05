#!/usr/bin/env python3
"""pres_01_agents_naip: 2 by 2 panel of NAIP before/after examples, one per change agent.

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

import slide_font
import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
SRC = os.path.join(ROOT, "presentation", "assets", "examples_w_scale")
OUT = os.path.join(ROOT, "presentation", "figures")

# panel order (reading order), each: (label, filename)
PANELS = [
    ("Harvest", "Thesis_Figures_-2-1_scalebar.png"),
    ("Development", "Thesis_Figures_-2-4_scalebar.png"),
    ("Beaver", "Thesis_Figures_-2-3_scalebar.png"),
    ("Insect/Disease Mortality", "Thesis_Figures_-2-2_scalebar.png"),
]


FIG_W, FIG_H = 14.0, 8.0
IMG_H = 0.37                     # every image gets the SAME display height (figure fraction)
GAP = 0.03                       # horizontal gap between the two images in a row
ROW_BOTTOM = [0.49, 0.05]        # bottom y of the top and bottom rows


def _crop_to_content(im):
    """Trim the uneven white margin baked into each source so the photo content is what gets sized."""
    rgb = im[..., :3]
    content = rgb.min(axis=2) < 0.90                      # not near-white
    rows = np.where(content.any(axis=1))[0]
    cols = np.where(content.any(axis=0))[0]
    return im[rows.min():rows.max() + 1, cols.min():cols.max() + 1]


def main():
    imgs = {}
    for _lbl, fn in PANELS:
        p = os.path.join(SRC, fn)
        if not os.path.isfile(p):
            raise SystemExit(f"missing source screenshot: {p}")
        imgs[fn] = _crop_to_content(plt.imread(p))

    plt.rcParams.update({"font.family": "sans-serif",
                         "font.sans-serif": ["Helvetica", "Arial", "DejaVu Sans"], "font.size": 16})
    slide_font.use_spectral()
    fig = plt.figure(figsize=(FIG_W, FIG_H))
    fig.suptitle("NAIP Examples by Change Agent (Before and After)", fontsize=21, fontweight="bold",
                 y=0.96)

    # uniform height, true proportions: axes width follows each image's aspect (w/h), so no distortion.
    def frac_w(fn):
        im = imgs[fn]
        aspect = im.shape[1] / im.shape[0]
        return aspect * IMG_H * FIG_H / FIG_W

    for row, y0 in zip((PANELS[:2], PANELS[2:]), ROW_BOTTOM):
        widths = [frac_w(fn) for _, fn in row]
        x = (1.0 - (sum(widths) + GAP * (len(row) - 1))) / 2.0        # center the row
        for (label, fn), w in zip(row, widths):
            ax = fig.add_axes([x, y0, w, IMG_H])
            ax.imshow(imgs[fn])
            ax.set_axis_off()
            ax.set_title(label, fontsize=18, fontweight="bold", pad=8)
            x += w + GAP

    print(f"compiled 4 NAIP before/after examples at uniform height from {SRC}")
    os.makedirs(OUT, exist_ok=True)
    fig.savefig(os.path.join(OUT, "pres_01_agents_naip.png"), dpi=300)
    plt.close(fig)
    print("wrote pres_01_agents_naip.png")


if __name__ == "__main__":
    main()
