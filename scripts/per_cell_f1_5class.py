#!/usr/bin/env python3
"""Per-grid-cell macro-F1 for the 5-class collapsed scheme, for six prediction sources.

Sources: embedding variants v2, v3, v4, v5, v6 (bands 1..5 of pred_<bracket>_cell<id>.tif), and the
spectral spec_all (single-band pred_specall_<bracket>_cell<id>.tif). Each grid cell is one sample.
For each (source, cell), the cell's 5-class confusion matrix is built against the crosswalked and
collapsed CKIT reference, and the cell's score is the unweighted mean of the per-class F1 over the
classes present in the cell (macro-F1 over present classes).

5-class collapse: Stable = {forest, urban, water, ag, grass/shrub, wetland}, Harvest, Development,
Insect/Disease, and Beaver. The CKIT reference is crosswalked to the 10-class schema first
(0->4, 1->6, 2->7, 3->3, 4->5, 5->8, 20->1, 30->2, 50->10, 62->9; Unknown(10) and Other(13) are
excluded, those pixels are dropped), then collapsed with the same 10-to-5 map used for the
predictions. Out-of-crosswalk reference values are counted and reported.

Include rule (the crux): a class is included in a cell's macro-F1 if it appears in the reference OR
the prediction for that cell. A predicted-but-not-referenced class is commission (F1 = 0 via zero
precision), a referenced-but-not-predicted class is omission (F1 = 0 via zero recall), and a class in
neither is skipped (F1 undefined). This is the reference-OR-prediction rule (default, commission
sensitive). The alternative, reference-only, is available with --include ref_only and is less
commission sensitive; the note states which was used.

Common cell set: the six sources are compared only on the intersection of cells usable for all six
and with a valid reference, since spec_all has entirely-nodata cells the embeddings do not. Each
source is also reported on its own full set of usable cells, clearly labeled, and the full sets differ
in N so they are not ranked head to head.

Outputs -> reports/per_cell_f1_5class/
  - per_cell_f1_allsources.csv        one row per (source, cell): source, cell_id, bracket, macro_f1,
                                      n_classes_included, in_common_set, and per-class F1
  - per_cell_f1_summary.csv           per source: mean and median (common and full), cell counts
  - f1_violin_common.png              per-cell F1 distribution by source, common cell set
  - f1_violin_fullset.png             per-cell F1 distribution by source, per-source full set
  - f1_by_n_classes.png               reference class composition and F1 stratified by n classes
  - note.md

Requires: rasterio, numpy, pandas, matplotlib
"""

import argparse
import glob
import importlib.util
import os
import re
from collections import defaultdict

import numpy as np
import pandas as pd
import rasterio


def _load(name, path):
    spec = importlib.util.spec_from_file_location(name, os.path.join(os.path.dirname(__file__), path))
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


bmc = _load("bmc", "build_transfer_confusion.py")          # crosswalk, grid check, reference selection
cc = _load("cc", "collapsed_5class_confusion.py")           # 10-to-5 collapse map, class names

TRUTH = "exports/truth_selections.csv"
EMB_DIR = "data/raw/transfer_predictions"
SPEC_DIR = "data/raw/spectral_transferability_10class_percell"
OUT = "reports/per_cell_f1_5class"
SOURCES = ["v2", "v3", "v4", "v5", "v6", "spec_all"]
REF_LUT = bmc._REF_LUT                                       # ckit -> 10-class, Unknown/Other -> 0
MODEL_COLLAPSE = cc._MODEL_COLLAPSE                          # 10-class -> 5-class (0 stays 0)
ALLOWED = bmc.ALLOWED                                        # crosswalk keys plus {10, 13}
NAMES5 = cc.NAMES5
F1_COLS = ["f1_stable", "f1_harvest", "f1_development", "f1_insectdisease", "f1_beaver"]
VPAL = {"v2": "#1f77b4", "v3": "#2ca02c", "v4": "#9467bd", "v5": "#ff7f0e", "v6": "#d62728"}
SRC_COLOR = {**VPAL, "spec_all": "#8c564b"}


