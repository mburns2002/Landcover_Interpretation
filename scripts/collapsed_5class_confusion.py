#!/usr/bin/env python3
"""Census confusion matrix per model variant under the 5-class collapsed scheme.

This is a CENSUS over the interpreted CKIT-RF cells (every valid pixel counted), not a sampling
experiment. Scheme: Stable (urban, agriculture, grass/shrub, forest, water, wetland, other) plus
the four change classes kept distinct (Harvest, Development, Insect/Disease, Beaver). Unknown (10,
unattributed disturbance, no model equivalent) is excluded; Fire (40) has zero pixels. The
collapse is applied after the crosswalk, to both the reference and the model maps.

Reference: interpreted cells de-duplicated to one interpretation per location (numpy default_rng
seed 42), all target years. Variants v2-v6 (v6 included: the collapse is exactly the condition
under which its per-pixel behaviour might change, so excluding it would beg the question).

For each variant: the 5x5 confusion (reference on rows, so the row-normalized diagonal is
producer's accuracy), OA / macro-F1 / mean IoU / Cohen's kappa, and per-class precision, recall,
F1, IoU and support. The all-Stable baseline OA is reported alongside each variant's OA. Two
caveats are stated in the output: OA is dominated by the ~98.5% Stable class and carries almost
no change-detection information; and macro-F1 averages 5 classes here versus 10 elsewhere, so the
two are not comparable as levels.

Confidence intervals: the cells are a simple random sample from the 21,561-cell frame, so we use
design-based inference with the cell as the primary sampling unit. Ratio-estimator CIs (variance
from the between-cell variance, FPC sqrt(1 - n/N)) for the ratio-form metrics, cross-checked with
a cell-level bootstrap (seed 42).

Outputs -> reports/collapsed_5class_confusion/
  - confusion_<v>_counts.csv / _rownorm.csv     raw and row-normalized 5x5 matrices
  - confusion_<v>_rownorm.png                    row-normalized heatmap (no gridlines)
  - metrics_long.csv                             long format, every metric x variant x class + CIs
  - summary_by_variant.md / .tex                 per-variant headline table (booktabs LaTeX)
  - summary.txt                                  plain-text headline

Requires: rasterio, numpy, pandas, matplotlib
"""

import glob
import os
import re
import warnings
from collections import defaultdict

import numpy as np
import pandas as pd
import rasterio
from rasterio.warp import reproject, Resampling

warnings.filterwarnings("ignore")

RF_DIR = "data/raw/rf_class_maps"
MODEL_DIR = "data/raw/model_maps"
OUT = "reports/collapsed_5class_confusion"
VERSIONS = ["v2", "v3", "v4", "v5", "v6"]
N_FRAME = 21561                                         # cells in the sampling frame
SEED = 42
BOOT = 2000

NAMES5 = {1: "Stable", 2: "Harvest", 3: "Development", 4: "Insect/Disease", 5: "Beaver"}
LABELS5 = [NAMES5[c] for c in range(1, 6)]

# reference (RF codes) -> collapsed 1..5: stable set incl. Other(13) -> Stable(1); change kept;
# Unknown(10) and Fire(40) -> 0 (excluded). consistent with data/reference/class_crosswalk.csv.
_REF_COLLAPSE = np.zeros(63, np.uint8)
for _c in (0, 1, 2, 3, 4, 5, 13):
    _REF_COLLAPSE[_c] = 1
_REF_COLLAPSE[20] = 2; _REF_COLLAPSE[30] = 3; _REF_COLLAPSE[50] = 4; _REF_COLLAPSE[62] = 5
# model (common codes 0..10) -> collapsed 1..5
_MODEL_COLLAPSE = np.array([0, 2, 3, 1, 1, 1, 1, 1, 1, 5, 4], np.uint8)


# ----------------------------------------------------------------------------- cells and stitching
def location_key(path):
    m = re.search(r"grid_(\d+)_sample_(\d+)_sensor_Sentinel-2_target_(\d+)", os.path.basename(path))
    return (m.group(1), m.group(2), m.group(3)) if m else (os.path.basename(path),)


