#!/usr/bin/env python3
"""pres_11_workflow_simple: sparse five-stage workflow for the defense talk.

Simplified companion to figure 2.2 (scripts/build_workflow_figure.py). Five stages left to right in one
row: Reference, Interpretation, Features, Classification, Evaluation. Stage 3 is the only fork, two
parallel feature tracks (AlphaEarth embeddings and spectral composites) that remerge into stage 4, since
that comparison is the experimental design. The fork and merge use clean orthogonal bus connectors (as
in figure 2.2). Colors reuse the manuscript palette (blue for the AlphaEarth embedding family, neutral
for the spectral composite). Text is kept as text and each box label is measured against its box.

Two outputs:
  pres_11_workflow_simple.png / .pdf          full diagram
  pres_11_workflow_simple_stage3.png          stages 4 and 5 at 25% opacity, for a two-state build

sizing: 12 x 5.6 in, a 16:9 slide content area.
"""

import os

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch, FancyArrowPatch

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
OUT = os.path.join(ROOT, "presentation", "figures")

EMB_FILL, EMB_EDGE = "#cfe3f2", "#0072B2"      # AlphaEarth embedding family (manuscript blue)
SPEC_FILL, SPEC_EDGE = "#efefef", "#555555"    # spectral composite (manuscript neutral)
STAGE_FILL, STAGE_EDGE = "white", "#333333"
ARROW = "#333333"

FIG_W, FIG_H = 12.0, 5.6
XS = [1.2, 3.45, 6.0, 8.55, 10.8]
WS, WB, H = 2.05, 2.4, 1.3          # single-box width, branch-box width, box height
CY, UP, LO = 2.6, 4.0, 1.2          # single-box centre, and the two stage-3 branch centres
LABEL_FS, DETAIL_FS = 20, 16

STAGES = [
    {"n": 1, "label": "Reference", "x": XS[0], "cy": CY, "w": WS,
     "lines": ["GLKN polygons", "NAIP, two dates"]},
    {"n": 2, "label": "Interpretation", "x": XS[1], "cy": CY, "w": WS,
     "lines": ["Points to", "every pixel"]},
    {"n": 3, "label": "Features", "x": XS[2], "cy": None, "w": WB,
     "branches": [
         {"cy": UP, "fill": EMB_FILL, "edge": EMB_EDGE, "lines": ["AlphaEarth", "embeddings v2-v6"]},
         {"cy": LO, "fill": SPEC_FILL, "edge": SPEC_EDGE, "lines": ["Spectral", "S2 + L8 + S1"]},
     ]},
    {"n": 4, "label": "Classification", "x": XS[3], "cy": CY, "w": WS,
     "lines": ["Random Forest", "300 trees"]},
    {"n": 5, "label": "Evaluation", "x": XS[4], "cy": CY, "w": WS,
     "lines": ["Accuracy 10/5", "spatial diag."]},
]

_texts = []


def _box(ax, cx, cy, w, lines, fill, edge, alpha, lw=2.4):
    ax.add_patch(FancyBboxPatch((cx - w / 2, cy - H / 2), w, H,
                                boxstyle="round,pad=0.02,rounding_size=0.10", facecolor=fill,
                                edgecolor=edge, linewidth=lw, zorder=3, alpha=alpha))
    t = ax.text(cx, cy, "\n".join(lines), ha="center", va="center", fontsize=DETAIL_FS, color="0.1",
                zorder=4, alpha=alpha, linespacing=1.45)
    _texts.append((t, (w - 0.42) * FIG_W / 12.0))     # box inner width in inches (strict margin)


def _label(ax, cx, y, text, alpha):
    ax.text(cx, y, text, ha="center", va="bottom", fontsize=LABEL_FS, fontweight="bold",
            color="#1a1a1a", zorder=4, alpha=alpha)


def _line(ax, xs, ys, alpha, lw=2.6):
    ax.plot(xs, ys, color=ARROW, lw=lw, alpha=alpha, zorder=2, solid_capstyle="round",
            solid_joinstyle="round")


