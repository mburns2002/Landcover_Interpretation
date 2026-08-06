#!/usr/bin/env python3
"""pres_07_speckle_with_ref: figure 2.9 speckle crop, extended with the interpreted reference.

Same location as figure 2.9 (cell 31320, EPSG:5070, bracket 2018_2020) and the same 10-class palette,
but with the adjudicated interpreted reference added as the first panel so the audience has a ground
truth to judge the classifications against. spec_all is added as a final panel because its
classification exists for this cell.

Panel order: reference, v2, v3, v4, v5, v6, spec_all. Each classified panel keeps its neighbor-change
annotation (the fraction of horizontally adjacent, both-valid pixel pairs assigned differing classes),
pooled over that source's cells; the reference panel is annotated the same way, over the adjudicated
references. A 1 km scale bar is on the first panel.

Sources (local only): reference from data/raw/rf_class_maps (adjudicated reviewer in
exports/truth_selections.csv, CKIT codes remapped to the 10-class schema); v2-v6 from
data/raw/transfer_predictions; spec_all from data/raw/spectral_transferability_10class_percell.

output (png only):
  presentation/figures/pres_07_speckle_with_ref.png
"""

import glob
import importlib.util
import os
import re

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

import slide_font
import numpy as np
import pandas as pd
import rasterio
from matplotlib.colors import ListedColormap, to_rgb
from matplotlib.patches import Patch, Rectangle

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
PRED_DIR = f"{ROOT}/data/raw/transfer_predictions"
SPEC_DIR = f"{ROOT}/data/raw/spectral_transferability_10class_percell"
RF_DIR = f"{ROOT}/data/raw/rf_class_maps"
TRUTH = f"{ROOT}/exports/truth_selections.csv"
OUT = f"{ROOT}/presentation/figures"
CROP_CELL = "31320"
BRACKET = "2018_2020"
VBAND = {"v2": 1, "v3": 2, "v4": 3, "v5": 4, "v6": 5}
NAME10 = {1: "Harvest", 2: "Development", 3: "Forest", 4: "Urban", 5: "Water",
          6: "Agriculture", 7: "Grass/Shrub", 8: "Wetland", 9: "Beaver", 10: "Insect/Disease"}
CROSSWALK = {0: 4, 1: 6, 2: 7, 3: 3, 4: 5, 5: 8, 20: 1, 30: 2, 50: 10, 62: 9}
LUT = np.zeros(63, np.uint8)
for _k, _v in CROSSWALK.items():
    LUT[_k] = _v


def _load(name, path):
    spec = importlib.util.spec_from_file_location(name, os.path.join(ROOT, "scripts", path))
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


C = _load("C", "compare_interpreted_vs_model.py")
C10 = C.load_mappings()[2]
CLUT = np.ones((11, 4))
for _code, _col in C10.items():
    CLUT[_code] = to_rgb(_col) + (1.0,)
CMAP = ListedColormap([CLUT[i] for i in range(11)])


def _pad(g):
    return str(int(g)).zfill(5)


def _nc(a):
    # neighbor-change counts for one class raster: (differing pairs, valid pairs)
    left, right = a[:, :-1], a[:, 1:]
    valid = (left > 0) & (right > 0)
    return int((valid & (left != right)).sum()), int(valid.sum())


def _adjudicated_reference_paths():
    # {cell -> adjudicated reference raster path}, 10 m rasters, reviewer from truth
    rx = re.compile(r"reviewer_([A-Za-z]+)_grid_(\d+)_sample_", re.I)
    idx = {}
    for p in sorted(glob.glob(os.path.join(RF_DIR, "**", "rf_class*.tif"), recursive=True)):
        m = rx.search(os.path.basename(p))
        if not m:
            continue
        with rasterio.open(p) as ds:
            if not (ds.transform.a == 10 and ds.transform.e == -10):
                continue
        idx.setdefault(_pad(m.group(2)), []).append((m.group(1).lower(), p))
    truth = {_pad(r.grid_id): str(r.reviewer).strip().lower()
             for r in pd.read_csv(TRUTH, dtype=str, keep_default_na=False).itertuples()}
    chosen = {}
    for cid, revs in idx.items():
        want = truth.get(cid)
        match = [p for r, p in revs if r == want] or [revs[0][1]]
        chosen[cid] = match[0]
    return chosen


def neighbor_change_variants():
    # v2-v6 pooled over the transfer-prediction cells (one open per file, 5 bands)
    diff = {v: 0 for v in VBAND}
    tot = {v: 0 for v in VBAND}
    files = sorted(glob.glob(f"{PRED_DIR}/*/pred_*.tif"))
    for f in files:
        with rasterio.open(f) as s:
            for v, b in VBAND.items():
                d, t = _nc(s.read(b))
                diff[v] += d
                tot[v] += t
    return {v: diff[v] / tot[v] for v in VBAND}, len(files)