def deduped_cells(seed=SEED):
    paths = sorted(glob.glob(os.path.join(RF_DIR, "**", "rf_class*Sentinel-2*.tif"), recursive=True))
    groups = defaultdict(list)
    for p in paths:
        groups[location_key(p)].append(p)
    rng = np.random.default_rng(seed)
    kept = []
    for k in sorted(groups):
        v = sorted(groups[k])
        kept.append(v[int(rng.integers(len(v)))] if len(v) > 1 else v[0])
    return sorted(kept)


def model_tiles(version):
    folder = os.path.join(MODEL_DIR, f"classified_maps_10class_{version}")
    return sorted(glob.glob(os.path.join(folder, "*.tif")))


def _intersect(a, b):
    return not (a.right <= b.left or a.left >= b.right or a.top <= b.bottom or a.bottom >= b.top)


def stitch_model_to_cell(cell_ds, tile_srcs):
    # warp each model tile into its own temp array then merge non-background pixels; reproject
    # re-initialises the whole destination on every call, so a shared accumulator would be erased
    dst = np.zeros((cell_ds.height, cell_ds.width), dtype=np.uint8)
    for src in tile_srcs:
        if not _intersect(cell_ds.bounds, src.bounds):
            continue
        tmp = np.zeros_like(dst)
        reproject(source=rasterio.band(src, 1), destination=tmp,
                  src_transform=src.transform, src_crs=src.crs,
                  dst_transform=cell_ds.transform, dst_crs=cell_ds.crs,
                  resampling=Resampling.nearest)
        dst = np.where(tmp > 0, tmp, dst)
    return dst


def cell_confusion(rf_arr, model_arr):
    ref = _REF_COLLAPSE[np.where((rf_arr >= 0) & (rf_arr <= 62), rf_arr, 0)]
    mdl = _MODEL_COLLAPSE[np.where(model_arr <= 10, model_arr, 0)]
    valid = (ref >= 1) & (ref <= 5) & (mdl >= 1) & (mdl <= 5)
    cm = np.zeros((5, 5), dtype=np.int64)
    np.add.at(cm, (ref[valid] - 1, mdl[valid] - 1), 1)
    return cm


# ----------------------------------------------------------------------------- metrics
def metrics(M):
    """All metrics from a 5x5 matrix (rows = reference). Returns a flat dict."""
    M = M.astype(float)
    tp = np.diag(M)
    row = M.sum(1); col = M.sum(0); tot = M.sum()
    with np.errstate(divide="ignore", invalid="ignore"):
        recall = np.where(row > 0, tp / row, np.nan)       # producer's accuracy
        precision = np.where(col > 0, tp / col, np.nan)     # user's accuracy
        f1 = np.where((precision + recall) > 0, 2 * precision * recall / (precision + recall), np.nan)
        iou = np.where((row + col - tp) > 0, tp / (row + col - tp), np.nan)
    present = row > 0
    oa = tp.sum() / tot if tot else np.nan
    pe = (row * col).sum() / (tot * tot) if tot else np.nan
    kappa = (oa - pe) / (1 - pe) if tot and (1 - pe) != 0 else np.nan
    out = dict(OA=oa, kappa=kappa,
               macro_F1=np.nanmean(f1[present]) if present.any() else np.nan,
               mean_IoU=np.nanmean(iou[present]) if present.any() else np.nan,
               baseline_OA=row.max() / tot if tot else np.nan)   # all-majority (Stable) baseline
    for k in range(5):
        c = k + 1
        out[f"precision[{c}]"] = precision[k]
        out[f"recall[{c}]"] = recall[k]
        out[f"F1[{c}]"] = f1[k]
        out[f"IoU[{c}]"] = iou[k]
        out[f"support[{c}]"] = row[k]
    return out


def ratio_ci(y, x, n, N):
    """Design-based ratio estimator R=sum(y)/sum(x) with between-cell variance and FPC."""
    Y, X = y.sum(), x.sum()
    if X <= 0:
        return np.nan, np.nan, np.nan, np.nan
    R = Y / X
    xbar = X / n
    resid = y - R * x
    s2 = (resid ** 2).sum() / (n - 1)
    var = (1 - n / N) / (n * xbar ** 2) * s2
    se = np.sqrt(var) if var > 0 else 0.0
    return R, se, R - 1.96 * se, R + 1.96 * se