def source_pred(source, bracket, cid):
    if source == "spec_all":
        return os.path.join(SPEC_DIR, bracket, f"pred_specall_{bracket}_cell{cid}.tif"), 1
    return os.path.join(EMB_DIR, bracket, f"pred_{bracket}_cell{cid}.tif"), cc.PRED_BAND[source]


def grids_match_meta(pds, meta):
    w, h, tr, crs = meta
    if pds.width != w or pds.height != h or str(pds.crs) != str(crs):
        return False
    t = pds.transform
    return np.allclose([t.a, t.b, t.c, t.d, t.e, t.f], [tr.a, tr.b, tr.c, tr.d, tr.e, tr.f], atol=1e-6)


def cell_macro_f1(M, include):
    """Per-cell macro-F1 over present classes. Returns (macro, f1_vector[5], n_included).

    f1_vector holds F1 for every class present in reference or prediction (0 when wrong), and NaN for
    a class absent in both. macro averages over the include set: present-in-either (ref_or_pred) or
    present-in-reference (ref_only).
    """
    M = M.astype(float)
    tp = np.diag(M)
    row = M.sum(1)                                          # reference support per class
    col = M.sum(0)                                          # predicted support per class
    f1 = np.full(5, np.nan)
    included = []
    for k in range(5):
        present_ref = row[k] > 0
        present_pred = col[k] > 0
        if present_ref or present_pred:
            p = tp[k] / col[k] if col[k] > 0 else 0.0
            r = tp[k] / row[k] if row[k] > 0 else 0.0
            f1[k] = 2 * p * r / (p + r) if (p + r) > 0 else 0.0
        keep = (present_ref or present_pred) if include == "ref_or_pred" else present_ref
        if keep:
            included.append(k)
    macro = float(np.mean([f1[k] for k in included])) if included else np.nan
    return macro, f1, len(included)


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--truth", default=TRUTH, help="adjudicated reviewer per cell")
    ap.add_argument("--include", choices=["ref_or_pred", "ref_only"], default="ref_or_pred",
                    help="include a class in the cell macro-F1 if present in reference or prediction "
                         "(default) or only in the reference")
    args = ap.parse_args()
    os.makedirs(OUT, exist_ok=True)

    ref_index = bmc.build_reference_index()
    truth = bmc.load_truth(args.truth)
    chosen_ref, n_multi, missing, mismatch = bmc.choose_references_truth(ref_index, truth)
    if mismatch:
        print("STOP: truth reviewer with no matching raster:", mismatch[:10]); raise SystemExit(1)

    # cell -> bracket from the reference filename (opt_<bracket>); this is the evaluated universe
    cells = {}
    for cid, rp in chosen_ref.items():
        m = re.search(r"opt_(\d{4}_\d{4})", os.path.basename(rp))
        if m:
            cells[cid] = m.group(1)
    print(f"reference cells: {len(chosen_ref)}   with a parseable bracket: {len(cells)}   "
          f"multi-interpreted: {n_multi}")

    rows = []
    usable = {s: set() for s in SOURCES}
    ref_valid_cells = set()
    n_ref_classes = {}
    drops = defaultdict(list)
    unmapped = defaultdict(int)

    for cid in sorted(cells):
        bracket = cells[cid]
        with rasterio.open(chosen_ref[cid]) as rds:
            ref_raw = rds.read(1)
            meta = (rds.width, rds.height, rds.transform, rds.crs)
        for val in np.unique(ref_raw):
            if int(val) not in ALLOWED:                    # out-of-crosswalk encoding error, reported
                unmapped[(cid, int(val))] += int((ref_raw == val).sum())
        ref5 = MODEL_COLLAPSE[REF_LUT[np.where((ref_raw >= 0) & (ref_raw <= 62), ref_raw, 0)]]
        ref_valid = (ref5 >= 1) & (ref5 <= 5)
        if not ref_valid.any():
            drops["reference_no_valid_px"].append(cid)
            continue
        ref_valid_cells.add(cid)
        n_ref_classes[cid] = int(np.unique(ref5[ref_valid]).size)

        for s in SOURCES:
            pp, band = source_pred(s, bracket, cid)
            if not os.path.exists(pp):
                drops[f"{s}_missing_pred"].append(cid)
                continue
            with rasterio.open(pp) as pds:
                if not grids_match_meta(pds, meta):
                    drops[f"{s}_grid_mismatch"].append(cid)
                    continue
                pred_raw = pds.read(band)
            if not (pred_raw >= 1).any():                  # entirely nodata prediction
                drops[f"{s}_blank_pred"].append(cid)
                continue
            pred5 = MODEL_COLLAPSE[np.where(pred_raw <= 10, pred_raw, 0)]
            valid = ref_valid & (pred5 >= 1) & (pred5 <= 5)
            M = np.zeros((5, 5), np.int64)
            np.add.at(M, (ref5[valid] - 1, pred5[valid] - 1), 1)
            macro, f1, ninc = cell_macro_f1(M, args.include)
            usable[s].add(cid)
            rows.append(dict(source=s, cell_id=cid, bracket=bracket, macro_f1=round(macro, 5),
                             n_classes_included=ninc,
                             **{col: (round(float(f1[k]), 5) if np.isfinite(f1[k]) else np.nan)
                                for k, col in enumerate(F1_COLS)}))

    common = {cid for cid in ref_valid_cells if all(cid in usable[s] for s in SOURCES)}
    print(f"reference-valid cells: {len(ref_valid_cells)}")
    for s in SOURCES:
        print(f"  {s:9} usable cells: {len(usable[s])}")
    print(f"common cell set (all six sources): {len(common)}")
    if unmapped:
        agg = defaultdict(int)
        for (cid, val), n in unmapped.items():
            agg[val] += n
        print(f"UNMAPPED reference values (outside crosswalk and exclude): {dict(agg)}")
    for reason, lst in sorted(drops.items()):
        if lst:
            print(f"  dropped {reason}: {len(lst)} {sorted(set(lst))[:5]}")

    df = pd.DataFrame(rows)
    df["in_common_set"] = df.cell_id.isin(common)
    df = df[["source", "cell_id", "bracket", "macro_f1", "n_classes_included", "in_common_set"] + F1_COLS]
    df.to_csv(os.path.join(OUT, "per_cell_f1_allsources.csv"), index=False)

    # summary per source
    srows = []
    for s in SOURCES:
        full = df[df.source == s].macro_f1
        comm = df[(df.source == s) & df.in_common_set].macro_f1
        srows.append(dict(source=s,
                          n_common=int(comm.size), mean_common=round(float(comm.mean()), 4),
                          median_common=round(float(comm.median()), 4),
                          n_full=int(full.size), mean_full=round(float(full.mean()), 4),
                          median_full=round(float(full.median()), 4)))
    summ = pd.DataFrame(srows)
    summ.to_csv(os.path.join(OUT, "per_cell_f1_summary.csv"), index=False)
    print("\nper-source per-cell macro-F1 (common set):")
    print(summ[["source", "n_common", "mean_common", "median_common"]].to_string(index=False))

    make_figs(df, common, n_ref_classes, args.include)
    write_note(df, common, ref_valid_cells, usable, drops, unmapped, n_ref_classes, args.include, summ)
    print(f"\nwrote {OUT}/")


