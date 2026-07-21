#!/usr/bin/env python3
"""Collapsed 5-class census confusion for the SPECTRAL spec_all classifier, plus a comparison to the
embedding collapsed census.

This is the spec_all counterpart to collapsed_5class_confusion.py. It reuses that module's crosswalk,
collapse maps, metrics, design-based CIs, and PA/UA figure, and swaps the map field from the embedding
per-bracket predictions to the spectral spec_all per-bracket predictions (single band, values 1 to 10,
the same 10-class schema, so the same _MODEL_COLLAPSE applies). The reference is the adjudicated CKIT-RF
interpretation, collapsed the same way. Scheme: Stable (all no-change classes folded) plus Harvest,
Development, Insect/Disease, and Beaver.

Census over every valid pixel of the interpreted cells, with the cell as the primary sampling unit for
inference (ratio-estimator CIs with FPC, cross-checked by a cell-level bootstrap). The all-Stable
baseline OA is reported alongside.

Outputs -> reports/spectral_composite_classified_maps/collapsed_5class/
  - confusion_specall_counts.csv / _rownorm.csv          raw and row-normalized 5x5
  - confusion_specall.png                                count heatmap, PA/UA margins with support, OA/kappa
  - metrics_long.csv                                     every metric x class with CIs
  - summary_by_variant.md / .tex / summary.txt           headline table
  - reference.txt                                        provenance
  - comparison_collapsed.csv                             spec_all vs embedding v2-v6 collapsed census
  - compare_collapsed_5class.png                         OA, kappa, macro-F1 by source, baseline line

Requires: rasterio, numpy, pandas, matplotlib
"""

import argparse
import importlib.util
import os
import re

import numpy as np
import pandas as pd
import rasterio

# reuse the embedding collapsed-census code
_spec = importlib.util.spec_from_file_location("cc", os.path.join(
    os.path.dirname(__file__), "collapsed_5class_confusion.py"))
cc = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(cc)

N_FRAME = cc.N_FRAME
LABELS5 = cc.LABELS5
NAMES5 = cc.NAMES5
SPEC_DIR = "data/raw/spectral_transferability_10class_percell"
EMB_COLLAPSED_LONG = "reports/collapsed_5class_confusion/metrics_long.csv"
OUT = "reports/spectral_composite_classified_maps/collapsed_5class"
EMB_VARIANTS = ["v2", "v3", "v4", "v5", "v6"]

# canonical variant palette, shared across the repo's figures; spec_all is the reference in black
VPAL = {"v2": "#1f77b4", "v3": "#2ca02c", "v4": "#9467bd", "v5": "#ff7f0e", "v6": "#d62728"}


EMB_PRED_DIR = "data/raw/transfer_predictions"


def build_census(cells, truth_desc):
    """Accumulate the per-cell collapsed matrices against the spectral spec_all map field.

    Returns the matrices, the skip list, and the scored cells (path, gid, bracket) so the embedding
    census can be built on the exact same cells for a like-for-like comparison.
    """
    cms, skipped, scored = [], [], []
    for cell in cells:
        with rasterio.open(cell) as ds:
            rf = ds.read(1)
        gid, bracket = cc._cell_bracket_gid(cell)
        pp = os.path.join(SPEC_DIR, bracket, f"pred_specall_{bracket}_cell{gid}.tif")
        if not os.path.exists(pp):
            skipped.append((gid, bracket, "no_spectral_pred"))
            continue
        with rasterio.open(pp) as pds:
            model = pds.read(1)
        if model.shape != rf.shape:
            skipped.append((gid, bracket, f"shape {model.shape} vs {rf.shape}"))
            continue
        # a spec_all raster that is entirely nodata is a missing prediction, not a valid map
        if not (model >= 1).any():
            skipped.append((gid, bracket, "blank_pred"))
            continue
        cm = cc.cell_confusion(rf, model)
        if cm.sum() > 0:
            cms.append(cm)
            scored.append((cell, gid, bracket))
    return np.array(cms), skipped, scored


def build_embedding_census(scored, variant):
    """Collapsed census for one embedding variant on the exact scored cells (fair comparison)."""
    band = cc.PRED_BAND[variant]
    cms = []
    for cell, gid, bracket in scored:
        with rasterio.open(cell) as ds:
            rf = ds.read(1)
        pp = os.path.join(EMB_PRED_DIR, bracket, f"pred_{bracket}_cell{gid}.tif")
        with rasterio.open(pp) as pds:
            model = pds.read(band)
        cm = cc.cell_confusion(rf, model)
        if cm.sum() > 0:
            cms.append(cm)
    return np.array(cms)


def _r(x):
    return round(float(x), 5) if np.isfinite(x) else ""


