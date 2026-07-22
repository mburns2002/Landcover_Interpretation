#!/usr/bin/env python3
"""Figure 2.2, the study workflow diagram (methods schematic, drawn not plotted).

Four horizontal bands, top to bottom: reference inputs, feature construction, classification, and
evaluation, with boxes connected by directional arrows. The five embedding configurations are shaded
by the baseline-versus-change distinction (the chapter thesis), reusing the Figure 2.3 tones. The
CKIT-RF interpreted cells are marked as validation (dashed) and routed to evaluation, not training.

Run: python scripts/build_workflow_figure.py
Requires: matplotlib
"""

import os
import textwrap

import matplotlib.pyplot as plt
from matplotlib.colors import to_rgb
from matplotlib.patches import FancyArrowPatch, FancyBboxPatch, Rectangle

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = f"{ROOT}/manuscript_formatting/figures"

BASELINE = "#0072B2"                                        # baseline-preserving (matches Figure 2.3)
CHANGE = "#E69F00"                                          # change-only
BASELINE_L = "#cfe3f2"                                      # light fills so labels read
CHANGE_L = "#f7e2b3"
BAND_BG = ["#f4f4f2", "#ffffff", "#f4f4f2", "#ffffff"]      # subtle band tints


def tcolor(fc):
    r, g, b = to_rgb(fc)
    return "white" if (0.299 * r + 0.587 * g + 0.114 * b) < 0.55 else "black"


def box(ax, cx, cy, w, h, text, note=None, fc="white", ec="0.2", ls="solid", fs=8.5, wrap=24, lw=1.2):
    ax.add_patch(FancyBboxPatch((cx - w / 2, cy - h / 2), w, h,
                                boxstyle="round,pad=0.015,rounding_size=0.06", facecolor=fc,
                                edgecolor=ec, linewidth=lw, linestyle=ls, zorder=3))
    t = "\n".join(textwrap.wrap(text, wrap))
    col = tcolor(fc)
    if note:
        ax.text(cx, cy + 0.16 * h, t, ha="center", va="center", fontsize=fs, color=col, zorder=4)
        ax.text(cx, cy - 0.30 * h, "\n".join(textwrap.wrap(note, wrap + 6)), ha="center", va="center",
                fontsize=fs - 1.5, color=col, style="italic", zorder=4)
    else:
        ax.text(cx, cy, t, ha="center", va="center", fontsize=fs, color=col, zorder=4)


def arrow(ax, p1, p2, ls="solid", color="0.35", lw=1.4):
    ax.add_patch(FancyArrowPatch(p1, p2, arrowstyle="-|>", mutation_scale=12, color=color,
                                 linewidth=lw, linestyle=ls, zorder=2, shrinkA=0, shrinkB=0))


def line(ax, xs, ys, color="0.35", lw=1.4, ls="solid"):
    ax.plot(xs, ys, color=color, lw=lw, ls=ls, zorder=2, solid_capstyle="round")


