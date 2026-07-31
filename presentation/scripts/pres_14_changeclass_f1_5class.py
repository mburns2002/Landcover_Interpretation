#!/usr/bin/env python3
"""pres_14_changeclass_f1_5class: five-class per-class F1 for the four change classes, all six sources.

Primary results figure for the defense talk. Grouped bars: x = source (v2..v6, then spec_all set apart
as a benchmark), four bars per group, one per change class (Harvest, Development, Beaver, Insect/Disease).
Stable is not shown. Colors reuse the 10-class model palette. No per-class winner arrows: the five
brackets use disjoint cell sets, so a pooled cross-source ranking is not a valid basis (the pooled
"winner" tracks bracket cell counts). The slide's claim is uniform failure, so the only annotation is a
ceiling line at the single highest F1 attained by any source on any change class.

Everything is recomputed locally from per-cell predictions on the COMMON cell set (every cell where all
six sources plus the adjudicated reference exist and spec_all is non-blank), using the canonical collapse
imported from scripts/collapsed_5class_confusion.py. No Earth Engine.

Outputs (presentation/figures/, PNG only for the Google Slides deck):
  pres_14_changeclass_f1_5class.png        version A, y auto-zoomed just above the tallest bar
  pres_14_changeclass_f1_5class_full.png   version B, y 0..1
  pres_14b_changeclass_f1_by_bracket.png   backup, faceted per bracket (uniform failure evidence)
"""

import glob
import importlib.util
import os
import re

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import rasterio

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
OUT = os.path.join(ROOT, "presentation", "figures")

M_spec = importlib.util.spec_from_file_location("M", f"{ROOT}/scripts/collapsed_5class_confusion.py")
M = importlib.util.module_from_spec(M_spec)
M_spec.loader.exec_module(M)

BRACKETS = ["2017_2019", "2018_2020", "2019_2021", "2020_2022", "2021_2023"]
PRED = f"{ROOT}/data/raw/transfer_predictions"
SPEC = f"{ROOT}/data/raw/spectral_transferability_10class_percell"
PRED_BAND = {"v2": 1, "v3": 2, "v4": 3, "v5": 4, "v6": 5}
SOURCES = ["v2", "v3", "v4", "v5", "v6", "spec_all"]
# 5-class change codes; display order Harvest, Development, Beaver, Insect/Disease
CHANGE = [(2, "Harvest"), (3, "Development"), (5, "Beaver"), (4, "Insect/Disease")]
# colors straight from data/reference/model_maps_10class_legend.csv
CLASS_COLOR = {"Harvest": "yellow", "Development": "red", "Beaver": "orange",
               "Insect/Disease": "#70A2DB"}


def gid(path):
    return str(int(re.search(r"cell(\d+)", os.path.basename(path)).group(1))).zfill(5)


def f1_from_cm(cm, c):
    tp = cm[c, c]
    fp = cm[:, c].sum() - tp
    fn = cm[c, :].sum() - tp
    return 2 * tp / (2 * tp + fp + fn) if (2 * tp + fp + fn) else float("nan")


def compute():
    """Return (mat, per_bracket, n_cells, per_bracket_n). mat/per_bracket keyed by source -> [F1 per class]."""
    kept, _ = M.select_by_truth(f"{ROOT}/exports/truth_selections.csv")
    refpath = {}
    for p in kept:
        g = re.search(r"grid_(\d+)_", os.path.basename(p)).group(1)
        refpath[str(int(g)).zfill(5)] = p

    conf = {s: np.zeros((6, 6), np.int64) for s in SOURCES}
    confb = {(s, b): np.zeros((6, 6), np.int64) for s in SOURCES for b in BRACKETS}
    n_cells = 0
    per_bracket_n = {b: 0 for b in BRACKETS}

    for b in BRACKETS:
        for ep in sorted(glob.glob(f"{PRED}/{b}/pred_{b}_cell*.tif")):
            cid = gid(ep)
            sp = f"{SPEC}/{b}/pred_specall_{b}_cell{cid}.tif"
            if not os.path.exists(sp) or cid not in refpath:
                continue
            with rasterio.open(sp) as ds:
                spec_img = ds.read(1)
            if not (spec_img > 0).any():          # blank spec_all -> not in common set
                continue
            with rasterio.open(refpath[cid]) as ds:
                ref5 = M.collapse_reference(ds.read(1))
            with rasterio.open(ep) as ds:
                emb = {v: ds.read(PRED_BAND[v]) for v in PRED_BAND}
            if any(x.shape != ref5.shape for x in list(emb.values()) + [spec_img]):
                continue
            preds = {v: M.collapse_prediction(emb[v]) for v in PRED_BAND}
            preds["spec_all"] = M.collapse_prediction(spec_img)
            n_cells += 1
            per_bracket_n[b] += 1
            for s in SOURCES:
                p5 = preds[s]
                valid = (ref5 > 0) & (p5 > 0)
                r, q = ref5[valid], p5[valid]
                idx = r * 6 + q
                add = np.bincount(idx, minlength=36).reshape(6, 6)
                conf[s] += add
                confb[(s, b)] += add

    mat = {s: [f1_from_cm(conf[s], c) for c, _ in CHANGE] for s in SOURCES}
    per_bracket = {b: {s: [f1_from_cm(confb[(s, b)], c) for c, _ in CHANGE] for s in SOURCES}
                   for b in BRACKETS}
    return mat, per_bracket, n_cells, per_bracket_n