def make_figs(df, common, n_ref_classes, include):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    def _style(ax):
        ax.grid(False)
        for sp in ("top", "right"):
            ax.spines[sp].set_visible(False)

    def _caption(fig, text, top=1.0, width=125):
        import textwrap
        wrapped = "\n".join(textwrap.wrap(text, width))
        nlines = wrapped.count("\n") + 1
        fig.tight_layout(rect=[0, 0.02 + 0.045 * nlines, 1, top])
        fig.text(0.5, 0.01, wrapped, ha="center", va="bottom", fontsize=8, color="0.35")

    def violins(subset, title, cap, path):
        data = [subset[subset.source == s].macro_f1.dropna().values for s in SOURCES]
        ns = [len(d) for d in data]
        fig, ax = plt.subplots(figsize=(10, 5.5))
        parts = ax.violinplot(data, positions=range(len(SOURCES)), showextrema=False, widths=0.8)
        for pc, s in zip(parts["bodies"], SOURCES):
            pc.set_facecolor(SRC_COLOR[s]); pc.set_alpha(0.5); pc.set_edgecolor("0.3")
        for i, d in enumerate(data):
            if len(d):
                med, mean = np.median(d), np.mean(d)
                ax.plot([i - 0.28, i + 0.28], [med, med], color="black", lw=2, zorder=4)
                ax.plot(i, mean, marker="D", color="black", ms=6, zorder=5)
        ax.set_xticks(range(len(SOURCES)))
        ax.set_xticklabels([f"{s}\n(n={n})" for s, n in zip(SOURCES, ns)])
        ax.set_ylabel("per-cell macro-F1 (5-class, over present classes)")
        ax.set_ylim(0, 1)
        ax.set_title(title, fontsize=11)
        ax.plot([], [], color="black", lw=2, label="median")
        ax.plot([], [], marker="D", color="black", ls="", label="mean")
        ax.legend(fontsize=8, frameon=False, loc="upper right")
        _style(ax)
        _caption(fig, cap)
        fig.savefig(path, dpi=150, bbox_inches="tight")
        plt.close(fig)

    inc_txt = ("present in reference or prediction" if include == "ref_or_pred"
               else "present in the reference only")
    common_df = df[df.in_common_set]
    violins(common_df, f"Per-cell macro-F1 by source, common cell set (N={len(common)})",
            "Per-cell 5-class macro-F1 for each source on the common cell set, one point per cell, "
            "with the median (bar) and mean (diamond) marked. A class is included in a cell's macro-F1 "
            f"if it is {inc_txt}. All six sources are scored on the identical cells, so the "
            "distributions are directly comparable; the change-class commission drags the macro-F1 "
            "down whenever a source over-predicts a change class the cell does not contain.",
            os.path.join(OUT, "f1_violin_common.png"))
    violins(df, "Per-cell macro-F1 by source, per-source full set (N differs per source)",
            "Per-cell 5-class macro-F1 for each source on its own full set of usable cells, one point "
            "per cell, median (bar) and mean (diamond) marked. The sources have different N here (see "
            "the axis labels), so read each distribution on its own and do not rank the sources head "
            "to head; spec_all in particular is scored on fewer cells since it has entirely-nodata "
            "rasters that the embeddings do not.",
            os.path.join(OUT, "f1_violin_fullset.png"))

    # composition: reference class count per cell (common set), and F1 by n_classes_included
    fig, axes = plt.subplots(1, 2, figsize=(14, 5))
    ncls = [n_ref_classes[c] for c in common]
    vals, counts = np.unique(ncls, return_counts=True)
    axes[0].bar(vals, counts, color="#4d4d4d", edgecolor="white")
    axes[0].set_xlabel("number of reference classes in the cell (5-class)")
    axes[0].set_ylabel("cells (common set)")
    axes[0].set_title("Reference class composition per cell", fontsize=10)
    axes[0].set_xticks(vals)
    _style(axes[0])
    groups = sorted(common_df.n_classes_included.dropna().unique())
    box = axes[1].boxplot([common_df[common_df.n_classes_included == g].macro_f1.dropna().values
                           for g in groups], positions=range(len(groups)), widths=0.6, patch_artist=True)
    for patch in box["boxes"]:
        patch.set_facecolor("#bdd7e7")
    for med in box["medians"]:
        med.set_color("black")
    axes[1].set_xticks(range(len(groups))); axes[1].set_xticklabels([int(g) for g in groups])
    axes[1].set_xlabel("classes included in the cell (reference or prediction)")
    axes[1].set_ylabel("per-cell macro-F1")
    axes[1].set_ylim(0, 1)
    axes[1].set_title("F1 by number of included classes (all sources pooled)", fontsize=10)
    _style(axes[1])
    _caption(fig, "Left: how many reference classes each cell contains under the 5-class collapse, on "
                  "the common cell set; this composition is fixed across sources and drives the "
                  "per-cell macro-F1. Right: per-cell macro-F1 grouped by the number of classes "
                  "included in the cell (reference or prediction), pooled over all six sources, showing "
                  "that cells with more classes tend to score lower, so a spread from cell composition "
                  "should not be misread as a source effect.", top=0.93)
    fig.savefig(os.path.join(OUT, "f1_by_n_classes.png"), dpi=150, bbox_inches="tight")
    plt.close(fig)


