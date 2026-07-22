#!/usr/bin/env python3
"""Figure 2.3, a methods schematic of the five embedding feature configurations (v2 to v6).

Drawn, not plotted from data. Two annual AlphaEarth embedding fields (2018 and 2020) at the top, the
two derived operations (delta and dot) defined once, then five rows showing each configuration's
classifier input stack as adjacent band blocks with band counts. Baseline blocks (a full 64-D
embedding field) and change blocks (delta or dot) use two consistent tones, so it is immediately
visible that v2, v3, and v5 keep a baseline block while v4 and v6 keep only change blocks. Band counts
are fixed: v2 = 128, v3 = 128, v4 = 64, v5 = 65, v6 = 1.

Run: python scripts/build_embedding_configs_figure.py
Requires: matplotlib
"""

import os

import matplotlib.pyplot as plt
from matplotlib.colors import to_rgb
from matplotlib.patches import FancyArrowPatch, Rectangle

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = f"{ROOT}/manuscript_formatting/figures/figure_embedding_configs"

# two colourblind-safe tones (Okabe-Ito blue and orange); differ in hue and lightness, so they read in
# grayscale too. no Figure 2.2 exists yet, so these are the reference tones for it to match.
BASELINE = "#0072B2"                                       # full embedding field
CHANGE = "#E69F00"                                         # delta or dot
W64 = 2.15                                                 # width of a 64-D block
WDOT = 0.16                                                # width of a 1-band block (visibly thin)
BH = 0.72                                                  # block height

# each config: label, description, blocks [(content, kind, width, band_count)], total
CONFIGS = [
    ("v2", "baseline + delta", [("2018", "baseline", W64, "64"), ("delta", "change", W64, "64")], "128 bands"),
    ("v3", "stacked years", [("2018", "baseline", W64, "64"), ("2020", "baseline", W64, "64")], "128 bands"),
    ("v4", "delta only", [("delta", "change", W64, "64")], "64 bands"),
    ("v5", "baseline + dot", [("2018", "baseline", W64, "64"), ("dot", "change", WDOT, "1")], "65 bands"),
    ("v6", "dot only", [("dot", "change", WDOT, "1")], "1 band"),
]


def text_color(fill):
    r, g, b = to_rgb(fill)
    return "white" if (0.299 * r + 0.587 * g + 0.114 * b) < 0.55 else "black"


def block(ax, x, y, w, kind, content, band):
    fill = BASELINE if kind == "baseline" else CHANGE
    hatch = None if kind == "baseline" else "///"          # redundant, non-color cue for change blocks
    ax.add_patch(Rectangle((x, y - BH / 2), w, BH, facecolor=fill, edgecolor="black",
                           linewidth=1.1, hatch=hatch, zorder=3))
    if w >= 0.6:                                            # label inside a wide block
        ax.text(x + w / 2, y, content, ha="center", va="center", fontsize=10.5, fontweight="bold",
                color=text_color(fill), zorder=4)
        ax.text(x + w / 2, y - BH / 2 - 0.16, band, ha="center", va="top", fontsize=7.5, color="0.4")
    else:                                                  # thin block, label above
        ax.text(x + w / 2, y + BH / 2 + 0.13, content, ha="center", va="bottom", fontsize=9.5,
                fontweight="bold", color="black", zorder=4)
        ax.text(x + w / 2, y - BH / 2 - 0.16, band, ha="center", va="top", fontsize=7.5, color="0.4")
    return x + w


def field_stack(ax, cx, cy, w=1.6, n=7):
    # stylized stack of thin rectangles to evoke many (64) dimensions, baseline tone
    rh, gap = 0.11, 0.05
    total = n * rh + (n - 1) * gap
    y = cy + total / 2 - rh
    for _ in range(n):
        ax.add_patch(Rectangle((cx - w / 2, y), w, rh, facecolor=BASELINE, edgecolor="black",
                               linewidth=0.5, zorder=3))
        y -= (rh + gap)


