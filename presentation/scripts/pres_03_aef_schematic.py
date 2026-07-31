#!/usr/bin/env python3
"""pres_03_aef_schematic: AlphaEarth inputs, training targets, and output (input/target split).

Left-to-right schematic in three registers. Register 1 is the three sources required at inference
(Sentinel-2 L1C, Landsat-8/9 L1C, Sentinel-1 GRD), drawn as solid boxes; these three are also training
targets, which is noted. Register 2 is the eight training-target-only sources from Table S1, grouped by
measurement type (radar, terrain and structure, climate and gravity, land cover, and text), drawn as
outlined boxes. Register 3 is the output, a 64-dimensional embedding per 10 m pixel, one per year,
constrained to the unit sphere. Solid versus outlined boxes make the inference/training split, the main
teaching point, unmistakable. A single sources-to-model-to-output arrow carries the flow, with a note
that only the input sources are read at inference, so no per-source arrow crosses another register.

Source of truth: the AlphaEarth Foundations paper (Brown et al. 2025). The user named
presentation/assets/alphaearth_paper.pdf (a zip of page images with OCR sidecars), but that file is not
in the repo; presentation/assets/alphaearth.pdf is the same paper as a genuine PDF and was read
directly. Table S1 (page 20) gives the eleven sources and their input-versus-target usage. The spatial
frame (1.28 x 1.28 km, 128 x 128 px at 10 m) is stated verbatim on page 24. The support period ("the
range of the input timestamps") and the valid period ("a temporal summary over [ts, te) that need not
fully intersect the support period", permitting interpolation and extrapolation) are defined on pages
3 and 4. The "at most one year" bound on the support period could not be confirmed from the OCR (page 24
says training frames were not limited in length), so it is deliberately left off; see the message.

Text is kept as text (pdf.fonttype 42), not converted to paths. No gradients, shadows, or icons.

sizing: 13.33 x 7.5 in, a full-bleed 16:9 slide, given the density (eleven source boxes plus callouts
and a timeline inset).

outputs (PNG only for the Google Slides deck):
  presentation/figures/pres_03_aef_schematic.png
"""

import os

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch, FancyArrowPatch, Rectangle

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
OUT = os.path.join(ROOT, "presentation", "figures")

# full Table S1 as read from page 20 (type, dataset, product, bands, usage). printed for checking
TABLE_S1 = [
    ("Optical", "Sentinel-2", "L1C", "B2, B3, B4, B8, B11", "input, target"),
    ("Optical, Thermal", "Landsat-8/9", "L1C", "B2-B6, B8 (pan), B10 (thermal)", "input, target"),
    ("C-band SAR", "Sentinel-1A/1B", "GRD", "VV, VH, HH, HV, angle", "input, target"),
    ("L-band SAR", "ALOS PALSAR ScanSAR", "Level 2.2", "HH, HV, lin", "target"),
    ("Elevation", "Copernicus DEM", "GLO-30", "DEM (elevation)", "target"),
    ("LiDAR", "GEDI", "L2A", "relative height metrics (rh*)", "target"),
    ("Climate", "ERA5-Land", "Monthly aggregates", "precip, temp, dewpoint, pressure", "target"),
    ("Gravity", "GRACE", "Monthly mass grids", "equivalent liquid water thickness", "target"),
    ("Land cover", "NLCD", "2019, 2021", "land cover", "target"),
    ("Text", "Wikipedia", "geocoded articles", "text embeddings", "target"),
    ("Text", "GBIF", "research-grade observations", "text embeddings (class/genus/species)", "target"),
]

# register 1: sources required at inference (and also targets). solid, colorblind-safe fills
INPUTS = [
    ("Sentinel-2 L1C", "optical", "#0072B2"),
    ("Landsat-8/9 L1C", "optical + thermal", "#8C5A2B"),
    ("Sentinel-1 GRD", "C-band SAR", "#2C7A73"),
]
# register 2: training-target-only sources, grouped by measurement type. outlined boxes.
# laid out in two sub-columns to keep the block compact
TARGETS_A = [
    ("Radar", [("ALOS PALSAR", "L-band SAR")]),
    ("Terrain & structure", [("Copernicus DEM", "elevation"), ("GEDI L2A", "LiDAR")]),
    ("Climate & gravity", [("ERA5-Land", "climate"), ("GRACE", "gravity")]),
]
TARGETS_B = [
    ("Land cover", [("NLCD", "land cover")]),
    ("Text", [("Wikipedia", "text"), ("GBIF", "text")]),
]
TARGET_EDGE = "#555555"
OUT_EDGE = "#7B5EA7"
OUT_FILL = "#ECE7F3"


def _fit_size(ax, renderer, text, max_w_frac, sizes, weight="normal"):
    ax_w = ax.get_window_extent(renderer).width
    for s in sizes:
        t = ax.text(0.5, 0.5, text, fontsize=s, fontweight=weight)
        w = t.get_window_extent(renderer).width / ax_w
        t.remove()
        if w <= max_w_frac:
            return s
    return sizes[-1]


