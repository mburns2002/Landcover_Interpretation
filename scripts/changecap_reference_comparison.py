#!/usr/bin/env python3
"""Two comparison plots for the change-cap sensitivity, both in the 5-class collapsed scheme.

Plot 2 (mapped area): predicted change-class area as a function of the training cap, with spec_all and
the interpreted reference area drawn as reference lines, so over-mapping and under-mapping are visible
directly.

Plot 3 (human benchmark): change-class PA (recall) as a function of the training cap, with spec_all
and the inter-reviewer agreement (F1, with its bootstrap CI) drawn as reference lines, so model recall
can be read against how well the human interpreters agree with each other on that class.

Everything is pooled on the common cell set, the cells spec_all classified (spec_all has 12 entirely
nodata rasters), so the cap sweep and spec_all are compared on identical cells. The inter-reviewer
agreement is a separate, fixed benchmark from the 72 double-interpreted cells.

Outputs -> reports/sensitivity_changecap_5class/
  - change_classes_area_vs_cap.png
  - change_classes_pa_vs_human_benchmark.png

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


scs = _load("scs", "build_changecap_sensitivity.py")     # cap paths, cap_source
cc = _load("cc", "collapsed_5class_confusion.py")         # collapse, metrics, cell_confusion
sp5 = _load("sp5", "spectral_collapsed_5class.py")        # spec_all census on its non-blank cells

CAPS = scs.CAPS
NAMES5 = cc.NAMES5
CHANGE5 = [2, 3, 4, 5]                                    # harvest, development, insect_disease, beaver
CHANGE5_TO_CKIT = {2: 20, 3: 30, 4: 50, 5: 62}           # collapsed class -> ckit code in the agreement table
TRUTH = "exports/truth_selections.csv"
AGREE_CSV = "reports/interpreter_agreement/per_class_agreement_ci.csv"
OUT = "reports/sensitivity_changecap_5class"

CAP_COLOR = "#1f77b4"        # v2 embedding cap sweep (v2 blue)
SPEC_COLOR = "#8c564b"       # spec_all (brown, as in the spectral area figure)
REF_COLOR = "black"          # interpreted reference
HUMAN_COLOR = "#555555"      # inter-reviewer agreement benchmark


def _caption(fig, text, width=115):
    import textwrap
    wrapped = "\n".join(textwrap.wrap(text, width))
    nlines = wrapped.count("\n") + 1
    fig.tight_layout(rect=[0, 0.02 + 0.05 * nlines, 1, 1])
    fig.text(0.5, 0.01, wrapped, ha="center", va="bottom", fontsize=8, color="0.35")


def _style(ax):
    ax.grid(False)
    for s in ("top", "right"):
        ax.spines[s].set_visible(False)


def cap_matrix_on_cells(cap, scored):
    """Collapsed 5x5 matrix for one cap over the given (cell, gid, bracket) list."""
    _, _, band = scs.cap_source(cap)
    M = np.zeros((5, 5), np.int64)
    for cell, gid, bracket in scored:
        with rasterio.open(scs.cap_path(cap, bracket, gid)) as pds, rasterio.open(cell) as rds:
            pred = pds.read(band)
            rf = rds.read(1)
        M += cc.cell_confusion(rf, pred)
    return M


def main():
    os.makedirs(OUT, exist_ok=True)

    # spec_all census on its non-blank cells; scored is the common cell set
    cells, mismatch = cc.select_by_truth(TRUTH)
    if mismatch:
        print("STOP: truth reviewer with no matching raster:", mismatch); raise SystemExit(1)
    cms_spec, skipped, scored = sp5.build_census(cells, TRUTH)
    spec_M = cms_spec.sum(0)
    n = len(scored)
    print(f"common cell set (spec_all non-blank): {n}")

    # cap matrices on the same cells
    cap_M = {cap: cap_matrix_on_cells(cap, scored) for cap in CAPS}

    # reference prevalence per class, directly from the reference on the common cells
    ref_counts = np.zeros(6, np.int64)
    for cell, gid, bracket in scored:
        with rasterio.open(cell) as rds:
            ref = cc._REF_COLLAPSE[np.where((rds.read(1) >= 0) & (rds.read(1) <= 62), rds.read(1), 0)]
        for c in range(1, 6):
            ref_counts[c] += int((ref == c).sum())
    ref_total = int(ref_counts[1:].sum())
    ref_prev = {c: ref_counts[c] / ref_total for c in range(1, 6)}

    # inter-reviewer agreement (F1 with CI) per change class
    ag = pd.read_csv(AGREE_CSV).set_index("code")
    human = {c: (float(ag.loc[k, "f1"]), float(ag.loc[k, "f1_lo"]), float(ag.loc[k, "f1_hi"]))
             for c, k in CHANGE5_TO_CKIT.items()}

    _plot_area(cap_M, spec_M, ref_prev, n)
    _plot_pa_human(cap_M, spec_M, human, n)
    print(f"wrote {OUT}/change_classes_area_vs_cap.png and change_classes_pa_vs_human_benchmark.png")


def _plot_area(cap_M, spec_M, ref_prev, n):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    spec_total = spec_M.sum()
    fig, axes = plt.subplots(1, 4, figsize=(17, 4.6))
    for ax, c in zip(axes, CHANGE5):
        k = c - 1
        cap_frac = [cap_M[cap].sum(0)[k] / cap_M[cap].sum() * 100 for cap in CAPS]
        spec_frac = spec_M.sum(0)[k] / spec_total * 100
        ax.plot(CAPS, cap_frac, "o-", lw=2.3, color=CAP_COLOR, label="v2 cap sweep", zorder=3)
        ax.axhline(spec_frac, ls="--", lw=1.8, color=SPEC_COLOR, label=f"spec_all ({spec_frac:.2f}%)")
        ax.axhline(ref_prev[c] * 100, ls="--", lw=1.8, color=REF_COLOR,
                   label=f"interpreted ({ref_prev[c] * 100:.2f}%)")
        ax.set_xticks(CAPS)
        ax.set_xlabel("training cap")
        ax.set_title(NAMES5[c], fontsize=10)
        ax.set_ylim(0, max(max(cap_frac), spec_frac, ref_prev[c] * 100) * 1.2)
        ax.legend(fontsize=7, frameon=False)
        _style(ax)
    axes[0].set_ylabel("percent of pooled pixels predicted as class")
    fig.suptitle(f"predicted change-class area vs training cap, with spec_all and the interpreted "
                 f"reference (pooled, {n} common cells)", fontsize=11)
    _caption(fig, "Share of pooled pixels each map assigns to the change class, as a function of the "
                  "v2 training cap (blue), with spec_all (brown) and the interpreted reference (black) "
                  "as horizontal lines. A curve or line above the interpreted reference is "
                  "over-mapping (commission), below is under-mapping (omission). Every classifier "
                  "over-maps all four change classes by one to two orders of magnitude relative to "
                  "what the interpreters actually mapped, and a lower cap reduces the v2 over-mapping "
                  "without reaching the interpreted level.")
    fig.savefig(os.path.join(OUT, "change_classes_area_vs_cap.png"), dpi=150, bbox_inches="tight")
    plt.close(fig)


def _plot_pa_human(cap_M, spec_M, human, n):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    fig, axes = plt.subplots(1, 4, figsize=(17, 4.6), sharey=True)
    for ax, c in zip(axes, CHANGE5):
        k = c - 1
        cap_pa = [cc.metrics(cap_M[cap])[f"recall[{c}]"] for cap in CAPS]
        spec_pa = cc.metrics(spec_M)[f"recall[{c}]"]
        f1, lo, hi = human[c]
        ax.plot(CAPS, cap_pa, "o-", lw=2.3, color=CAP_COLOR, label="v2 cap sweep PA", zorder=3)
        ax.axhline(spec_pa, ls="--", lw=1.8, color=SPEC_COLOR, label=f"spec_all PA ({spec_pa:.2f})")
        ax.axhline(f1, ls="-", lw=1.8, color=HUMAN_COLOR, label=f"human agreement F1 ({f1:.2f})")
        ax.fill_between(CAPS, lo, hi, color=HUMAN_COLOR, alpha=0.12, zorder=1)
        ax.set_xticks(CAPS)
        ax.set_xlabel("training cap")
        ax.set_title(NAMES5[c], fontsize=10)
        ax.set_ylim(0, 1)
        ax.legend(fontsize=7, frameon=False)
        _style(ax)
    axes[0].set_ylabel("producer's accuracy (recall / PA)")
    fig.suptitle(f"change-class recall vs training cap, with spec_all and inter-reviewer agreement "
                 f"(pooled, {n} common cells; agreement from 72 double-interpreted cells)", fontsize=11)
    _caption(fig, "Model recall (PA) of each change class versus the v2 training cap (blue), with "
                  "spec_all (brown) and the inter-reviewer agreement F1 with its 95 percent bootstrap "
                  "CI (grey) as reference lines. The human agreement is low for development, insect, "
                  "and especially beaver (F1 ~0.08), so the interpreted reference is itself unreliable "
                  "there and model recall on those classes is bounded by reference noise. Model recall "
                  "that sits above the human line is not genuine skill: the change-class user's "
                  "accuracy stays near zero, so the model reaches these recall values by over-mapping "
                  "the class, not by separating it cleanly.")
    fig.savefig(os.path.join(OUT, "change_classes_pa_vs_human_benchmark.png"), dpi=150, bbox_inches="tight")
    plt.close(fig)


if __name__ == "__main__":
    main()
