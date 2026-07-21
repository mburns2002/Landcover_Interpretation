#!/usr/bin/env python3
"""Training-cap sensitivity analysis for the change classes, especially beaver.

A v2 embedding classifier was trained on 2018/2020 with the four change classes (harvest, development,
beaver, insect_disease) capped at 50, 100, and 150 training points, stable classes held at 200. Each
bracket's interpreted cells were classified with that bracket's own-year embeddings (temporally
matched). The cap=200 point already exists as band 1 (v2) of the transferability prediction rasters
and is added here as the fourth cap. This tests whether commission of rare change classes, especially
beaver, is a balanced-training artifact.

Interpretive context that shapes the figures: the four change classes have very different training
ceilings (harvest ~18,807 and development ~8,482 unique training pixels, but beaver only ~502 and
insect_disease ~662), so the 50/100/150 sweep is a trivial fraction of the harvest and development
pools but 10 to 30 percent of the beaver and insect pools. The cap therefore acts very differently on
large-pool versus small-pool classes, so beaver and insect are the informative ones. Overall accuracy
is dominated by the stable classes and is reported only as a secondary check.

Inputs:
  - cap 50/100/150: data/raw/sensitivity_changecap_10class_percell/<bracket>/sens_<bracket>_cell<id>.tif
    3 bands, band1=cap50, band2=cap100, band3=cap150, values 1 to 10.
  - cap 200: data/raw/transfer_predictions/<bracket>/pred_<bracket>_cell<id>.tif, band 1 (v2).
  - reference: data/raw/rf_class_maps/, CKIT label_id codes, crosswalked to the 10-class schema.

All four caps are evaluated on the same pooled cell set (the intersection of cells usable across all
four caps and the reference), so the cap comparison is not confounded by cell composition.

Outputs -> reports/sensitivity_changecap/

Requires: rasterio, numpy, pandas, matplotlib
"""

import argparse
import glob
import importlib.util
import os
import re
from collections import defaultdict

import numpy as np
import pandas as pd
import rasterio

# reuse the embedding matrix-building code
_spec = importlib.util.spec_from_file_location("bmc", os.path.join(
    os.path.dirname(__file__), "build_transfer_confusion.py"))
bmc = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(bmc)

BRACKETS = bmc.BRACKETS
NAMES = bmc.NAMES
LABELS = bmc.LABELS
CROSSWALK = bmc.CROSSWALK
EXCLUDE = bmc.EXCLUDE
ALLOWED = bmc.ALLOWED
_REF_LUT = bmc._REF_LUT

SENS_DIR = "data/raw/sensitivity_changecap_10class_percell"
TRANSFER_DIR = "data/raw/transfer_predictions"
OUT = "reports/sensitivity_changecap"

CAPS = [50, 100, 150, 200]
CHANGE_CLASSES = [1, 2, 9, 10]   # harvest, development, beaver, insect_disease
# stated training ceilings (unique training pixels available), from the sample generation
TRAIN_CEILING = {1: 18807, 2: 8482, 9: 502, 10: 662}

# ua is commission (precision), pa is omission (recall); one colour each, used across every figure
UA_COLOR = "#2c7fb8"
PA_COLOR = "#d95f0e"


def cap_source(cap):
    # returns (directory, filename prefix, band) for a cap
    if cap == 200:
        return TRANSFER_DIR, "pred", 1                 # band 1 of the 5-band transfer raster is v2
    band = {50: 1, 100: 2, 150: 3}[cap]
    return SENS_DIR, "sens", band


def cap_path(cap, bracket, cid):
    d, prefix, _ = cap_source(cap)
    return os.path.join(d, bracket, f"{prefix}_{bracket}_cell{cid}.tif")


def collapse_ref(ref_raw):
    safe = np.where((ref_raw >= 0) & (ref_raw <= 62), ref_raw, 0)
    return _REF_LUT[safe]


