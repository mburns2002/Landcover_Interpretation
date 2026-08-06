#!/usr/bin/env python3
"""pres_watershed_accuracy: per-class accuracy for interpreted cells inside vs outside a GLKN watershed.

Splits the 180 interpreted cells into those whose center falls inside one of the seven GLKN park
watersheds and those outside, then compares per-class F1 (5-class collapse, model prediction vs the
adjudicated interpreted reference) between the two groups, pooled over each group's cells.

Reuses model_class_ci_5class.cell_confusions (same 5-class collapse and cell set); the figure shows a
representative embedding model, and the full inside/outside table is printed for every source.

Run from the repo root: python presentation/scripts/pres_watershed_accuracy.py
Outputs (PNG + CSV) in presentation/figures/watershed_accuracy/.
"""

import importlib.util
import os
import re
import sys

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

import slide_font
import geopandas as gpd
import numpy as np
import pandas as pd

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.join(ROOT, "scripts"))
slide_font.use_spectral()


def _load(name, path):
    spec = importlib.util.spec_from_file_location(name, os.path.join(ROOT, "scripts", path))
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


MC = _load("MC", "model_class_ci_5class.py")          # cell_confusions, ICI, SOURCES, NAMES5
SA = _load("SA", "build_study_area_figure.py")        # build_grid
CELLS = os.path.join(ROOT, "exports", "gee", "interpreted_cells_by_bracket.csv")
GLKN = os.path.join(ROOT, "data", "raw", "glkn", "GLKN_watershed_boundaries_7park_5070.shp")
OUT_DIR = os.path.join(ROOT, "presentation", "figures", "watershed_accuracy")

ORDER = MC.ORDER                                       # [1..5] Stable, Harvest, Development, Insect, Beaver
NAMES5 = MC.NAMES5
SOURCES = MC.SOURCES
FIG_SOURCE = "v2"                                      # representative embedding for the figure
IN_COLOR, OUT_COLOR = "#2a9d8f", "#9c9c9c"


def _inside_map():
    """{padded cell key -> True if the cell center is inside a GLKN watershed}."""
    grid = SA.build_grid()
    keep = set(pd.read_csv(CELLS, dtype=str).cell_id)
    interp = grid[grid.key.isin(keep)].copy()
    wu = gpd.read_file(GLKN).to_crs(5070).geometry.union_all()
    inside = interp.geometry.centroid.within(wu)
    return {k: bool(v) for k, v in zip(interp.key, inside)}, int(inside.sum()), int((~inside).sum())


def _pool(confs):
    """Per-class F1 and reference support from a list of 5x5 confusion matrices (rows=reference)."""
    P = np.sum(confs, axis=0) if confs else np.zeros((5, 5))
    f1, _ = MC.ICI.per_class(P)
    support = P.sum(1)                                 # reference pixels per class
    return f1, support


def _key(cid):
    return str(int(re.sub(r"\D", "", str(cid)))).zfill(5)


def main():
    os.makedirs(OUT_DIR, exist_ok=True)
    inside_map, n_in, n_out = _inside_map()
    print(f"interpreted cells: inside watershed (centroid) = {n_in}, outside = {n_out}")

    per_source, _ref_valid, _drops = MC.cell_confusions(MC.TRUTH)

    rows = []
    fig_res = {}
    for s in SOURCES:
        ins = [M for cid, M in per_source[s] if inside_map.get(_key(cid), False)]
        outs = [M for cid, M in per_source[s] if not inside_map.get(_key(cid), False)]
        f1_in, sup_in = _pool(ins)
        f1_out, sup_out = _pool(outs)
        if s == FIG_SOURCE:
            fig_res = dict(inside=f1_in, outside=f1_out, n_in=len(ins), n_out=len(outs))
        for k, c in enumerate(ORDER):
            rows.append(dict(source=s, cls=NAMES5[c], f1_inside=round(float(f1_in[k]), 3),
                             f1_outside=round(float(f1_out[k]), 3),
                             diff=round(float(f1_in[k] - f1_out[k]), 3),
                             support_inside=int(sup_in[k]), support_outside=int(sup_out[k]),
                             n_inside=len(ins), n_outside=len(outs)))
    df = pd.DataFrame(rows)
    df.to_csv(os.path.join(OUT_DIR, "watershed_accuracy_per_class_f1.csv"), index=False)

    # printed table
    print("\n===== per-class 5-class F1: inside vs outside GLKN watershed =====")
    print(f"{'source':<9}{'class':<16}{'inside':>8}{'outside':>9}{'diff':>8}")
    for r in df.itertuples():
        print(f"{r.source:<9}{r.cls:<16}{r.f1_inside:>8.3f}{r.f1_outside:>9.3f}{r.diff:>8.3f}")

    _draw(fig_res)


def _draw(res):
    x = np.arange(len(ORDER))
    bw = 0.38
    fig, ax = plt.subplots(figsize=(10, 6))
    fig.subplots_adjust(left=0.09, right=0.98, top=0.88, bottom=0.24)
    ax.bar(x - bw / 2, res["inside"], bw, color=IN_COLOR, edgecolor="black", linewidth=0.6,
           label=f"inside watershed (n = {res['n_in']} cells)", zorder=3)
    ax.bar(x + bw / 2, res["outside"], bw, color=OUT_COLOR, edgecolor="black", linewidth=0.6,
           label=f"outside watershed (n = {res['n_out']} cells)", zorder=3)
    for xi, v in zip(x - bw / 2, res["inside"]):
        ax.text(xi, v + 0.012, f"{v:.2f}", ha="center", va="bottom", fontsize=9, color="0.2")
    for xi, v in zip(x + bw / 2, res["outside"]):
        ax.text(xi, v + 0.012, f"{v:.2f}", ha="center", va="bottom", fontsize=9, color="0.2")

    ax.set_xticks(x)
    ax.set_xticklabels([NAMES5[c] for c in ORDER], fontsize=13)
    ax.set_ylim(0, 1.0)
    ax.set_ylabel("Per-class F1 (five-class)", fontsize=14)
    ax.tick_params(axis="y", labelsize=12)
    ax.grid(False)
    for sp in ("top", "right"):
        ax.spines[sp].set_visible(False)
    ax.set_title("Per-Class Accuracy Inside vs Outside a GLKN Watershed", fontsize=18,
                 fontweight="bold", pad=12)
    ax.legend(fontsize=12, frameon=False, loc="upper right")
    fig.text(0.5, 0.03, f"Five-class per-class F1 of the {FIG_SOURCE} classifier vs the interpreted "
             "reference, pooled over each cell group.\n'Inside' = cell center within a GLKN watershed. The "
             "inside group is small (13 cells); see the printed table for every source and per-class support.",
             ha="center", va="bottom", fontsize=10, color="0.35", linespacing=1.4)

    fig.savefig(os.path.join(OUT_DIR, "watershed_accuracy_per_class_f1.png"), dpi=300)
    plt.close(fig)
    print("\nwrote watershed_accuracy_per_class_f1.png and .csv")


if __name__ == "__main__":
    main()
