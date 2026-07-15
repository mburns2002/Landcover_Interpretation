#!/usr/bin/env python3
"""Spatial-structure diagnostics for the model maps and the interpreted cells.

`neighbor_change` cleanly separates the speckly v6 but barely distinguishes the
smooth variants (v2/v3/v5). These richer diagnostics capture spatial grain:

  - mean patch size per class -- connected-component labeling (8-connectivity) on
    each class mask; a patch is a contiguous run of one class.
  - Moran's I on the class raster -- global spatial autocorrelation (queen/8-neighbor
    contiguity). High = smooth, near 0 = per-pixel noise.

Both are computed on the interpreted cells too, so the interpretations act as the
reference scale (not an absolute target). To keep the comparison fair, the model is
measured **within the same interpreted-cell footprints** (same 10 m window size), and
both maps are put on the common 10-class scheme via the crosswalk.

Note on Moran's I: class codes are nominal, so treat the value as a smoothness
diagnostic (structure vs. speckle), not a quantitative autocorrelation of a
meaningful variable.

Outputs (reports/spatial_structure/):
  - spatial_structure_summary.csv        per source: patches, mean/median patch, Moran's I
  - patch_size_by_class.csv              per source x class
  - patch_size_ecdf.png                  patch-size ECDF, all sources vs interpreted
  - patch_size_hist_smallmultiples.png   per-variant distribution vs interpreted
  - mean_patch_size_by_class.png         per-class mean patch size by source
  - morans_i_by_source.png               Moran's I by source (interpreted = reference)

Usage:
    python scripts/spatial_structure.py
    python scripts/spatial_structure.py --targets 2019
    python scripts/spatial_structure.py --versions v2 v6

Requires: rasterio, numpy, pandas, matplotlib, scipy
"""

import argparse
import glob
import os
import sys
import warnings

import numpy as np
import pandas as pd
import rasterio
from scipy import ndimage

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import compare_interpreted_vs_model as C  # reuse stitch/crosswalk/dedup helpers

warnings.filterwarnings("ignore")

OUT = "reports/spatial_structure"
PIX_HA = 0.01               # 10 m pixel = 100 m^2 = 0.01 ha
STRUCT = np.ones((3, 3), int)  # 8-connectivity


def patch_sizes(arr_common, classes):
    """Return {class: np.array of patch sizes (px)} via 8-connected labeling."""
    out = {}
    for c in classes:
        mask = arr_common == c
        if not mask.any():
            continue
        lab, n = ndimage.label(mask, structure=STRUCT)
        if n:
            out[c] = np.bincount(lab.ravel())[1:]  # drop background label 0
    return out


def morans_i(x, valid):
    """Global Moran's I, queen (8-neighbour) contiguity, over valid pixels.

    Counts each adjacency once (E, S, SE, SW); edges handled by slicing (no wrap).
    """
    x = x.astype(np.float64)
    N = int(valid.sum())
    if N < 3:
        return np.nan
    m = x[valid].mean()
    d = np.where(valid, x - m, 0.0)
    denom = float(((x[valid] - m) ** 2).sum())
    if denom == 0:
        return np.nan
    pairs = [((slice(None), slice(0, -1)), (slice(None), slice(1, None))),   # E
             ((slice(0, -1), slice(None)), (slice(1, None), slice(None))),   # S
             ((slice(0, -1), slice(0, -1)), (slice(1, None), slice(1, None))),   # SE
             ((slice(0, -1), slice(1, None)), (slice(1, None), slice(0, -1)))]   # SW
    num = 0.0
    W = 0
    for sa, sb in pairs:
        both = valid[sa] & valid[sb]
        num += float((d[sa][both] * d[sb][both]).sum())
        W += int(both.sum())
    if W == 0:
        return np.nan
    return (N / W) * (num / denom)