def usable_cells(chosen_ref):
    """Census per cap and reference, then intersect. Returns the common cell set and a drop report."""
    # index sensitivity cells by (bracket, cid)
    cells = []
    for p in sorted(glob.glob(os.path.join(SENS_DIR, "**", "sens_*.tif"), recursive=True)):
        m = re.search(r"sens_(\d{4}_\d{4})_cell(\d+)\.tif$", os.path.basename(p))
        cells.append((m.group(1), bmc.pad(m.group(2))))

    usable = {cap: set() for cap in CAPS}
    ref_ok = set()
    drops = defaultdict(list)      # reason -> [(bracket, cid, detail)]
    unmapped = defaultdict(int)

    for bracket, cid in cells:
        if cid not in chosen_ref:
            drops["missing_reference"].append((bracket, cid, ""))
            continue
        rp = chosen_ref[cid]
        with rasterio.open(rp) as rds:
            ref_raw = rds.read(1)
            ref_transform, ref_crs = rds.transform, rds.crs
            ref_wh = (rds.width, rds.height)
            for val in np.unique(ref_raw):
                iv = int(val)
                if iv not in ALLOWED:
                    unmapped[(bracket, cid, iv)] += int((ref_raw == val).sum())
            ref = collapse_ref(ref_raw)
            if not (ref >= 1).any():
                drops["reference_no_valid_px"].append((bracket, cid, ""))
                continue
            ref_ok.add(cid)
            # per cap: prediction present, grid identical, band not entirely nodata
            for cap in CAPS:
                pp = cap_path(cap, bracket, cid)
                if not os.path.exists(pp):
                    drops[f"cap{cap}_missing_pred"].append((bracket, cid, ""))
                    continue
                with rasterio.open(pp) as pds:
                    if (pds.width, pds.height) != ref_wh or str(pds.crs) != str(ref_crs) or \
                       not np.allclose([pds.transform.a, pds.transform.b, pds.transform.c,
                                        pds.transform.d, pds.transform.e, pds.transform.f],
                                       [ref_transform.a, ref_transform.b, ref_transform.c,
                                        ref_transform.d, ref_transform.e, ref_transform.f], atol=1e-6):
                        drops[f"cap{cap}_grid_mismatch"].append((bracket, cid, ""))
                        continue
                    _, _, band = cap_source(cap)
                    if not (pds.read(band) >= 1).any():
                        drops[f"cap{cap}_blank_pred"].append((bracket, cid, ""))
                        continue
                usable[cap].add(cid)

    common = ref_ok.copy()
    for cap in CAPS:
        common &= usable[cap]
    return common, usable, ref_ok, drops, unmapped


def build_matrix(cap, chosen_ref, common, cell_bracket):
    M = np.zeros((10, 10), np.int64)
    _, _, band = cap_source(cap)
    for cid in sorted(common):
        bracket = cell_bracket[cid]
        rp = chosen_ref[cid]
        with rasterio.open(cap_path(cap, bracket, cid)) as pds, rasterio.open(rp) as rds:
            pred = pds.read(band)
            ref = collapse_ref(rds.read(1))
        valid = (ref >= 1) & (ref <= 10) & (pred >= 1) & (pred <= 10)
        np.add.at(M, (ref[valid] - 1, pred[valid] - 1), 1)
    return M


def _r(x):
    return round(float(x), 5) if np.isfinite(x) else ""


# ----------------------------------------------------------------------------- figures
def _style(ax):
    ax.grid(False)
    for s in ("top", "right"):
        ax.spines[s].set_visible(False)