def write_metrics_long(pt, rci, bci, path):
    rows = []
    for mk in ["OA", "kappa", "macro_F1", "mean_IoU", "baseline_OA"]:
        r = rci.get(mk, (np.nan, np.nan, np.nan, np.nan))
        b = bci.get(mk, (np.nan, np.nan))
        rows.append(dict(variant="spec_all", scope="overall", cls="", metric=mk,
                         estimate=round(pt[mk], 5), ratio_se=_r(r[1]),
                         ratio_ci_lo=_r(r[2]), ratio_ci_hi=_r(r[3]),
                         boot_ci_lo=_r(b[0]), boot_ci_hi=_r(b[1]), support=""))
    for k in range(5):
        c = k + 1
        for metric in ["precision", "recall", "F1", "IoU"]:
            key = f"{metric}[{c}]"
            r = rci.get(key, (np.nan, np.nan, np.nan, np.nan))
            b = bci.get(key, (np.nan, np.nan))
            rows.append(dict(variant="spec_all", scope="class", cls=NAMES5[c], metric=metric,
                             estimate=_r(pt[key]), ratio_se=_r(r[1]),
                             ratio_ci_lo=_r(r[2]), ratio_ci_hi=_r(r[3]),
                             boot_ci_lo=_r(b[0]), boot_ci_hi=_r(b[1]),
                             support=int(pt[f"support[{c}]"])))
    pd.DataFrame(rows).to_csv(path, index=False)


def write_summary_txt(pt, n, n_blank, path):
    lines = ["collapsed 5-class census, spectral spec_all (model vs interpreted reference)",
             f"cells: {n} (adjudicated reference, spectral spec_all per-bracket map field) "
             f"from the {N_FRAME:,}-cell frame; FPC sqrt(1 - n/N) applied to ratio-estimator CIs",
             f"note: {n_blank} interpreted cells dropped because their spec_all prediction is entirely "
             f"nodata (out-of-sample brackets), so this census is on {n} cells, not 180",
             "",
             "OA is dominated by the ~98.5% Stable class. Read the all-Stable baseline and kappa,",
             "not OA alone.", "",
             f"{'source':10}{'OA':>8}{'all-Stable':>12}{'kappa':>8}{'macro-F1':>10}",
             f"{'spec_all':10}{pt['OA']:>8.3f}{pt['baseline_OA']:>12.3f}{pt['kappa']:>8.3f}"
             f"{pt['macro_F1']:>10.3f}",
             "",
             "macro-F1 averages 5 classes here vs 10 in the 10-class matrices; not comparable",
             "as a level. Full per-class precision/recall/F1/IoU with CIs in metrics_long.csv."]
    with open(path, "w") as fh:
        fh.write("\n".join(lines) + "\n")


def _caption(fig, text, top=1.0, width=125):
    import textwrap
    wrapped = "\n".join(textwrap.wrap(text, width))
    nlines = wrapped.count("\n") + 1
    fig.tight_layout(rect=[0, 0.02 + 0.035 * nlines, 1, top])
    fig.text(0.5, 0.01, wrapped, ha="center", va="bottom", fontsize=8, color="0.35")