def collect_source(name, arrays_iter, classes):
    """Aggregate patch sizes (per class + pooled) and per-cell Moran's I for a source."""
    by_class = {c: [] for c in classes}
    pooled = []
    morans = []
    for arr_common in arrays_iter:
        ps = patch_sizes(arr_common, classes)
        for c, sizes in ps.items():
            by_class[c].append(sizes)
            pooled.append(sizes)
        morans.append(morans_i(arr_common, arr_common > 0))
    pooled = np.concatenate(pooled) if pooled else np.array([])
    by_class = {c: (np.concatenate(v) if v else np.array([])) for c, v in by_class.items()}
    morans = np.array([x for x in morans if not np.isnan(x)])
    return dict(name=name, pooled=pooled, by_class=by_class, morans=morans)


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--versions", nargs="+", default=["v2", "v3", "v4", "v5", "v6"])
    ap.add_argument("--targets", nargs="+", default=None, help="restrict to these target years")
    ap.add_argument("--keep-duplicates", action="store_true",
                    help="use every raster (default: one interpretation per location)")
    ap.add_argument("--seed", type=int, default=0)
    args = ap.parse_args()

    rf2common, names, colors = C.load_mappings()
    classes = sorted(names)  # common codes 1..10

    cells = sorted(glob.glob(os.path.join(C.RF_DIR, "**", "rf_class*Sentinel-2*.tif"), recursive=True))
    if args.targets:
        keep = set(args.targets)
        cells = [c for c in cells if C.target_year(c) in keep]
    if not args.keep_duplicates:
        cells, n_dup = C.dedupe_cells(cells, args.seed)
        print(f"de-duplicated: {n_dup} location(s); {len(cells)} unique cells")
    print(f"cells: {len(cells)}   sources: interpreted + {' '.join(args.versions)}")

    os.makedirs(OUT, exist_ok=True)

    # interpreted (remap RF codes -> common)
    def interp_arrays():
        for f in cells:
            with rasterio.open(f) as ds:
                yield C.to_common_rf(ds.read(1), rf2common)
    print("  interpreted ...", flush=True)
    sources = [collect_source("interpreted", interp_arrays(), classes)]

    # each model version (stitched to the same cell footprints; codes already common)
    for v in args.versions:
        tiles = [rasterio.open(t) for t in C.model_tiles(v)]

        def model_arrays(tiles=tiles):
            for f in cells:
                with rasterio.open(f) as ds:
                    yield C.stitch_model_to_cell(ds, tiles)
        print(f"  model {v} ...", flush=True)
        sources.append(collect_source(v, model_arrays(), classes))
        for t in tiles:
            t.close()

    # ---- summary table ----
    rows = []
    for s in sources:
        p = s["pooled"]
        rows.append(dict(source=s["name"], n_patches=int(p.size),
                         mean_patch_px=round(float(p.mean()), 2) if p.size else np.nan,
                         mean_patch_ha=round(float(p.mean()) * PIX_HA, 4) if p.size else np.nan,
                         median_patch_px=float(np.median(p)) if p.size else np.nan,
                         morans_i_mean=round(float(s["morans"].mean()), 4) if s["morans"].size else np.nan,
                         morans_i_std=round(float(s["morans"].std()), 4) if s["morans"].size else np.nan))
    summ = pd.DataFrame(rows)
    summ.to_csv(os.path.join(OUT, "spatial_structure_summary.csv"), index=False)

    # ---- per-class table ----
    crows = []
    for s in sources:
        for c in classes:
            v = s["by_class"][c]
            if v.size:
                crows.append(dict(source=s["name"], code=c, cls=names[c], n_patches=int(v.size),
                                  mean_patch_px=round(float(v.mean()), 2),
                                  median_patch_px=float(np.median(v))))
    pd.DataFrame(crows).to_csv(os.path.join(OUT, "patch_size_by_class.csv"), index=False)

    make_plots(sources, classes, names, colors, args.versions)

    print("\n" + "=" * 60)
    print(summ.to_string(index=False))
    print(f"\noutputs -> {OUT}/")


