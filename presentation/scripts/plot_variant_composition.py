#!/usr/bin/env python3
"""Publication figure and LaTeX table for the variant-composition ablation.

Renders the embeddings-alone versus combo comparison for RF variants v2 through v6 as a
dumbbell plot, with the shared spec_all value drawn once as a reference line, plus a
companion booktabs table. All numbers are hardcoded below, so there is no CSV input, and
there are no command-line arguments. Three y-axis treatments are written, one with a
compressed range and a clipped marker for the v6 outlier, one with a broken axis, and one
with a single continuous range rescaled to include the v6 outlier, so the caller can pick
between them.

The full continuous version is rendered in several combo-marker treatments listed in
STYLES. The chosen treatment (CHOSEN_STYLE) lands in the figures root, and the rest go to
a marker_style_options subfolder so the marker color and shape can be compared by eye.

design note: this uses two panels. Panel A is the dumbbell, and Panel B is a bar of the
combo gain in OA. Panel B is kept because that gain is combo minus the stronger of the two
single-source models, which is not the same span as the emb_alone to combo arrow shown in
Panel A, so it carries information the dumbbell does not.

outputs (png only, per the presentation figures convention):
  presentation/figures/variant_composition_clipped.png
  presentation/figures/variant_composition_full_navy_diamond.png (chosen style)
  presentation/figures/marker_style_options/variant_composition_broken.png
  presentation/figures/marker_style_options/variant_composition_full_<style>.png
  presentation/tables/variant_composition.tex
"""

import os

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

import slide_font
import matplotlib.transforms as mtransforms
from matplotlib.lines import Line2D
from matplotlib.patches import FancyArrowPatch


# hardcoded results, ordered v2, v3, v4, v5, v6
DATA = [
    {"variant": "v2", "composition": "2018 embedding + delta (2020 - 2018)", "bands": 128,
     "emb_alone": 0.810, "spec_all": 0.830, "combo": 0.854, "delta_vs_best": 0.024},
    {"variant": "v3", "composition": "2018 embedding + 2020 embedding", "bands": 128,
     "emb_alone": 0.827, "spec_all": 0.830, "combo": 0.860, "delta_vs_best": 0.030},
    {"variant": "v4", "composition": "delta only (2020 - 2018)", "bands": 64,
     "emb_alone": 0.760, "spec_all": 0.830, "combo": 0.851, "delta_vs_best": 0.021},
    {"variant": "v5", "composition": "2018 embedding + dot product", "bands": 65,
     "emb_alone": 0.747, "spec_all": 0.830, "combo": 0.831, "delta_vs_best": 0.001},
    {"variant": "v6", "composition": "dot product only", "bands": 1,
     "emb_alone": 0.285, "spec_all": 0.830, "combo": 0.838, "delta_vs_best": 0.008},
]

SPEC_ALL = 0.830  # shared spectral-only reference, identical for every variant

# colorblind-safe palette from the okabe-ito set, avoiding the red/green pair
EMB_COLOR = "#0072B2"      # blue, embeddings alone
COMBO_COLOR = "#E69F00"    # orange, embeddings plus spectral
REF_COLOR = "#555555"      # neutral grey, reference line
CONNECT_COLOR = "#999999"  # light grey, dumbbell connector

# per-variant palette, matching the convention used elsewhere in the repo
VPAL = {"v2": "#1f77b4", "v3": "#2ca02c", "v4": "#9467bd", "v5": "#ff7f0e", "v6": "#d62728"}

EMB_MARKER = "o"           # circle

# combo-marker treatments to compare, keyed by a filename-safe label. the clipped and
# broken versions use the first entry, and the full version is rendered once per entry.
# byvariant colors both endpoints by the repo variant palette and leans on shape alone
# to separate embeddings-alone from combo, tying the top panel to the delta bars.
STYLES = [
    {"key": "orange", "byvariant": False, "combo_color": "#E69F00", "combo_marker": "s"},
    {"key": "teal", "byvariant": False, "combo_color": "#009E73", "combo_marker": "s"},
    {"key": "purple", "byvariant": False, "combo_color": "#CC79A7", "combo_marker": "s"},
    {"key": "navy_diamond", "byvariant": False, "combo_color": "#1B2A4A", "combo_marker": "D",
     "combo_ms": 6.5},
    {"key": "variant", "byvariant": True},
]

# the chosen combo-marker treatment, written to the figures root; the rest go to a subfolder
CHOSEN_STYLE = "navy_diamond"

HERE = os.path.dirname(os.path.abspath(__file__))
PRES = os.path.dirname(HERE)
FIG_DIR = os.path.join(PRES, "figures")
ALT_DIR = os.path.join(FIG_DIR, "marker_style_options")  # non-chosen alternatives live here
TAB_DIR = os.path.join(PRES, "tables")