def compare_figure(comp, n_cells, path):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    sources = ["spec_all"] + EMB_VARIANTS
    metrics_ = [("OA", "overall accuracy"), ("kappa", "Cohen's kappa"), ("macro_F1", "macro-F1")]
    fig, axes = plt.subplots(1, 3, figsize=(14, 4.4))
    for ax, (mk, title) in zip(axes, metrics_):
        vals = [comp[s][mk] for s in sources]
        colors = ["black"] + [VPAL[v] for v in EMB_VARIANTS]
        ax.bar(range(len(sources)), vals, color=colors, edgecolor="white", zorder=3)
        if mk == "OA":
            base = comp["spec_all"]["baseline_OA"]
            ax.axhline(base, color="firebrick", lw=1.5, ls="--", zorder=4,
                       label=f"all-Stable baseline {base:.3f}")
            ax.legend(fontsize=8, frameon=False)
        ax.set_xticks(range(len(sources)))
        ax.set_xticklabels(sources, rotation=45, ha="right", fontsize=9)
        ax.set_title(title, fontsize=10)
        ax.grid(False)
        for s in ("top", "right"):
            ax.spines[s].set_visible(False)
    fig.suptitle(f"collapsed 5-class census: spectral spec_all vs embedding variants "
                 f"(temporally matched, adjudicated reference, same {n_cells} cells)", fontsize=11)
    _caption(fig, "Overall accuracy, Cohen's kappa, and macro-F1 of the collapsed 5-class census for "
                  f"the spectral spec_all classifier and each embedding variant, on the same {n_cells} "
                  "cells. OA is dominated by the ~98.5% Stable class and stays below the all-Stable "
                  "baseline (dashed) for every source, so kappa is the honest read of change-detection "
                  "skill, and it stays near zero throughout.", top=0.92)
    fig.savefig(path, dpi=150, bbox_inches="tight")
    plt.close(fig)


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--truth", default="exports/truth_selections.csv",
                    help="adjudicated reviewer per location (matches the embedding collapsed basis)")
    args = ap.parse_args()
    os.makedirs(OUT, exist_ok=True)

    cells, mismatch = cc.select_by_truth(args.truth)
    if mismatch:
        print("STOP: truth reviewer with no matching raster:", mismatch); raise SystemExit(1)

    cms, skipped, scored = build_census(cells, args.truth)
    n = len(cms)
    blank = sorted((g, b) for g, b, why in skipped if why == "blank_pred")

    with open(os.path.join(OUT, "reference.txt"), "w") as fh:
        fh.write(f"reference points: adjudicated reviewer per location ({os.path.basename(args.truth)})\n"
                 f"map field: spectral spec_all per-bracket predictions ({SPEC_DIR})\n"
                 f"cells scored: {n} of {len(cells)} (dropped {len(blank)} cells whose spec_all "
                 f"prediction is entirely nodata)\n"
                 + "".join(f"  blank {b}: cell {g}\n" for g, b in blank))
    census = cms.sum(0)
    pt = cc.metrics(census)
    rci = cc.ratio_cis(cms, n, N_FRAME)
    bci = cc.bootstrap_cis(cms, n)
    fpc = np.sqrt(1 - n / N_FRAME)
    print(f"adjudicated interpreted cells scored against spec_all: {n}")
    if skipped:
        print(f"  skipped {len(skipped)}: {skipped[:5]}")
    print(f"  spec_all: cells={n}  valid_px={int(census.sum()):,}  OA={pt['OA']:.3f}  "
          f"baseline(all-Stable)={pt['baseline_OA']:.3f}  kappa={pt['kappa']:.3f}  "
          f"macroF1={pt['macro_F1']:.3f}  (FPC={fpc:.3f})")

    # matrices and figure
    pd.DataFrame(census, index=LABELS5, columns=LABELS5).to_csv(
        os.path.join(OUT, "confusion_specall_counts.csv"))
    with np.errstate(invalid="ignore"):
        rn = census / census.sum(1, keepdims=True)
    pd.DataFrame(np.round(rn, 4), index=LABELS5, columns=LABELS5).to_csv(
        os.path.join(OUT, "confusion_specall_rownorm.csv"))
    cc.plot_rownorm(census, "spec_all", pt, os.path.join(OUT, "confusion_specall.png"))

    write_metrics_long(pt, rci, bci, os.path.join(OUT, "metrics_long.csv"))
    write_summary_txt(pt, n, len(blank), os.path.join(OUT, "summary.txt"))

    # headline table via the reused writer (single spec_all row)
    variant_row = dict(
        variant="spec_all", n_cells=n, valid_px=int(census.sum()), baseline_OA=pt["baseline_OA"],
        OA_ci=cc.fmt_ci(pt["OA"], rci["OA"][2], rci["OA"][3]),
        kappa_ci=cc.fmt_ci(pt["kappa"], *bci["kappa"]),
        macroF1_ci=cc.fmt_ci(pt["macro_F1"], *bci["macro_F1"]),
        mIoU_ci=cc.fmt_ci(pt["mean_IoU"], *bci["mean_IoU"]))
    cc.write_tables([variant_row], OUT)

    # ---- comparison against the embedding collapsed census, on the SAME scored cells ----
    # embedding is recomputed on the exact cells spec_all classified, so the comparison carries no
    # cell-set confound from the blank spec_all predictions
    comp = {"spec_all": {"OA": pt["OA"], "kappa": pt["kappa"], "macro_F1": pt["macro_F1"],
                         "mean_IoU": pt["mean_IoU"], "baseline_OA": pt["baseline_OA"]}}
    for v in EMB_VARIANTS:
        ept = cc.metrics(build_embedding_census(scored, v).sum(0))
        comp[v] = {mk: float(ept[mk]) for mk in ["OA", "kappa", "macro_F1", "mean_IoU", "baseline_OA"]}
    # all sources are now on the same n scored cells
    ncells = {s: n for s in ["spec_all"] + EMB_VARIANTS}
    rows = [dict(source=s, n_cells=ncells[s], OA=round(comp[s]["OA"], 5),
                 all_stable_baseline=round(comp[s]["baseline_OA"], 5),
                 kappa=round(comp[s]["kappa"], 5), macro_F1=round(comp[s]["macro_F1"], 5),
                 mean_IoU=round(comp[s]["mean_IoU"], 5)) for s in ["spec_all"] + EMB_VARIANTS]
    pd.DataFrame(rows).to_csv(os.path.join(OUT, "comparison_collapsed.csv"), index=False)
    compare_figure(comp, n, os.path.join(OUT, "compare_collapsed_5class.png"))

    print("\ncollapsed comparison (OA / baseline / kappa / macroF1):")
    for s in ["spec_all"] + EMB_VARIANTS:
        c = comp[s]
        print(f"  {s:9} OA={c['OA']:.3f}  base={c['baseline_OA']:.3f}  "
              f"kappa={c['kappa']:.3f}  macroF1={c['macro_F1']:.3f}")
    print(f"\nwrote {OUT}/")


if __name__ == "__main__":
    main()
