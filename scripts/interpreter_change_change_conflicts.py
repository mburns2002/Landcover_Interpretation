#!/usr/bin/env python3
"""Change/change conflicts between interpreters: both reviewers called a pixel change, but
disagreed on which change type.

Using the RF interpreted scheme, the change classes are Harvest (20), Development (30),
Insect/Disease (50) and Beaver (62). Fire (40) has zero pixels. Unknown (10) is unattributed
disturbance, so an Unknown-vs-Harvest disagreement is one reviewer declining to attribute, not a
type conflict; it is excluded from the conflict count and reported separately.

For every double-interpreted cell (two reviewers on the same grid/sample/target, reviewer order
alphabetical and therefore arbitrary) this finds pixels where reviewer A and reviewer B both
assigned a change class and the classes differ, and reports:
  - total conflict pixels and area, as a fraction of all disagreement and of all change-labeled px
  - directed change-class pair counts (kept) plus the symmetrized counts (convention noted)
  - which cells and reviewer pairs the conflicts occur in (long-format table)
  - 8-connected component patches: count, median and max area

Outputs -> reports/interpreter_agreement/change_change_conflicts/
  - change_change_pixels_long.csv   one row per (cell, revA, revB, A_class, B_class)
  - ordered_pairs.csv               directed and symmetrized change-class pair totals
  - change_change_patches.csv       one row per connected-component patch
  - summary.txt                     the headline numbers in plain text

Requires: rasterio, numpy, pandas, scipy
"""

import glob
import os
import re
import warnings
from collections import defaultdict

import numpy as np
import pandas as pd
import rasterio
from scipy import ndimage

warnings.filterwarnings("ignore")

RF_DIR = "data/raw/rf_class_maps"
RF_LEGEND = "data/reference/label_lookup.csv"
OUT = "reports/interpreter_agreement/change_change_conflicts"

NAME_RE = re.compile(r"reviewer_([a-z]+)_grid_(\d+)_sample_(\d+)_sensor_Sentinel-2_target_(\d+)", re.I)
CHANGE = [20, 30, 50, 62]                               # harvest, development, insect/disease, beaver
UNKNOWN = 10                                            # unattributed disturbance, not a type conflict
STRUCT = np.ones((3, 3), int)                           # 8-connectivity
PIX_HA = 0.01                                           # one 10 m pixel = 0.01 ha


def load_names():
    df = pd.read_csv(RF_LEGEND)
    return {int(r.code): r.display_name for r in df.itertuples()}, [int(c) for c in df.code]


def find_pairs():
    """{(grid,sample,target): [(reviewer, path), ...]} for cells with >1 reviewer, alphabetical."""
    groups = defaultdict(list)
    for f in sorted(glob.glob(os.path.join(RF_DIR, "**", "rf_class*Sentinel-2*.tif"), recursive=True)):
        m = NAME_RE.search(os.path.basename(f))
        if m:
            groups[(m.group(2), m.group(3), m.group(4))].append((m.group(1).lower(), f))
    return {k: sorted(v) for k, v in groups.items() if len(v) > 1}


