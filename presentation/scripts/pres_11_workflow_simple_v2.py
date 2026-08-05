#!/usr/bin/env python3
"""pres_11_workflow_simple_v2: colored five-stage workflow with a classified land-cover map box.

New version of the colored workflow diagram (pres_11_workflow_simple_colored). Left to right:
  Reference -> Features (the single fork) -> Classification -> Land-Cover Map -> Evaluation
The classified land-cover map is now its own box in the pipeline: the Random Forest arrow feeds it,
and it in turn feeds Evaluation. The map grid is drawn like the one in pres_16_spectral_baseline but
with a different (illustrative) pixel pattern.

Text differences from the original:
  - Reference drops the "wall-to-wall labels" line.
  - Features / embeddings reads "two-date AlphaEarth".
  - Features / spectral reads "Spectral composite" over "Sentinel-2, Landsat 8, Sentinel-1, bands +
    indices" (the "about 50 bands" line is gone).

Geometry: columns are laid out left to right with per-column widths (the map box is a narrower square),
so text stays fit inside each box (body 13 pt, labels 20 pt).

Output (PNG only for the Google Slides deck):
  pres_11_workflow_simple_colored_v2.png
"""

import os

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

import slide_font
import numpy as np
from matplotlib.patches import FancyBboxPatch, FancyArrowPatch, Rectangle
slide_font.use_spectral()

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
OUT = os.path.join(ROOT, "presentation", "figures")

EMB_FILL, EMB_EDGE = "#cfe3f2", "#0072B2"
SPEC_FILL, SPEC_EDGE = "#f5e6c8", "#c4941f"         # muted amber, complements the embedding blue
MAP_FILL, MAP_EDGE = "#f2f2f4", "#4d4d4d"           # light neutral so the colorful grid pops
ARROW = "#333333"
CONTROL = "#0072B2"
# soft, clearly distinct per-stage tints for the colored variant (single-box stages)
STAGE_COLORS = {"Reference": ("#dcefe1", "#4e9e72"),        # green
                "Classification": ("#f4e0ea", "#b56a92"),   # rose
                "Evaluation": ("#dfe6ef", "#647a9e")}        # steel blue

# illustrative land-cover classes for the classified-map icon (not real values); different pixels than pres_16
LC_COLORS = ["#2e7d32", "#e6c229", "#2f6fb0", "#8a8f98", "#8bc34a", "#4db6ac"]
LC_PATTERN = np.random.default_rng(11).integers(0, len(LC_COLORS), size=(10, 10)).tolist()

WB, MAPB = 2.5, 1.9                                 # text-box width, map-box width (in)
PAD_X, GAP, MARGIN = 0.24, 0.5, 0.3                 # side pad, inter-stage gap, page margin (in)
LH, VPAD = 0.34, 0.22                               # line height, box vertical pad (in)
MAP_BOX_H = 1.6                                     # map-box height (in); grid drawn inside
LABEL_FS, DETAIL_FS, CTRL_FS = 20, 13, 12
LABEL_H = 0.42                                      # approx label height above a box (in)
DIM = {"Classification", "Evaluation"}
INNER = WB - 2 * PAD_X
CTRL_LINES = []

STAGES = [
    {"label": "Reference", "w": WB, "phrases": ["GLKN change polygons", "NAIP, two dates"]},
    {"label": "Features", "w": WB, "branches": [
        {"fill": EMB_FILL, "edge": EMB_EDGE, "phrases": ["two-date AlphaEarth",
                                                         "5 embedding configurations"]},
        {"fill": SPEC_FILL, "edge": SPEC_EDGE, "phrases": ["Spectral composite",
                                                          "Sentinel-2, Landsat 8, Sentinel-1, bands + indices"]},
    ]},
    {"label": "Classification", "w": WB, "phrases": ["Random Forest, 300 trees"]},
    {"label": "Land-Cover Map", "w": MAPB, "map": True},
    {"label": "Evaluation", "w": WB, "phrases": ["spatial structure,", "accuracy, 10 and 5 class"]},
]
CTRL_TEXT = "identical across all configurations"

WIDTHS = [s["w"] for s in STAGES]
FIG_W = 2 * MARGIN + sum(WIDTHS) + GAP * (len(STAGES) - 1)
FIG_H = 5.2


def _tw(fig, r, s, fs):
    t = fig.text(0, 0, s, fontsize=fs)
    w = t.get_window_extent(r).width / fig.dpi
    t.remove()
    return w


def _wrap(fig, r, phrase, max_w, fs):
    lines, cur = [], ""
    for word in phrase.split():
        trial = (cur + " " + word).strip()
        if not cur or _tw(fig, r, trial, fs) <= max_w:
            cur = trial
        else:
            lines.append(cur)
            cur = word
    if cur:
        lines.append(cur)
    over = max((_tw(fig, r, ln, fs) for ln in lines), default=0) > max_w + 1e-6
    return lines, over


