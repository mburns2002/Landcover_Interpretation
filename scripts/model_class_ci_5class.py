#!/usr/bin/env python3
"""Per-class model F1 vs the adjudicated reference, overlaid on the inter-interpreter ceiling.

The companion figure `reports/interpreter_agreement/per_class_agreement_forest_5class.png` shows how
well two humans agree per class in the 5-class collapsed scheme. This script computes the same kind of
per-class F1 for each PREDICTION source (embedding variants v2-v6 and spectral spec_all) against the
adjudicated interpreted reference, and draws one forest plot per model that places the model's per-class
F1 next to the inter-interpreter agreement for the same class. The interpreter bar is the reliability
ceiling: where two humans barely agree on a class, a model cannot be scored above that reference noise.

Method (mirrors interpreter_class_ci.py so the two are comparable):
  - reference: adjudicated CKIT cell, crosswalked to the 10-class schema then collapsed to 5 classes
    (Stable plus Harvest, Development, Insect/Disease, Beaver); Other folds into Stable, Unknown is dropped.
  - prediction: the source's 10-class map collapsed with the same 10-to-5 map.
  - per class F1 = 2*TP / (reference support + predicted support), pooled over all usable cells.
  - CI: cluster (cell) bootstrap resamples the cells with replacement, re-pools their 5x5 confusion
    matrices, and recomputes each class F1, matching the interpreter cluster (pair) bootstrap.
  - each model is scored on its own full set of usable cells (spec_all has entirely-nodata rasters the
    embeddings do not), so N is reported per model and the figures are read one model at a time.

Outputs -> reports/model_vs_interpreter_5class/
  - model_per_class_ci_5class.csv          one row per (source, class): F1 point plus CI, IoU, tiers
  - forest_5class_<source>.png             per model: model F1 vs interpreter agreement, per class
  - note.md

Requires: rasterio, numpy, pandas, matplotlib
"""

import argparse
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


pcf = _load("pcf", "per_cell_f1_5class.py")                 # per-cell loading, sources, colors
ICI = _load("ICI", "interpreter_class_ci.py")               # per_class, ci, tier, thresholds
bmc = pcf.bmc

TRUTH = "exports/truth_selections.csv"
OUT = "reports/model_vs_interpreter_5class"
SOURCES = pcf.SOURCES                                        # v2..v6, spec_all
NAMES5 = pcf.NAMES5
ORDER = [1, 2, 3, 4, 5]                                      # Stable, Harvest, Development, Insect, Beaver
SRC_COLOR = pcf.SRC_COLOR
INTERP_CI = "reports/interpreter_agreement/per_class_agreement_ci_5class.csv"
HIGH, MOD = ICI.HIGH, ICI.MOD


def cell_confusions(truth_path):
    """Return {source: [(cell_id, 5x5 confusion), ...]} for model prediction vs collapsed reference."""
    ref_index = bmc.build_reference_index()
    truth = bmc.load_truth(truth_path)
    chosen_ref, n_multi, missing, mismatch = bmc.choose_references_truth(ref_index, truth)
    if mismatch:
        print("STOP: truth reviewer with no matching raster:", mismatch[:10]); raise SystemExit(1)

    cells = {}
    for cid, rp in chosen_ref.items():
        m = re.search(r"opt_(\d{4}_\d{4})", os.path.basename(rp))
        if m:
            cells[cid] = m.group(1)

    per_source = {s: [] for s in SOURCES}
    drops = defaultdict(list)
    ref_valid_cells = set()
    for cid in sorted(cells):
        bracket = cells[cid]
        with rasterio.open(chosen_ref[cid]) as rds:
            ref_raw = rds.read(1)
            meta = (rds.width, rds.height, rds.transform, rds.crs)
        ref5 = pcf.cc.collapse_reference(ref_raw)       # canonical: Other(13) -> Stable, Unknown -> drop
        ref_valid = (ref5 >= 1) & (ref5 <= 5)
        if not ref_valid.any():
            drops["reference_no_valid_px"].append(cid)
            continue
        ref_valid_cells.add(cid)
        for s in SOURCES:
            pp, band = pcf.source_pred(s, bracket, cid)
            if not os.path.exists(pp):
                drops[f"{s}_missing_pred"].append(cid)
                continue
            with rasterio.open(pp) as pds:
                if not pcf.grids_match_meta(pds, meta):
                    drops[f"{s}_grid_mismatch"].append(cid)
                    continue
                pred_raw = pds.read(band)
            if not (pred_raw >= 1).any():
                drops[f"{s}_blank_pred"].append(cid)
                continue
            pred5 = pcf.cc.collapse_prediction(pred_raw)
            valid = ref_valid & (pred5 >= 1) & (pred5 <= 5)
            M = np.zeros((5, 5), np.int64)
            np.add.at(M, (ref5[valid] - 1, pred5[valid] - 1), 1)   # rows = reference, cols = prediction
            per_source[s].append((cid, M))
    return per_source, ref_valid_cells, drops


