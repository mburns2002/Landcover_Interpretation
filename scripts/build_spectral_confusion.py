#!/usr/bin/env python3
"""Confusion matrices for the SPECTRAL transferability experiment, plus an embedding-vs-spectral
comparison.

A Random Forest was trained once on 2018/2020 spectral composites (spec_all: Sentinel-2, Landsat 8,
and Sentinel-1 raw bands and indices, 50 bands) and applied to five NAIP brackets, restricted to the
CKIT-RF interpreted cells for each bracket (36 disjoint cells per bracket, 180 total). This mirrors
the embedding transferability experiment exactly, same cells, brackets, and 2018/2020 training, so
the two input types are directly comparable on identical cells. 2018/2020 is the in-sample control.

The matrix-building code is reused from build_transfer_confusion.py (crosswalk, grid-identity
assertion, reference selection, and metrics). The only differences for the spectral inputs: filenames
are pred_specall_<bracket>_cell<id>.tif and the rasters are single band (embedding files were
pred_<bracket>_cell<id>.tif with 5 bands, one per variant v2-v6).

Poolings reproduced: the embedding results use per-bracket pooling only (25 matrices, 5 variants by 5
brackets, no pooled matrix). This script builds the spectral per-bracket matrices to match, and adds a
pooled-across-180 matrix for both input types so the pooled comparison is like-for-like.

Outputs -> reports/spectral_composite_classified_maps/
  - cm_specall_<bracket>.csv, cm_specall_pooled.csv       10x10 raw counts (reference on rows)
  - cm_specall_<bracket>.png, cm_specall_pooled.png       count heatmaps, PA/UA margins, OA/kappa
  - spectral_metrics_long.csv                             per (bracket-or-pooled, class), source col
  - note.md                                               crosswalk, exclusions, reports, caveats
  - comparison/combined_metrics_long.csv                  spectral stacked with embedding v2-v6
  - comparison/overall_comparison.csv                     OA, macro-F1, kappa by source and bracket
  - comparison/compare_overall_metrics.png               OA/macro-F1/kappa, spectral vs embedding
  - comparison/compare_perclass_ua_pooled.png            pooled per-class user's accuracy
  - comparison/compare_perclass_pa_pooled.png            pooled per-class producer's accuracy
  - comparison/compare_change_class_ua_by_bracket.png    change-class UA per bracket (beaver etc.)

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

# reuse the embedding matrix-building code
_spec = importlib.util.spec_from_file_location("bmc", os.path.join(
    os.path.dirname(__file__), "build_transfer_confusion.py"))
bmc = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(bmc)

BRACKETS = bmc.BRACKETS
CONTROL = bmc.CONTROL
NAMES = bmc.NAMES
LABELS = bmc.LABELS
MIN_SUP = bmc.MIN_SUP
MIN_CELLS = bmc.MIN_CELLS
CROSSWALK = bmc.CROSSWALK
EXCLUDE = bmc.EXCLUDE
ALLOWED = bmc.ALLOWED
_REF_LUT = bmc._REF_LUT

SPEC_DIR = "data/raw/spectral_transferability_10class_percell"
EMB_LONG = "reports/transfer_confusion_adjudicated/transfer_metrics_long.csv"
EMB_CM_DIR = "reports/transfer_confusion_adjudicated"
OUT = "reports/spectral_composite_classified_maps"
CMP = os.path.join(OUT, "comparison")
EMB_VARIANTS = ["v2", "v3", "v4", "v5", "v6"]
CHANGE_CLASSES = [1, 2, 9, 10]   # harvest, development, beaver, insect_disease

# canonical variant palette, shared across the repo's figures; spec_all is the distinguished
# reference in black
VPAL = {"v2": "#1f77b4", "v3": "#2ca02c", "v4": "#9467bd", "v5": "#ff7f0e", "v6": "#d62728"}
SPEC_COLOR = "black"


def src_color(src):
    if src in ("spectral_specall", "spec_all"):
        return SPEC_COLOR
    return VPAL[src.replace("embedding_", "")]


def _r(x):
    return round(float(x), 5) if np.isfinite(x) else ""


def long_rows_from_matrix(source, bracket, M, cells_present_vec, n_cells):
    """Build 10 per-class metric rows for one matrix, matching the embedding long-table schema."""
    mt = bmc.metrics(M)
    tot = int(M.sum())
    rows = []
    for k in range(10):
        c = k + 1
        sup = int(mt["support"][k])
        cp = int(cells_present_vec[c])
        low = cp < MIN_CELLS or sup < MIN_SUP
        rows.append(dict(
            source=source, bracket=bracket, control=(bracket == CONTROL),
            class_code=c, class_name=NAMES[c],
            precision=_r(mt["precision"][k]), recall=_r(mt["recall"][k]),
            f1=_r(mt["f1"][k]), iou=_r(mt["iou"][k]), support=sup,
            cells_present=cp, low_support=low,
            OA=round(mt["OA"], 5), macro_F1=round(mt["macro_F1"], 5),
            mean_IoU=round(mt["mean_IoU"], 5), kappa=round(mt["kappa"], 5),
            n_cells=n_cells, total_pixels=tot))
    return rows, mt


def build_spectral(chosen_ref):
    """Accumulate the spectral per-bracket 10x10 matrices and the pooled matrix."""
    cms = {b: np.zeros((10, 10), np.int64) for b in BRACKETS}
    cells_used = defaultdict(set)
    cells_present = {b: np.zeros(11, int) for b in BRACKETS}
    skipped = {"missing_ref": [], "grid_mismatch": [], "band_count": [], "blank_pred": []}
    unmapped = defaultdict(int)

    for bracket in BRACKETS:
        preds = sorted(glob.glob(os.path.join(SPEC_DIR, bracket,
                                              f"pred_specall_{bracket}_cell*.tif")))
        for pp in preds:
            m = re.search(r"cell(\d+)\.tif$", os.path.basename(pp))
            cid = bmc.pad(m.group(1))
            if cid not in chosen_ref:
                skipped["missing_ref"].append((bracket, cid))
                continue
            rp = chosen_ref[cid]
            with rasterio.open(pp) as pds, rasterio.open(rp) as rds:
                if pds.count != 1:                       # spectral rasters are single band
                    skipped["band_count"].append((bracket, cid, pds.count))
                    continue
                ok, why = bmc.grids_match(pds, rds)
                if not ok:
                    skipped["grid_mismatch"].append((bracket, cid, why))
                    continue
                pred = pds.read(1)
                # a spec_all raster that is entirely nodata is a missing prediction, not a valid
                # all-Stable map; drop it and report rather than counting it as a scored cell
                if not (pred >= 1).any():
                    skipped["blank_pred"].append((bracket, cid))
                    continue
                ref_raw = rds.read(1)
                for val in np.unique(ref_raw):
                    iv = int(val)
                    if iv not in ALLOWED:                 # report encoding errors, do not drop silently
                        unmapped[(bracket, cid, iv)] += int((ref_raw == val).sum())
                safe = np.where((ref_raw >= 0) & (ref_raw <= 62), ref_raw, 0)
                ref = _REF_LUT[safe]                      # excluded/unmapped -> 0
                for k in range(1, 11):
                    if (ref == k).any():
                        cells_present[bracket][k] += 1
                valid = (ref >= 1) & (ref <= 10) & (pred >= 1) & (pred <= 10)
                if valid.any():
                    np.add.at(cms[bracket], (ref[valid] - 1, pred[valid] - 1), 1)
                cells_used[bracket].add(cid)

    pooled = sum(cms.values())
    pooled_present = sum(cells_present[b] for b in BRACKETS)
    n_pooled = sum(len(cells_used[b]) for b in BRACKETS)
    return cms, pooled, cells_used, cells_present, pooled_present, n_pooled, skipped, unmapped


def embedding_pooled_matrix(variant):
    """Pooled-180 embedding matrix = sum of the five per-bracket count CSVs (cells are disjoint)."""
    M = np.zeros((10, 10), np.int64)
    for b in BRACKETS:
        df = pd.read_csv(os.path.join(EMB_CM_DIR, f"cm_{variant}_{b}.csv"), index_col=0)
        M += df.values.astype(np.int64)
    return M


def write_note(chosen_desc, cells_used, cells_present, skipped, unmapped, spectral_long):
    long = pd.DataFrame(spectral_long)
    low = []
    for bracket in BRACKETS:
        sub = long[(long.bracket == bracket) & long.low_support]
        low.append((bracket, [f"{r.class_name} ({r.support} px, {r.cells_present} cells)"
                              for r in sub.itertuples()]))
    lines = [
        "# spectral_composite_classified_maps",
        "",
        "Per-class confusion matrices and accuracy metrics for the SPECTRAL transferability "
        "experiment: a Random Forest trained once on 2018/2020 spectral composites (spec_all, "
        "Sentinel-2, Landsat 8, and Sentinel-1 raw bands and indices, 50 bands), applied to five NAIP "
        "brackets and compared against the CKIT-RF interpreted reference. Generated by "
        "`scripts/build_spectral_confusion.py`, which reuses the embedding matrix code in "
        "`scripts/build_transfer_confusion.py`.",
        "",
        "## Inputs",
        "",
        "- Predictions: `data/raw/spectral_transferability_10class_percell/<bracket>/"
        "pred_specall_<bracket>_cell<id>.tif`, single band, values 1 to 10.",
        "- Reference: `data/raw/rf_class_maps/`, single band, CKIT label_id codes, "
        + chosen_desc + ".",
        "",
        "## Crosswalk (reference only)",
        "",
        "CKIT label_id to the 10-class schema: "
        + ", ".join(f"{k}->{v}" for k, v in CROSSWALK.items()) + ".",
        "",
        f"Excluded reference values (no 10-class equivalent, pixel dropped): {sorted(EXCLUDE)} "
        "(10 = unknown abstention, 13 = other_no_change). Any reference value outside the crosswalk "
        "and the exclude set is treated as an encoding error, counted, and reported.",
        "",
        "## Poolings",
        "",
        "The embedding results use per-bracket pooling only (25 matrices, no pooled matrix). This "
        "analysis reproduces the per-bracket pooling for spectral and adds a pooled-across-180 matrix "
        "for both input types, so the pooled spectral-vs-embedding comparison is like-for-like.",
        "",
        "## Missing brackets and grid checks",
        "",
        f"- Brackets found: {', '.join(b + ' (' + str(len(cells_used[b])) + ' cells)' for b in BRACKETS)}.",
        f"- Blank spec_all predictions (entire raster nodata, dropped and not counted as scored "
        f"cells): {len(skipped['blank_pred'])}. "
        + ("; ".join(f"{b}: {sorted(c for bb, c in skipped['blank_pred'] if bb == b)}"
                     for b in BRACKETS if any(bb == b for bb, _ in skipped['blank_pred']))
           or "none") + ". These fall in the out-of-sample brackets, so spec_all covers fewer than "
        "36 cells there, and the spectral-vs-embedding comparison is on 168 spectral cells versus 180 "
        "embedding cells; the pooled and per-bracket metrics reflect only the cells spec_all actually "
        "classified.",
        f"- Missing reference: {len(skipped['missing_ref'])}.",
        f"- Grid mismatch (pinning failed, not resampled): {len(skipped['grid_mismatch'])}.",
        f"- Prediction band count not 1: {len(skipped['band_count'])}.",
        f"- Unmapped reference values: {len(unmapped)} (cell, value) occurrences.",
        "",
        "## Disjoint-cell caveat",
        "",
        "The five brackets use disjoint cell sets (36 cells each, no cell shared across brackets), so "
        "a bracket-to-bracket difference within one input type confounds temporal transfer with the "
        "differing cell composition and landscape difficulty. Per-bracket matrices are five "
        "independent assessments on different footprints. Only the pooled matrix, or a same-bracket "
        "comparison, is like-for-like. The spectral and embedding predictions sit on the identical 180 "
        "cells, so spectral-vs-embedding comparisons (same bracket or pooled) carry no disjoint-cell "
        "confound between the two input types; the disjoint caveat is only across brackets within one "
        "input type.",
        "",
        "## Support and low-support classes",
        "",
        "At 36 cells per bracket several change classes have very few reference pixels, and their "
        "per-class metrics then rest on little data. `spectral_metrics_long.csv` carries `support` "
        "(reference pixel count per class) and `cells_present` (how many cells contain the class). The "
        f"`low_support` flag fires when a class appears in fewer than {MIN_CELLS} cells or has under "
        f"{MIN_SUP} px, since pixels within a cell are autocorrelated. Low-support classes per bracket:",
        "",
    ]
    for bracket, lc in low:
        lines.append(f"- {bracket}: {', '.join(lc) if lc else 'none flagged'}")
    lines += [
        "",
        "## Outputs",
        "",
        "- `cm_specall_<bracket>.csv` and `cm_specall_pooled.csv`: 10x10 raw counts, reference on rows "
        "(diagonal is producer's accuracy), prediction on columns. Row-normalized and column-"
        "normalized CSVs are omitted to match the embedding convention, which stores counts only.",
        "- `spectral_metrics_long.csv`: one row per (bracket-or-pooled, class) with per-class "
        "precision, recall, F1, IoU, support, cells_present, and low_support, the aggregate OA, "
        "macro-F1, mean IoU, and kappa, and a `source` column set to spectral_specall.",
        "- `comparison/`: the combined spectral-and-embedding long table, an overall comparison table, "
        "and the comparison figures.",
    ]
    with open(os.path.join(OUT, "note.md"), "w") as fh:
        fh.write("\n".join(lines) + "\n")


# ----------------------------------------------------------------------------- figures
def _style(ax):
    ax.grid(False)
    for s in ("top", "right"):
        ax.spines[s].set_visible(False)


def fig_overall(overall, path):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    order = BRACKETS + ["pooled"]
    sources = ["spectral_specall"] + [f"embedding_{v}" for v in EMB_VARIANTS]
    metrics_ = [("OA", "overall accuracy"), ("macro_F1", "macro-F1"), ("kappa", "Cohen's kappa")]
    fig, axes = plt.subplots(1, 3, figsize=(15, 4.6))
    for ax, (mk, title) in zip(axes, metrics_):
        for src in sources:
            y = [overall[(src, b)][mk] for b in order]
            spec = src == "spectral_specall"
            ax.plot(range(len(order)), y, marker="o",
                    lw=2.8 if spec else 1.6, color=src_color(src),
                    zorder=3 if spec else 2, label="spec_all" if spec else src.replace("embedding_", ""))
        ax.set_xticks(range(len(order)))
        ax.set_xticklabels([b.replace("_", "-") for b in order], rotation=45, ha="right", fontsize=8)
        ax.set_title(title, fontsize=10)
        _style(ax)
    axes[0].set_ylabel("value")
    axes[-1].legend(fontsize=8, frameon=False, title="source")
    fig.suptitle("spectral spec_all vs embedding variants, per bracket and pooled "
                 "(2018-2020 is the in-sample control)", fontsize=11)
    fig.tight_layout(rect=[0, 0, 1, 0.95])
    fig.savefig(path, dpi=150, bbox_inches="tight")
    plt.close(fig)


def fig_perclass(combined, metric, title, path):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    sub = combined[combined.bracket == "pooled"]
    sources = ["spectral_specall"] + [f"embedding_{v}" for v in EMB_VARIANTS]
    x = np.arange(10)
    w = 0.13
    fig, ax = plt.subplots(figsize=(13, 5))
    for i, src in enumerate(sources):
        s = sub[sub.source == src].sort_values("class_code")
        vals = pd.to_numeric(s[metric], errors="coerce").values
        spec = src == "spectral_specall"
        ax.bar(x + (i - 2.5) * w, vals, w, label="spec_all" if spec else src.replace("embedding_", ""),
               color=src_color(src), edgecolor="white", linewidth=0.3,
               zorder=3 if spec else 2)
    ax.set_xticks(x)
    ax.set_xticklabels(LABELS, rotation=40, ha="right", fontsize=8)
    ax.set_ylabel(title)
    ax.set_ylim(0, 1)
    ax.set_title(f"pooled per-class {title}, spectral spec_all vs embedding variants "
                 "(change classes: harvest, development, beaver, insect_disease)", fontsize=10)
    ax.legend(fontsize=8, frameon=False, ncol=6, loc="upper center", bbox_to_anchor=(0.5, -0.18))
    _style(ax)
    fig.tight_layout()
    fig.savefig(path, dpi=150, bbox_inches="tight")
    plt.close(fig)


def fig_change_ua(combined, path):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    order = BRACKETS + ["pooled"]
    sources = ["spectral_specall"] + [f"embedding_{v}" for v in EMB_VARIANTS]
    fig, axes = plt.subplots(1, 4, figsize=(17, 4.4), sharey=True)
    for ax, cc in zip(axes, CHANGE_CLASSES):
        for src in sources:
            s = combined[(combined.source == src) & (combined.class_code == cc)]
            s = s.set_index("bracket").reindex(order)
            y = pd.to_numeric(s["precision"], errors="coerce").values
            spec = src == "spectral_specall"
            ax.plot(range(len(order)), y, marker="o",
                    lw=2.8 if spec else 1.6, color=src_color(src),
                    zorder=3 if spec else 2, label="spec_all" if spec else src.replace("embedding_", ""))
        ax.set_title(f"{NAMES[cc]} UA (commission)", fontsize=9)
        ax.set_xticks(range(len(order)))
        ax.set_xticklabels([b.replace("_", "-") for b in order], rotation=45, ha="right", fontsize=7)
        ax.set_ylim(0, 1)
        _style(ax)
    axes[0].set_ylabel("user's accuracy (precision)")
    axes[-1].legend(fontsize=7, frameon=False, title="source")
    fig.suptitle("change-class user's accuracy per bracket, spectral vs embedding "
                 "(low UA means commission, e.g. false beaver)", fontsize=11)
    fig.tight_layout(rect=[0, 0, 1, 0.94])
    fig.savefig(path, dpi=150, bbox_inches="tight")
    plt.close(fig)


def fig_change_classes_pooled(combined, path):
    """Focused pooled comparison of the four change classes: UA (commission) and PA (omission),
    spec_all vs each embedding variant."""
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    sub = combined[combined.bracket == "pooled"]
    sources = ["spectral_specall"] + [f"embedding_{v}" for v in EMB_VARIANTS]
    codes = CHANGE_CLASSES
    # reference support is the same across sources, read it from spec_all for the axis labels
    spec_sub = sub[sub.source == "spectral_specall"].set_index("class_code")
    sup = {c: int(spec_sub.loc[c, "support"]) for c in codes}
    x = np.arange(len(codes))
    w = 0.13
    fig, axes = plt.subplots(1, 2, figsize=(15, 5.2), sharey=True)
    panels = [(axes[0], "precision", "user's accuracy (UA), low means commission"),
              (axes[1], "recall", "producer's accuracy (PA), low means omission")]
    for ax, metric, title in panels:
        for i, src in enumerate(sources):
            s = sub[sub.source == src].set_index("class_code")
            vals = [pd.to_numeric(s.loc[c, metric], errors="coerce") if c in s.index else np.nan
                    for c in codes]
            spec = src == "spectral_specall"
            ax.bar(x + (i - 2.5) * w, vals, w, color=src_color(src), edgecolor="white",
                   linewidth=0.3, zorder=3 if spec else 2,
                   label="spec_all" if spec else src.replace("embedding_", ""))
        ax.set_xticks(x)
        ax.set_xticklabels([f"{NAMES[c]}\n(n={sup[c]:,} px)" for c in codes], fontsize=9)
        ax.set_title(title, fontsize=10)
        ax.set_ylim(0, 1)
        _style(ax)
    axes[0].set_ylabel("accuracy")
    axes[1].legend(fontsize=8, frameon=False, ncol=6, loc="upper center", bbox_to_anchor=(0.5, -0.13))
    fig.suptitle("pooled change-class accuracy (10-class scheme, 168 cells): spectral spec_all vs "
                 "embedding variants", fontsize=11)
    fig.tight_layout(rect=[0, 0, 1, 0.95])
    fig.savefig(path, dpi=150, bbox_inches="tight")
    plt.close(fig)


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--truth", default="exports/truth_selections.csv",
                    help="adjudicated reviewer per cell (matches the embedding adjudicated basis)")
    args = ap.parse_args()

    os.makedirs(OUT, exist_ok=True)
    os.makedirs(CMP, exist_ok=True)

    # reference selection, identical to the embedding adjudicated run
    ref_index = bmc.build_reference_index()
    truth = bmc.load_truth(args.truth)
    chosen_ref, n_multi, missing, mismatch = bmc.choose_references_truth(ref_index, truth)
    chosen_desc = (f"the adjudicated reviewer from {os.path.basename(args.truth)} "
                   f"({n_multi} multi-interpreted cells)")
    print(f"reference cells indexed: {len(ref_index)}   adjudicated chosen: {len(chosen_ref)}   "
          f"multi: {n_multi}")
    if mismatch:
        print("STOP: truth reviewer with no matching raster:", mismatch[:10]); raise SystemExit(1)

    cms, pooled, cells_used, cells_present, pooled_present, n_pooled, skipped, unmapped = \
        build_spectral(chosen_ref)

    # per-bracket report
    for b in BRACKETS:
        n = len(cells_used[b])
        flag = "" if n >= 30 else "   <-- SHORT of ~36"
        print(f"  {b}: {n} cells, {int(cms[b].sum()):,} px{flag}")
    print(f"  pooled: {n_pooled} cells, {int(pooled.sum()):,} px")
    if unmapped:
        print("UNMAPPED reference values (outside crosswalk and {10,13}):")
        agg = defaultdict(int)
        for (b, cid, iv), nn in unmapped.items():
            agg[iv] += nn
        print("  totals by value:", dict(agg))
    for key, lst in skipped.items():
        if lst:
            print(f"  skipped {key}: {len(lst)} {lst[:5]}")

    # matrices, pngs, spectral long table
    spectral_long = []
    print(f"\n{'bracket':11}{'OA':>7}{'macF1':>7}{'mIoU':>7}{'kappa':>7}")
    for b in BRACKETS + ["pooled"]:
        M = pooled if b == "pooled" else cms[b]
        cp = pooled_present if b == "pooled" else cells_present[b]
        nc = n_pooled if b == "pooled" else len(cells_used[b])
        pd.DataFrame(M, index=LABELS, columns=LABELS).to_csv(
            os.path.join(OUT, f"cm_specall_{b}.csv"))
        rows, mt = long_rows_from_matrix("spectral_specall", b, M, cp, nc)
        spectral_long += rows
        bmc.render_cm_png(M, mt, "spec_all", b, os.path.join(OUT, f"cm_specall_{b}.png"))
        print(f"{b:11}{mt['OA']:>7.3f}{mt['macro_F1']:>7.3f}{mt['mean_IoU']:>7.3f}{mt['kappa']:>7.3f}")
    pd.DataFrame(spectral_long).to_csv(os.path.join(OUT, "spectral_metrics_long.csv"), index=False)
    write_note(chosen_desc, cells_used, cells_present, skipped, unmapped, spectral_long)

    # ---- combined spectral + embedding long table ----
    emb = pd.read_csv(EMB_LONG)
    emb["source"] = "embedding_" + emb["variant"]
    emb = emb.drop(columns=["variant"])
    # embedding pooled rows, built from the summed per-bracket matrices
    emb_pooled_rows = []
    for v in EMB_VARIANTS:
        M = embedding_pooled_matrix(v)
        # pooled cells_present and n_cells summed from the embedding per-bracket long table
        sub = emb[(emb.source == f"embedding_{v}")]
        cp = np.zeros(11, int)
        for c in range(1, 11):
            cp[c] = int(sub[sub.class_code == c]["cells_present"].sum())
        nc = int(sub.groupby("bracket")["n_cells"].first().sum())
        rows, _ = long_rows_from_matrix(f"embedding_{v}", "pooled", M, cp, nc)
        emb_pooled_rows += rows
    combined = pd.concat([pd.DataFrame(spectral_long), emb,
                          pd.DataFrame(emb_pooled_rows)], ignore_index=True)
    cols = ["source", "bracket", "control", "class_code", "class_name", "precision", "recall",
            "f1", "iou", "support", "cells_present", "low_support", "OA", "macro_F1", "mean_IoU",
            "kappa", "n_cells", "total_pixels"]
    combined = combined[cols]
    combined.to_csv(os.path.join(CMP, "combined_metrics_long.csv"), index=False)

    # ---- overall comparison table (one row per source x bracket) ----
    overall = {}
    ov_rows = []
    for (src, b), g in combined.groupby(["source", "bracket"]):
        r = g.iloc[0]
        overall[(src, b)] = {"OA": r.OA, "macro_F1": r.macro_F1, "kappa": r.kappa}
        ov_rows.append(dict(source=src, bracket=b, control=r.control, OA=r.OA,
                            macro_F1=r.macro_F1, mean_IoU=r.mean_IoU, kappa=r.kappa,
                            n_cells=r.n_cells, total_pixels=r.total_pixels))
    pd.DataFrame(ov_rows).sort_values(["bracket", "source"]).to_csv(
        os.path.join(CMP, "overall_comparison.csv"), index=False)

    # ---- figures ----
    fig_overall(overall, os.path.join(CMP, "compare_overall_metrics.png"))
    fig_perclass(combined, "recall", "producer's accuracy (PA)",
                 os.path.join(CMP, "compare_perclass_pa_pooled.png"))
    fig_perclass(combined, "precision", "user's accuracy (UA)",
                 os.path.join(CMP, "compare_perclass_ua_pooled.png"))
    fig_change_ua(combined, os.path.join(CMP, "compare_change_class_ua_by_bracket.png"))
    fig_change_classes_pooled(combined, os.path.join(CMP, "compare_change_classes_pooled.png"))

    print(f"\nwrote {OUT}/ (6 matrices, spectral_metrics_long.csv, note.md) and "
          f"{CMP}/ (combined table, overall table, 5 figures)")


if __name__ == "__main__":
    main()