def write_note(df, common, ref_valid_cells, usable, drops, unmapped, n_ref_classes, include, summ):
    inc_line = ("present in the reference OR the prediction (the default, commission sensitive, so a "
                "predicted-but-not-referenced class counts as F1 = 0)"
                if include == "ref_or_pred" else
                "present in the reference only (the less commission-sensitive alternative)")
    lines = [
        "# per_cell_f1_5class",
        "",
        "Per-grid-cell macro-F1 under the 5-class collapsed scheme for six prediction sources "
        "(embedding v2-v6 and spectral spec_all), treating each grid cell as one sample. Generated by "
        "`scripts/per_cell_f1_5class.py`.",
        "",
        "## Collapse, crosswalk, and exclusions",
        "",
        "5-class collapse: Stable = {forest, urban, water, agriculture, grass/shrub, wetland}, plus "
        "Harvest, Development, Insect/Disease, and Beaver. The CKIT reference is crosswalked to the "
        "10-class schema (" + ", ".join(f"{k}->{v}" for k, v in bmc.CROSSWALK.items())
        + "), with Unknown(10) and Other(13) excluded and those pixels dropped, then collapsed with "
        "the same 10-to-5 map applied to the predictions. Out-of-crosswalk reference values found: "
        + (str({v: n for v, n in ((val, sum(m for (c, val2), m in unmapped.items() if val2 == val))
                                  for val in sorted({v for _, v in unmapped}))}) if unmapped else "none")
        + ".",
        "",
        "## Per-cell F1 rule",
        "",
        f"For each cell and source, the 5-class confusion is built (reference on rows, prediction on "
        f"columns), the per-class F1 = 2PR/(P+R) is computed within the cell, and the cell's score is "
        f"the unweighted mean of the F1 over the included classes (macro-F1 over present classes, no "
        f"support weighting). A class is included if it is {inc_line}. A class in neither the reference "
        f"nor the prediction is skipped (F1 undefined), and F1 = 0 when P + R = 0 for an included "
        f"class. Switch the rule with `--include ref_only`.",
        "",
        "## Common cell set and per-source full sets",
        "",
        f"The six sources are compared only on the common cell set, the intersection of cells usable "
        f"for all six and with a valid reference: **N = {len(common)}**. spec_all has entirely-nodata "
        f"rasters the embeddings do not, so a cell blank for spec_all is dropped for all sources on "
        f"this set. Each source is also reported on its own full set of usable cells, which differ in "
        f"N, so the full-set figure is not a head-to-head ranking. Reference-valid cells: "
        f"{len(ref_valid_cells)}. Per-source usable cells: "
        + ", ".join(f"{s}={len(usable[s])}" for s in SOURCES) + ".",
        "",
        "## Dropped cells",
        "",
    ]
    if drops:
        for reason, lst in sorted(drops.items()):
            lines.append(f"- {reason}: {len(lst)}.")
    else:
        lines.append("- none.")
    lines += [
        "",
        "## Caveat",
        "",
        "Per-cell macro-F1 over present classes is sensitive to how many classes a cell contains: a "
        "cell with only Stable scores near 1 for a good map, while a cell with several rare change "
        "classes is penalized hard by the change-class commission and omission. The reference class "
        "composition is the same across sources on the common set, so `f1_by_n_classes.png` shows this "
        "composition and F1 stratified by the number of included classes, to keep a composition spread "
        "from being misread as a source effect.",
        "",
        "## Headline (common set)",
        "",
        f"{'source':9}{'mean':>8}{'median':>9}",
    ]
    for r in summ.itertuples():
        lines.append(f"{r.source:9}{r.mean_common:>8.3f}{r.median_common:>9.3f}")
    lines += [
        "",
        "## Outputs",
        "",
        "- `per_cell_f1_allsources.csv`: one row per (source, cell) with macro_f1, n_classes_included, "
        "in_common_set, and per-class F1 (NaN where the class is absent in the cell).",
        "- `per_cell_f1_summary.csv`: per source, mean and median per-cell macro-F1 on the common and "
        "full sets, with cell counts.",
        "- `f1_violin_common.png`, `f1_violin_fullset.png`, `f1_by_n_classes.png`.",
    ]
    with open(os.path.join(OUT, "note.md"), "w") as fh:
        fh.write("\n".join(lines) + "\n")


if __name__ == "__main__":
    main()