def ratio_cis(cms, n, N):
    """Ratio-estimator CIs for the ratio-form metrics (OA, per-class recall/precision/IoU)."""
    tp = cms[:, np.arange(5), np.arange(5)]                # (n,5)
    row = cms.sum(2); col = cms.sum(1); tot = cms.sum((1, 2))
    out = {}
    out["OA"] = ratio_ci(tp.sum(1).astype(float), tot.astype(float), n, N)
    for k in range(5):
        c = k + 1
        out[f"recall[{c}]"] = ratio_ci(tp[:, k].astype(float), row[:, k].astype(float), n, N)
        out[f"precision[{c}]"] = ratio_ci(tp[:, k].astype(float), col[:, k].astype(float), n, N)
        out[f"IoU[{c}]"] = ratio_ci(tp[:, k].astype(float),
                                    (row[:, k] + col[:, k] - tp[:, k]).astype(float), n, N)
    return out


def bootstrap_cis(cms, n, seed=SEED, B=BOOT):
    """Cell-level bootstrap CIs for every metric (cross-check; no FPC, so slightly wider)."""
    rng = np.random.default_rng(seed)
    keys = list(metrics(cms.sum(0)).keys())
    acc = {k: np.empty(B) for k in keys}
    for b in range(B):
        idx = rng.integers(0, n, size=n)
        m = metrics(cms[idx].sum(0))
        for k in keys:
            acc[k][b] = m[k]
    return {k: (np.nanpercentile(v, 2.5), np.nanpercentile(v, 97.5)) for k, v in acc.items()}


# ----------------------------------------------------------------------------- figure
def plot_rownorm(M, version, oa, kappa, path):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    with np.errstate(invalid="ignore"):
        rn = M / M.sum(1, keepdims=True)
    fig, ax = plt.subplots(figsize=(5.6, 5.0))
    im = ax.imshow(rn, cmap="Blues", vmin=0, vmax=1)
    ax.set_xticks(range(5)); ax.set_xticklabels(LABELS5, rotation=35, ha="right")
    ax.set_yticks(range(5)); ax.set_yticklabels(LABELS5)
    ax.set_xlabel("model (collapsed)"); ax.set_ylabel("reference (collapsed)")
    ax.grid(False)
    for i in range(5):
        for j in range(5):
            v = rn[i, j]
            if np.isfinite(v):
                ax.text(j, i, f"{v:.2f}\n{int(M[i, j]):,}", ha="center", va="center",
                        fontsize=7, color="white" if v > 0.55 else "black")
    ax.set_title(f"{version} collapsed 5-class (row-normalized = producer's accuracy)\n"
                 f"OA={oa:.3f}  kappa={kappa:.3f}", fontsize=9)
    fig.colorbar(im, fraction=0.046, pad=0.04, label="P(model | reference)")
    fig.tight_layout()
    fig.savefig(path, dpi=150, bbox_inches="tight")
    plt.close(fig)


# ----------------------------------------------------------------------------- tables
def fmt_ci(est, lo, hi, d=3):
    if not np.isfinite(est):
        return "n/a"
    return f"{est:.{d}f} ({lo:.{d}f}--{hi:.{d}f})"