def _wrap_all():
    fig = plt.figure(figsize=(FIG_W, FIG_H))
    fig.canvas.draw()
    r = fig.canvas.get_renderer()
    overflow = []

    def box_lines(phrases):
        out = []
        for p in phrases:
            lines, over = _wrap(fig, r, p, INNER, DETAIL_FS)
            if over:
                overflow.append(p)
            out += lines
        return out

    for s in STAGES:
        if "branches" in s:
            for br in s["branches"]:
                br["_lines"] = box_lines(br["phrases"])
        elif "phrases" in s:
            s["_lines"] = box_lines(s["phrases"])
    CTRL_LINES[:] = _wrap(fig, r, CTRL_TEXT, INNER, CTRL_FS)[0]
    plt.close(fig)
    return overflow


def _h(n):
    return n * LH + 2 * VPAD


def _box(ax, cx, cyc, lines, fill, edge, alpha, w, lw=2.4):
    h = _h(len(lines))
    ax.add_patch(FancyBboxPatch((cx - w / 2, cyc - h / 2), w, h,
                                boxstyle="round,pad=0.015,rounding_size=0.07", facecolor=fill,
                                edgecolor=edge, linewidth=lw, zorder=3, alpha=alpha))
    ax.text(cx, cyc, "\n".join(lines), ha="center", va="center", fontsize=DETAIL_FS,
            color="0.1", zorder=4, alpha=alpha, linespacing=1.4)


def _mapbox(ax, cx, cyc, w, h, alpha):
    """A pipeline box whose content is a classified land-cover map (grid of illustrative class colors)."""
    ax.add_patch(FancyBboxPatch((cx - w / 2, cyc - h / 2), w, h,
                                boxstyle="round,pad=0.015,rounding_size=0.07", facecolor=MAP_FILL,
                                edgecolor=MAP_EDGE, linewidth=2.4, zorder=3, alpha=alpha))
    n = len(LC_PATTERN)
    g = min(w - 0.4, h - 0.4)
    cs = g / n
    x0, y0 = cx - g / 2, cyc - g / 2
    for i in range(n):
        for j in range(n):
            ax.add_patch(Rectangle((x0 + j * cs, y0 + (n - 1 - i) * cs), cs, cs,
                                   facecolor=LC_COLORS[LC_PATTERN[i][j]], edgecolor="none",
                                   zorder=4, alpha=alpha))
    ax.add_patch(Rectangle((x0, y0), g, g, fill=False, edgecolor="#333333", linewidth=1.4,
                           zorder=5, alpha=alpha))


def _label(ax, cx, y, text, alpha):
    ax.text(cx, y, text, ha="center", va="bottom", fontsize=LABEL_FS, fontweight="bold",
            color="#1a1a1a", zorder=4, alpha=alpha)


def _line(ax, xs, ys, alpha, lw=2.6):
    ax.plot(xs, ys, color=ARROW, lw=lw, alpha=alpha, zorder=2, solid_capstyle="round",
            solid_joinstyle="round")


def _arrow(ax, p1, p2, alpha, lw=2.6):
    ax.add_patch(FancyArrowPatch(p1, p2, arrowstyle="-|>", mutation_scale=18, color=ARROW,
                                 linewidth=lw, zorder=2, shrinkA=0, shrinkB=1, alpha=alpha))


