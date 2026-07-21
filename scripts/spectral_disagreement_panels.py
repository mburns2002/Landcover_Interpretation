#!/usr/bin/env python3
"""Multi-panel map visualization of the top spec_all-vs-interpreted disagreement cells.

For the ten interpreted cells where the spectral spec_all classified map disagrees most with the
interpreted reference (per-pixel, common 10-class codes), render a panel figure with the interpreted
reference, the spec_all map, the embedding variants v2, v3, v4, and v5 (v6, the dot-only variant, is
omitted), and an agree/disagree map between spec_all and the reference in colorblind-friendly colors.

Reference is the adjudicated interpreted cell; predictions are the temporally-matched per-bracket
maps (spec_all from the spectral export, v2-v5 from the embedding transfer export). Cells whose
spec_all raster is entirely nodata are skipped.

Outputs -> reports/spectral_composite_classified_maps/comparison/top_disagreement_maps/
  - rank<NN>_cell<gid>_<bracket>.png      one 7-panel figure per top-disagreement cell
  - top_disagreement_summary.csv          rank, cell, bracket, disagreement fraction, valid pixels

Requires: rasterio, numpy, pandas, matplotlib
"""

import glob
import importlib.util
import os
import re

import numpy as np
import pandas as pd
import rasterio


def _load(name, path):
    spec = importlib.util.spec_from_file_location(name, os.path.join(os.path.dirname(__file__), path))
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


bmc = _load("bmc", "build_transfer_confusion.py")          # adjudicated reference selection
C = _load("C", "compare_interpreted_vs_model.py")           # class names, colors, RF crosswalk
cc = _load("cc", "collapsed_5class_confusion.py")           # 5-class collapse maps and names

# collapsed 5-class colours: Stable neutral grey, the four change classes in the shared 5-class palette
COLLAPSE_COLORS = {1: "#cccccc", 2: "#ff7f0e", 3: "#2ca02c", 4: "#d62728", 5: "#9467bd"}

TRUTH = "exports/truth_selections.csv"
SPEC_DIR = "data/raw/spectral_transferability_10class_percell"
EMB_DIR = "data/raw/transfer_predictions"
EMB_VARIANTS = ["v2", "v3", "v4", "v5"]                      # exclude v6 (dot only)
VBAND = {"v2": 1, "v3": 2, "v4": 3, "v5": 4, "v6": 5}
OUT = "reports/spectral_composite_classified_maps/comparison/top_disagreement_maps"
TOP_N = 10
# colorblind-friendly (Okabe-Ito): blue = agree, vermillion = disagree
AGREE_COLOR = "#0072B2"
DISAGREE_COLOR = "#D55E00"


def read_band(path, band):
    with rasterio.open(path) as ds:
        return ds.read(band)