def _arrow(ax, p1, p2, alpha, lw=2.6):
    ax.add_patch(FancyArrowPatch(p1, p2, arrowstyle="-|>", mutation_scale=20, color=ARROW,
                                 linewidth=lw, zorder=2, shrinkA=0, shrinkB=1, alpha=alpha))


def draw(dim45=False):
    _texts.clear()
    plt.rcParams.update({"font.family": "sans-serif",
                         "font.sans-serif": ["Helvetica", "Arial", "Helvetica Neue", "DejaVu Sans"],
                         "pdf.fonttype": 42, "ps.fonttype": 42})
    fig, ax = plt.subplots(figsize=(FIG_W, FIG_H))
    ax.set_xlim(0, 12)
    ax.set_ylim(0, 5.4)
    ax.axis("off")

    def a(n):
        return 0.25 if (dim45 and n in (4, 5)) else 1.0

    for s in STAGES:
        if s["n"] == 3:
            for br in s["branches"]:
                _box(ax, s["x"], br["cy"], s["w"], br["lines"], br["fill"], br["edge"], a(3))
            _label(ax, s["x"], UP + H / 2 + 0.12, s["label"], a(3))
        else:
            _box(ax, s["x"], s["cy"], s["w"], s["lines"], STAGE_FILL, STAGE_EDGE, a(s["n"]))
            _label(ax, s["x"], s["cy"] + H / 2 + 0.12, s["label"], a(s["n"]))

    b2r = XS[1] + WS / 2          # interpretation box right edge
    b3l, b3r = XS[2] - WB / 2, XS[2] + WB / 2   # feature boxes left/right
    b4l = XS[3] - WS / 2          # classification box left edge
    xf = (b2r + b3l) / 2          # fork bus x
    xm = (b3r + b4l) / 2          # merge bus x

    _arrow(ax, (XS[0] + WS / 2, CY), (XS[1] - WS / 2, CY), 1.0)      # 1 -> 2
    # fork: stub from stage 2, vertical bus, arrows into each branch (full opacity)
    _line(ax, [b2r, xf], [CY, CY], 1.0)
    _line(ax, [xf, xf], [LO, UP], 1.0)
    _arrow(ax, (xf, UP), (b3l, UP), 1.0)
    _arrow(ax, (xf, LO), (b3l, LO), 1.0)
    # merge: stubs from each branch, vertical bus, arrow into stage 4 (revealed with stage 4)
    _line(ax, [b3r, xm], [UP, UP], a(4))
    _line(ax, [b3r, xm], [LO, LO], a(4))
    _line(ax, [xm, xm], [LO, UP], a(4))
    _arrow(ax, (xm, CY), (b4l, CY), a(4))
    _arrow(ax, (XS[3] + WS / 2, CY), (XS[4] - WS / 2, CY), a(5))     # 4 -> 5

    fig.canvas.draw()
    r = fig.canvas.get_renderer()
    for t, inner_in in _texts:
        w_in = t.get_window_extent(r).width / fig.dpi
        if w_in > inner_in:
            print(f"  WARN overflow: {t.get_text().splitlines()} -> {w_in:.2f} in > {inner_in:.2f} in")
    return fig


def main():
    print("box text placed (label; then up to two lines):")
    for s in STAGES:
        if s["n"] == 3:
            print(f"  {s['n']}. {s['label']}")
            print(f"     [embeddings] {' / '.join(s['branches'][0]['lines'])}")
            print(f"     [spectral]   {' / '.join(s['branches'][1]['lines'])}")
        else:
            print(f"  {s['n']}. {s['label']}: {' / '.join(s['lines'])}")
    print("fit check (warnings if any):")

    fig = draw(dim45=False)
    fig.savefig(f"{OUT}/pres_11_workflow_simple.png", dpi=300, bbox_inches="tight")
    fig.savefig(f"{OUT}/pres_11_workflow_simple.pdf", bbox_inches="tight")
    plt.close(fig)
    fig = draw(dim45=True)
    fig.savefig(f"{OUT}/pres_11_workflow_simple_stage3.png", dpi=300, bbox_inches="tight")
    plt.close(fig)
    print("wrote pres_11_workflow_simple.png/.pdf and pres_11_workflow_simple_stage3.png")


if __name__ == "__main__":
    main()
