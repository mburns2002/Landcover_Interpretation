#!/usr/bin/env python3
"""pres_patch_size_distribution: per-model patch-size distribution vs the interpreted reference (deck).

Deck (Spectral) copy of reports/spatial_structure/with_spec_all/patch_size_hist_smallmultiples.png, but
laid out as two rows of three (v2, v3, v4 / v5, v6, spec_all). Each panel overlays that model's
patch-size histogram (density, hectares on a log axis; 8-connected patches) on the interpreted reference.

Reuses spatial_structure's select_by_truth and patch_sizes on the same cell set (adjudicated reference,
temporally-matched per-bracket predictions, spec_all single-band predictions), so the patches match the
report. Moran's I is not computed here (not needed for the histogram).

Run from the repo root: python presentation/scripts/pres_patch_size_distribution.py
Output (PNG only): presentation/figures/pres_21_patch_size_distribution.png
"""

import glob
import importlib.util
import os
import sys

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

import slide_font
import numpy as np
import rasterio
slide_font.use_spectral()

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.join(ROOT, "scripts"))


def _load(name, path):
    spec = importlib.util.spec_from_file_location(name, os.path.join(ROOT, "scripts", path))
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


SS = _load("SS", "spatial_structure.py")
C = SS.C
PIX_HA = SS.PIX_HA
TRUTH = os.path.join(ROOT, "exports", "truth_selections.csv")
PREDS = os.path.join(ROOT, "data", "raw", "transfer_predictions")
SPEC = os.path.join(ROOT, "data", "raw", "spectral_transferability_10class_percell")
OUT = os.path.join(ROOT, "presentation", "figures", "pres_21_patch_size_distribution.png")
VERSIONS = ["v2", "v3", "v4", "v5", "v6", "spec_all"]
SRC_COLOR = {"v2": "#1f77b4", "v3": "#2ca02c", "v4": "#9467bd", "v5": "#ff7f0e", "v6": "#d62728",
             "spec_all": "#8c564b"}


def _pooled(arrays_iter, classes):
    """Pooled patch sizes (hectares) over all cells for one source."""
    acc = []
    for arr in arrays_iter:
        for sizes in SS.patch_sizes(arr, classes).values():
            acc.append(sizes)
    return (np.concatenate(acc) * PIX_HA) if acc else np.array([])


def main():
    rf2common, names, _colors = C.load_mappings()
    classes = sorted(names)
    cells = sorted(glob.glob(os.path.join(C.RF_DIR, "**", "rf_class*Sentinel-2*.tif"), recursive=True))
    cells, _missing, mismatch = SS.select_by_truth(cells, TRUTH)
    if mismatch:
        raise SystemExit(f"STOP: truth reviewer with no matching raster: {mismatch[:5]}")
    print(f"cells: {len(cells)}")

    def interp_arrays():
        for f in cells:
            with rasterio.open(f) as ds:
                yield C.to_common_rf(ds.read(1), rf2common)

    def model_arrays(v):
        band = SS.PRED_BAND[v]
        for f in cells:
            gid, bracket = SS._cell_bracket_gid(f)
            with rasterio.open(os.path.join(PREDS, bracket, f"pred_{bracket}_cell{gid}.tif")) as ds:
                yield ds.read(band)

    def spec_arrays():
        for f in cells:
            gid, bracket = SS._cell_bracket_gid(f)
            with rasterio.open(os.path.join(SPEC, bracket, f"pred_specall_{bracket}_cell{gid}.tif")) as ds:
                yield ds.read(1)

    print("  interpreted ...", flush=True)
    ref = _pooled(interp_arrays(), classes)
    pooled = {}
    for v in VERSIONS:
        print(f"  {v} ...", flush=True)
        pooled[v] = _pooled(model_arrays(v) if v != "spec_all" else spec_arrays(), classes)

    bins = np.logspace(np.log10(max(ref.min(), PIX_HA)), np.log10(ref.max() + 1), 40)

    fig, axes = plt.subplots(2, 3, figsize=(11, 7.2), sharex=True, sharey=True)
    for ax, v in zip(axes.ravel(), VERSIONS):
        ax.hist(ref, bins=bins, density=True, color="black", histtype="step", lw=2, label="interpreted")
        p = pooled[v]
        if p.size:
            ax.hist(p, bins=bins, density=True, color=SRC_COLOR[v], alpha=0.5, label=v)
        ax.set_xscale("log")
        ax.set_title(v, fontsize=14, fontweight="bold")
        ax.grid(False)
        for sp in ("top", "right"):
            ax.spines[sp].set_visible(False)
        ax.legend(fontsize=10, frameon=False)
    for ax in axes[1, :]:
        ax.set_xlabel("Patch size (ha)", fontsize=13)
    for ax in axes[:, 0]:
        ax.set_ylabel("Density", fontsize=13)

    fig.suptitle("Per-Model Patch-Size Distribution vs. the Interpreted Reference", fontsize=18,
                 fontweight="bold", y=0.98)
    fig.text(0.5, 0.015, "Patch-size histograms (density, hectares on a log axis; 8-connected patches) for "
             "each classified map (filled) over the interpreted reference (black outline).\nMass shifted "
             "toward smaller patches means a more fragmented map: the dot-product v6 is the most speckled.",
             ha="center", va="bottom", fontsize=10, color="0.35", linespacing=1.4)
    fig.subplots_adjust(left=0.07, right=0.98, top=0.91, bottom=0.19, hspace=0.30, wspace=0.12)

    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    fig.savefig(OUT, dpi=300)
    plt.close(fig)
    print(f"wrote {os.path.basename(OUT)}")


if __name__ == "__main__":
    main()
