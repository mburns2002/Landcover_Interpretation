#!/usr/bin/env python3
"""Top-disagreement map panels for the change-cap sensitivity, in the collapsed 5-class scheme.

Mirrors reports/spectral_composite_classified_maps/comparison/top_disagreement_maps, but the "maps"
are the change-cap predictions instead of spec_all and the embedding variants. For each of the three
swept caps (50, 100, 150), the cells are ranked by the disagreement between that cap's prediction and
the interpreted reference (collapsed 5-class), and the top ten are rendered as a panel figure showing
the interpreted reference, all four cap maps (50, 100, 150, 200), and an agree/disagree map for the
ranking cap. One output folder per ranking cap.

Reference is the adjudicated interpreted cell; predictions are the change-cap maps (cap 50/100/150 from
the sensitivity export, cap 200 from the transferability export, band 1 = v2). Classes are collapsed to
Stable plus Harvest, Development, Insect/Disease, and Beaver, coloured by the canonical class legend.

Two modes, one output tree each, both with cap50/cap100/cap150 subfolders:
  - default (caps): each panel shows the interpreted reference and all four cap maps (50/100/150/200)
    plus the ranking cap's agree/disagree map, in reports/.../top_disagreement_maps/.
  - --embeddings: each panel shows the interpreted reference, only the ranking cap, and the embedding
    variants v2-v5 plus the ranking cap's agree/disagree map, in reports/.../cap_vs_embedding_maps/.

Each subfolder holds rank<NN>_cell<gid>_<bracket>.png and top_disagreement_summary.csv.

Requires: rasterio, numpy, pandas, matplotlib
"""

import importlib.util
import os

import numpy as np
import pandas as pd
import rasterio


def _load(name, path):
    spec = importlib.util.spec_from_file_location(name, os.path.join(os.path.dirname(__file__), path))
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


scs = _load("scs", "build_changecap_sensitivity.py")       # cap paths, usable cells, reference base
cc = _load("cc", "collapsed_5class_confusion.py")           # 5-class collapse maps and names
C = _load("C", "compare_interpreted_vs_model.py")           # canonical class legend colours
bmc = scs.bmc

TRUTH = "exports/truth_selections.csv"
RANK_CAPS = [50, 100, 150]                                  # one output folder per swept cap
ALL_CAPS = [50, 100, 150, 200]                              # caps mode shows every cap in each panel
EMB_DIR = "data/raw/transfer_predictions"
EMB_VARIANTS = ["v2", "v3", "v4", "v5"]                     # embeddings mode shows these (v6 omitted)
VBAND = {"v2": 1, "v3": 2, "v4": 3, "v5": 4, "v6": 5}
OUT_CAPS = "reports/sensitivity_changecap_5class/top_disagreement_maps"
OUT_EMB = "reports/sensitivity_changecap_5class/cap_vs_embedding_maps"
TOP_N = 10
AGREE_COLOR = "#0072B2"                                     # colorblind-friendly (Okabe-Ito)
DISAGREE_COLOR = "#D55E00"
# collapsed change classes reuse the 10-class legend colours; Stable is a neutral grey
_C10 = C.load_mappings()[2]
CLASS_COLORS = {1: "#cccccc", 2: _C10[1], 3: _C10[2], 4: _C10[10], 5: _C10[9]}


def read_band(path, band):
    with rasterio.open(path) as ds:
        return ds.read(band)


def to_ref(raw):
    return cc._REF_COLLAPSE[np.where((raw >= 0) & (raw <= 62), raw, 0)]


def to_pred(raw):
    return cc._MODEL_COLLAPSE[np.where(raw <= 10, raw, 0)]


