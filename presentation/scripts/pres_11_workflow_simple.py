#!/usr/bin/env python3
"""pres_11_workflow_simple: four-stage workflow for the defense talk, fixed 12 x 5.8 in canvas.

Four columns left to right: Reference, Features, Classification, Evaluation. Reference is the merged
pipeline (GLKN change polygons and NAIP, interpreted to a wall-to-wall labeled reference). Features is
the only fork, two parallel tracks stacked in one column (AlphaEarth embeddings above, spectral
composites below) that open after Reference and remerge into Classification. Colors reuse the
manuscript palette (blue = AlphaEarth embedding family, neutral = spectral composite).

Text: each line is a complete noun phrase; a phrase may wrap onto a second line inside its own box.
The canvas is fixed at 12 x 5.8 in and text is fit inside it, so 16 pt body and 20 pt labels are 16
and 20 at final size (no downstream scaling). The classifier-control claim "identical across all
configurations" is an italic annotation at the merge.

Two outputs:
  pres_11_workflow_simple.png / .pdf          full diagram
  pres_11_workflow_simple_stage3.png          Classification and Evaluation at 25% opacity (two-state build)
"""

import os

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch, FancyArrowPatch

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
OUT = os.path.join(ROOT, "presentation", "figures")

EMB_FILL, EMB_EDGE = "#cfe3f2", "#0072B2"
SPEC_FILL, SPEC_EDGE = "#f5e6c8", "#c4941f"         # muted amber, complements the embedding blue
STAGE_FILL, STAGE_EDGE = "white", "#333333"
ARROW = "#333333"
CONTROL = "#0072B2"
# soft per-stage tints for the colored variant (single-box stages)
STAGE_COLORS = {"Reference": ("#dcefe1", "#4e9e72"),
                "Classification": ("#e6e1f2", "#7b5ea7"),
                "Evaluation": ("#d9ecec", "#3f8f8a")}

FIG_W, FIG_H = 12.0, 5.8
WB, PAD_X, GAP, MARGIN = 2.5, 0.24, 0.47, 0.28     # box width, side pad, inter-stage gap, margin (in)
LH, VPAD = 0.30, 0.22                               # line height, box vertical pad (in)
LABEL_FS, DETAIL_FS, CTRL_FS = 20, 14, 12
DIM = {"Classification", "Evaluation"}
INNER = WB - 2 * PAD_X
CTRL_LINES = []

STAGES = [
    {"label": "Reference", "phrases": ["GLKN change polygons", "NAIP, two dates", "wall-to-wall labels"]},
    {"label": "Features", "branches": [
        {"fill": EMB_FILL, "edge": EMB_EDGE, "phrases": ["AlphaEarth 2018, 2020",
                                                         "5 embedding configurations"]},
        {"fill": SPEC_FILL, "edge": SPEC_EDGE, "phrases": ["spectral composite",
                                                          "Sentinel-2, Landsat 8, Sentinel-1",
                                                          "about 50 bands"]},
    ]},
    {"label": "Classification", "phrases": ["Random Forest, 300 trees"]},
    {"label": "Evaluation", "phrases": ["spatial structure,", "accuracy, 10 and 5 class"]},
]
CTRL_TEXT = "identical across all configurations"


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


def _label(ax, cx, y, text, alpha):
    ax.text(cx, y, text, ha="center", va="bottom", fontsize=LABEL_FS, fontweight="bold",
            color="#1a1a1a", zorder=4, alpha=alpha)


def _line(ax, xs, ys, alpha, lw=2.6):
    ax.plot(xs, ys, color=ARROW, lw=lw, alpha=alpha, zorder=2, solid_capstyle="round",
            solid_joinstyle="round")


def _arrow(ax, p1, p2, alpha, lw=2.6):
    ax.add_patch(FancyArrowPatch(p1, p2, arrowstyle="-|>", mutation_scale=18, color=ARROW,
                                 linewidth=lw, zorder=2, shrinkA=0, shrinkB=1, alpha=alpha))


def draw(dim=False, colored=False):
    cx = [MARGIN + WB / 2 + i * (WB + GAP) for i in range(len(STAGES))]
    kf = next(i for i, s in enumerate(STAGES) if "branches" in s)     # fork column index
    he = _h(len(STAGES[kf]["branches"][0]["_lines"]))
    hs = _h(len(STAGES[kf]["branches"][1]["_lines"]))
    h_class = _h(len(STAGES[kf + 1]["_lines"]))
    sep = 0.55

    emb_cy = sep / 2 + he / 2
    spec_cy = -sep / 2 - hs / 2
    top_y = h_class / 2
    ctrl_top = top_y - h_class - 0.14                        # control annotation sits under Classification
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
    fig, top_e, bot_e = draw(dim=False)
    fig.savefig(f"{OUT}/pres_11_workflow_simple.png", dpi=300, bbox_inches="tight")
    fig.savefig(f"{OUT}/pres_11_workflow_simple.pdf", bbox_inches="tight")
    plt.close(fig)
    fig, _, _ = draw(dim=True)
    fig.savefig(f"{OUT}/pres_11_workflow_simple_stage3.png", dpi=300, bbox_inches="tight")
    plt.close(fig)
    fig, _, _ = draw(dim=False, colored=True)     # colored-box variant, png only
    fig.savefig(f"{OUT}/pres_11_workflow_simple_colored.png", dpi=300, bbox_inches="tight")
    plt.close(fig)

    print(f"canvas 12 x 5.8 in; content spans y [{bot_e:.2f}, {top_e:.2f}] of 5.8")
    print("  DOES NOT FIT height" if (bot_e < 0.1 or top_e > 5.7)
          else f"  fits at {DETAIL_FS} pt body, {LABEL_FS} pt labels on the fixed 12 x 5.8 in canvas.")
    print("wrote pres_11_workflow_simple.png/.pdf and pres_11_workflow_simple_stage3.png")


if __name__ == "__main__":
    main()
