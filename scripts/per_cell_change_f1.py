#!/usr/bin/env python3
"""Per-class, per-grid-cell F1 for the four change classes, across six prediction sources (Option B).

For each source (embedding v2-v6 and spectral spec_all), each grid cell, and each of the four change
classes (Harvest, Development, Insect/Disease, Beaver), the cell's 5-class confusion matrix is built
against the crosswalked and collapsed CKIT reference, and that class's F1 in the cell is computed. The
distribution of interest, per (source, change class), is the set of per-cell F1 values across the cells
where the class is present. Change classes are kept separate; they are not averaged into one per-cell
number.

5-class collapse: Stable = {forest, urban, water, ag, grass/shrub, wetland} (kept in the matrix but not
analyzed), Harvest, Development, Insect/Disease, and Beaver. The CKIT reference is crosswalked to the
10-class schema (0->4, 1->6, 2->7, 3->3, 4->5, 5->8, 20->1, 30->2, 50->10, 62->9), with Unknown(10) and
Other(13) excluded and those pixels dropped, then collapsed with the same 10-to-5 map used for the
predictions. Out-of-crosswalk reference values are counted and reported.

Include rule (the crux): a cell is part of class X's distribution if X is present in the cell's
reference OR prediction (any reference pixels of X, or any predicted pixels of X). A cell where X is
predicted but not referenced is commission (F1 = 0 via zero precision), a cell where X is referenced
but never predicted is omission (F1 = 0 via zero recall), and a cell with X in neither is excluded (F1
undefined). This is the reference-OR-prediction rule (default, commission sensitive); the reference-only
alternative is available with --include ref_only, and the note states which was used.

Common cell set: the six sources are compared only on the cells usable for all six and with a valid
reference, since spec_all has entirely-nodata cells the embeddings do not. Within that set, a class's
distribution still includes only cells where the class is present for that source, so the per-class N
can differ across sources; N is reported per (source, class) everywhere.

Outputs -> reports/per_cell_change_f1/
  - per_cell_change_f1.csv    one row per (source, change_class, cell): f1, ref/pred pixels, present_via
  - change_f1_summary.csv      per (source, change class): n cells, mean, median, fraction with F1 = 0
  - change_f1_violins.png      per change class, six sources' per-cell F1 distributions with N
  - change_f1_heatmap.png      median per-cell F1 by change class and source, with N
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


pcf = _load("pcf", "per_cell_f1_5class.py")                 # reference/collapse/common-set machinery
bmc = pcf.bmc

TRUTH = pcf.TRUTH
OUT = "reports/per_cell_change_f1"
SOURCES = pcf.SOURCES
REF_LUT = pcf.REF_LUT
MODEL_COLLAPSE = pcf.MODEL_COLLAPSE
ALLOWED = pcf.ALLOWED
SRC_COLOR = pcf.SRC_COLOR
# change classes only (5-class codes -> csv name)
CHANGE = {2: "harvest", 3: "development", 4: "insect_disease", 5: "beaver"}


def class_f1(M, k):
    """F1, ref support, pred count for 5-class index k (0-based) from a 5x5 matrix."""
    tp = float(M[k, k])
    row = float(M[k, :].sum())                             # reference pixels of the class in the cell
    col = float(M[:, k].sum())                             # predicted pixels of the class in the cell
    p = tp / col if col > 0 else 0.0
    r = tp / row if row > 0 else 0.0
    f1 = 2 * p * r / (p + r) if (p + r) > 0 else 0.0
    return f1, int(row), int(col)


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--truth", default=TRUTH, help="adjudicated reviewer per cell")
    ap.add_argument("--include", choices=["ref_or_pred", "ref_only"], default="ref_or_pred",
                    help="include a cell in a class distribution if the class is present in reference "
                         "or prediction (default) or only in the reference")
    args = ap.parse_args()
    os.makedirs(OUT, exist_ok=True)

    ref_index = bmc.build_reference_index()
    truth = bmc.load_truth(args.truth)
    chosen_ref, n_multi, missing, mismatch = bmc.choose_references_truth(ref_index, truth)
    if mismatch:
        print("STOP: truth reviewer with no matching raster:", mismatch[:10]); raise SystemExit(1)

    cells = {}
    for cid, rp in chosen_ref.items():
        m = re.search(r"opt_(\d{4}_\d{4})", os.path.basename(rp))
        if m:
            cells[cid] = m.group(1)
    print(f"reference cells: {len(chosen_ref)}   multi-interpreted: {n_multi}")

    stored = {}                                            # (source, cid) -> 5x5 matrix
    usable = {s: set() for s in SOURCES}
    ref_valid_cells = set()
    drops = defaultdict(list)
    unmapped = defaultdict(int)

    for cid in sorted(cells):
        bracket = cells[cid]
        with rasterio.open(chosen_ref[cid]) as rds:
            ref_raw = rds.read(1)
            meta = (rds.width, rds.height, rds.transform, rds.crs)
        for val in np.unique(ref_raw):
            if int(val) not in ALLOWED:
                unmapped[(cid, int(val))] += int((ref_raw == val).sum())
        ref5 = MODEL_COLLAPSE[REF_LUT[np.where((ref_raw >= 0) & (ref_raw <= 62), ref_raw, 0)]]
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
            pred5 = MODEL_COLLAPSE[np.where(pred_raw <= 10, pred_raw, 0)]
            valid = ref_valid & (pred5 >= 1) & (pred5 <= 5)
            M = np.zeros((5, 5), np.int64)
            np.add.at(M, (ref5[valid] - 1, pred5[valid] - 1), 1)
            stored[(s, cid)] = M
            usable[s].add(cid)

    common = sorted(cid for cid in ref_valid_cells if all(cid in usable[s] for s in SOURCES))
    print(f"reference-valid cells: {len(ref_valid_cells)}")
    for s in SOURCES:
        print(f"  {s:9} usable: {len(usable[s])}")
    print(f"common cell set (all six sources): {len(common)}")
    if unmapped:
        agg = defaultdict(int)
        for (cid, val), n in unmapped.items():
            agg[val] += n
        print(f"UNMAPPED reference values: {dict(agg)}")
    for reason, lst in sorted(drops.items()):
        if lst:
            print(f"  dropped {reason}: {len(lst)}")

    # record per (source, change class, cell) rows on the common set
    rows = []
    for cid in common:
        bracket = cells[cid]
        for s in SOURCES:
            M = stored[(s, cid)]
            for c, cname in CHANGE.items():
                k = c - 1
                f1, ref_px, pred_px = class_f1(M, k)
                present_ref = ref_px > 0
                present_pred = pred_px > 0
                keep = (present_ref or present_pred) if args.include == "ref_or_pred" else present_ref
                if not keep:
                    continue
                present_via = "both" if (present_ref and present_pred) else (
                    "reference" if present_ref else "prediction")
                rows.append(dict(source=s, change_class=cname, cell_id=cid, bracket=bracket,
                                 f1=round(f1, 5), ref_pixels_of_class=ref_px,
                                 pred_pixels_of_class=pred_px, present_via=present_via))

    df = pd.DataFrame(rows)
    df.to_csv(os.path.join(OUT, "per_cell_change_f1.csv"), index=False)

    # summary per (source, change class)
    srows = []
    for cname in CHANGE.values():
        for s in SOURCES:
            g = df[(df.source == s) & (df.change_class == cname)].f1
            srows.append(dict(change_class=cname, source=s, n_cells=int(g.size),
                              mean_f1=round(float(g.mean()), 4) if g.size else np.nan,
                              median_f1=round(float(g.median()), 4) if g.size else np.nan,
                              frac_f1_zero=round(float((g == 0).mean()), 4) if g.size else np.nan))
    summ = pd.DataFrame(srows)
    summ.to_csv(os.path.join(OUT, "change_f1_summary.csv"), index=False)
    print("\nper (change class, source): n cells, mean F1, frac zero")
    print(summ.to_string(index=False))

    make_figs(df, len(common), args.include)
    write_note(df, summ, common, ref_valid_cells, usable, drops, unmapped, args.include)
    print(f"\nwrote {OUT}/")


def make_figs(df, n_common, include):
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

    rng = np.random.default_rng(0)                         # fixed jitter for the strip overlay
    # a) per change class, six sources' per-cell F1 distributions
    fig, axes = plt.subplots(2, 2, figsize=(15, 10))
    for ax, cname in zip(axes.flat, CHANGE.values()):
        data = [df[(df.source == s) & (df.change_class == cname)].f1.values for s in SOURCES]
        ns = [len(d) for d in data]
        for i, (d, s) in enumerate(zip(data, SOURCES)):
            if len(d) >= 2:
                pc = ax.violinplot([d], positions=[i], showextrema=False, widths=0.8)["bodies"][0]
                pc.set_facecolor(SRC_COLOR[s]); pc.set_alpha(0.4); pc.set_edgecolor("0.4")
            if len(d):
                ax.scatter(i + rng.uniform(-0.12, 0.12, len(d)), d, s=8, color=SRC_COLOR[s],
                           alpha=0.5, edgecolor="none", zorder=3)
                ax.plot([i - 0.28, i + 0.28], [np.median(d), np.median(d)], color="black", lw=2, zorder=4)
                ax.plot(i, np.mean(d), marker="D", color="black", ms=6, zorder=5)
        ax.set_xticks(range(len(SOURCES)))
        ax.set_xticklabels([f"{s}\n(n={n})" for s, n in zip(SOURCES, ns)], fontsize=9)
        ax.set_ylabel("per-cell F1")
        ax.set_ylim(-0.03, 1.03)
        ax.set_title(cname, fontsize=12)
        _style(ax)
    axes.flat[0].plot([], [], color="black", lw=2, label="median")
    axes.flat[0].plot([], [], marker="D", color="black", ls="", label="mean")
    axes.flat[0].legend(fontsize=8, frameon=False, loc="upper right")
    inc_txt = ("reference or prediction" if include == "ref_or_pred" else "reference only")
    fig.suptitle(f"Per-cell F1 by source, one panel per change class (common cell set, {n_common} cells)",
                 fontsize=13)
    _caption(fig, "Distribution across cells of each change class's per-cell F1, one panel per class "
                  "and six sources per panel, with individual cells as points, the median as a bar, and "
                  "the mean as a diamond. A cell contributes to a class only where the class is present "
                  f"({inc_txt}), so the per-source N differs and is annotated under each source; a "
                  "distribution over a handful of cells is not comparable in size to one over many. A "
                  "spike at 0 means the class is mostly commission or omission there.", top=0.94)
    fig.savefig(os.path.join(OUT, "change_f1_violins.png"), dpi=150, bbox_inches="tight")
    plt.close(fig)

    # b) mean per-cell F1 heatmap, change class x source, with N (median is 0 for every change class)
    classes = list(CHANGE.values())
    mean = np.full((len(classes), len(SOURCES)), np.nan)
    ncell = np.zeros((len(classes), len(SOURCES)), int)
    for ci, cname in enumerate(classes):
        for si, s in enumerate(SOURCES):
            g = df[(df.source == s) & (df.change_class == cname)].f1
            if g.size:
                mean[ci, si] = g.mean()
                ncell[ci, si] = g.size
    fig, ax = plt.subplots(figsize=(10, 5))
    vmax = max(0.02, np.nanmax(mean))
    im = ax.imshow(mean, cmap="Greens", vmin=0, vmax=vmax, aspect="auto")
    for ci in range(len(classes)):
        for si in range(len(SOURCES)):
            if np.isfinite(mean[ci, si]):
                ax.text(si, ci, f"{mean[ci, si]:.3f}\nn={ncell[ci, si]}", ha="center", va="center",
                        fontsize=8, color="white" if mean[ci, si] > 0.5 * vmax else "black")
    ax.set_xticks(range(len(SOURCES))); ax.set_xticklabels(SOURCES)
    ax.set_yticks(range(len(classes))); ax.set_yticklabels(classes)
    ax.set_title("Mean per-cell F1 by change class and source (common cell set)", fontsize=11)
    ax.grid(False)
    fig.colorbar(im, fraction=0.046, pad=0.04, label="mean per-cell F1")
    _caption(fig, "Mean per-cell F1 for each change class and source on the common cell set, with the "
                  "number of contributing cells (n) in each tile. The median is 0 for every change "
                  "class and source, so the mean is shown to separate the sources; even so the means "
                  "sit well under 0.1. Read across a row for how the sources compare on one class, and "
                  "note the n: beaver and insect/disease rest on far fewer cells than harvest, so the "
                  "classes are comparable as how the class does where it occurs, not as sample sizes.")
    fig.savefig(os.path.join(OUT, "change_f1_heatmap.png"), dpi=150, bbox_inches="tight")
    plt.close(fig)


def write_note(df, summ, common, ref_valid_cells, usable, drops, unmapped, include):
    inc_line = ("present in the reference OR the prediction (the default, commission sensitive, so a "
                "predicted-but-not-referenced cell counts with F1 = 0)"
                if include == "ref_or_pred" else
                "present in the reference only (the less commission-sensitive alternative)")
    lines = [
        "# per_cell_change_f1",
        "",
        "Per-class, per-grid-cell F1 for the four change classes (Harvest, Development, Insect/Disease, "
        "and Beaver), across six prediction sources (embedding v2-v6 and spectral spec_all), treating "
        "each grid cell as one sample. This is Option B: per-class distributions, not a change-macro "
        "averaged within cells. Generated by `scripts/per_cell_change_f1.py`.",
        "",
        "## Collapse, crosswalk, and exclusions",
        "",
        "5-class collapse: Stable = {forest, urban, water, agriculture, grass/shrub, wetland} (kept in "
        "the matrix so precision and recall are computed against everything else, but not analyzed), "
        "plus Harvest, Development, Insect/Disease, and Beaver. The CKIT reference is crosswalked to the "
        "10-class schema (" + ", ".join(f"{k}->{v}" for k, v in bmc.CROSSWALK.items())
        + "), with Unknown(10) and Other(13) excluded and dropped, then collapsed with the same "
        "10-to-5 map applied to the predictions. Out-of-crosswalk reference values found: "
        + (str({v: sum(m for (c, v2), m in unmapped.items() if v2 == v)
                for v in sorted({v for _, v in unmapped})}) if unmapped else "none") + ".",
        "",
        "## Per-class per-cell F1 rule",
        "",
        f"For each source, cell, and change class X, the cell's 5-class confusion is built and F1_X = "
        f"2PR/(P+R) is computed with P and R the precision and recall of X in the cell (F1 = 0 when "
        f"P + R = 0). A cell contributes to X's distribution if X is {inc_line}. Switch with "
        f"`--include ref_only`.",
        "",
        "## Common cell set",
        "",
        f"The six sources are compared on the common cell set, the intersection usable for all six with "
        f"a valid reference: **N = {len(common)}**. Within that set, class X's distribution for a source "
        f"includes only the cells where X is present for that source, so the per-class N differs across "
        f"sources (one source may predict X in a cell another does not). Reference-valid cells: "
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
        "## Occurrence and sample sizes",
        "",
        "The four change classes occur at very different rates. Beaver is the rarest (roughly 502 "
        "training pixels total and few reference cells), so its per-cell F1 distribution rests on far "
        "fewer cells than harvest's, and the two are not comparable as sample sizes, only as how the "
        "class does where it occurs. A distribution spiking at 0 for a class is a finding (mostly "
        "commission or omission), not noise. Contributing cells per (change class, source):",
        "",
        f"{'change_class':16}" + "".join(f"{s:>10}" for s in SOURCES),
    ]
    for cname in CHANGE.values():
        ns = [int(summ[(summ.change_class == cname) & (summ.source == s)].n_cells.iloc[0])
              for s in SOURCES]
        lines.append(f"{cname:16}" + "".join(f"{n:>10}" for n in ns))
    lines += [
        "",
        "## Outputs",
        "",
        "- `per_cell_change_f1.csv`: one row per (source, change_class, cell) with f1, "
        "ref_pixels_of_class, pred_pixels_of_class, and present_via (reference, prediction, or both).",
        "- `change_f1_summary.csv`: per (source, change class), the contributing cell count, mean and "
        "median F1, and the fraction of contributing cells with F1 = 0.",
        "- `change_f1_violins.png`, `change_f1_heatmap.png`.",
    ]
    with open(os.path.join(OUT, "note.md"), "w") as fh:
        fh.write("\n".join(lines) + "\n")


if __name__ == "__main__":
    main()