def main():
    import argparse
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--embeddings", action="store_true",
                    help="show the ranking cap plus the embedding v2-v5 maps instead of all four caps")
    args = ap.parse_args()
    mode = "embeddings" if args.embeddings else "caps"
    OUT = OUT_EMB if args.embeddings else OUT_CAPS
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    from matplotlib.colors import ListedColormap
    from matplotlib.patches import Patch

    ref_index = bmc.build_reference_index()
    truth = bmc.load_truth(TRUTH)
    chosen_ref, n_multi, missing, mismatch = bmc.choose_references_truth(ref_index, truth)
    if mismatch:
        print("STOP: truth reviewer with no matching raster:", mismatch[:10]); raise SystemExit(1)
    common, usable, ref_ok, drops, unmapped = scs.usable_cells(chosen_ref)
    cell_bracket = {}
    import glob
    import re
    for p in glob.glob(os.path.join(scs.SENS_DIR, "**", "sens_*.tif"), recursive=True):
        m = re.search(r"sens_(\d{4}_\d{4})_cell(\d+)\.tif$", os.path.basename(p))
        cell_bracket[bmc.pad(m.group(2))] = m.group(1)
    print(f"common cell set: {len(common)}")

    class_cmap = ListedColormap(["#ffffff"] + [CLASS_COLORS[c] for c in range(1, 6)])
    ad_cmap = ListedColormap(["#ffffff", AGREE_COLOR, DISAGREE_COLOR])
    class_handles = [Patch(facecolor=CLASS_COLORS[c], edgecolor="0.4", label=cc.NAMES5[c])
                     for c in range(1, 6)]
    ad_handles = [Patch(facecolor=AGREE_COLOR, label="agree"),
                  Patch(facecolor=DISAGREE_COLOR, label="disagree")]

    for rank_cap in RANK_CAPS:
        _, _, rband = scs.cap_source(rank_cap)
        # rank cells by this cap's collapsed disagreement with the reference
        recs = []
        for cid in sorted(common):
            bracket = cell_bracket[cid]
            ref = to_ref(read_band(chosen_ref[cid], 1))
            pred = to_pred(read_band(scs.cap_path(rank_cap, bracket, cid), rband))
            valid = (ref >= 1) & (ref <= 5) & (pred >= 1) & (pred <= 5)
            nv = int(valid.sum())
            if nv == 0:
                continue
            recs.append(dict(disagree=float((ref[valid] != pred[valid]).mean()),
                             gid=cid, bracket=bracket, n_valid=nv))
        recs.sort(key=lambda r: r["disagree"], reverse=True)
        top = recs[:TOP_N]
        out = os.path.join(OUT, f"cap{rank_cap}")
        os.makedirs(out, exist_ok=True)
        pd.DataFrame([{k: r[k] for k in ("gid", "bracket", "disagree", "n_valid")}
                     for r in top]).assign(rank=range(1, len(top) + 1)).to_csv(
            os.path.join(out, "top_disagreement_summary.csv"), index=False)

        for i, r in enumerate(top, 1):
            gid, bracket = r["gid"], r["bracket"]
            ref = to_ref(read_band(chosen_ref[gid], 1))
            capX = to_pred(read_band(scs.cap_path(rank_cap, bracket, gid), rband))
            valid = (ref >= 1) & (ref <= 5) & (capX >= 1) & (capX <= 5)
            ad = np.zeros(ref.shape, np.uint8)
            ad[valid & (ref == capX)] = 1
            ad[valid & (ref != capX)] = 2

            fig, axes = plt.subplots(2, 4, figsize=(15, 8))
            if mode == "embeddings":
                # top row: interpreted, the ranking cap, agree/disagree, legend; bottom row: v2-v5
                for ax, arr, title, bold in [(axes[0, 0], ref, "interpreted reference", False),
                                             (axes[0, 1], capX, f"cap {rank_cap}", True)]:
                    ax.imshow(arr, cmap=class_cmap, vmin=-0.5, vmax=5.5, interpolation="nearest")
                    ax.set_title(title, fontsize=11, fontweight="bold" if bold else "normal")
                    ax.set_xticks([]); ax.set_yticks([])
                adax = axes[0, 2]
                for ax, v in zip(axes[1], EMB_VARIANTS):
                    ev = to_pred(read_band(os.path.join(EMB_DIR, bracket,
                                                        f"pred_{bracket}_cell{gid}.tif"), VBAND[v]))
                    ax.imshow(ev, cmap=class_cmap, vmin=-0.5, vmax=5.5, interpolation="nearest")
                    ax.set_title(f"embedding {v}", fontsize=11); ax.set_xticks([]); ax.set_yticks([])
                legax = axes[0, 3]
            else:
                capmaps = {cap: to_pred(read_band(scs.cap_path(cap, bracket, gid),
                                                  scs.cap_source(cap)[2])) for cap in ALL_CAPS}
                panels = [(axes[0, 0], ref, "interpreted reference"),
                          (axes[0, 1], capmaps[50], "cap 50"), (axes[0, 2], capmaps[100], "cap 100"),
                          (axes[0, 3], capmaps[150], "cap 150"), (axes[1, 0], capmaps[200], "cap 200")]
                for ax, arr, title in panels:
                    ax.imshow(arr, cmap=class_cmap, vmin=-0.5, vmax=5.5, interpolation="nearest")
                    mark = "  (ranked)" if title == f"cap {rank_cap}" else ""
                    ax.set_title(title + mark, fontsize=11, fontweight="bold" if mark else "normal")
                    ax.set_xticks([]); ax.set_yticks([])
                adax = axes[1, 1]
                legax = axes[1, 2]
                axes[1, 3].axis("off")
            adax.imshow(ad, cmap=ad_cmap, vmin=-0.5, vmax=2.5, interpolation="nearest")
            adax.set_title(f"agree / disagree\n(cap {rank_cap} vs interpreted)", fontsize=11)
            adax.set_xticks([]); adax.set_yticks([])
            adax.legend(handles=ad_handles, loc="lower right", fontsize=8, framealpha=0.9)
            legax.axis("off")
            legax.legend(handles=class_handles, loc="center left", fontsize=9, frameon=False,
                         title="collapsed 5-class scheme")

            fig.suptitle(f"cell {gid}  ·  bracket {bracket.replace('_', '-')}  ·  rank {i} of {TOP_N} "
                         f"by cap {rank_cap}-vs-interpreted disagreement ({r['disagree'] * 100:.0f}% of "
                         f"{r['n_valid']:,} valid px)", fontsize=13)
            if mode == "embeddings":
                caption = (f"Collapsed 5-class maps for one interpreted cell: the interpreted "
                           f"reference, the cap {rank_cap} change-cap prediction, and the embedding "
                           "variants v2, v3, v4, and v5 (v6, the dot-only variant, is omitted). The "
                           f"agree/disagree panel marks where the cap {rank_cap} map matches the "
                           "reference (blue) or differs (vermillion). This cell is among the ten where "
                           f"the cap {rank_cap} prediction disagrees most with the interpreted "
                           "reference, so the panels compare it against the embedding maps at a hard "
                           "location.")
            else:
                caption = ("Collapsed 5-class maps for one interpreted cell: the interpreted reference "
                           "and the four change-cap predictions (50, 100, 150, and 200 training points "
                           f"per change class). The agree/disagree panel marks where the cap {rank_cap} "
                           "map matches the reference (blue) or differs (vermillion), in "
                           f"colorblind-friendly colors. This cell is among the ten where the cap "
                           f"{rank_cap} prediction disagrees most with the interpreted reference, so the "
                           "panels show how the predicted change changes with the training cap at a hard "
                           "location.")
            fig.text(0.5, 0.01, caption, ha="center", va="bottom", fontsize=8, color="0.35", wrap=True)
            fig.tight_layout(rect=[0, 0.06, 1, 0.95])
            fig.savefig(os.path.join(out, f"rank{i:02d}_cell{gid}_{bracket}.png"), dpi=140,
                        bbox_inches="tight")
            plt.close(fig)
        print(f"  cap {rank_cap}: wrote {len(top)} figures -> {out}/")

    print(f"\nwrote {OUT}/ (cap50, cap100, cap150 subfolders)")


if __name__ == "__main__":
    main()
