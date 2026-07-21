#!/usr/bin/env python3
"""Per-cap confusion matrices for the change-cap sensitivity analysis under the 5-class collapse.

The 5-class counterpart to build_changecap_sensitivity.py. It reuses that script's cell-set logic (so
the four caps are scored on the identical common cell set) and the 5-class collapse from
collapsed_5class_confusion.py. Scheme: Stable (all no-change classes folded) plus Harvest,
Development, Insect/Disease, and Beaver. The reference is collapsed with _REF_COLLAPSE (CKIT codes to
1..5, Other(13) to Stable, Unknown(10) and Fire(40) dropped) and the cap predictions with
_MODEL_COLLAPSE (10-class 1..10 to 1..5).

Caps: 50/100/150 are bands 1/2/3 of the sensitivity rasters, cap 200 is band 1 (v2) of the
transferability rasters, matching the 10-class analysis.

Outputs -> reports/sensitivity_changecap_5class/
  - cm_cap<cap>_counts.csv / _rownorm.csv / _colnorm.csv     pooled 5x5 matrices, reference on rows
  - cm_cap<cap>.png                                          count heatmap, PA/UA margins, OA/kappa
  - sensitivity_metrics_long_5class.csv                      one row per (cap, collapsed class)
  - note.md

Requires: rasterio, numpy, pandas, matplotlib
"""

import argparse
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


scs = _load("scs", "build_changecap_sensitivity.py")     # cap sensitivity helpers (usable cells, paths)
cc = _load("cc", "collapsed_5class_confusion.py")         # 5-class collapse, metrics, PA/UA figure
C = _load("C", "compare_interpreted_vs_model.py")         # canonical class legend colours
bmc = scs.bmc                                             # confusion-matrix base (reference selection)

CAPS = scs.CAPS
LABELS5 = cc.LABELS5
NAMES5 = cc.NAMES5
CHANGE5 = [2, 3, 4, 5]                                    # harvest, development, insect_disease, beaver
# change classes reuse the canonical 10-class legend colours (collapsed code -> 10-class code):
# harvest 2->1, development 3->2, insect/disease 4->10, beaver 5->9
_CLASS_COLORS = C.load_mappings()[2]
CHANGE5_COLOR = {c: _CLASS_COLORS[t] for c, t in {2: 1, 3: 2, 4: 10, 5: 9}.items()}
OUT = "reports/sensitivity_changecap_5class"


def _r(x):
    return round(float(x), 5) if np.isfinite(x) else ""


def _caption(fig, text, top=1.0, width=110):
    """Add a wrapped descriptive caption below the figure, reserving space for it (and leaving room
    above for a suptitle when top < 1)."""
    import textwrap
    wrapped = "\n".join(textwrap.wrap(text, width))
    nlines = wrapped.count("\n") + 1
    fig.tight_layout(rect=[0, 0.02 + 0.045 * nlines, 1, top])
    fig.text(0.5, 0.01, wrapped, ha="center", va="bottom", fontsize=8, color="0.35")


def fig_change_pa_vs_cap(res, path):
    """PA (recall) of each collapsed change class as a function of the training cap."""
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    fig, ax = plt.subplots(figsize=(8, 5))
    ymax = 0.0
    for c in CHANGE5:
        pa = [res[cap]["recall"][c - 1] for cap in CAPS]
        ymax = max(ymax, max(pa))
        ax.plot(CAPS, pa, "o-", lw=2.2, color=CHANGE5_COLOR[c], label=NAMES5[c])
    ax.set_xticks(CAPS)
    ax.set_xlabel("change-class training cap (training points)")
    ax.set_ylabel("producer's accuracy (recall / PA)")
    ax.set_ylim(0, ymax * 1.15)
    ax.set_title("Collapsed change-class recall (PA) vs training cap (pooled, 180 cells)")
    ax.legend(fontsize=8, frameon=False, title="change class")
    ax.grid(False)
    for s in ("top", "right"):
        ax.spines[s].set_visible(False)
    _caption(fig, "Producer's accuracy (recall) of each collapsed change class as a function of the "
                  "change-class training cap, pooled over the common 180 cells (v2). PA generally "
                  "rises with more training points for beaver, development, and harvest, since the "
                  "classifier recovers more of the true change pixels, and it stays low and flat for "
                  "insect/disease. The cap=200 point comes from a separate training run rather than "
                  "the 50/100/150 sweep, which is why harvest and development dip there. Higher is "
                  "better recall; commission (user's accuracy) stays near zero for all four classes "
                  "regardless of cap, so improved recall does not come with improved precision.")
    fig.savefig(path, dpi=150, bbox_inches="tight")
    plt.close(fig)


