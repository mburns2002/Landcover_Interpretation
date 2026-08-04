#!/usr/bin/env python3
"""pres_16_spectral_baseline: the spectral baseline is a matched control.

Makes the experimental control visible: both feature families start from the SAME three sensors, so the
comparison varies representation while holding input information constant. This is a zoom on the feature
fork that pres_11 shows at low detail; unlike pres_11 (which lists the sensors only inside the spectral
branch), here the three sensors are a shared upstream column that forks into both representations.

Layout, left to right:
  three sensor boxes on a shared bus: Sentinel-2, Landsat 8, Sentinel-1
  fork into two branches: AlphaEarth embeddings (64 numbers/pixel) and Spectral composites (50 bands)
  both branches remerge into: Random Forest, 300 trees
Fork annotation "same inputs, different representation" is styled like pres_11's italic-blue
"identical across all configurations" control annotation.

Band count: 50 bands is the repo's stated count for the spectral composite (Methods draft,
reports/spectral_composite_classified_maps/note.md, scripts/build_spectral_confusion.py); the composite
is built in Earth Engine so there is no per-band manifest in the repo to enumerate.

Styling matches pres_03 / pres_11 (rounded FancyBboxPatch, #333333 arrows, blue/amber branch colors,
DejaVu font). Output (PNG only for the Google Slides deck): presentation/figures/pres_16_spectral_baseline.png
"""

import os

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import FancyArrowPatch, FancyBboxPatch

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
OUT = os.path.join(ROOT, "presentation", "figures")

# palette lifted from pres_11
EMB_FILL, EMB_EDGE = "#cfe3f2", "#0072B2"
SPEC_FILL, SPEC_EDGE = "#f5e6c8", "#c4941f"
STAGE_FILL, STAGE_EDGE = "white", "#333333"
ARROW = "#333333"
CONTROL = "#0072B2"

FIG_W, FIG_H = 12.0, 5.0
LABEL_FS, BODY_FS, CTRL_FS = 20, 16, 13       # stage labels 20, body 16, control annotation 13 (pres_11 style)

# geometry: data units == inches, because main() pins the axes to fill the whole figure (0..12 x 0..5)
SX, SW, SBH, SGAP = 0.5, 2.0, 0.72, 0.16      # sensor column x-left, width, box height, gap
BUS_X = 2.7
FORK_X = 3.05
RX, RW, RBH = 5.5, 2.7, 1.6                    # representation boxes x-left, width, height (2-line title)
MERGE_X = 8.55
FX, FW, FBH = 8.8, 2.8, 1.0                    # random-forest box x-left, width, height
EMB_CY, SPEC_CY, MID = 3.4, 1.45, 2.45
SENSOR_CY = [MID + (SBH + SGAP), MID, MID - (SBH + SGAP)]   # 3.33, 2.45, 1.57
LH = 0.30                                      # line height inside boxes


def _box(ax, x, cy, w, h, fill, edge, title_lines, sub):
    ax.add_patch(FancyBboxPatch((x, cy - h / 2), w, h,
                                boxstyle="round,pad=0.015,rounding_size=0.07", facecolor=fill,
                                edgecolor=edge, linewidth=2.4, zorder=3))
    cx = x + w / 2
    lines = list(title_lines) + ([sub] if sub else [])
    y_top = cy + (len(lines) - 1) * LH / 2
    for i, text in enumerate(lines):
        is_sub = sub and i == len(lines) - 1
        ax.text(cx, y_top - i * LH, text, ha="center", va="center",
                fontsize=BODY_FS if is_sub else LABEL_FS,
                fontweight="normal" if is_sub else "bold",
                color="0.25" if is_sub else "#1a1a1a", zorder=4)


def _line(ax, xs, ys, lw=2.6):
    ax.plot(xs, ys, color=ARROW, lw=lw, zorder=2, solid_capstyle="round", solid_joinstyle="round")