def make_plots(sources, classes, names, colors, versions):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    by_name = {s["name"]: s for s in sources}
    order = ["interpreted"] + list(versions)
    palette = {"interpreted": "black", "v2": "#1f77b4", "v3": "#2ca02c",
               "v4": "#9467bd", "v5": "#ff7f0e", "v6": "#d62728"}

    def ecdf(a):
        a = np.sort(a)
        return a, np.arange(1, a.size + 1) / a.size

    # 1) ECDF overlay (patch size in ha, log-x)
    fig, ax = plt.subplots(figsize=(8, 5.5))
    for nm in order:
        p = by_name[nm]["pooled"] * PIX_HA
        if p.size:
            xs, ys = ecdf(p)
            ax.plot(xs, ys, label=nm, color=palette.get(nm), lw=2 if nm == "interpreted" else 1.3,
                    ls="-" if nm == "interpreted" else "--")
    ax.set_xscale("log")
    ax.set_xlabel("patch size (ha, log scale)")
    ax.set_ylabel("cumulative fraction of patches")
    ax.set_title("Patch-size distribution: model variants vs. interpreted (reference)")
    ax.legend(); ax.grid(alpha=0.3)
    fig.tight_layout(); fig.savefig(os.path.join(OUT, "patch_size_ecdf.png"), dpi=140, bbox_inches="tight")
    plt.close(fig)

    # 2) small multiples: each variant's histogram vs interpreted
    ref = by_name["interpreted"]["pooled"] * PIX_HA
    bins = np.logspace(np.log10(max(ref.min(), PIX_HA)), np.log10(ref.max() + 1), 40) if ref.size else 40
    fig, axes = plt.subplots(1, len(versions), figsize=(3.2 * len(versions), 3.6), sharey=True)
    axes = np.atleast_1d(axes)
    for ax, v in zip(axes, versions):
        p = by_name[v]["pooled"] * PIX_HA
        ax.hist(ref, bins=bins, density=True, color="black", histtype="step", lw=2, label="interpreted")
        if p.size:
            ax.hist(p, bins=bins, density=True, color=palette.get(v), alpha=0.5, label=v)
        ax.set_xscale("log"); ax.set_title(v, fontsize=10); ax.set_xlabel("patch ha")
        ax.legend(fontsize=7)
    axes[0].set_ylabel("density")
    fig.suptitle("Per-variant patch-size distribution vs. interpreted", fontsize=11)
    fig.tight_layout(rect=[0, 0, 1, 0.94])
    fig.savefig(os.path.join(OUT, "patch_size_hist_smallmultiples.png"), dpi=140, bbox_inches="tight")
    plt.close(fig)

    # 3) mean patch size per class, grouped by source
    fig, ax = plt.subplots(figsize=(11, 5))
    labels = [names[c] for c in classes]
    x = np.arange(len(classes)); w = 0.8 / len(order)
    for i, nm in enumerate(order):
        vals = [by_name[nm]["by_class"][c].mean() * PIX_HA if by_name[nm]["by_class"][c].size else 0
                for c in classes]
        ax.bar(x + i * w, vals, w, label=nm, color=palette.get(nm))
    ax.set_xticks(x + 0.4 - w / 2); ax.set_xticklabels(labels, rotation=45, ha="right")
    ax.set_ylabel("mean patch size (ha)")
    ax.set_title("Mean patch size per class, by source")
    ax.legend(ncol=len(order), fontsize=8)
    fig.tight_layout(); fig.savefig(os.path.join(OUT, "mean_patch_size_by_class.png"), dpi=140, bbox_inches="tight")
    plt.close(fig)

    # 4) Moran's I by source
    fig, ax = plt.subplots(figsize=(7, 4.5))
    means = [by_name[nm]["morans"].mean() if by_name[nm]["morans"].size else np.nan for nm in order]
    errs = [by_name[nm]["morans"].std() if by_name[nm]["morans"].size else 0 for nm in order]
    ax.bar(order, means, yerr=errs, capsize=4,
           color=[palette.get(nm) for nm in order])
    ref_i = by_name["interpreted"]["morans"].mean() if by_name["interpreted"]["morans"].size else np.nan
    ax.axhline(ref_i, ls="--", color="black", lw=1, label=f"interpreted ref ({ref_i:.2f})")
    ax.set_ylabel("Moran's I (mean per cell)")
    ax.set_title("Spatial autocorrelation of the class raster")
    ax.legend(); ax.grid(alpha=0.3, axis="y")
    fig.tight_layout(); fig.savefig(os.path.join(OUT, "morans_i_by_source.png"), dpi=140, bbox_inches="tight")
    plt.close(fig)


if __name__ == "__main__":
    main()