def fig_predicted_pixels_vs_cap(res, path):
    """Predicted pixel count of each collapsed change class as a function of the training cap, one
    panel per change class, with the interpreted reference count as a horizontal line."""
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    fig, axes = plt.subplots(1, 4, figsize=(17, 4.4))
    for ax, c in zip(axes, CHANGE5):
        k = c - 1
        pred = [int(res[cap]["pred_count"][k]) for cap in CAPS]
        ref = res[CAPS[-1]]["support"][k]                  # interpreted reference count (fixed cells)
        ax.plot(CAPS, pred, "o-", lw=2.4, color=CHANGE5_COLOR[c], label="predicted", zorder=3)
        ax.axhline(ref, ls="--", lw=1.5, color="black", zorder=4, label=f"interpreted ({ref:,} px)")
        ax.set_xticks(CAPS)
        ax.set_xlabel("change-class training cap (training points)")
        ax.set_title(NAMES5[c], fontsize=10)
        ax.set_ylim(0, max(max(pred), ref) * 1.15)
        ax.ticklabel_format(axis="y", style="plain")
        ax.legend(fontsize=8, frameon=False)
        ax.grid(False)
        for s in ("top", "right"):
            ax.spines[s].set_visible(False)
    axes[0].set_ylabel("predicted pixels (pooled)")
    fig.suptitle(f"predicted change-class pixel count vs training cap (pooled, {res['n_cells']} cells)",
                 fontsize=11)
    _caption(fig, "Number of pixels the model assigns to each collapsed change class as a function of "
                  "the change-class training cap, one panel per class, with the interpreted reference "
                  "count as a dashed black line. The predicted count grows with the cap for beaver, "
                  "development, and harvest, since a larger cap trains the classifier to call those "
                  "classes more often, and every cap over-predicts each class by one to two orders of "
                  "magnitude relative to the interpreted reference. The cap=200 point comes from a "
                  "separate training run, so it does not always continue the 50/100/150 trend.",
                  top=0.9)
    fig.savefig(path, dpi=150, bbox_inches="tight")
    plt.close(fig)


def build_matrix(cap, chosen_ref, common, cell_bracket):
    """Pooled collapsed 5x5 matrix for one cap over the common cell set."""
    _, _, band = scs.cap_source(cap)
    M = np.zeros((5, 5), np.int64)
    for cid in sorted(common):
        bracket = cell_bracket[cid]
        rp = chosen_ref[cid]
        with rasterio.open(scs.cap_path(cap, bracket, cid)) as pds, rasterio.open(rp) as rds:
            pred = pds.read(band)
            rf = rds.read(1)
        M += cc.cell_confusion(rf, pred)                 # applies _REF_COLLAPSE and _MODEL_COLLAPSE
    return M


def fig_overall(res, path):
    """Secondary: collapsed overall OA, macro-F1, and kappa vs cap, with the all-Stable baseline.

    Unlike the 10-class overall figure this one carries the all-Stable baseline, since collapsed OA is
    dominated by the ~98.5% Stable class and sits below that trivial baseline at every cap.
    """
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    fig, ax = plt.subplots(figsize=(7.5, 5))
    for mk, lab, col in [("OA", "overall accuracy", "#444444"),
                         ("macro_F1", "macro-F1 (5 classes)", "#1b9e77"),
                         ("kappa", "kappa", "#7570b3")]:
        ax.plot(CAPS, [res[c][mk] for c in CAPS], marker="o", lw=2.2, color=col, label=lab)
    base = res[CAPS[0]]["baseline_OA"]
    ax.axhline(base, color="firebrick", lw=1.5, ls="--", zorder=1,
               label=f"all-Stable baseline ({base:.3f})")
    ax.set_xticks(CAPS)
    ax.set_xlabel("change-class training cap")
    ax.set_ylabel("value")
    ax.set_ylim(0, 1)
    ax.set_title("SECONDARY: collapsed overall metrics vs cap\n(OA is dominated by Stable and stays "
                 "below the all-Stable baseline; kappa is the honest read)", fontsize=10)
    ax.legend(fontsize=8, frameon=False)
    ax.grid(False)
    for s in ("top", "right"):
        ax.spines[s].set_visible(False)
    fig.tight_layout()
    fig.savefig(path, dpi=150, bbox_inches="tight")
    plt.close(fig)