def _arrow(ax, p0, p1, lw=2.6):
    ax.add_patch(FancyArrowPatch(p0, p1, arrowstyle="-|>", mutation_scale=18, color=ARROW,
                                 linewidth=lw, zorder=2, shrinkA=0, shrinkB=1))


def _fit_check(fig, lines):
    """Warn if any 20 pt title line is wider than its box interior (text-must-fit-in-boxes rule)."""
    fig.canvas.draw()
    r = fig.canvas.get_renderer()
    over = []
    for text, w in lines:
        t = fig.text(0, 0, text, fontsize=LABEL_FS, fontweight="bold")
        tw = t.get_window_extent(r).width / fig.dpi
        t.remove()
        if tw > w - 0.3:
            over.append((text, round(tw, 2), round(w - 0.3, 2)))
    return over


def main():
    fig, ax = plt.subplots(figsize=(FIG_W, FIG_H))
    ax.set_xlim(0, FIG_W)
    ax.set_ylim(0, FIG_H)
    ax.axis("off")
    ax.set_position([0, 0, 1, 1])                 # axes fills the figure: 1 data unit == 1 inch

    over = _fit_check(fig, [("AlphaEarth", RW), ("embeddings", RW), ("Spectral", RW),
                            ("composites", RW), ("Random Forest", FW), ("Sentinel-2", SW),
                            ("Landsat 8", SW), ("Sentinel-1", SW)])
    if over:
        print("WARN title line wider than box interior:", over)

    # sensor column on a shared bus
    for name, cy in zip(("Sentinel-2", "Landsat 8", "Sentinel-1"), SENSOR_CY):
        _box(ax, SX, cy, SW, SBH, STAGE_FILL, STAGE_EDGE, [name], None)
        _line(ax, [SX + SW, BUS_X], [cy, cy])                      # stub to the bus
    _line(ax, [BUS_X, BUS_X], [SENSOR_CY[2], SENSOR_CY[0]])        # vertical bus
    _line(ax, [BUS_X, FORK_X], [MID, MID])                        # shared trunk

    # fork into the two representations
    _line(ax, [FORK_X, FORK_X], [SPEC_CY, EMB_CY])
    _arrow(ax, (FORK_X, EMB_CY), (RX, EMB_CY))
    _arrow(ax, (FORK_X, SPEC_CY), (RX, SPEC_CY))
    _box(ax, RX, EMB_CY, RW, RBH, EMB_FILL, EMB_EDGE, ["AlphaEarth", "embeddings"],
         "64 numbers per pixel")
    _box(ax, RX, SPEC_CY, RW, RBH, SPEC_FILL, SPEC_EDGE, ["Spectral", "composites"], "50 bands")

    # fork annotation (pres_11 control style: italic, blue)
    ax.text((FORK_X + RX) / 2, MID, "same inputs,\ndifferent representation", ha="center", va="center",
            fontsize=CTRL_FS, style="italic", color=CONTROL, zorder=5, linespacing=1.35)

    # remerge into the classifier
    rep_r = RX + RW
    _line(ax, [rep_r, MERGE_X], [EMB_CY, EMB_CY])
    _line(ax, [rep_r, MERGE_X], [SPEC_CY, SPEC_CY])
    _line(ax, [MERGE_X, MERGE_X], [SPEC_CY, EMB_CY])
    _arrow(ax, (MERGE_X, MID), (FX, MID))
    _box(ax, FX, MID, FW, FBH, STAGE_FILL, STAGE_EDGE, ["Random Forest"], "300 trees")

    os.makedirs(OUT, exist_ok=True)
    fig.savefig(f"{OUT}/pres_16_spectral_baseline.png", dpi=300)
    plt.close(fig)
    print("spectral composite band count used: 50 (repo-stated; no per-band manifest in repo)")
    print("wrote pres_16_spectral_baseline.png")


if __name__ == "__main__":
    main()