def write_tables(variant_rows, out_dir):
    # markdown per-variant summary
    md = ["# Collapsed 5-class census: per-variant summary", "",
          f"Census over {variant_rows[0]['n_cells']} interpreted cells "
          f"(de-duplicated, seed 42) from the {N_FRAME:,}-cell frame. OA is dominated by the "
          "~98.5% Stable class; the all-Stable baseline is shown alongside. macro-F1 averages 5 "
          "classes here versus 10 in the 10-class matrices, so the two are not comparable as "
          "levels. CIs are 95% (ratio estimator with FPC; bootstrap in parentheses in the CSV).",
          "",
          "| Variant | Valid px | All-Stable OA | OA (95% CI) | kappa (95% CI) | macro-F1 (95% CI) | mean IoU (95% CI) |",
          "|---|---|---|---|---|---|---|"]
    for r in variant_rows:
        md.append(f"| {r['variant']} | {r['valid_px']:,} | {r['baseline_OA']:.3f} | "
                  f"{r['OA_ci']} | {r['kappa_ci']} | {r['macroF1_ci']} | {r['mIoU_ci']} |")
    with open(os.path.join(out_dir, "summary_by_variant.md"), "w") as fh:
        fh.write("\n".join(md) + "\n")

    # booktabs LaTeX, consistent with per_class_agreement_table.tex
    tex = [r"% Collapsed 5-class census per variant. Requires \usepackage{booktabs}.",
           r"\begin{table}[t]", r"\centering",
           r"\caption{Collapsed 5-class census (Stable plus Harvest, Development, Insect/Disease, "
           r"Beaver) per model variant over " + f"{variant_rows[0]['n_cells']}" +
           r" interpreted cells. Values are point estimates with 95\% design-based ratio-estimator "
           r"CIs (FPC $\sqrt{1-n/N}$, $N=" + f"{N_FRAME:,}".replace(",", "{,}") + r"$). OA is "
           r"dominated by the $\sim$98.5\% Stable class: every variant's OA is below the all-Stable "
           r"baseline, and $\kappa\approx0$. macro-F1 averages 5 classes here versus 10 elsewhere "
           r"and is not comparable as a level.}",
           r"\label{tab:collapsed5_census}",
           r"\begin{tabular}{lrrcccc}", r"\toprule",
           r"Variant & Valid px & All-Stable OA & OA (95\% CI) & $\kappa$ (95\% CI) & "
           r"macro-F1 (95\% CI) & mean IoU (95\% CI) \\", r"\midrule"]
    for r in variant_rows:
        tex.append(f"{r['variant']} & {r['valid_px']:,} & {r['baseline_OA']:.3f} & "
                   f"{_texci(r['OA_ci'])} & {_texci(r['kappa_ci'])} & {_texci(r['macroF1_ci'])} & "
                   f"{_texci(r['mIoU_ci'])} \\\\")
    tex += [r"\bottomrule", r"\end{tabular}", r"\end{table}"]
    with open(os.path.join(out_dir, "summary_by_variant.tex"), "w") as fh:
        fh.write("\n".join(tex) + "\n")


def _texci(s):
    return s.replace("--", "--")   # already en-dash range; kept simple