def write_note(common, res, path):
    lines = [
        "# sensitivity_changecap_5class",
        "",
        "Per-cap confusion matrices for the change-cap sensitivity analysis under the 5-class collapse, "
        "the counterpart to `reports/sensitivity_changecap/` (10-class). Generated by "
        "`scripts/build_changecap_sensitivity_5class.py`, reusing the cell-set logic of "
        "`scripts/build_changecap_sensitivity.py` and the collapse of "
        "`scripts/collapsed_5class_confusion.py`.",
        "",
        "## Collapse",
        "",
        "Scheme: Stable (all no-change classes folded, including Other) plus Harvest, Development, "
        "Insect/Disease, and Beaver. The reference is collapsed from CKIT codes to 1..5 "
        "(Other(13) to Stable, Unknown(10) and Fire(40) dropped), and the cap predictions from the "
        "10-class schema to 1..5. Note this differs slightly from the 10-class reference crosswalk, "
        "which drops Other(13) rather than folding it into Stable, so the collapsed matrices are the "
        "authority for the 5-class view, not a re-aggregation of the 10-class counts.",
        "",
        f"## Common cell set",
        "",
        f"All four caps are scored on the same {len(common)} cells, the common set from the 10-class "
        "sensitivity analysis, so the two views are directly comparable.",
        "",
        "## Per-cap headline (collapsed)",
        "",
        f"{'cap':>5}  {'OA':>7}  {'all-Stable':>10}  {'kappa':>7}  {'beaver UA':>9}  {'beaver PA':>9}",
    ]
    for cap in CAPS:
        r = res[cap]
        lines.append(f"{cap:>5}  {r['OA']:>7.3f}  {r['baseline_OA']:>10.3f}  {r['kappa']:>7.3f}  "
                     f"{r['precision'][5 - 1]:>9.3f}  {r['recall'][5 - 1]:>9.3f}")
    lines += [
        "",
        "OA is dominated by the ~98.5% Stable class, so read the all-Stable baseline and kappa, not OA "
        "alone. Beaver is class 5 in the collapsed scheme.",
        "",
        "## Outputs",
        "",
        "- `cm_cap<cap>_counts.csv`, `_rownorm.csv`, `_colnorm.csv`: pooled 5x5 matrices, reference on "
        "rows (diagonal is producer's accuracy), prediction on columns.",
        "- `cm_cap<cap>.png`: count heatmaps with PA/UA margins and OA/kappa.",
        "- `sensitivity_metrics_long_5class.csv`: one row per (cap, collapsed class) with per-class UA, "
        "PA, F1, IoU, support, and predicted pixels, plus the aggregate OA, all-Stable baseline, "
        "macro-F1, mean IoU, and kappa.",
        "- `overall_metrics_vs_cap.png`: secondary, collapsed OA, macro-F1, and kappa vs cap with the "
        "all-Stable baseline. This differs from the 10-class overall figure: the collapse raises OA "
        "(within-stable error removed) but lowers kappa, so it is a distinct view, not a duplicate.",
        "- `change_classes_pa_vs_cap.png`: producer's accuracy (recall) of each collapsed change class "
        "as a function of the training cap, one line per class.",
        "- `change_classes_predicted_pixels_vs_cap.png`: predicted pixel count of each collapsed "
        "change class as a function of the training cap, one panel per class, with the interpreted "
        "reference count.",
    ]
    with open(path, "w") as fh:
        fh.write("\n".join(lines) + "\n")


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--truth", default="exports/truth_selections.csv",
                    help="adjudicated reviewer per cell (matches the 10-class sensitivity basis)")
    args = ap.parse_args()
    os.makedirs(OUT, exist_ok=True)

    ref_index = bmc.build_reference_index()
    truth = bmc.load_truth(args.truth)
    chosen_ref, n_multi, missing, mismatch = bmc.choose_references_truth(ref_index, truth)
    if mismatch:
        print("STOP: truth reviewer with no matching raster:", mismatch[:10]); raise SystemExit(1)

    common, usable, ref_ok, drops, unmapped = scs.usable_cells(chosen_ref)
    cell_bracket = {}
    for p in glob.glob(os.path.join(scs.SENS_DIR, "**", "sens_*.tif"), recursive=True):
        m = re.search(r"sens_(\d{4}_\d{4})_cell(\d+)\.tif$", os.path.basename(p))
        cell_bracket[bmc.pad(m.group(2))] = m.group(1)
    print(f"common cell set (same as the 10-class analysis): {len(common)}")

    res, long_rows = {}, []
    print(f"\n{'cap':>5}{'OA':>8}{'baseline':>10}{'macF1':>8}{'kappa':>8}   beaver:{'UA':>7}{'PA':>7}{'predpx':>10}")
    for cap in CAPS:
        M = build_matrix(cap, chosen_ref, common, cell_bracket)
        mt = cc.metrics(M)
        total = int(M.sum())
        res[cap] = dict(precision=[mt[f"precision[{c}]"] for c in range(1, 6)],
                        recall=[mt[f"recall[{c}]"] for c in range(1, 6)],
                        pred_count=M.sum(0), support=[int(mt[f"support[{c}]"]) for c in range(1, 6)],
                        OA=mt["OA"], baseline_OA=mt["baseline_OA"], kappa=mt["kappa"],
                        macro_F1=mt["macro_F1"], mean_IoU=mt["mean_IoU"])
        pd.DataFrame(M, index=LABELS5, columns=LABELS5).to_csv(os.path.join(OUT, f"cm_cap{cap}_counts.csv"))
        with np.errstate(invalid="ignore"):
            rn = M / np.where(M.sum(1, keepdims=True) > 0, M.sum(1, keepdims=True), np.nan)
            cn = M / np.where(M.sum(0, keepdims=True) > 0, M.sum(0, keepdims=True), np.nan)
        pd.DataFrame(np.round(rn, 5), index=LABELS5, columns=LABELS5).to_csv(
            os.path.join(OUT, f"cm_cap{cap}_rownorm.csv"))
        pd.DataFrame(np.round(cn, 5), index=LABELS5, columns=LABELS5).to_csv(
            os.path.join(OUT, f"cm_cap{cap}_colnorm.csv"))
        cc.plot_rownorm(M, f"cap{cap}", mt, os.path.join(OUT, f"cm_cap{cap}.png"))
        for k in range(5):
            c = k + 1
            long_rows.append(dict(
                cap=cap, class_code=c, class_name=NAMES5[c],
                precision=_r(mt[f"precision[{c}]"]), recall=_r(mt[f"recall[{c}]"]),
                f1=_r(mt[f"F1[{c}]"]), iou=_r(mt[f"IoU[{c}]"]), support=int(mt[f"support[{c}]"]),
                predicted_pixels=int(M.sum(0)[k]), is_change_class=(c in CHANGE5),
                OA=round(mt["OA"], 5), baseline_OA=round(mt["baseline_OA"], 5),
                macro_F1=round(mt["macro_F1"], 5), mean_IoU=round(mt["mean_IoU"], 5),
                kappa=round(mt["kappa"], 5), n_cells=len(common), total_pixels=total))
        print(f"{cap:>5}{mt['OA']:>8.3f}{mt['baseline_OA']:>10.3f}{mt['macro_F1']:>8.3f}"
              f"{mt['kappa']:>8.3f}   {mt['precision[5]']:>13.3f}{mt['recall[5]']:>7.3f}"
              f"{int(M.sum(0)[4]):>10,}")

    res["n_cells"] = len(common)
    pd.DataFrame(long_rows).to_csv(os.path.join(OUT, "sensitivity_metrics_long_5class.csv"), index=False)
    fig_overall(res, os.path.join(OUT, "overall_metrics_vs_cap.png"))
    fig_change_pa_vs_cap(res, os.path.join(OUT, "change_classes_pa_vs_cap.png"))
    fig_predicted_pixels_vs_cap(res, os.path.join(OUT, "change_classes_predicted_pixels_vs_cap.png"))
    write_note(common, res, os.path.join(OUT, "note.md"))
    print(f"\nwrote {OUT}/ (4 collapsed matrices x 3 csv + png, sensitivity_metrics_long_5class.csv, "
          f"overall_metrics_vs_cap.png, change_classes_pa_vs_cap.png, "
          f"change_classes_predicted_pixels_vs_cap.png, note.md)")


if __name__ == "__main__":
    main()