TITLE = "Adding spectral bands lifts every variant to or above spec_all"


def _style():
    plt.rcParams.update({
        "font.family": "sans-serif",
        "font.sans-serif": ["Helvetica", "Arial", "DejaVu Sans"],
        "font.size": 9,
        "axes.linewidth": 0.8,
    })
    slide_font.use_spectral()


def _marker(ax, xi, y, marker, mfc, mec="black", mew=0.6, ms=7):
    # draw one dumbbell endpoint
    ax.plot(xi, y, linestyle="none", marker=marker, markersize=ms,
            markerfacecolor=mfc, markeredgecolor=mec, markeredgewidth=mew,
            zorder=5, clip_on=True)


def _connector(ax, xi, y_from, y_to, color=CONNECT_COLOR):
    # thin vertical connector with a small arrowhead pointing from emb_alone to combo,
    # a patch rather than an annotation so its path clips to the axes box and a
    # broken-axis span does not bleed across the figure
    arr = FancyArrowPatch((xi, y_from), (xi, y_to), arrowstyle="-|>", mutation_scale=11,
                          color=color, lw=0.9, shrinkA=3, shrinkB=3, zorder=3)
    ax.add_patch(arr)


def _endpoint_style(style, variant):
    # resolve the emb and combo endpoint styling for one variant under a given treatment
    if style["byvariant"]:
        vc = VPAL[variant]
        emb = dict(marker=EMB_MARKER, mfc="white", mec=vc, mew=1.6, ms=8)
        combo = dict(marker="s", mfc=vc, mec="black", mew=0.6, ms=8)
        return emb, combo, vc
    emb = dict(marker=EMB_MARKER, mfc=EMB_COLOR, mec="black", mew=0.6, ms=7)
    combo = dict(marker=style["combo_marker"], mfc=style["combo_color"], mec="black", mew=0.6,
                 ms=style.get("combo_ms", 7))
    return emb, combo, CONNECT_COLOR


def draw_dumbbell(ax, x, style, ylo=None, clip_v6=False):
    # plot both endpoints and their connector for every variant on the given axis
    for xi, r in zip(x, DATA):
        emb, combo, conn = _endpoint_style(style, r["variant"])
        if clip_v6 and r["variant"] == "v6":
            # combo stays on scale, emb_alone is far below the floor so it is left off this panel
            _marker(ax, xi, r["combo"], **combo)
            continue
        _connector(ax, xi, r["emb_alone"], r["combo"], color=conn)
        _marker(ax, xi, r["emb_alone"], **emb)
        _marker(ax, xi, r["combo"], **combo)


def _legend(ax, style):
    # single-column legend outside the axes on the right, no frame. when the markers are
    # colored by variant, the swatches are neutral and the note explains the color mapping
    if style["byvariant"]:
        emb_h = Line2D([0], [0], linestyle="none", marker=EMB_MARKER, markersize=8,
                       markerfacecolor="white", markeredgecolor="black", markeredgewidth=1.2,
                       label="Embeddings alone")
        combo_h = Line2D([0], [0], linestyle="none", marker="s", markersize=8,
                         markerfacecolor="0.4", markeredgecolor="black", markeredgewidth=0.6,
                         label="Embeddings + spectral")
    else:
        emb_h = Line2D([0], [0], linestyle="none", marker=EMB_MARKER, markersize=7,
                       markerfacecolor=EMB_COLOR, markeredgecolor="black", markeredgewidth=0.6,
                       label="Embeddings alone")
        combo_h = Line2D([0], [0], linestyle="none", marker=style["combo_marker"],
                         markersize=style.get("combo_ms", 7), markerfacecolor=style["combo_color"],
                         markeredgecolor="black", markeredgewidth=0.6, label="Embeddings + spectral")
    ref_h = Line2D([0], [0], linestyle="--", color=REF_COLOR, lw=1,
                   label=f"spec_all = {SPEC_ALL:.3f}")
    ax.legend(handles=[emb_h, combo_h, ref_h], loc="lower left", bbox_to_anchor=(1.02, 0.0),
              frameon=False, ncol=1, fontsize=8, handlelength=1.8, borderaxespad=0.0)
    if style["byvariant"]:
        ax.text(1.02, 0.42, "marker color = variant", transform=ax.transAxes,
                fontsize=7.5, color="0.3")


def _spec_label(ax):
    # label the reference line just outside the right edge, aligned to its y value
    trans = mtransforms.blended_transform_factory(ax.transAxes, ax.transData)
    ax.text(1.02, SPEC_ALL, f"spec_all = {SPEC_ALL:.3f}", transform=trans,
            ha="left", va="center", fontsize=8, color=REF_COLOR)