def fig_beaver_headline(res, path):
    """Headline: beaver UA and PA vs cap, plus total predicted-beaver-pixel count vs cap."""
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    k = 9 - 1                                            # beaver index
    ua = [res[c]["precision"][k] for c in CAPS]
    pa = [res[c]["recall"][k] for c in CAPS]
    pred_px = [int(res[c]["pred_count"][k]) for c in CAPS]
    ref_px = int(res[CAPS[-1]]["support"][k])            # reference beaver support (same cell set)
    fig, axes = plt.subplots(1, 2, figsize=(13, 5))
    ax = axes[0]
    ax.plot(CAPS, ua, marker="o", lw=2.4, color=UA_COLOR, label="UA (user's / commission)")
    ax.plot(CAPS, pa, marker="s", lw=2.4, color=PA_COLOR, label="PA (producer's / recall)")
    ax.set_xticks(CAPS)
    ax.set_xlabel("change-class training cap")
    ax.set_ylabel("accuracy")
    ax.set_ylim(0, max(0.05, max(ua + pa) * 1.2))
    ax.set_title("beaver UA and PA vs cap", fontsize=10)
    ax.legend(fontsize=8, frameon=False)
    _style(ax)
    ax = axes[1]
    ax.bar([str(c) for c in CAPS], pred_px, color="#7a7a7a", edgecolor="white", zorder=3)
    ax.axhline(ref_px, color="black", lw=1.5, ls="--", zorder=4,
               label=f"interpreted beaver pixels ({ref_px:,})")
    ax.set_xlabel("change-class training cap")
    ax.set_ylabel("predicted beaver pixels (pooled)")
    ax.set_title("total predicted-beaver area vs cap", fontsize=10)
    ax.legend(fontsize=8, frameon=False)
    _style(ax)
    fig.suptitle(f"beaver commission sensitivity to training cap (pooled, {res['n_cells']} cells; "
                 f"beaver training ceiling ~{TRAIN_CEILING[9]:,} px)", fontsize=11)
    fig.tight_layout(rect=[0, 0, 1, 0.95])
    fig.savefig(path, dpi=150, bbox_inches="tight")
    plt.close(fig)


def fig_change_small_multiples(res, path):
    """One panel per change class: UA and PA vs cap, shared y so the classes are comparable."""
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    ymax = 0.0
    for c in CAPS:
        for cc in CHANGE_CLASSES:
            k = cc - 1
            ymax = max(ymax, np.nanmax([res[c]["precision"][k], res[c]["recall"][k]]))
    ymax = np.ceil(ymax * 11) / 10
    fig, axes = plt.subplots(1, 4, figsize=(17, 4.4), sharey=True)
    for ax, cc in zip(axes, CHANGE_CLASSES):
        k = cc - 1
        ua = [res[c]["precision"][k] for c in CAPS]
        pa = [res[c]["recall"][k] for c in CAPS]
        ax.plot(CAPS, ua, marker="o", lw=2.2, color=UA_COLOR, label="UA (commission)")
        ax.plot(CAPS, pa, marker="s", lw=2.2, color=PA_COLOR, label="PA (recall)")
        ax.set_xticks(CAPS)
        ax.set_xlabel("training cap")
        ax.set_ylim(0, ymax)
        ax.set_title(f"{NAMES[cc]}\n(ceiling ~{TRAIN_CEILING[cc]:,} px, "
                     f"ref {int(res[CAPS[-1]]['support'][k]):,} px)", fontsize=9)
        _style(ax)
    axes[0].set_ylabel("accuracy")
    axes[-1].legend(fontsize=8, frameon=False)
    fig.suptitle(f"change-class UA and PA vs training cap (pooled, {res['n_cells']} cells); "
                 "small-pool classes (beaver, insect) are the informative ones", fontsize=11)
    fig.tight_layout(rect=[0, 0, 1, 0.93])
    fig.savefig(path, dpi=150, bbox_inches="tight")
    plt.close(fig)