# ---- styling ----
FIG_W, FIG_H = 12.0, 5.8
BODY_FS, AXIS_FS, TICK_FS = 16, 18, 16
BAR_W = 0.19          # width of each of the four class bars within a group
GROUP_GAP = 0.55      # extra gap before the spec_all group
SRC_LABEL = {"v2": "v2", "v3": "v3", "v4": "v4", "v5": "v5", "v6": "v6", "spec_all": "spec_all"}


def group_centers():
    """x center of each source group; spec_all pushed right by GROUP_GAP to set it apart."""
    xs = []
    x = 0.0
    for i, s in enumerate(SOURCES):
        if s == "spec_all":
            x += GROUP_GAP
        xs.append(x)
        x += 1.0
    return xs


def draw_main(mat, n_cells, peak, peak_src, y_full):
    centers = group_centers()
    offs = (np.arange(4) - 1.5) * BAR_W        # four bars centered on the group

    fig, ax = plt.subplots(figsize=(FIG_W, FIG_H))
    for j, (_, name) in enumerate(CHANGE):
        vals = [mat[s][j] for s in SOURCES]
        ax.bar([c + offs[j] for c in centers], vals, BAR_W, label=name,
               color=CLASS_COLOR[name], edgecolor="0.25", linewidth=0.7, zorder=3)

    ax.set_xticks(centers)
    ax.set_xticklabels([SRC_LABEL[s] for s in SOURCES], fontsize=TICK_FS)
    ax.set_xlabel("Source", fontsize=AXIS_FS)
    ax.set_ylabel("Per-class F1 (five-class)", fontsize=AXIS_FS)
    ax.tick_params(axis="y", labelsize=TICK_FS)

    if y_full:
        ax.set_ylim(0, 1.0)
        ymax = 1.0
    else:
        ymax = float(np.ceil(peak * 100 + 1.0)) / 100      # just above the tallest bar
        ax.set_ylim(0, ymax)

    ax.set_xlim(centers[0] - 0.7, centers[-1] + 0.7)
    for sp in ("top", "right"):
        ax.spines[sp].set_visible(False)
    ax.grid(False)
    ax.set_title("Per-Class Change F1 by Source (Five-Class)", fontsize=AXIS_FS + 2,
                 fontweight="bold", pad=14)
    ax.legend(ncol=4, fontsize=BODY_FS - 2, frameon=False, loc="upper center",
              bbox_to_anchor=(0.5, -0.12), handlelength=1.3, columnspacing=1.6)
    fig.text(0.5, 0.02,
             "F1 for the four change classes across five embedding configurations (v2–v6)\n"
             "and the spectral benchmark (spec_all), on the common 168-cell reference set.",
             ha="center", va="bottom", fontsize=BODY_FS - 4, color="0.3", linespacing=1.4)
    fig.subplots_adjust(left=0.085, right=0.985, top=0.87, bottom=0.28)
    return fig