def _spines(ax, keep_bottom=True):
    # keep bottom and left spines only, drop top and right
    for s in ("top", "right"):
        ax.spines[s].set_visible(False)
    if not keep_bottom:
        ax.spines["bottom"].set_visible(False)


def _xaxis_labels(ax, x):
    # variant id on the first line, band count on a smaller second line below the axis,
    # placed with fixed point offsets so the two lines never crowd each other
    ax.set_xticks(x)
    ax.set_xticklabels([])
    trans = mtransforms.blended_transform_factory(ax.transData, ax.transAxes)
    for xi, r in zip(x, DATA):
        unit = "band" if r["bands"] == 1 else "bands"
        ax.annotate(r["variant"], xy=(xi, 0), xycoords=trans,
                    xytext=(0, -7), textcoords="offset points",
                    ha="center", va="top", fontsize=9)
        ax.annotate(f"{r['bands']} {unit}", xy=(xi, 0), xycoords=trans,
                    xytext=(0, -21), textcoords="offset points",
                    ha="center", va="top", fontsize=7, color="0.3")


def _panel_b(axB, x):
    # bar of the combo gain in OA, colored by variant with the repo palette, value labels at the ends
    deltas = [r["delta_vs_best"] for r in DATA]
    colors = [VPAL[r["variant"]] for r in DATA]
    axB.bar(x, deltas, width=0.6, color=colors, edgecolor="black", linewidth=0.4, zorder=3)
    for xi, d in zip(x, deltas):
        axB.annotate(f"+{d:.3f}", xy=(xi, d), xytext=(0, 2), textcoords="offset points",
                     ha="center", va="bottom", fontsize=7.5)
    axB.set_ylim(0, max(deltas) * 1.35)
    axB.set_ylabel("Combo gain\n(Delta OA)", fontsize=8)
    _spines(axB)


def _save(fig, stem, outdir=FIG_DIR):
    # pngs only, per the presentation figures convention
    os.makedirs(outdir, exist_ok=True)
    fig.savefig(os.path.join(outdir, f"{stem}.png"), dpi=300, bbox_inches="tight")
    plt.close(fig)


def make_clipped():
    # version (a): compressed y-axis, v6 emb_alone shown as a clipped arrow at the floor
    _style()
    x = list(range(len(DATA)))
    fig, (axA, axB) = plt.subplots(2, 1, figsize=(6.5, 5.0), sharex=True,
                                   gridspec_kw=dict(height_ratios=[3, 1]))
    fig.subplots_adjust(left=0.13, right=0.7, top=0.9, bottom=0.15, hspace=0.2)

    ylo, yhi = 0.72, 0.88
    axA.set_ylim(ylo, yhi)
    axA.set_xlim(-0.5, len(DATA) - 0.5)
    axA.axhline(SPEC_ALL, linestyle="--", color=REF_COLOR, lw=1, zorder=2)
    draw_dumbbell(axA, x, STYLES[0], ylo=ylo, clip_v6=True)
    axA.set_ylabel("Overall accuracy (OA)")
    axA.set_title(TITLE, fontsize=10, fontweight="bold")
    _spines(axA)
    _spec_label(axA)
    _legend(axA, STYLES[0])

    _panel_b(axB, x)
    _xaxis_labels(axB, x)

    _save(fig, "variant_composition_clipped")


def make_full(style):
    # version (c): one continuous y-axis rescaled so the v6 outlier at 0.285 fits with no break,
    # rendered in the given combo-marker treatment
    _style()
    x = list(range(len(DATA)))
    fig, (axA, axB) = plt.subplots(2, 1, figsize=(6.5, 5.0), sharex=True,
                                   gridspec_kw=dict(height_ratios=[3, 1]))
    fig.subplots_adjust(left=0.13, right=0.7, top=0.9, bottom=0.15, hspace=0.2)

    axA.set_ylim(0.25, 0.88)
    axA.set_xlim(-0.5, len(DATA) - 0.5)
    axA.axhline(SPEC_ALL, linestyle="--", color=REF_COLOR, lw=1, zorder=2)
    draw_dumbbell(axA, x, style)
    axA.set_ylabel("Overall accuracy (OA)")
    axA.set_title(TITLE, fontsize=10, fontweight="bold")
    _spines(axA)
    _spec_label(axA)
    _legend(axA, style)

    _panel_b(axB, x)
    _xaxis_labels(axB, x)

    # the chosen treatment lands in the figures root, the alternatives in a subfolder
    outdir = FIG_DIR if style["key"] == CHOSEN_STYLE else ALT_DIR
    _save(fig, f"variant_composition_full_{style['key']}", outdir=outdir)