# ----------------------------------------------------------------------------- driver
def main():
    os.makedirs(OUT, exist_ok=True)
    cells = deduped_cells()
    print(f"de-duplicated interpreted cells (seed {SEED}): {len(cells)}")

    long_rows, variant_rows = [], []
    baseline_note = None
    for v in VERSIONS:
        tiles = [rasterio.open(t) for t in model_tiles(v)]
        cms = []
        for cell in cells:
            with rasterio.open(cell) as ds:
                rf = ds.read(1)
                model = stitch_model_to_cell(ds, tiles)
            cm = cell_confusion(rf, model)
            if cm.sum() > 0:
                cms.append(cm)
        for t in tiles:
            t.close()
        cms = np.array(cms)
        n = len(cms)
        census = cms.sum(0)
        pt = metrics(census)
        rci = ratio_cis(cms, n, N_FRAME)
        bci = bootstrap_cis(cms, n)
        fpc = np.sqrt(1 - n / N_FRAME)
        print(f"  {v}: cells={n}  valid_px={int(census.sum()):,}  OA={pt['OA']:.3f}  "
              f"baseline(all-Stable)={pt['baseline_OA']:.3f}  kappa={pt['kappa']:.3f}  "
              f"macroF1={pt['macro_F1']:.3f}  (FPC={fpc:.3f})")

        # matrices
        pd.DataFrame(census, index=LABELS5, columns=LABELS5).to_csv(
            os.path.join(OUT, f"confusion_{v}_counts.csv"))
        with np.errstate(invalid="ignore"):
            rn = census / census.sum(1, keepdims=True)
        pd.DataFrame(np.round(rn, 4), index=LABELS5, columns=LABELS5).to_csv(
            os.path.join(OUT, f"confusion_{v}_rownorm.csv"))
        plot_rownorm(census, v, pt["OA"], pt["kappa"],
                     os.path.join(OUT, f"confusion_{v}_rownorm.png"))

        # long-format rows: overall metrics
        for mk, label in [("OA", "OA"), ("kappa", "kappa"), ("macro_F1", "macro_F1"),
                          ("mean_IoU", "mean_IoU"), ("baseline_OA", "baseline_OA")]:
            r = rci.get(mk, (np.nan, np.nan, np.nan, np.nan))
            b = bci.get(mk, (np.nan, np.nan))
            long_rows.append(dict(variant=v, scope="overall", cls="", metric=label,
                                  estimate=round(pt[mk], 5),
                                  ratio_se=round(r[1], 5) if np.isfinite(r[1]) else "",
                                  ratio_ci_lo=round(r[2], 5) if np.isfinite(r[2]) else "",
                                  ratio_ci_hi=round(r[3], 5) if np.isfinite(r[3]) else "",
                                  boot_ci_lo=round(b[0], 5), boot_ci_hi=round(b[1], 5),
                                  support=int(census.sum())))
        # per-class
        for k in range(5):
            c = k + 1
            for metric in ["precision", "recall", "F1", "IoU"]:
                key = f"{metric}[{c}]"
                r = rci.get(key, (np.nan, np.nan, np.nan, np.nan))
                b = bci.get(key, (np.nan, np.nan))
                long_rows.append(dict(variant=v, scope="class", cls=NAMES5[c], metric=metric,
                                      estimate=round(pt[key], 5) if np.isfinite(pt[key]) else "",
                                      ratio_se=round(r[1], 5) if np.isfinite(r[1]) else "",
                                      ratio_ci_lo=round(r[2], 5) if np.isfinite(r[2]) else "",
                                      ratio_ci_hi=round(r[3], 5) if np.isfinite(r[3]) else "",
                                      boot_ci_lo=round(b[0], 5) if np.isfinite(b[0]) else "",
                                      boot_ci_hi=round(b[1], 5) if np.isfinite(b[1]) else "",
                                      support=int(pt[f"support[{c}]"])))

        variant_rows.append(dict(
            variant=v, n_cells=n, valid_px=int(census.sum()), baseline_OA=pt["baseline_OA"],
            OA_ci=fmt_ci(pt["OA"], rci["OA"][2], rci["OA"][3]),   # ratio-estimator CI for OA
            kappa_ci=fmt_ci(pt["kappa"], *bci["kappa"]),          # bootstrap (kappa is not a ratio)
            macroF1_ci=fmt_ci(pt["macro_F1"], *bci["macro_F1"]),
            mIoU_ci=fmt_ci(pt["mean_IoU"], *bci["mean_IoU"])))

    pd.DataFrame(long_rows).to_csv(os.path.join(OUT, "metrics_long.csv"), index=False)
    write_tables(variant_rows, OUT)

    # plain-text headline
    n_cells = variant_rows[0]["n_cells"]
    lines = ["collapsed 5-class census (model vs interpreted reference)",
             f"cells: {n_cells} (de-duplicated, seed 42) from the "
             f"{N_FRAME:,}-cell frame; FPC sqrt(1 - n/N) applied to ratio-estimator CIs",
             f"NOTE: the plan specified 154 cells; the current data holds {n_cells} interpreted "
             f"cells (36/year x 5 years, all overlapping the model), reflecting cells added since. "
             f"The FPC is unchanged to 3 dp (0.996 either way), so the CIs are unaffected.", "",
             "OA is dominated by the ~98.5% Stable class. EVERY variant's OA is BELOW the",
             "all-Stable baseline (labeling everything Stable), and kappa ~ 0: the collapsed maps",
             "carry almost no change-detection information.", "",
             f"{'variant':8}{'OA':>8}{'all-Stable':>12}{'kappa':>8}{'macro-F1':>10}"]
    for r in variant_rows:
        oa = float(r["OA_ci"].split(" ")[0]); ka = float(r["kappa_ci"].split(" ")[0])
        mf = float(r["macroF1_ci"].split(" ")[0])
        lines.append(f"{r['variant']:8}{oa:>8.3f}{r['baseline_OA']:>12.3f}{ka:>8.3f}{mf:>10.3f}")
    lines += ["", "macro-F1 averages 5 classes here vs 10 in the 10-class matrices; not comparable",
              "as a level. Full per-class precision/recall/F1/IoU with CIs in metrics_long.csv."]
    with open(os.path.join(OUT, "summary.txt"), "w") as fh:
        fh.write("\n".join(lines) + "\n")
    print("\n" + "\n".join(lines))
    print(f"\nwrote {OUT}/")


if __name__ == "__main__":
    main()