def draw_bracket_facets(per_bracket, per_bracket_n):
    centers = group_centers()
    offs = (np.arange(4) - 1.5) * BAR_W
    peak = max(max(v for v in per_bracket[b][s]) for b in BRACKETS for s in SOURCES)
    ymax = float(np.ceil(peak * 100 + 2)) / 100

    fig, axes = plt.subplots(2, 3, figsize=(15, 8.2))
    axes = axes.ravel()
    for k, b in enumerate(BRACKETS):
        ax = axes[k]
        for j, (_, name) in enumerate(CHANGE):
            vals = [per_bracket[b][s][j] for s in SOURCES]
            ax.bar([c + offs[j] for c in centers], vals, BAR_W, color=CLASS_COLOR[name],
                   edgecolor="0.25", linewidth=0.5, zorder=3, label=name if k == 0 else None)
        yr = b.replace("_", "–")
        ax.set_title(f"{yr}   (n = {per_bracket_n[b]} cells)", fontsize=BODY_FS - 1)
        ax.set_xticks(centers)
        ax.set_xticklabels([SRC_LABEL[s] for s in SOURCES], fontsize=TICK_FS - 3)
        ax.set_ylim(0, ymax)
        ax.tick_params(axis="y", labelsize=TICK_FS - 4)
        ax.axvline((centers[4] + centers[5]) / 2, color="0.75", lw=0.8, ls=(0, (4, 3)), zorder=1)
        for sp in ("top", "right"):
            ax.spines[sp].set_visible(False)
        ax.grid(False)
        if k % 3 == 0:
            ax.set_ylabel("Per-class F1", fontsize=BODY_FS - 1)

    # last cell: legend + note
    axes[5].axis("off")
    handles, labels = axes[0].get_legend_handles_labels()
    axes[5].legend(handles, labels, fontsize=BODY_FS - 3, frameon=False, loc="upper center",
                   bbox_to_anchor=(0.5, 1.04), title="Change class", title_fontsize=BODY_FS - 1,
                   labelspacing=0.55, handlelength=1.3)
    axes[5].text(0.5, 0.44,
                 "Backup slide. Failure is uniform\n"
                 "in every bracket: no source clears\n"
                 "F1 ≈ 0.23 on any change class, and\n"
                 "the source ranking is not stable\n"
                 "across brackets. Disjoint cell sets\n"
                 "mean sources are not comparable.",
                 transform=axes[5].transAxes, ha="center", va="top",
                 fontsize=BODY_FS - 5, color="0.25", linespacing=1.4)
    fig.suptitle("Five-Class Change F1 by Bracket", fontsize=AXIS_FS + 1, y=0.98)
    fig.subplots_adjust(left=0.06, right=0.99, top=0.9, bottom=0.06, hspace=0.32, wspace=0.2)
    return fig


def main():
    mat, per_bracket, n_cells, per_bracket_n = compute()

    # ---- console report ----
    print(f"common cell set N = {n_cells}  (per bracket: {per_bracket_n})")
    print("\n6 x 4 F1 matrix (rows=source, cols=Harvest, Development, Beaver, Insect/Disease):")
    hdr = f"{'source':<9}" + "".join(f"{n:>16}" for _, n in CHANGE)
    print(hdr)
    peak, peak_src, peak_cls = -1.0, None, None
    for s in SOURCES:
        print(f"{s:<9}" + "".join(f"{v:>16.4f}" for v in mat[s]))
        for j, (_, name) in enumerate(CHANGE):
            if mat[s][j] > peak:
                peak, peak_src, peak_cls = mat[s][j], s, name
    print(f"\nceiling (single highest F1 anywhere) = {peak:.4f}  ({peak_src}, {peak_cls})")
    print("NO arrows drawn: brackets use disjoint cell sets, so a pooled per-class source ranking is "
          "not a valid basis (per user).")

    print("\nper-bracket winner per change class (talk notes):")
    print(f"  {'bracket':<12}" + "".join(f"{n:>16}" for _, n in CHANGE))
    for b in BRACKETS:
        row = []
        for j, (_, name) in enumerate(CHANGE):
            col = {s: per_bracket[b][s][j] for s in SOURCES}
            w = max(col, key=col.get)
            row.append(f"{w}:{col[w]:.3f}")
        print(f"  {b:<12}" + "".join(f"{c:>16}" for c in row))

    os.makedirs(OUT, exist_ok=True)
    # PNG only (Google Slides deck does not accept PDF images)
    # version A: auto-zoomed
    fig = draw_main(mat, n_cells, peak, peak_src, y_full=False)
    fig.savefig(f"{OUT}/pres_14_changeclass_f1_5class.png", dpi=300)
    plt.close(fig)
    # version B: full 0..1
    fig = draw_main(mat, n_cells, peak, peak_src, y_full=True)
    fig.savefig(f"{OUT}/pres_14_changeclass_f1_5class_full.png", dpi=300)
    plt.close(fig)
    # backup: per-bracket facets
    fig = draw_bracket_facets(per_bracket, per_bracket_n)
    fig.savefig(f"{OUT}/pres_14b_changeclass_f1_by_bracket.png", dpi=300)
    plt.close(fig)

    print("\nwrote pres_14_changeclass_f1_5class.png, _full.png, "
          "pres_14b_changeclass_f1_by_bracket.png")


if __name__ == "__main__":
    main()