def source_table(stack, boot, seed):
    """Pooled per-class F1 (+IoU) with a cluster (cell) bootstrap CI, as a DataFrame over ORDER."""
    pooled = stack.sum(0)
    f1_pt, iou_pt = ICI.per_class(pooled)
    support = (pooled.sum(0) + pooled.sum(1) - np.diag(pooled))      # union pixels per class
    n_cells_cls = np.array([int(((stack[:, k, :].sum(1) + stack[:, :, k].sum(1)) > 0).sum())
                            for k in range(5)])
    rng = np.random.default_rng(seed)
    n = stack.shape[0]
    bf1 = np.full((boot, 5), np.nan)
    biou = np.full((boot, 5), np.nan)
    for b in range(boot):
        idx = rng.integers(0, n, n)
        cmb = stack[idx].sum(0)
        bf1[b], biou[b] = ICI.per_class(cmb)
    rows = []
    for k, c in enumerate(ORDER):
        if support[k] == 0:
            continue
        f1lo, f1hi = ICI.ci(bf1[:, k])
        iolo, iohi = ICI.ci(biou[:, k])
        rows.append(dict(code=c, cls=NAMES5[c], n_cells=int(n_cells_cls[k]), support_px=int(support[k]),
                         f1=round(float(f1_pt[k]), 3), f1_lo=round(f1lo, 3), f1_hi=round(f1hi, 3),
                         iou=round(float(iou_pt[k]), 3), iou_lo=round(iolo, 3), iou_hi=round(iohi, 3),
                         reliability=ICI.tier(f1_pt[k])))
    return pd.DataFrame(rows), n


def _caption(fig, text, top=1.0, width=118):
    import textwrap
    wrapped = "\n".join(textwrap.wrap(text, width))
    nlines = wrapped.count("\n") + 1
    fig.tight_layout(rect=[0, 0.02 + 0.05 * nlines, 1, top])
    fig.text(0.5, 0.01, wrapped, ha="center", va="bottom", fontsize=8, color="0.35")


def forest_overlay(model_df, interp_df, source, color, n_cells, path):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    from matplotlib.lines import Line2D

    md = model_df.set_index("code")
    idf = interp_df.set_index("code")
    y = np.arange(len(ORDER))                               # 0..4, Stable at top after invert
    dy = 0.17
    fig, ax = plt.subplots(figsize=(8.5, 0.7 * len(ORDER) + 2.0))
    for i, c in enumerate(ORDER):
        # interpreter agreement (human ceiling): grey diamond just above the class line
        if c in idf.index:
            r = idf.loc[c]
            ax.plot([r.f1_lo, r.f1_hi], [i - dy, i - dy], color="0.55", lw=2, zorder=1)
            ax.scatter(r.f1, i - dy, color="0.35", marker="D", s=42, zorder=3)
        # model vs reference: the source colour just below the class line
        if c in md.index:
            r = md.loc[c]
            ax.plot([r.f1_lo, r.f1_hi], [i + dy, i + dy], color=color, lw=2, zorder=1)
            ax.scatter(r.f1, i + dy, color=color, marker="o", s=48, zorder=3)

    ax.set_yticks(y)
    ax.set_yticklabels([f"{NAMES5[c]}\n(n={int(md.loc[c].n_cells) if c in md.index else 0} cells)"
                        for c in ORDER])
    ax.invert_yaxis()                                       # Stable at top
    ax.axvline(HIGH, ls="--", lw=0.8, color="gray"); ax.axvline(MOD, ls="--", lw=0.8, color="gray")
    ax.set_xlim(0, 1)
    ax.set_xlabel("per-class F1 (95% CI)")
    ax.set_ylim(len(ORDER) - 0.5, -0.5)
    ax.grid(False)
    for sp in ("top", "right"):
        ax.spines[sp].set_visible(False)
    ax.set_title(f"{source}: per-class F1 vs the inter-interpreter agreement ceiling\n"
                 f"(5-class scheme, N = {n_cells} cells; dashed: Low/Moderate/High thresholds)",
                 fontsize=11)
    handles = [Line2D([], [], color=color, marker="o", ls="", ms=8, label=f"{source} vs reference"),
               Line2D([], [], color="0.35", marker="D", ls="", ms=8, label="interpreter agreement")]
    ax.legend(handles=handles, loc="lower right", fontsize=9, frameon=True, framealpha=0.9)
    _caption(fig, f"Per-class F1 in the 5-class collapsed scheme for {source} (colored circle) scored "
                  "against the adjudicated interpreted reference, next to the inter-interpreter agreement "
                  "for the same class (grey diamond), each with its 95% bootstrap confidence interval. "
                  "The model uses a cluster (cell) bootstrap and the interpreter a cluster (pair) "
                  "bootstrap. The interpreter bar is the reliability ceiling: where two humans barely "
                  "agree, such as Development, Insect/Disease, and Beaver, the model score is bounded by "
                  "reference noise rather than model error alone, so the gap to the grey diamond, not the "
                  "absolute F1, is the reducible part.")
    fig.savefig(path, dpi=150, bbox_inches="tight")
    plt.close(fig)


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--truth", default=TRUTH)
    ap.add_argument("--boot", type=int, default=2000, help="bootstrap replicates (default: 2000)")
    ap.add_argument("--seed", type=int, default=0)
    args = ap.parse_args()
    os.makedirs(OUT, exist_ok=True)

    interp_df = pd.read_csv(INTERP_CI)
    per_source, ref_valid_cells, drops = cell_confusions(args.truth)
    print(f"reference-valid cells: {len(ref_valid_cells)}")

    all_rows = []
    n_by_source = {}
    for s in SOURCES:
        stack = np.stack([M for _, M in per_source[s]])
        df, n = source_table(stack, args.boot, args.seed)
        n_by_source[s] = n
        forest_overlay(df, interp_df, s, SRC_COLOR[s], n, os.path.join(OUT, f"forest_5class_{s}.png"))
        df.insert(0, "source", s)
        all_rows.append(df)
        print(f"  {s:9} cells={n:3d}  " +
              "  ".join(f"{NAMES5[r.code]}={r.f1:.2f}" for r in df.itertuples()))

    out_df = pd.concat(all_rows, ignore_index=True)
    out_df.to_csv(os.path.join(OUT, "model_per_class_ci_5class.csv"), index=False)
    write_note(out_df, interp_df, n_by_source, ref_valid_cells, drops, args.boot)
    print(f"\noutputs -> {OUT}/")