def main():
    global OUT
    import argparse
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--rank-by", choices=["spectral", "embedding"], default="spectral",
                    help="rank cells by spec_all-vs-reference (default) or by the mean "
                         "embedding(v2-v5)-vs-reference disagreement")
    ap.add_argument("--out", default=OUT, help="output folder")
    ap.add_argument("--collapse", action="store_true",
                    help="collapse reference and predictions to the 5-class scheme (Stable plus the "
                         "four change classes) instead of the 10-class scheme")
    args = ap.parse_args()
    OUT = args.out
    rank_by = args.rank_by
    collapse = args.collapse
    os.makedirs(OUT, exist_ok=True)
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    from matplotlib.colors import ListedColormap
    from matplotlib.patches import Patch

    rf2common, names, colors = C.load_mappings()
    ref_index = bmc.build_reference_index()
    truth = bmc.load_truth(TRUTH)
    chosen_ref, n_multi, missing, mismatch = bmc.choose_references_truth(ref_index, truth)
    if mismatch:
        print("STOP: truth reviewer with no matching raster:", mismatch[:10]); raise SystemExit(1)

    # class scheme: 10-class common codes, or the 5-class collapse (Stable plus four change classes)
    if collapse:
        N = 5
        class_names, class_colors = cc.NAMES5, COLLAPSE_COLORS
        scheme_label = "collapsed 5-class"

        def to_ref(raw):
            return cc._REF_COLLAPSE[np.where((raw >= 0) & (raw <= 62), raw, 0)]

        def to_pred(raw):
            return cc._MODEL_COLLAPSE[np.where(raw <= 10, raw, 0)]
    else:
        N = 10
        class_names, class_colors = names, colors
        scheme_label = "common 10-class"

        def to_ref(raw):
            return C.to_common_rf(raw, rf2common)

        def to_pred(raw):
            return raw

    # classified-map colormap: index 0 = nodata (white), 1..N = class colors
    class_cmap = ListedColormap(["#ffffff"] + [class_colors[c] for c in range(1, N + 1)])
    ad_cmap = ListedColormap(["#ffffff", AGREE_COLOR, DISAGREE_COLOR])   # 0 nodata, 1 agree, 2 disagree

    # rank cells by disagreement vs the interpreted reference. rank_by=spectral uses spec_all;
    # rank_by=embedding uses the mean per-pixel disagreement of v2-v5. spec_all must be non-blank
    # either way so there is a spectral map to view at each location.
    records = []
    for bracket in bmc.BRACKETS:
        for sp in sorted(glob.glob(os.path.join(SPEC_DIR, bracket, "pred_specall_*.tif"))):
            gid = bmc.pad(re.search(r"cell(\d+)\.tif$", os.path.basename(sp)).group(1))
            if gid not in chosen_ref:
                continue
            spec_raw = read_band(sp, 1)
            if not (spec_raw >= 1).any():                   # entirely nodata
                continue
            spec = to_pred(spec_raw)
            with rasterio.open(chosen_ref[gid]) as rds:
                ref = to_ref(rds.read(1))
            valid = (ref >= 1) & (ref <= N) & (spec >= 1) & (spec <= N)
            nvalid = int(valid.sum())
            if nvalid == 0:
                continue
            if rank_by == "spectral":
                disagree = float((ref[valid] != spec[valid]).mean())
            else:                                            # mean embedding disagreement over v2-v5
                ds = []
                for v in EMB_VARIANTS:
                    ev = to_pred(read_band(os.path.join(EMB_DIR, bracket,
                                                        f"pred_{bracket}_cell{gid}.tif"), VBAND[v]))
                    vv = (ref >= 1) & (ref <= N) & (ev >= 1) & (ev <= N)
                    if vv.any():
                        ds.append(float((ref[vv] != ev[vv]).mean()))
                if not ds:
                    continue
                disagree = float(np.mean(ds))
            records.append(dict(disagree=disagree, gid=gid, bracket=bracket,
                                ref_path=chosen_ref[gid], spec_path=sp, n_valid=nvalid))

    records.sort(key=lambda r: r["disagree"], reverse=True)
    top = records[:TOP_N]
    pd.DataFrame([{k: r[k] for k in ("gid", "bracket", "disagree", "n_valid")}
                 for r in top]).assign(rank=range(1, len(top) + 1)).to_csv(
        os.path.join(OUT, "top_disagreement_summary.csv"), index=False)

    class_handles = [Patch(facecolor=class_colors[c], edgecolor="0.4", label=class_names[c])
                     for c in range(1, N + 1)]
    ad_handles = [Patch(facecolor=AGREE_COLOR, label="agree"),
                  Patch(facecolor=DISAGREE_COLOR, label="disagree")]

    for i, r in enumerate(top, 1):
        gid, bracket = r["gid"], r["bracket"]
        ref = to_ref(read_band(r["ref_path"], 1))
        spec = to_pred(read_band(r["spec_path"], 1))
        emb = {v: to_pred(read_band(os.path.join(EMB_DIR, bracket, f"pred_{bracket}_cell{gid}.tif"),
                                    VBAND[v])) for v in EMB_VARIANTS}
        fig, axes = plt.subplots(2, 4, figsize=(15, 8))
        # top row: interpreted, spec_all, disagreement panel, class legend
        for ax, (arr, title) in zip(
                [axes[0, 0], axes[0, 1]],
                [(ref, "interpreted reference"), (spec, "spec_all (spectral)")]):
            ax.imshow(arr, cmap=class_cmap, vmin=-0.5, vmax=N + 0.5, interpolation="nearest")
            ax.set_title(title, fontsize=11); ax.set_xticks([]); ax.set_yticks([])
        adax = axes[0, 2]
        adax.set_xticks([]); adax.set_yticks([])
        if rank_by == "embedding":
            # count how many of v2-v5 differ from the reference per pixel (0..4); this is the ranked
            # quantity, so the panel visualizes the embedding disagreement rather than spec_all
            ref_valid = (ref >= 1) & (ref <= N)
            count = np.zeros(ref.shape, np.int16)
            any_valid = np.zeros(ref.shape, bool)
            for v in EMB_VARIANTS:
                ev = emb[v]
                vv = ref_valid & (ev >= 1) & (ev <= N)
                count[vv & (ev != ref)] += 1
                any_valid |= vv
            disp = np.where(any_valid, count + 1, 0)       # 0 = nodata, 1..5 = 0..4 disagreeing
            ecmap = ListedColormap(["#cccccc", "#eff3ff", "#bdd7e7", "#6baed6", "#3182bd", "#08519c"])
            adax.imshow(disp, cmap=ecmap, vmin=-0.5, vmax=5.5, interpolation="nearest")
            adax.set_title("embedding disagreement\n(# of v2-v5 differing from reference)", fontsize=11)
            ecolors = ["#eff3ff", "#bdd7e7", "#6baed6", "#3182bd", "#08519c"]
            ec_handles = [Patch(facecolor=ecolors[k],
                                label=f"{k}" + (" (all agree)" if k == 0 else
                                                " (all disagree)" if k == 4 else "")) for k in range(5)]
            adax.legend(handles=ec_handles, loc="lower right", fontsize=6.5, framealpha=0.9,
                        title="# disagreeing", title_fontsize=6.5)
        else:
            valid = (ref >= 1) & (ref <= N) & (spec >= 1) & (spec <= N)
            ad = np.zeros(spec.shape, np.uint8)
            ad[valid & (ref == spec)] = 1
            ad[valid & (ref != spec)] = 2
            adax.imshow(ad, cmap=ad_cmap, vmin=-0.5, vmax=2.5, interpolation="nearest")
            adax.set_title("agree / disagree\n(spec_all vs interpreted)", fontsize=11)
            adax.legend(handles=ad_handles, loc="lower right", fontsize=8, framealpha=0.9)
        axes[0, 3].axis("off")
        axes[0, 3].legend(handles=class_handles, loc="center left", fontsize=9,
                          frameon=False, title=f"{scheme_label} scheme")
        # bottom row: the four embedding variants
        for ax, v in zip(axes[1], EMB_VARIANTS):
            ax.imshow(emb[v], cmap=class_cmap, vmin=-0.5, vmax=N + 0.5, interpolation="nearest")
            ax.set_title(f"embedding {v}", fontsize=11); ax.set_xticks([]); ax.set_yticks([])

        rank_desc = ("spec_all-vs-interpreted" if rank_by == "spectral"
                     else "mean embedding(v2-v5)-vs-interpreted")
        fig.suptitle(f"cell {gid}  ·  bracket {bracket.replace('_', '-')}  ·  rank {i} of {TOP_N} by "
                     f"{rank_desc} disagreement ({r['disagree'] * 100:.0f}% of "
                     f"{r['n_valid']:,} valid px)", fontsize=13)
        if rank_by == "spectral":
            panel_desc = ("The agree/disagree panel marks where spec_all matches the reference (blue) "
                          "or differs (vermillion), in colorblind-friendly colors. ")
            rank_caption = ("This cell is among the ten with the most spec_all-vs-interpreted "
                            "disagreement, so it shows where the spectral classifier departs most from "
                            "the human interpretation.")
        else:
            panel_desc = ("The disagreement panel shades each pixel by how many of the embedding "
                          "variants v2-v5 differ from the reference there (light = agreement, dark = "
                          "all four disagree). ")
            rank_caption = ("This cell is among the ten where the embedding variants v2-v5 disagree "
                            "most with the interpreted reference, on average, so the panels let you "
                            "see whether the spectral spec_all map tracks the reference where the "
                            "embeddings do not.")
        fig.text(0.5, 0.01,
                 f"Classified maps ({scheme_label} scheme) for one interpreted cell: the interpreted "
                 "reference, the spectral spec_all map, and the embedding variants v2, v3, v4, and v5 "
                 "(v6, the dot-only variant, is omitted). " + panel_desc + rank_caption,
                 ha="center", va="bottom", fontsize=8, color="0.35", wrap=True)
        fig.tight_layout(rect=[0, 0.06, 1, 0.95])
        fig.savefig(os.path.join(OUT, f"rank{i:02d}_cell{gid}_{bracket}.png"), dpi=140,
                    bbox_inches="tight")
        plt.close(fig)
        print(f"  rank {i:2d}: cell {gid} {bracket}  disagree {r['disagree'] * 100:.0f}%")

    print(f"\nwrote {OUT}/ ({len(top)} figures, top_disagreement_summary.csv)")


if __name__ == "__main__":
    main()