def neighbor_change_files(files, remap=None):
    diff = tot = 0
    for f in files:
        with rasterio.open(f) as s:
            a = s.read(1)
        if remap is not None:
            a = remap[np.clip(a, 0, 62)]
        d, t = _nc(a)
        diff += d
        tot += t
    return (diff / tot if tot else float("nan")), len(files)


def prepare():
    """Reference-path index plus the pooled neighbor-change values (identical for every location)."""
    ref_paths = _adjudicated_reference_paths()
    nc_v, n_pred = neighbor_change_variants()
    nc_ref, n_ref = neighbor_change_files(list(ref_paths.values()), remap=LUT)
    spec_files = sorted(glob.glob(f"{SPEC_DIR}/*/pred_specall_*.tif"))
    nc_spec, n_spec = neighbor_change_files(spec_files)
    print(f"neighbor-change (pooled): reference {nc_ref:.4f} ({n_ref} cells), "
          + ", ".join(f"{v} {nc_v[v]:.4f}" for v in VBAND) + f", spec_all {nc_spec:.4f} ({n_spec} cells)")
    return ref_paths, (nc_v, nc_ref, nc_spec)


def build_for_cell(cell, bracket, ref_paths, ncs, out_path):
    """Render the interpreted reference + every classification for one cell (Spectral, 300 dpi)."""
    nc_v, nc_ref, nc_spec = ncs
    if cell not in ref_paths:
        raise SystemExit(f"STOP: cell {cell} has no interpreted reference.")
    with rasterio.open(glob.glob(f"{RF_DIR}/**/rf_class_reviewer_*grid_{cell}_*.tif",
                                 recursive=True)[0]) as s:
        ref_img = LUT[np.clip(s.read(1), 0, 62)]
        res = s.res[0]
    with rasterio.open(glob.glob(f"{PRED_DIR}/{bracket}/pred_{bracket}_cell{cell}.tif")[0]) as s:
        var_img = {v: s.read(b) for v, b in VBAND.items()}
    spec_crop = glob.glob(f"{SPEC_DIR}/{bracket}/pred_specall_{bracket}_cell{cell}.tif")
    spec_img = None
    if spec_crop:
        with rasterio.open(spec_crop[0]) as s:
            spec_img = s.read(1)

    # panel list: (title, image, neighbor-change)
    panels = [("Reference", ref_img, nc_ref)]
    panels += [(v, var_img[v], nc_v[v]) for v in VBAND]
    if spec_img is not None:
        panels.append(("spec_all", spec_img, nc_spec))

    plt.rcParams.update({"font.family": "sans-serif",
                         "font.sans-serif": ["Helvetica", "Arial", "DejaVu Sans"], "font.size": 14})
    slide_font.use_spectral()
    fig, axes = plt.subplots(1, len(panels), figsize=(2.55 * len(panels), 5.6))
    for ax, (pname, img, nc) in zip(axes, panels):
        ax.imshow(img, cmap=CMAP, vmin=0, vmax=10, interpolation="nearest")
        ax.set_title(pname, fontsize=15, fontweight="bold")
        ax.text(0.5, -0.05, f"neighbor-change {nc:.3f}", transform=ax.transAxes,
                ha="center", va="top", fontsize=12)
        ax.set_xticks([])
        ax.set_yticks([])

    # 1 km scale bar on the reference panel (1 km = 100 px at 10 m)
    h, w = ref_img.shape
    km_px = 1000 / res
    y0 = h - 22
    axes[0].add_patch(Rectangle((12, y0), km_px, 6, facecolor="black", edgecolor="white", lw=0.6))
    axes[0].text(12 + km_px / 2, y0 - 6, "1 km", ha="center", va="bottom", fontsize=9, color="black")

    present = sorted({int(c) for _t, img, _n in panels for c in np.unique(img) if c > 0})
    handles = [Patch(facecolor=CLUT[c], edgecolor="0.4", label=NAME10[c]) for c in present]
    fig.subplots_adjust(left=0.015, right=0.985, top=0.86, bottom=0.20, wspace=0.05)
    fig.legend(handles=handles, loc="lower center", ncol=min(len(present), 8), fontsize=12,
               frameon=False, bbox_to_anchor=(0.5, 0.02))
    fig.suptitle(f"Interpreted Reference and Each Classification, Same Location (Cell {cell})",
                 fontsize=17, fontweight="bold", y=0.96)

    os.makedirs(os.path.dirname(out_path), exist_ok=True)
    fig.savefig(out_path, dpi=300, bbox_inches="tight")
    plt.close(fig)
    print(f"wrote {out_path}")


def main():
    ref_paths, ncs = prepare()
    if CROP_CELL not in ref_paths:
        raise SystemExit(f"STOP: default cell {CROP_CELL} has no interpreted reference.")
    build_for_cell(CROP_CELL, BRACKET, ref_paths, ncs, f"{OUT}/pres_07_speckle_with_ref.png")


if __name__ == "__main__":
    main()