def _arrow(ax, x0, y0, x1, y1, color="#333333", lw=2.6, style="-|>"):
    ax.add_patch(FancyArrowPatch((x0, y0), (x1, y1), arrowstyle=style, mutation_scale=20,
                                 lw=lw, color=color, shrinkA=2, shrinkB=2, zorder=2))


def _print_sources():
    print("Table S1 sources extracted (page 20 of the paper):")
    print(f"  {'type':<17}{'dataset':<22}{'product':<20}{'usage'}")
    for typ, ds, prod, _bands, usage in TABLE_S1:
        print(f"  {typ:<17}{ds:<22}{prod:<20}{usage}")
    n_input = sum(1 for r in TABLE_S1 if "input" in r[4])
    print(f"  ({len(TABLE_S1)} sources total: {n_input} are inputs+targets, "
          f"{len(TABLE_S1) - n_input} are targets only)")


def _draw_target_subcolumn(ax, renderer, x, top_y, w, groups):
    # draw type-grouped outlined boxes flowing downward, return the y of the lowest box bottom.
    # taller boxes with tighter gaps keep the column the same height while giving the two text
    # lines clear margins from the box borders
    tbh, gap, lab, ggap = 0.072, 0.010, 0.032, 0.020
    y = top_y
    low = top_y
    for gname, boxes in groups:
        ax.text(x, y, gname, fontsize=13.5, fontweight="bold", color=TARGET_EDGE, va="top")
        y -= lab
        for name, modality in boxes:
            ax.add_patch(FancyBboxPatch((x, y - tbh), w, tbh, boxstyle="round,pad=0.003,rounding_size=0.01",
                                        linewidth=1.8, edgecolor=TARGET_EDGE, facecolor="white", zorder=3))
            ns = _fit_size(ax, renderer, name, w - 0.018, [15, 14.5, 14, 13.5], weight="bold")
            ax.text(x + 0.011, y - 0.025, name, fontsize=ns, fontweight="bold", color="0.1", va="center")
            ax.text(x + 0.011, y - 0.051, modality, fontsize=12.5, color="0.35", va="center")
            low = y - tbh
            y -= tbh + gap
        y -= ggap
    return low