def main():
    os.makedirs(OUT, exist_ok=True)
    names, legend_codes = load_names()
    legend_arr = np.zeros(256, dtype=bool); legend_arr[legend_codes] = True
    change_arr = np.zeros(256, dtype=bool); change_arr[CHANGE] = True

    pairs = find_pairs()
    print(f"double-interpreted cells (pairs, first two reviewers): {len(pairs)}")

    long_rows, patch_rows = [], []
    directed = defaultdict(int)                          # (a_class, b_class) -> pixels
    tot_conflict = tot_disagree = tot_changelab = tot_unknown = 0
    n_cells_with_conflict = 0

    for (gid, samp, tgt), revs in sorted(pairs.items()):
        (revA, fA), (revB, fB) = revs[0], revs[1]
        with rasterio.open(fA) as s:
            a = s.read(1)
        with rasterio.open(fB) as s:
            b = s.read(1)
        if a.shape != b.shape:
            print(f"  skip grid {gid}: shape mismatch")
            continue

        valid = legend_arr[a] & legend_arr[b]
        achg, bchg = change_arr[a], change_arr[b]
        disagree = valid & (a != b)
        change_lab = valid & (achg | bchg)
        conflict = achg & bchg & (a != b)               # both change, different type
        unknown_change = ((a == UNKNOWN) & bchg) | ((b == UNKNOWN) & achg)

        tot_disagree += int(disagree.sum())
        tot_changelab += int(change_lab.sum())
        tot_unknown += int(unknown_change.sum())
        nconf = int(conflict.sum())
        tot_conflict += nconf
        if nconf == 0:
            continue
        n_cells_with_conflict += 1

        # per class-pair pixel counts within this cell
        av, bv = a[conflict], b[conflict]
        pair_counts = defaultdict(int)
        for ca, cb in zip(av.tolist(), bv.tolist()):
            pair_counts[(ca, cb)] += 1
        for (ca, cb), cnt in sorted(pair_counts.items(), key=lambda kv: -kv[1]):
            directed[(ca, cb)] += cnt
            long_rows.append(dict(
                grid=gid, sample=samp, target=tgt, revA=revA, revB=revB,
                A_class=names[ca], B_class=names[cb], class_pair=f"{names[ca]}->{names[cb]}",
                pixels=cnt, area_ha=round(cnt * PIX_HA, 3)))

        # connected-component patches of the conflict mask (8-connectivity)
        lab, n = ndimage.label(conflict, structure=STRUCT)
        if n:
            areas = np.bincount(lab.ravel())[1:]
            for k, ar in enumerate(areas, 1):
                patch_rows.append(dict(grid=gid, revA=revA, revB=revB, patch_id=k,
                                       pixels=int(ar), area_ha=round(int(ar) * PIX_HA, 3)))

    # long-format pixel table
    long_df = pd.DataFrame(long_rows)
    long_df.to_csv(os.path.join(OUT, "change_change_pixels_long.csv"), index=False)

    # directed and symmetrized change-class pair totals
    dir_rows = []
    for (ca, cb), cnt in directed.items():
        dir_rows.append(dict(A_class=names[ca], B_class=names[cb],
                             class_pair=f"{names[ca]}->{names[cb]}",
                             pixels=cnt, area_ha=round(cnt * PIX_HA, 3)))
    sym = defaultdict(int)
    for (ca, cb), cnt in directed.items():
        sym[frozenset((ca, cb))] += cnt
    for key, cnt in sym.items():
        c = sorted(key)
        dir_rows.append(dict(A_class=names[c[0]], B_class=names[c[1]],
                             class_pair=f"{names[c[0]]}<->{names[c[1]]} (symmetrized)",
                             pixels=cnt, area_ha=round(cnt * PIX_HA, 3)))
    pd.DataFrame(sorted(dir_rows, key=lambda d: -d["pixels"])).to_csv(
        os.path.join(OUT, "ordered_pairs.csv"), index=False)

    # patches
    patch_df = pd.DataFrame(patch_rows)
    patch_df.to_csv(os.path.join(OUT, "change_change_patches.csv"), index=False)

    # summary
    frac_dis = tot_conflict / tot_disagree if tot_disagree else float("nan")
    frac_chg = tot_conflict / tot_changelab if tot_changelab else float("nan")
    if len(patch_df):
        p_n, p_med, p_max = len(patch_df), patch_df.pixels.median(), patch_df.pixels.max()
    else:
        p_n = p_med = p_max = 0
    lines = [
        "change/change conflicts between interpreters",
        "(both reviewers called change, disagreed on which change type)",
        "",
        f"double-interpreted cells (pairs): {len(pairs)}",
        f"cells with at least one conflict: {n_cells_with_conflict}",
        "",
        f"total conflict pixels: {tot_conflict:,}  ({tot_conflict * PIX_HA:,.1f} ha)",
        f"  as a fraction of all disagreement pixels ({tot_disagree:,}): {frac_dis:.4%}",
        f"  as a fraction of all change-labeled pixels ({tot_changelab:,}): {frac_chg:.4%}",
        "",
        f"Unknown-vs-change pixels (reported separately, NOT counted as conflicts): "
        f"{tot_unknown:,}  ({tot_unknown * PIX_HA:,.1f} ha)",
        "",
        f"connected-component patches (8-connectivity): {p_n}",
        f"  median patch area: {p_med * PIX_HA:.3f} ha ({int(p_med) if p_n else 0} px)",
        f"  max patch area:    {p_max * PIX_HA:.3f} ha ({int(p_max) if p_n else 0} px)",
        "",
        "convention: reviewer A/B ordering is alphabetical and arbitrary, so directed pair",
        "counts (A_class->B_class) carry no meaning on their own; the symmetrized counts in",
        "ordered_pairs.csv are the reviewer-order-independent totals.",
    ]
    if tot_conflict < 5000:
        lines.insert(7, "  (this is small: a few thousand pixels across all pairs, as expected)")
    summary = "\n".join(lines)
    with open(os.path.join(OUT, "summary.txt"), "w") as fh:
        fh.write(summary + "\n")
    print("\n" + summary)
    print(f"\nwrote {OUT}/ (long, ordered_pairs, patches, summary)")


if __name__ == "__main__":
    main()