def fig_predicted_area(res, path):
    """One panel per change class: predicted area fraction vs cap, with the reference prevalence line."""
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    fig, axes = plt.subplots(1, 4, figsize=(17, 4.4))
    for ax, cc in zip(axes, CHANGE_CLASSES):
        k = cc - 1
        pred_frac = [res[c]["pred_count"][k] / res[c]["total"] for c in CAPS]
        ref_frac = res[CAPS[-1]]["support"][k] / res[CAPS[-1]]["total"]
        ax.plot(CAPS, [p * 100 for p in pred_frac], marker="o", lw=2.4, color="#4d4d4d",
                label="predicted", zorder=3)
        ax.axhline(ref_frac * 100, color="black", lw=1.5, ls="--", zorder=4,
                   label=f"interpreted ({ref_frac * 100:.2f}%)")
        ax.set_xticks(CAPS)
        ax.set_xlabel("training cap")
        ax.set_title(f"{NAMES[cc]}", fontsize=10)
        ax.set_ylim(0, max(max(pred_frac), ref_frac) * 120)
        ax.legend(fontsize=8, frameon=False)
        _style(ax)
    axes[0].set_ylabel("percent of pooled pixels predicted as class")
    fig.suptitle(f"predicted change-class area vs training cap (pooled, {res['n_cells']} cells); "
                 "bar above the dashed reference line is over-mapping / commission", fontsize=11)
    fig.tight_layout(rect=[0, 0, 1, 0.93])
    fig.savefig(path, dpi=150, bbox_inches="tight")
    plt.close(fig)


def fig_overall_secondary(res, path):
    """Secondary: overall OA, macro-F1, and kappa vs cap, dominated by the stable classes."""
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    fig, ax = plt.subplots(figsize=(7.5, 5))
    for mk, lab, col in [("OA", "overall accuracy", "#444444"),
                         ("macro_F1", "macro-F1", "#1b9e77"),
                         ("kappa", "kappa", "#7570b3")]:
        ax.plot(CAPS, [res[c][mk] for c in CAPS], marker="o", lw=2.2, color=col, label=lab)
    ax.set_xticks(CAPS)
    ax.set_xlabel("change-class training cap")
    ax.set_ylabel("value")
    ax.set_title("SECONDARY: overall metrics vs cap\n(dominated by stable classes, not the "
                 "change-class subject of this analysis)", fontsize=10)
    ax.legend(fontsize=8, frameon=False)
    _style(ax)
    fig.tight_layout()
    fig.savefig(path, dpi=150, bbox_inches="tight")
    plt.close(fig)