def main():
    os.makedirs(OUT, exist_ok=True)
    plt.rcParams["font.family"] = "DejaVu Sans"
    fig, ax = plt.subplots(figsize=(8.5, 12.0))
    ax.set_xlim(0, 10); ax.set_ylim(0, 14.6); ax.axis("off")

    bands = [(10.55, 14.35, "1", "Reference inputs"),
             (6.75, 10.45, "2", "Feature construction"),
             (4.15, 6.65, "3", "Classification"),
             (0.35, 4.05, "4", "Evaluation")]
    for (y0, y1, num, title), bg in zip(bands, BAND_BG):
        ax.add_patch(Rectangle((0, y0), 10, y1 - y0, facecolor=bg, edgecolor="none", zorder=0))
        ax.text(0.12, y1 - 0.18, f"{num}", fontsize=14, fontweight="bold", color="0.45",
                va="top", ha="left")
        ax.text(0.45, y1 - 0.18, title, fontsize=11.5, fontweight="bold", color="0.25",
                va="top", ha="left")

    # ---- band 1: reference inputs ----
    box(ax, 1.95, 13.15, 2.9, 0.85, "GLKN attributed change polygons", wrap=20)
    ax.text(1.95, 12.5, "4 change classes: harvest, development,\ninsect/disease, beaver",
            ha="center", va="top", fontsize=7, style="italic", color="0.4")
    box(ax, 5.0, 13.15, 2.5, 0.85, "NAIP-interpreted stable points", wrap=18)
    ax.text(5.0, 12.5, "6 stable classes", ha="center", va="top", fontsize=7, style="italic",
            color="0.4")
    box(ax, 8.2, 13.15, 3.0, 0.85, "CKIT-RF interpreted cells (wall-to-wall reference)", wrap=24,
        ls=(0, (4, 2)), ec="#117733", lw=1.5)
    ax.text(8.2, 12.5, "validation; design in Ch. 3", ha="center", va="top", fontsize=7,
            style="italic", color="#117733")
    box(ax, 3.45, 11.15, 4.0, 0.9, "Balanced training set: 200 points/class x 10 classes",
        note="deduplicated to one point per 10 m pixel", wrap=30)
    arrow(ax, (1.95, 12.72), (2.85, 11.62))
    arrow(ax, (5.0, 12.72), (4.05, 11.62))

    # ---- band 2: feature construction ----
    ax.text(0.45, 10.0, "features sampled at the training points, which supply the labels",
            fontsize=7.5, style="italic", color="0.4", ha="left", va="top")
    # tiny tone legend, top right of the band
    ax.add_patch(Rectangle((7.0, 10.05), 0.26, 0.18, facecolor=BASELINE_L, edgecolor=BASELINE, lw=1))
    ax.text(7.35, 10.14, "baseline-preserving (v2, v3, v5)", fontsize=7, va="center", ha="left")
    ax.add_patch(Rectangle((7.0, 9.78), 0.26, 0.18, facecolor=CHANGE_L, edgecolor=CHANGE, lw=1))
    ax.text(7.35, 9.87, "change-only (v4, v6)", fontsize=7, va="center", ha="left")

    box(ax, 3.42, 9.35, 3.5, 0.75, "AlphaEarth embeddings (2018, 2020)", wrap=22)
    # bracket over the five configs
    line(ax, [0.83, 0.83, 6.01, 6.01], [8.2, 8.42, 8.42, 8.2], color="0.45", lw=1.1)
    ax.text(3.42, 8.62, "5 embedding configurations", fontsize=8, ha="center", color="0.3")
    arrow(ax, (3.42, 8.97), (3.42, 8.45))
    cfg = [("v2", "baseline\n+ delta", BASELINE_L, BASELINE), ("v3", "stacked\nyears", BASELINE_L, BASELINE),
           ("v4", "delta\nonly", CHANGE_L, CHANGE), ("v5", "baseline\n+ dot", BASELINE_L, BASELINE),
           ("v6", "dot\nonly", CHANGE_L, CHANGE)]
    cfg_cx = [1.3 + i * 1.06 for i in range(5)]
    for cx, (code, desc, fc, ec) in zip(cfg_cx, cfg):
        ax.add_patch(FancyBboxPatch((cx - 0.47, 7.35), 0.94, 0.82,
                                    boxstyle="round,pad=0.01,rounding_size=0.04", facecolor=fc,
                                    edgecolor=ec, linewidth=1.3, zorder=3))
        ax.text(cx, 8.0, code, ha="center", va="center", fontsize=9, fontweight="bold", zorder=4)
        ax.text(cx, 7.6, desc, ha="center", va="center", fontsize=6.6, zorder=4)

    box(ax, 7.95, 9.35, 3.2, 0.75, "Spectral composites (2018, 2020)", wrap=20)
    box(ax, 7.95, 7.75, 3.5, 0.9, "spec_all: S2 + L8 + S1 bands and indices (50 bands)", wrap=24)
    arrow(ax, (7.95, 8.97), (7.95, 8.22))

    # ---- band 3: classification ----
    # convergence bus: five configs plus spec_all drop to a bus, then one arrow into the RF box
    bus_y = 6.5
    line(ax, [1.3, 7.95], [bus_y, bus_y], color="0.45", lw=1.2)
    for cx in cfg_cx:
        line(ax, [cx, cx], [7.33, bus_y], color="0.5", lw=1.0)
    line(ax, [7.95, 7.95], [7.28, bus_y], color="0.5", lw=1.0)
    arrow(ax, (4.1, bus_y), (4.1, 6.24))
    box(ax, 4.1, 5.75, 4.9, 0.92, "Random Forest: 300 trees, fixed across all configurations",
        note="identical classifier isolates the representation effect", wrap=34)
    box(ax, 4.1, 4.55, 4.3, 0.66, "Ten-class classified maps (one per configuration)", wrap=30)
    arrow(ax, (4.1, 5.28), (4.1, 4.9))
    # experiments offshoot (dashed)
    box(ax, 8.35, 5.35, 2.9, 1.15,
        "Experiments: training-cap sensitivity (v2); temporal transferability (v2-v6, 5 brackets "
        "2017-2023)", wrap=26, ls=(0, (4, 2)), ec="0.45")
    arrow(ax, (6.55, 5.6), (6.9, 5.5), ls=(0, (4, 2)), color="0.5")
    # training points feed the RF, skipping band 2, routed down the left margin
    line(ax, [2.0, 0.5, 0.5], [10.7, 10.7, 5.75], color="0.5", lw=1.3)
    arrow(ax, (0.5, 5.75), (1.65, 5.75), color="0.5", lw=1.3)
    ax.text(0.32, 8.2, "training points (labels)", rotation=90, fontsize=7, va="center", ha="center",
            color="0.4")

    # ---- band 4: evaluation ----
    ev_y, ev_h = 1.85, 1.7
    evs = [(1.9, "Accuracy assessment: per-cell confusion matrices; OA, kappa, per-class "
            "PA/UA/F1/IoU (10-class and 5-class collapse)"),
           (5.0, "Spatial coherence: patch size and area-weighted ECDF, Moran's I, neighbor-change"),
           (8.1, "Reliability ceiling: model F1 vs inter-interpreter agreement")]
    for cx, txt in evs:
        box(ax, cx, ev_y, 2.95, ev_h, txt, wrap=26, fs=8.5)
    # distribution bus: classified maps and the validation reference feed all three eval boxes
    dist_y = 3.35
    line(ax, [1.9, 9.82], [dist_y, dist_y], color="0.45", lw=1.2)
    arrow(ax, (4.1, 4.22), (4.1, dist_y + 0.02))                     # classified maps into the bus
    for cx, _ in evs:
        arrow(ax, (cx, dist_y), (cx, ev_y + ev_h / 2 + 0.02))
    # validation reference down the right margin into the bus
    line(ax, [8.2, 9.82, 9.82], [12.72, 12.72, dist_y], color="#117733", lw=1.3, ls=(0, (4, 2)))
    ax.text(9.96, 8.0, "validation reference (CKIT-RF cells)", rotation=90, fontsize=7, va="center",
            ha="center", color="#117733")

    fig.tight_layout()
    png = f"{OUT}/figure_2_2_workflow.png"
    pdf = f"{OUT}/figure_2_2_workflow.pdf"
    fig.savefig(png, dpi=300, bbox_inches="tight")
    fig.savefig(pdf, bbox_inches="tight")
    plt.close(fig)
    print(f"wrote {png} and {pdf}")


if __name__ == "__main__":
    main()