def main():
    os.makedirs(OUT, exist_ok=True)
    plt.rcParams["font.family"] = "DejaVu Sans"
    fig, ax = plt.subplots(figsize=(8.0, 9.0))
    ax.set_xlim(0, 12); ax.set_ylim(0.6, 15.0); ax.axis("off")

    def header(y, txt):
        ax.text(0.3, y, txt, fontsize=12.5, fontweight="bold", ha="left")

    # zone A: source embedding fields
    header(14.6, "Source embedding fields")
    for cx, yr in [(3.3, "2018"), (7.0, "2020")]:
        field_stack(ax, cx, 13.55)
        ax.text(cx, 12.55, f"{yr} embedding (64-D)", ha="center", va="top", fontsize=10.5)
    ax.add_patch(FancyArrowPatch((5.15, 12.35), (5.15, 11.95), arrowstyle="-|>",
                                 mutation_scale=13, color="0.55", linewidth=1.2))

    # zone B: derived operations, defined once
    header(11.75, "Derived operations (from the 2018 and 2020 fields)")
    # delta: wide 64-D change block
    ax.add_patch(Rectangle((0.5, 10.85), 1.35, 0.55, facecolor=CHANGE, edgecolor="black",
                           linewidth=1.1, hatch="///", zorder=3))
    ax.text(1.175, 11.125, "delta", ha="center", va="center", fontsize=9.5, fontweight="bold",
            color="black", zorder=4)
    ax.text(2.1, 11.125, "delta = 2018 - 2020, element-wise; a 64-band difference image (64-D)",
            ha="left", va="center", fontsize=10)
    # dot: thin 1-band change block
    ax.add_patch(Rectangle((1.1, 10.0), WDOT, 0.55, facecolor=CHANGE, edgecolor="black",
                           linewidth=1.1, hatch="///", zorder=3))
    ax.text(0.5, 10.275, "dot", ha="left", va="center", fontsize=9.5, fontweight="bold", color="black")
    ax.text(2.1, 10.275, "dot = Σ(2018 × 2020) over 64 dims; cosine similarity, 1-D, "
            "range -1 to 1", ha="left", va="center", fontsize=10)
    ax.add_patch(FancyArrowPatch((5.15, 9.75), (5.15, 9.35), arrowstyle="-|>",
                                 mutation_scale=13, color="0.55", linewidth=1.2))

    # zone C: the five configurations
    header(9.15, "Feature configurations (classifier input stacks)")
    x_block = 3.3
    x_count = 9.9
    ys = [8.2 - i * 1.4 for i in range(len(CONFIGS))]
    for y, (code, desc, blocks, total) in zip(ys, CONFIGS):
        ax.text(0.3, y, code, ha="left", va="center", fontsize=12.5, fontweight="bold")
        ax.text(0.95, y, desc, ha="left", va="center", fontsize=10)
        x = x_block
        for content, kind, w, band in blocks:
            x = block(ax, x, y, w, kind, content, band)
        ax.text(x_count, y, total, ha="left", va="center", fontsize=11, fontweight="bold")

    # legend: the two tones
    ly = 1.35
    ax.add_patch(Rectangle((0.5, ly - 0.2), 0.55, 0.4, facecolor=BASELINE, edgecolor="black",
                           linewidth=1.0))
    ax.text(1.2, ly, "baseline (full embedding field)", ha="left", va="center", fontsize=10.5)
    ax.add_patch(Rectangle((5.6, ly - 0.2), 0.55, 0.4, facecolor=CHANGE, edgecolor="black",
                           linewidth=1.0, hatch="///"))
    ax.text(6.3, ly, "change (delta or dot)", ha="left", va="center", fontsize=10.5)

    fig.tight_layout()
    png = f"{OUT}/figure_2_3_embedding_configs.png"
    pdf = f"{OUT}/figure_2_3_embedding_configs.pdf"
    fig.savefig(png, dpi=300, bbox_inches="tight")
    fig.savefig(pdf, bbox_inches="tight")
    plt.close(fig)
    print(f"wrote {png} and {pdf}")


if __name__ == "__main__":
    main()
