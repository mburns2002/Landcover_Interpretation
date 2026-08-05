#!/usr/bin/env python3
"""pres_11_workflow_simple_v2: colored four-stage workflow, with a classified land-cover map.

New version of the colored workflow diagram (pres_11_workflow_simple_colored). Same four columns left to
right (Reference, Features, Classification, Evaluation) and the same single fork at Features, but:
  - Reference drops the "wall-to-wall labels" line.
  - Features / embeddings reads "two-date AlphaEarth 2018, 2020".
  - Features / spectral reads "Spectral composite" over "Sentinel-2, Landsat 8, Sentinel-1 bands +
    indices" (the "about 50 bands" line is gone).
  - Classification shows a small classified land-cover map under the Random Forest box, drawn like the
    one in pres_16_spectral_baseline but with a different (illustrative) pixel pattern.

Geometry follows the original: fixed canvas, text fit inside each box (body 13 pt, labels 20 pt).

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
STAGE_FILL, STAGE_EDGE = "white", "#333333"
ARROW = "#333333"
CONTROL = "#0072B2"
# soft, clearly distinct per-stage tints for the colored variant (single-box stages)
STAGE_COLORS = {"Reference": ("#dcefe1", "#4e9e72"),        # green
                "Classification": ("#f4e0ea", "#b56a92"),   # rose
                "Evaluation": ("#dfe6ef", "#647a9e")}        # steel blue

# illustrative land-cover classes for the classified-map icon (not real values); different pixels than pres_16
LC_COLORS = ["#2e7d32", "#e6c229", "#2f6fb0", "#8a8f98", "#8bc34a", "#4db6ac"]
LC_PATTERN = np.random.default_rng(11).integers(0, len(LC_COLORS), size=(10, 10)).tolist()

FIG_W, FIG_H = 12.0, 6.8
WB, PAD_X, GAP, MARGIN = 2.5, 0.24, 0.47, 0.28     # box width, side pad, inter-stage gap, margin (in)
LH, VPAD = 0.34, 0.22                               # line height, box vertical pad (in)
LABEL_FS, DETAIL_FS, CTRL_FS = 20, 13, 12
MAP_SZ, MAP_GAP, CAP_GAP = 1.0, 0.16, 0.12          # classified-map icon size and gaps (in)
DIM = {"Classification", "Evaluation"}
INNER = WB - 2 * PAD_X
CTRL_LINES = []

STAGES = [
    {"label": "Reference", "phrases": ["GLKN change polygons", "NAIP, two dates"]},
    {"label": "Features", "branches": [
        {"fill": EMB_FILL, "edge": EMB_EDGE, "phrases": ["two-date AlphaEarth 2018, 2020",
                                                         "5 embedding configurations"]},
        {"fill": SPEC_FILL, "edge": SPEC_EDGE, "phrases": ["Spectral composite",
                                                          "Sentinel-2, Landsat 8, Sentinel-1 bands + indices"]},
    ]},
    {"label": "Classification", "phrases": ["Random Forest, 300 trees"]},
    {"label": "Evaluation", "phrases": ["spatial structure,", "accuracy, 10 and 5 class"]},
]
CTRL_TEXT = "identical across all configurations"
CAP_LINES = ["classified", "land-cover map"]


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
        else:
            s["_lines"] = box_lines(s["phrases"])
    CTRL_LINES[:] = _wrap(fig, r, CTRL_TEXT, INNER, CTRL_FS)[0]
    plt.close(fig)
    return overflow


def _h(n):
    return n * LH + 2 * VPAD


def _box(ax, cx, top, lines, fill, edge, alpha, lw=2.4):
    h = _h(len(lines))
    ax.add_patch(FancyBboxPatch((cx - WB / 2, top - h), WB, h,
                                boxstyle="round,pad=0.015,rounding_size=0.07", facecolor=fill,
                                edgecolor=edge, linewidth=lw, zorder=3, alpha=alpha))
    ax.text(cx, top - h / 2, "\n".join(lines), ha="center", va="center", fontsize=DETAIL_FS,
            color="0.1", zorder=4, alpha=alpha, linespacing=1.4)


def _map(ax, cx, cy, size, alpha):
    """Classified land-cover map icon: a grid of illustrative class colors, with a caption below."""
    n = len(LC_PATTERN)
    cs = size / n
    x0, y0 = cx - size / 2, cy - size / 2
    for i in range(n):
        for j in range(n):
            ax.add_patch(Rectangle((x0 + j * cs, y0 + (n - 1 - i) * cs), cs, cs,
                                   facecolor=LC_COLORS[LC_PATTERN[i][j]], edgecolor="none",
                                   zorder=3, alpha=alpha))
    ax.add_patch(Rectangle((x0, y0), size, size, fill=False, edgecolor="#333333", linewidth=1.8,
                           zorder=4, alpha=alpha))
    ax.text(cx, y0 - CAP_GAP, "\n".join(CAP_LINES), ha="center", va="top", fontsize=DETAIL_FS,
            color="0.1", zorder=4, alpha=alpha, linespacing=1.3)


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
    cx = [MARGIN + WB / 2 + i * (WB + GAP) for i in range(len(STAGES))]
    kf = next(i for i, s in enumerate(STAGES) if "branches" in s)     # fork column index
    he = _h(len(STAGES[kf]["branches"][0]["_lines"]))
    hs = _h(len(STAGES[kf]["branches"][1]["_lines"]))
    h_class = _h(len(STAGES[kf + 1]["_lines"]))
    cap_h = _h(len(CAP_LINES)) - 2 * VPAD + 0.10                       # caption block height (no box pad)
    sep = 0.55

    emb_cy = sep / 2 + he / 2
    spec_cy = -sep / 2 - hs / 2
    top_y = h_class / 2
    # classified-map icon under the Classification box, then the control annotation under the map
    map_top = top_y - h_class - MAP_GAP
    map_cy = map_top - MAP_SZ / 2
    ctrl_top = map_top - MAP_SZ - cap_h - 0.16               # control annotation sits under the map + caption
    ctrl_bot = ctrl_top - _h(len(CTRL_LINES))
    tops = [top_y + 0.12 + 0.3, emb_cy + he / 2 + 0.12 + 0.3]
    bots = [top_y - _h(len(STAGES[0]["_lines"])), spec_cy - hs / 2, ctrl_bot]
    ya = FIG_H / 2 - (max(tops) + min(bots)) / 2

    fig, ax = plt.subplots(figsize=(FIG_W, FIG_H))
    ax.set_xlim(0, FIG_W)
    ax.set_ylim(0, FIG_H)
    ax.axis("off")

    def a(label):
        return 0.25 if (dim and label in DIM) else 1.0

    for i, s in enumerate(STAGES):
        al = a(s["label"])
        if "branches" in s:
            _box(ax, cx[i], ya + emb_cy + he / 2, s["branches"][0]["_lines"],
                 s["branches"][0]["fill"], s["branches"][0]["edge"], al)
            _box(ax, cx[i], ya + spec_cy + hs / 2, s["branches"][1]["_lines"],
                 s["branches"][1]["fill"], s["branches"][1]["edge"], al)
            _label(ax, cx[i], ya + emb_cy + he / 2 + 0.12, s["label"], al)
        else:
            fill, edge = STAGE_COLORS.get(s["label"], (STAGE_FILL, STAGE_EDGE)) if colored \
                else (STAGE_FILL, STAGE_EDGE)
            _box(ax, cx[i], ya + top_y, s["_lines"], fill, edge, al)
            _label(ax, cx[i], ya + top_y + 0.12, s["label"], al)

    ca = ya
    up, lo = ya + emb_cy, ya + spec_cy
    b0r = cx[kf - 1] + WB / 2
    b1l, b1r = cx[kf] - WB / 2, cx[kf] + WB / 2
    b2l = cx[kf + 1] - WB / 2
    xf, xm = (b0r + b1l) / 2, (b1r + b2l) / 2
    am = a(STAGES[kf + 1]["label"])   # merge is revealed with Classification

    # classified land-cover map under the Classification box
    _map(ax, cx[kf + 1], ya + map_cy, MAP_SZ, am)

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
    # remaining single-chain arrow (Classification -> Evaluation)
    _arrow(ax, (cx[kf + 1] + WB / 2, ca), (cx[kf + 2] - WB / 2, ca), a(STAGES[kf + 2]["label"]))

    ax.text(cx[kf + 1], ya + ctrl_top, "\n".join(CTRL_LINES), ha="center", va="top",
            fontsize=CTRL_FS, style="italic", color=CONTROL, alpha=am, zorder=4, linespacing=1.3)

    return fig, ya + max(tops), ya + min(bots)


def main():
    overflow = _wrap_all()
    print("wrapped box text (each phrase whole, wrapped inside its box):")
    for s in STAGES:
        if "branches" in s:
            print(f"  Features, embeddings: {s['branches'][0]['_lines']}")
            print(f"  Features, spectral:   {s['branches'][1]['_lines']}")
        else:
            print(f"  {s['label']}: {s['_lines']}")
    print(f"  merge annotation (italic): {CTRL_TEXT}")
    if overflow:
        print("  WARN word wider than box:", overflow)

    os.makedirs(OUT, exist_ok=True)
    fig, top_e, bot_e = draw(dim=False, colored=True)     # colored-box variant with classified map, png only
    fig.savefig(f"{OUT}/pres_11_workflow_simple_colored_v2.png", dpi=300, bbox_inches="tight")
    plt.close(fig)

    print(f"canvas {FIG_W:.0f} x {FIG_H:.1f} in; content spans y [{bot_e:.2f}, {top_e:.2f}] of {FIG_H}")
    print("  DOES NOT FIT height" if (bot_e < 0.1 or top_e > FIG_H - 0.1)
          else f"  fits at {DETAIL_FS} pt body, {LABEL_FS} pt labels on the fixed {FIG_W:.0f} x {FIG_H:.1f} in canvas.")
    print("wrote pres_11_workflow_simple_colored_v2.png")


if __name__ == "__main__":
    main()