def write_note(common, usable, ref_ok, drops, unmapped, res, path):
    lines = [
        "# sensitivity_changecap",
        "",
        "Training-cap sensitivity for the change classes. A v2 embedding classifier trained on "
        "2018/2020 with the four change classes (harvest, development, beaver, insect_disease) capped "
        "at 50, 100, and 150 training points, stable classes held at 200, applied per bracket with "
        "that bracket's own-year embeddings. The cap=200 point is band 1 (v2) of the transferability "
        "rasters. Generated by `scripts/build_changecap_sensitivity.py`, reusing the confusion-matrix "
        "code in `scripts/build_transfer_confusion.py`.",
        "",
        "## Training ceilings (the key interpretive constraint)",
        "",
        "The four change classes have very different unique-training-pixel ceilings, so the 50/100/150 "
        "sweep means different things for each:",
        "",
        f"- harvest ~{TRAIN_CEILING[1]:,} px: the cap is a trivial fraction of the pool.",
        f"- development ~{TRAIN_CEILING[2]:,} px: the cap is a small fraction of the pool.",
        f"- beaver ~{TRAIN_CEILING[9]:,} px: the cap is 10 to 30 percent of the whole pool, the tight "
        "constraint and the reason beaver is the headline.",
        f"- insect_disease ~{TRAIN_CEILING[10]:,} px: also a small pool, so it is informative alongside "
        "beaver.",
        "",
        "The cap acts differently on large-pool versus small-pool classes, so beaver and insect are "
        "the informative classes, and overall accuracy (dominated by the stable classes) is reported "
        "only as a secondary check.",
        "",
        "## Common cell set",
        "",
        f"All four caps are evaluated on the same pooled cell set of **{len(common)} cells**, the "
        "intersection of cells usable across all four caps and the reference. Per-cap usable counts: "
        + ", ".join(f"cap{cap}={len(usable[cap])}" for cap in CAPS)
        + f", reference usable={len(ref_ok)}.",
        "",
    ]
    total_drops = sum(len(v) for v in drops.values())
    if total_drops:
        lines.append("Cells dropped (with reason):")
        for reason, lst in sorted(drops.items()):
            lines.append(f"- {reason}: {len(lst)}"
                         + (f" ({[c for _, c, _ in lst][:8]})" if lst else ""))
    else:
        lines.append("No cells were dropped: every sensitivity cell had a matching, grid-identical, "
                     "non-blank prediction for all four caps and a valid reference.")
    lines += [
        "",
        "## Crosswalk and exclusions (reference only)",
        "",
        "CKIT label_id to the 10-class schema: " + ", ".join(f"{k}->{v}" for k, v in CROSSWALK.items())
        + f". Excluded reference values (pixel dropped): {sorted(EXCLUDE)} (10 = unknown abstention, "
        "13 = other_no_change). Unmapped reference values found: "
        + (str(len(unmapped)) + " (cell, value) occurrences." if unmapped else "none."),
        "",
        "## Interpretive guardrail",
        "",
        "Do not read lower cap as better from UA alone. With beaver's tight training ceiling the live "
        "question is whether reduced commission (higher UA at lower cap) comes at the cost of recall "
        "(PA) or is just relabeling, so UA and PA are shown together. If beaver UA does not improve as "
        "the cap drops, that too is a finding, since it would suggest the commission is not a simple "
        "oversampling effect and beaver is genuinely hard to separate.",
        "",
        "## Outputs",
        "",
        "- `cm_cap<cap>_counts.csv`, `_rownorm.csv`, `_colnorm.csv`: the four pooled 10x10 matrices, "
        "reference on rows, prediction on columns.",
        "- `cm_cap<cap>.png`: count heatmaps with PA/UA margins and OA/kappa.",
        "- `sensitivity_metrics_long.csv`: one row per (cap, class) with per-class UA, PA, F1, IoU, and "
        "support, plus the aggregate OA, macro-F1, mean IoU, and kappa.",
        "- Figures: `beaver_headline.png` (primary), `change_classes_ua_pa_vs_cap.png`, "
        "`change_classes_predicted_area_vs_cap.png`, and `overall_metrics_vs_cap.png` (secondary).",
    ]
    with open(path, "w") as fh:
        fh.write("\n".join(lines) + "\n")


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--truth", default="exports/truth_selections.csv",
                    help="adjudicated reviewer per cell (matches the transferability adjudicated basis)")
    args = ap.parse_args()
    os.makedirs(OUT, exist_ok=True)

    # reference selection, identical to the adjudicated transferability run
    ref_index = bmc.build_reference_index()
    truth = bmc.load_truth(args.truth)
    chosen_ref, n_multi, missing, mismatch = bmc.choose_references_truth(ref_index, truth)
    if mismatch:
        print("STOP: truth reviewer with no matching raster:", mismatch[:10]); raise SystemExit(1)

    common, usable, ref_ok, drops, unmapped = usable_cells(chosen_ref)
    cell_bracket = {}
    for p in glob.glob(os.path.join(SENS_DIR, "**", "sens_*.tif"), recursive=True):
        m = re.search(r"sens_(\d{4}_\d{4})_cell(\d+)\.tif$", os.path.basename(p))
        cell_bracket[bmc.pad(m.group(2))] = m.group(1)

    print(f"reference cells indexed: {len(ref_index)}   adjudicated multi-interpreted: {n_multi}")
    print(f"per-cap usable: " + ", ".join(f"cap{c}={len(usable[c])}" for c in CAPS)
          + f"   reference usable={len(ref_ok)}")
    print(f"common cell set (all four caps and reference): {len(common)}")
    if drops:
        for reason, lst in sorted(drops.items()):
            print(f"  dropped {reason}: {len(lst)}")
    if unmapped:
        agg = defaultdict(int)
        for (_, _, iv), n in unmapped.items():
            agg[iv] += n
        print(f"  unmapped reference values: {dict(agg)}")

    # build the four pooled matrices, metrics, and per-cap prediction marginals
    res = {"n_cells": len(common)}
    long_rows = []
    print(f"\n{'cap':>5}{'OA':>8}{'macF1':>8}{'kappa':>8}   beaver: {'UA':>6}{'PA':>6}{'predpx':>10}")
    for cap in CAPS:
        M = build_matrix(cap, chosen_ref, common, cell_bracket)
        mt = bmc.metrics(M)
        total = int(M.sum())
        res[cap] = dict(precision=mt["precision"], recall=mt["recall"], f1=mt["f1"], iou=mt["iou"],
                        support=mt["support"], pred_count=M.sum(0), total=total,
                        OA=mt["OA"], macro_F1=mt["macro_F1"], mean_IoU=mt["mean_IoU"], kappa=mt["kappa"])
        # matrices: counts, row-normalized, column-normalized
        pd.DataFrame(M, index=LABELS, columns=LABELS).to_csv(os.path.join(OUT, f"cm_cap{cap}_counts.csv"))
        with np.errstate(invalid="ignore"):
            rn = M / np.where(M.sum(1, keepdims=True) > 0, M.sum(1, keepdims=True), np.nan)
            cn = M / np.where(M.sum(0, keepdims=True) > 0, M.sum(0, keepdims=True), np.nan)
        pd.DataFrame(np.round(rn, 5), index=LABELS, columns=LABELS).to_csv(
            os.path.join(OUT, f"cm_cap{cap}_rownorm.csv"))
        pd.DataFrame(np.round(cn, 5), index=LABELS, columns=LABELS).to_csv(
            os.path.join(OUT, f"cm_cap{cap}_colnorm.csv"))
        bmc.render_cm_png(M, mt, f"cap{cap}", "pooled", os.path.join(OUT, f"cm_cap{cap}.png"))
        # long rows
        for k in range(10):
            c = k + 1
            long_rows.append(dict(
                cap=cap, class_code=c, class_name=NAMES[c],
                precision=_r(mt["precision"][k]), recall=_r(mt["recall"][k]),
                f1=_r(mt["f1"][k]), iou=_r(mt["iou"][k]), support=int(mt["support"][k]),
                predicted_pixels=int(M.sum(0)[k]),
                is_change_class=(c in CHANGE_CLASSES),
                train_ceiling=TRAIN_CEILING.get(c, ""),
                OA=round(mt["OA"], 5), macro_F1=round(mt["macro_F1"], 5),
                mean_IoU=round(mt["mean_IoU"], 5), kappa=round(mt["kappa"], 5),
                n_cells=len(common), total_pixels=total))
        bk = 9 - 1
        print(f"{cap:>5}{mt['OA']:>8.3f}{mt['macro_F1']:>8.3f}{mt['kappa']:>8.3f}   "
              f"       {mt['precision'][bk]:>6.3f}{mt['recall'][bk]:>6.3f}{int(M.sum(0)[bk]):>10,}")

    pd.DataFrame(long_rows).to_csv(os.path.join(OUT, "sensitivity_metrics_long.csv"), index=False)

    # figures
    fig_beaver_headline(res, os.path.join(OUT, "beaver_headline.png"))
    fig_change_small_multiples(res, os.path.join(OUT, "change_classes_ua_pa_vs_cap.png"))
    fig_predicted_area(res, os.path.join(OUT, "change_classes_predicted_area_vs_cap.png"))
    fig_overall_secondary(res, os.path.join(OUT, "overall_metrics_vs_cap.png"))

    write_note(common, usable, ref_ok, drops, unmapped, res, os.path.join(OUT, "note.md"))
    print(f"\nwrote {OUT}/ (4 matrices x 3 csv + png, sensitivity_metrics_long.csv, 4 figures, note.md)")


if __name__ == "__main__":
    main()