def write_note(out_df, interp_df, n_by_source, ref_valid_cells, drops, boot):
    idf = interp_df.set_index("cls")
    lines = [
        "# model_vs_interpreter_5class",
        "",
        "Per-class F1 in the 5-class collapsed scheme for each prediction source (embedding v2-v6 and "
        "spectral spec_all) against the adjudicated interpreted reference, drawn next to the "
        "inter-interpreter agreement ceiling for the same class. Generated by "
        "`scripts/model_class_ci_5class.py`. One forest plot per model.",
        "",
        "## Why overlay the interpreter agreement",
        "",
        "The inter-interpreter forest (`reports/interpreter_agreement/per_class_agreement_forest_5class"
        ".png`) shows that two humans agree almost perfectly on Stable and well on Harvest, but barely "
        "on Development, Insect/Disease, and Beaver. A model evaluated against a single interpretation "
        "of those weak classes is bounded by that reference noise, so the interpreter bar is the "
        "ceiling and the gap from the model dot to the grey diamond, not the raw F1, is the reducible "
        "error.",
        "",
        "## Method",
        "",
        "F1 per class = 2*TP / (reference support + predicted support), pooled over the usable cells "
        "with reference on rows and prediction on columns. The reference is the adjudicated CKIT cell "
        "collapsed to 5 classes with Other folded into Stable and Unknown excluded. "
        f"Confidence intervals use a cluster (cell) bootstrap ({boot} replicates) that resamples cells "
        "with replacement and re-pools their confusion matrices, mirroring the cluster (pair) bootstrap "
        "used for the interpreter agreement. Each model is scored on its own full set of usable cells, "
        "so N differs across models (spec_all has entirely-nodata rasters the embeddings do not) and "
        "the figures are read one model at a time.",
        "",
        f"Reference-valid cells: {len(ref_valid_cells)}. Usable cells per model: "
        + ", ".join(f"{s}={n}" for s, n in n_by_source.items()) + ".",
        "",
        "## Interpreter agreement ceiling (5-class)",
        "",
        "| Class | Interpreter F1 (95% CI) | Reliability |",
        "|-------|-------------------------|-------------|",
    ]
    for c in ORDER:
        nm = NAMES5[c]
        r = idf.loc[nm]
        lines.append(f"| {nm} | {r.f1:.2f} ({r.f1_lo:.2f}-{r.f1_hi:.2f}) | {r.reliability} |")
    lines += [
        "",
        "## Model per-class F1 (point estimate)",
        "",
        "| Source | " + " | ".join(NAMES5[c] for c in ORDER) + " |",
        "|--------|" + "|".join(["------"] * len(ORDER)) + "|",
    ]
    for s in n_by_source:
        sub = out_df[out_df.source == s].set_index("code")
        vals = " | ".join(f"{sub.loc[c].f1:.2f}" if c in sub.index else "-" for c in ORDER)
        lines.append(f"| {s} | {vals} |")
    lines += [
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
        "## Outputs",
        "",
        "- `model_per_class_ci_5class.csv`: one row per (source, class) with F1 and IoU point estimates, "
        "95% CI bounds, cell and pixel support, and the reliability tier.",
        "- `forest_5class_<source>.png`: one forest plot per model, model F1 (colored circle) next to "
        "the inter-interpreter agreement (grey diamond) per class.",
    ]
    with open(os.path.join(OUT, "note.md"), "w") as fh:
        fh.write("\n".join(lines) + "\n")


if __name__ == "__main__":
    main()
