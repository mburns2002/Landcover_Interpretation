#!/usr/bin/env python3
"""Classification-schema figure: the 10-class schema and its 5-class collapse.

Left, the 10 classes (colored by the canonical model legend from load_mappings), grouped into the six
no-change (stable) classes and the four change (disturbance) classes, each with its class code. Right,
the 5-class collapse that folds the six stable classes into a single Stable class and keeps the four
change classes, with connectors showing the mapping. Colors are the project legend, not matplotlib
defaults; the collapsed Stable class is a neutral grey and the four change classes keep their 10-class
colors.

Run: python scripts/build_class_schema_figure.py
Requires: matplotlib
"""

import importlib.util
import os

import matplotlib.pyplot as plt
from matplotlib.colors import to_rgb
from matplotlib.patches import FancyArrowPatch, Rectangle

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = f"{ROOT}/figure_study_area"


def _load(name, path):
    spec = importlib.util.spec_from_file_location(name, os.path.join(ROOT, "scripts", path))
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


C = _load("C", "compare_interpreted_vs_model.py")
C10 = C.load_mappings()[2]                                  # canonical 10-class colors {code: color}

# 10-class code to name and to the source CKIT label id (from the reference crosswalk)
NAME10 = {1: "Harvest", 2: "Development", 3: "Forest", 4: "Urban", 5: "Water",
          6: "Agriculture", 7: "Grass/Shrub", 8: "Wetland", 9: "Beaver", 10: "Insect/Disease"}
CKIT = {1: 20, 2: 30, 3: 3, 4: 0, 5: 4, 6: 1, 7: 2, 8: 5, 9: 62, 10: 50}
STABLE = [3, 4, 5, 6, 7, 8]                                 # display order, no-change classes
CHANGE = [1, 2, 10, 9]                                      # display order, disturbance classes
# 5-class collapse: the six stable classes fold to Stable, the four change classes map to themselves
C5 = {"Stable": "#cccccc", "Harvest": C10[1], "Development": C10[2],
      "Insect/Disease": C10[10], "Beaver": C10[9]}


def text_color(fill):
    r, g, b = to_rgb(fill)
    return "white" if (0.299 * r + 0.587 * g + 0.114 * b) < 0.55 else "black"


def main():
    os.makedirs(OUT, exist_ok=True)
    fig, ax = plt.subplots(figsize=(8.2, 5.8))
    ax.set_xlim(0, 12); ax.set_ylim(0, 11); ax.axis("off")

    # column headers
    ax.text(3.0, 10.4, "10-class schema", fontsize=13, fontweight="bold", ha="center")
    ax.text(10.0, 10.4, "5-class collapse", fontsize=13, fontweight="bold", ha="center")

    sw_x, sw_w, sw_h = 0.6, 0.82, 0.52                     # class swatch geometry
    name_x = 1.6

    def row(y, code):
        fill = C10[code]
        ax.add_patch(Rectangle((sw_x, y - sw_h / 2), sw_w, sw_h, facecolor=fill,
                               edgecolor="0.3", linewidth=0.6))
        ax.text(sw_x + sw_w / 2, y, str(code), ha="center", va="center", fontsize=9,
                fontweight="bold", color=text_color(fill))
        ax.text(name_x, y, NAME10[code], ha="left", va="center", fontsize=11)

    # stable block
    ax.text(sw_x, 9.55, "No-change (stable)", fontsize=9.5, style="italic", color="0.35")
    ys_stable = [9.0 - i * 0.72 for i in range(len(STABLE))]
    for y, code in zip(ys_stable, STABLE):
        row(y, code)
    # change block
    change_top = ys_stable[-1] - 1.3
    ax.text(sw_x, change_top + 0.62, "Change (disturbance)", fontsize=9.5, style="italic", color="0.35")
    ys_change = [change_top - i * 0.72 for i in range(len(CHANGE))]
    for y, code in zip(ys_change, CHANGE):
        row(y, code)

    # 5-class boxes on the right
    box_l, box_w = 9.0, 2.2
    def box(y, h, label, fill):
        ax.add_patch(Rectangle((box_l, y - h / 2), box_w, h, facecolor=fill,
                               edgecolor="0.3", linewidth=0.8))
        ax.text(box_l + box_w / 2, y, label, ha="center", va="center", fontsize=11,
                fontweight="bold", color=text_color(fill))

    stable_mid = (ys_stable[0] + ys_stable[-1]) / 2
    stable_h = (ys_stable[0] - ys_stable[-1]) + sw_h + 0.25
    ax.add_patch(Rectangle((box_l, stable_mid - stable_h / 2), box_w, stable_h,
                           facecolor=C5["Stable"], edgecolor="0.3", linewidth=0.8))
    ax.text(box_l + box_w / 2, stable_mid + 0.22, "Stable", ha="center", va="center",
            fontsize=12, fontweight="bold", color=text_color(C5["Stable"]))
    ax.text(box_l + box_w / 2, stable_mid - 0.3, "6 no-change classes", ha="center", va="center",
            fontsize=8.5, color="0.25")
    for y, code in zip(ys_change, CHANGE):
        box(y, sw_h + 0.18, NAME10[code], C5[NAME10[code]])

    # connectors: the six stable rows converge to the Stable box, change rows map one to one
    bus_x = 7.6
    for y in ys_stable:
        ax.plot([6.2, bus_x], [y, stable_mid], color="0.6", linewidth=0.7, zorder=1)
    ax.add_patch(FancyArrowPatch((bus_x, stable_mid), (box_l - 0.03, stable_mid),
                                 arrowstyle="-|>", mutation_scale=11, color="0.4", linewidth=1.0))
    for y in ys_change:
        ax.add_patch(FancyArrowPatch((6.2, y), (box_l - 0.03, y), arrowstyle="-|>",
                                     mutation_scale=11, color="0.4", linewidth=1.0))

    ax.text(6.0, 0.35, "Class code shown in each swatch. The 5-class collapse folds the six stable "
            "classes into Stable and keeps the four change classes.", ha="center", va="center",
            fontsize=7.5, color="0.4")

    fig.tight_layout()
    png = f"{OUT}/figure_class_schema.png"
    pdf = f"{OUT}/figure_class_schema.pdf"
    fig.savefig(png, dpi=300, bbox_inches="tight")
    fig.savefig(pdf, bbox_inches="tight")
    plt.close(fig)
    print(f"wrote {png} and {pdf}")


if __name__ == "__main__":
    main()