def make_broken():
    # version (b): broken y-axis, two stacked dumbbell axes plus the delta panel below
    _style()
    x = list(range(len(DATA)))
    fig = plt.figure(figsize=(6.5, 5.6))
    gs = fig.add_gridspec(3, 1, height_ratios=[2.6, 0.7, 1.1], hspace=0.2)
    axtop = fig.add_subplot(gs[0])
    axbot = fig.add_subplot(gs[1], sharex=axtop)
    axB = fig.add_subplot(gs[2], sharex=axtop)
    fig.subplots_adjust(left=0.13, right=0.7, top=0.9, bottom=0.15)

    axtop.set_ylim(0.72, 0.88)
    axbot.set_ylim(0.25, 0.33)
    axtop.set_xlim(-0.5, len(DATA) - 0.5)
    axtop.axhline(SPEC_ALL, linestyle="--", color=REF_COLOR, lw=1, zorder=2)

    # identical content on both axes, each axis clips to its own y range
    draw_dumbbell(axtop, x, STYLES[0])
    draw_dumbbell(axbot, x, STYLES[0])

    # hide the shared inner spines so the break reads cleanly
    _spines(axtop, keep_bottom=False)
    _spines(axbot)
    axtop.tick_params(bottom=False)
    axbot.tick_params(bottom=False)

    # diagonal break marks at the bottom of the top axis and the top of the bottom axis
    d = 0.008
    kw = dict(transform=axtop.transAxes, color="black", clip_on=False, lw=0.9)
    axtop.plot((-d, +d), (-d, +d), **kw)
    axtop.plot((1 - d, 1 + d), (-d, +d), **kw)
    kw.update(transform=axbot.transAxes)
    axbot.plot((-d, +d), (1 - d, 1 + d), **kw)
    axbot.plot((1 - d, 1 + d), (1 - d, 1 + d), **kw)

    axtop.set_title(TITLE, fontsize=10, fontweight="bold")
    # one y label centered across the two broken axes
    fig.text(0.035, 0.63, "Overall accuracy (OA)", rotation=90, va="center", fontsize=9)
    _spec_label(axtop)
    _legend(axtop, STYLES[0])

    _panel_b(axB, x)
    _xaxis_labels(axB, x)

    # keep the inner tick labels off the upper axes, the delta panel carries them
    plt.setp(axtop.get_xticklabels(), visible=False)
    plt.setp(axbot.get_xticklabels(), visible=False)

    _save(fig, "variant_composition_broken", outdir=ALT_DIR)


def write_table():
    # booktabs fragment, no vertical rules, spec_all folded into a multicolumn note
    os.makedirs(TAB_DIR, exist_ok=True)
    lines = [
        "% variant-composition ablation, generated by presentation/scripts/plot_variant_composition.py",
        "% requires \\usepackage{booktabs} in the document preamble",
        "\\begin{tabular}{llrrrr}",
        "\\toprule",
        "Variant & Composition & Bands & Emb alone & Combo & Delta \\\\",
        "\\midrule",
    ]
    for r in DATA:
        lines.append(
            f"{r['variant']} & {r['composition']} & {r['bands']} & "
            f"{r['emb_alone']:.3f} & {r['combo']:.3f} & +{r['delta_vs_best']:.3f} \\\\"
        )
    lines.append("\\bottomrule")
    lines.append(
        f"\\multicolumn{{6}}{{l}}{{\\footnotesize spec\\_all = {SPEC_ALL:.3f} for every variant, "
        f"drawn once as a reference line rather than repeated as a column.}} \\\\"
    )
    lines.append("\\end{tabular}")
    path = os.path.join(TAB_DIR, "variant_composition.tex")
    with open(path, "w") as fh:
        fh.write("\n".join(lines) + "\n")
    return path


def main():
    make_clipped()
    make_broken()
    for style in STYLES:
        make_full(style)
    tab = write_table()

    # print what was plotted so the values can be eyeballed against the source table
    print("plotted values (ordered v2, v3, v4, v5, v6):")
    for r in DATA:
        print(f"  {r['variant']:>3}  {r['bands']:>4} bands  "
              f"emb_alone={r['emb_alone']:.3f}  combo={r['combo']:.3f}  "
              f"delta_vs_best=+{r['delta_vs_best']:.3f}")
    print(f"  spec_all reference (all variants) = {SPEC_ALL:.3f}")

    # cross-check the hardcoded delta against combo minus the stronger single-source model
    print("cross-check delta_vs_best vs combo - max(emb_alone, spec_all):")
    for r in DATA:
        recomputed = r["combo"] - max(r["emb_alone"], SPEC_ALL)
        flag = "ok" if abs(recomputed - r["delta_vs_best"]) < 1e-9 else "MISMATCH"
        print(f"  {r['variant']:>3}  given=+{r['delta_vs_best']:.3f}  "
              f"recomputed=+{recomputed:.3f}  {flag}")

    print(f"wrote figures to {FIG_DIR}")
    print(f"wrote table to {tab}")


if __name__ == "__main__":
    main()