def main():
    _print_sources()

    plt.rcParams.update({
        "font.family": "sans-serif",
        "font.sans-serif": ["Helvetica", "Arial", "DejaVu Sans"],
        "font.size": 15,
        "pdf.fonttype": 42,   # keep text as text (embedded TrueType), not paths
        "ps.fonttype": 42,
    })

    fig, ax = plt.subplots(figsize=(13.33, 7.5))
    ax.set_xlim(0, 1)
    ax.set_ylim(0, 1)
    ax.axis("off")
    fig.canvas.draw()
    renderer = fig.canvas.get_renderer()

    ax.text(0.5, 0.975, "AlphaEarth: Inference Inputs Versus Training Targets",
            ha="center", va="top", fontsize=22, fontweight="bold")

    # ---- register 1: inputs (solid) ----
    c1x, c1w = 0.015, 0.185
    ax.text(c1x, 0.905, "Required at inference", fontsize=15, fontweight="bold", color="0.1")
    ax.text(c1x, 0.878, "(the 3 inputs are also targets)", fontsize=12.5, color="0.35", style="italic")
    bh = 0.12
    for (name, modality, color), yc in zip(INPUTS, [0.78, 0.625, 0.47]):
        ax.add_patch(FancyBboxPatch((c1x, yc - bh / 2), c1w, bh, boxstyle="round,pad=0.004,rounding_size=0.012",
                                    linewidth=0, facecolor=color, zorder=3))
        ns = _fit_size(ax, renderer, name, c1w - 0.02, [16, 15, 14.5, 14], weight="bold")
        ax.text(c1x + 0.012, yc + 0.022, name, fontsize=ns, fontweight="bold", color="white", va="center")
        ax.text(c1x + 0.012, yc - 0.026, modality, fontsize=13, color="white", va="center")

    # ---- register 2: training targets (outlined), two sub-columns with a clear gap ----
    ax.text(0.245, 0.905, "Training targets only", fontsize=15, fontweight="bold", color="0.1")
    _draw_target_subcolumn(ax, renderer, 0.245, 0.855, 0.14, TARGETS_A)
    _draw_target_subcolumn(ax, renderer, 0.455, 0.855, 0.13, TARGETS_B)
    block_right = 0.455 + 0.13

    # ---- model band and the single sources -> model -> output flow ----
    mx, mw, mc, mh = 0.60, 0.13, 0.63, 0.20
    ax.add_patch(FancyBboxPatch((mx, mc - mh / 2), mw, mh, boxstyle="round,pad=0.006,rounding_size=0.02",
                                linewidth=2.2, edgecolor="0.2", facecolor="#f2f2f2", zorder=3))
    model_label = "AlphaEarth\nFoundations\nmodel"   # 3 lines so the widest word fits the narrow box
    msize = _fit_size(ax, renderer, model_label, mw - 0.03, [17, 16, 15, 14, 13], weight="bold")
    ax.text(mx + mw / 2, mc, model_label, ha="center", va="center",
            fontsize=msize, fontweight="bold", color="0.1")
    _arrow(ax, block_right + 0.008, mc, mx, mc)
    ax.text(mx + mw / 2, mc - mh / 2 - 0.02, "at inference: input sources only", ha="center", va="top",
            fontsize=12.5, color="0.35")

    # ---- register 3: output ----
    ocx = 0.85
    ax.text(ocx, 0.905, "Output", fontsize=15, fontweight="bold", color="0.1")
    _arrow(ax, mx + mw, mc, ocx - 0.05, mc)
    side = 0.30
    w, h = side / 13.33, side / 7.5
    s = 0.05
    for off in [2, 1, 0, -2, -3]:
        yc = mc + off * s
        ax.add_patch(Rectangle((ocx - w / 2, yc - h / 2), w, h, linewidth=1.6,
                               edgecolor=OUT_EDGE, facecolor=OUT_FILL, zorder=4))
    for dy in (-0.014, 0.0, 0.014):
        ax.plot(ocx, mc - s + dy, marker="o", ms=3, color=OUT_EDGE, zorder=4)
    top = mc + 2 * s + h / 2
    bot = mc - 3 * s - h / 2
    ax.annotate("", xy=(ocx + w / 2 + 0.02, top), xytext=(ocx + w / 2 + 0.02, bot),
                arrowprops=dict(arrowstyle="<->", color=OUT_EDGE, lw=1.5))
    ax.text(ocx + w / 2 + 0.03, mc, "64\ndims", ha="left", va="center", fontsize=14,
            fontweight="bold", color=OUT_EDGE)
    ax.text(ocx, bot - 0.02, "64-D embedding, per 10 m pixel,\none per year, on the unit sphere",
            ha="center", va="top", fontsize=13.5, color="0.1")

    # ---- callouts (not boxes), bottom-left ----
    for i, line in enumerate([
        "Spatial frame: 1.28 x 1.28 km  (128 x 128 px at 10 m)",
        "Support period: the range of the input timestamps",
        "Valid period: the summarized window; it need not intersect the",
        "support period, allowing interpolation and extrapolation",
    ]):
        ax.text(0.015, 0.27 - i * 0.05, line, fontsize=14, color="0.15", va="top")

    # ---- timeline inset (bottom-right): support and valid periods overlap only partially ----
    tlx0, tlx1 = 0.62, 0.99
    def _t(u):
        return tlx0 + (tlx1 - tlx0) * u
    ax.text(_t(0.0), 0.35, "Support vs valid period (they can differ)", fontsize=13.5,
            fontweight="bold", color="0.2", va="top")
    axis_y = 0.14
    ax.plot([_t(0.02), _t(0.96)], [axis_y, axis_y], color="0.6", lw=1.2, zorder=2)
    ax.annotate("", xy=(_t(1.0), axis_y), xytext=(_t(0.96), axis_y),
                arrowprops=dict(arrowstyle="-|>", color="0.6", lw=1.2))
    ax.text(_t(1.0), axis_y - 0.028, "time", fontsize=12.5, color="0.6", ha="right", va="top")
    ax.add_patch(Rectangle((_t(0.06), axis_y + 0.03), _t(0.52) - _t(0.06), 0.035, facecolor="#0072B2",
                           edgecolor="none", zorder=3))
    ax.text(_t(0.06), axis_y + 0.075, "support (input timestamps)", fontsize=12.5, color="#0072B2", va="bottom")
    ax.add_patch(Rectangle((_t(0.4), axis_y - 0.065), _t(0.88) - _t(0.4), 0.035, facecolor="#7B5EA7",
                           edgecolor="none", zorder=3))
    ax.text(_t(0.88), axis_y - 0.07, "valid (summarized)", fontsize=12.5, color="#7B5EA7", va="top", ha="right")
    ax.annotate("", xy=(_t(0.88), axis_y - 0.012), xytext=(_t(0.52), axis_y - 0.012),
                arrowprops=dict(arrowstyle="<->", color="0.4", lw=1.0))
    ax.text(_t(0.7), axis_y + 0.006, "outside support", fontsize=11.5, color="0.4", ha="center", va="bottom")

    os.makedirs(OUT, exist_ok=True)
    fig.savefig(os.path.join(OUT, "pres_03_aef_schematic.png"), dpi=300, bbox_inches="tight")
    plt.close(fig)
    print("\nwrote pres_03_aef_schematic.png")


if __name__ == "__main__":
    main()