def draw(dim=False, colored=True):
    # column centers from per-column widths
    xs, x = [], MARGIN
    for w in WIDTHS:
        xs.append(x + w / 2)
        x += w + GAP
    kf = next(i for i, s in enumerate(STAGES) if "branches" in s)     # fork column index

    he = _h(len(STAGES[kf]["branches"][0]["_lines"]))
    hs = _h(len(STAGES[kf]["branches"][1]["_lines"]))
    h_class = _h(len(STAGES[kf + 1]["_lines"]))
    sep = 0.55
    emb_cy = sep / 2 + he / 2
    spec_cy = -sep / 2 - hs / 2

    # control annotation sits under the Classification box (blocks stay centered on the arrow line)
    ctrl_top = -h_class / 2 - 0.16
    ctrl_bot = ctrl_top - len(CTRL_LINES) * LH

    def box_h(s):
        return MAP_BOX_H if s.get("map") else _h(len(s["_lines"]))

    tops, bots = [], [ctrl_bot]
    for i, s in enumerate(STAGES):
        if "branches" in s:
            tops.append(emb_cy + he / 2 + 0.12 + LABEL_H)
            bots.append(spec_cy - hs / 2)
        else:
            tops.append(box_h(s) / 2 + 0.12 + LABEL_H)
            bots.append(-box_h(s) / 2)
    ya = FIG_H / 2 - (max(tops) + min(bots)) / 2

    fig, ax = plt.subplots(figsize=(FIG_W, FIG_H))
    ax.set_xlim(0, FIG_W)
    ax.set_ylim(0, FIG_H)
    ax.axis("off")

    def a(label):
        return 0.25 if (dim and label in DIM) else 1.0

    for i, s in enumerate(STAGES):
        al, w = a(s["label"]), WIDTHS[i]
        if "branches" in s:
            _box(ax, xs[i], ya + emb_cy, s["branches"][0]["_lines"],
                 s["branches"][0]["fill"], s["branches"][0]["edge"], al, w)
            _box(ax, xs[i], ya + spec_cy, s["branches"][1]["_lines"],
                 s["branches"][1]["fill"], s["branches"][1]["edge"], al, w)
            _label(ax, xs[i], ya + emb_cy + he / 2 + 0.12, s["label"], al)
        elif s.get("map"):
            _mapbox(ax, xs[i], ya, w, MAP_BOX_H, al)
            _label(ax, xs[i], ya + MAP_BOX_H / 2 + 0.12, s["label"], al)
        else:
            fill, edge = STAGE_COLORS.get(s["label"], ("white", "#333333"))
            h = _h(len(s["_lines"]))
            _box(ax, xs[i], ya, s["_lines"], fill, edge, al, w)
            _label(ax, xs[i], ya + h / 2 + 0.12, s["label"], al)

    ca = ya
    up, lo = ya + emb_cy, ya + spec_cy
    b0r = xs[kf - 1] + WIDTHS[kf - 1] / 2
    b1l, b1r = xs[kf] - WIDTHS[kf] / 2, xs[kf] + WIDTHS[kf] / 2
    b2l = xs[kf + 1] - WIDTHS[kf + 1] / 2
    xf, xm = (b0r + b1l) / 2, (b1r + b2l) / 2
    am = a(STAGES[kf + 1]["label"])   # merge is revealed with Classification

    # fork: Reference into the two feature tracks
    _line(ax, [b0r, xf], [ca, ca], 1.0)
    _line(ax, [xf, xf], [lo, up], 1.0)
    _arrow(ax, (xf, up), (b1l, up), 1.0)
    _arrow(ax, (xf, lo), (b1l, lo), 1.0)
    # merge: the two feature tracks into Classification
    _line(ax, [b1r, xm], [up, up], am)
    _line(ax, [b1r, xm], [lo, lo], am)
    _line(ax, [xm, xm], [lo, up], am)
    _arrow(ax, (xm, ca), (b2l, ca), am)
    # single chain after the merge: Classification -> Land-Cover Map -> Evaluation
    for i in range(kf + 1, len(STAGES) - 1):
        _arrow(ax, (xs[i] + WIDTHS[i] / 2, ca), (xs[i + 1] - WIDTHS[i + 1] / 2, ca),
               a(STAGES[i + 1]["label"]))

    ax.text(xs[kf + 1], ya + ctrl_top, "\n".join(CTRL_LINES), ha="center", va="top",
            fontsize=CTRL_FS, style="italic", color=CONTROL, alpha=am, zorder=4, linespacing=1.3)

    return fig, ya + max(tops), ya + min(bots)


def main():
    overflow = _wrap_all()
    print("wrapped box text (each phrase whole, wrapped inside its box):")
    for s in STAGES:
        if "branches" in s:
            print(f"  Features, embeddings: {s['branches'][0]['_lines']}")
            print(f"  Features, spectral:   {s['branches'][1]['_lines']}")
        elif "phrases" in s:
            print(f"  {s['label']}: {s['_lines']}")
    print(f"  merge annotation (italic): {CTRL_TEXT}")
    if overflow:
        print("  WARN word wider than box:", overflow)

    os.makedirs(OUT, exist_ok=True)
    fig, top_e, bot_e = draw(dim=False, colored=True)     # colored variant with the map box, png only
    fig.savefig(f"{OUT}/pres_11_workflow_simple_colored_v2.png", dpi=300, bbox_inches="tight")
    plt.close(fig)

    print(f"canvas {FIG_W:.2f} x {FIG_H:.1f} in; content spans y [{bot_e:.2f}, {top_e:.2f}] of {FIG_H}")
    print("  DOES NOT FIT height" if (bot_e < 0.1 or top_e > FIG_H - 0.1)
          else f"  fits at {DETAIL_FS} pt body, {LABEL_FS} pt labels on the {FIG_W:.2f} x {FIG_H:.1f} in canvas.")
    print("wrote pres_11_workflow_simple_colored_v2.png")


if __name__ == "__main__":
    main()
