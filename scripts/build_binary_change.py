#!/usr/bin/env python3
"""Binary change / no-change census confusion for the embedding variants and spec_all.

A further collapse of the 5-class scheme to two classes: No-change (the collapsed Stable class) and
Change (Harvest, Development, Insect/Disease, and Beaver folded together). For each source the 2x2
census confusion is built over the interpreted cells (adjudicated reference, temporally-matched
per-bracket predictions), with Change as the positive class.

All six sources (v2-v6 and spec_all) are scored on the same common cell set, the cells spec_all
classified (spec_all has 12 entirely-nodata rasters), so the confusion matrices are directly
comparable. The per-cell matrices come from the collapsed 5-class census, which are then folded to
2x2. Design-based CIs use the cell as the primary sampling unit (ratio estimator with FPC for the
ratio-form metrics, cell-level bootstrap for kappa and F1).

Outputs -> reports/binary_change_no_change/
  - cm_<source>_counts.csv                    2x2 counts, reference on rows
  - cm_<source>.png                           count heatmap, PA/UA margins, OA/kappa
  - binary_metrics_long.csv                   per source: overall and per-class metrics with CIs
  - compare_binary_change_metrics.png         Change UA, PA, F1 across sources
  - compare_binary_overall.png                OA, kappa, all-No-change baseline across sources
  - note.md

Requires: rasterio, numpy, pandas, matplotlib
"""

import importlib.util
import os

import numpy as np
import pandas as pd


def _load(name, path):
    spec = importlib.util.spec_from_file_location(name, os.path.join(os.path.dirname(__file__), path))
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


cc = _load("cc", "collapsed_5class_confusion.py")           # 5-class census, ratio_ci, N_FRAME, SEED
sp5 = _load("sp5", "spectral_collapsed_5class.py")           # spec_all census and embedding-on-cells

TRUTH = "exports/truth_selections.csv"
SOURCES = ["v2", "v3", "v4", "v5", "v6", "spec_all"]
N_FRAME = cc.N_FRAME
SEED = cc.SEED
BOOT = cc.BOOT
OUT = "reports/binary_change_no_change"
BIN_LABELS = ["No-change", "Change"]
VPAL = {"v2": "#1f77b4", "v3": "#2ca02c", "v4": "#9467bd", "v5": "#ff7f0e", "v6": "#d62728"}
SPEC_COLOR = "#8c564b"


def src_color(s):
    return SPEC_COLOR if s == "spec_all" else VPAL[s]


def to_binary(cms5):
    """Fold an (n,5,5) collapsed array to (n,2,2): class 1 -> No-change, classes 2..5 -> Change."""
    n = cms5.shape[0]
    b = np.zeros((n, 2, 2), np.int64)
    b[:, 0, 0] = cms5[:, 0, 0]
    b[:, 0, 1] = cms5[:, 0, 1:].sum(1)
    b[:, 1, 0] = cms5[:, 1:, 0].sum(1)
    b[:, 1, 1] = cms5[:, 1:, 1:].sum((1, 2))
    return b


def _kappa(B):
    B = B.astype(float); tot = B.sum()
    oa = np.trace(B) / tot
    pe = (B.sum(1) * B.sum(0)).sum() / (tot * tot)
    return (oa - pe) / (1 - pe) if (1 - pe) else np.nan


def _f1_change(B):
    B = B.astype(float)
    tp, fp, fn = B[1, 1], B[0, 1], B[1, 0]
    p = tp / (tp + fp) if (tp + fp) else np.nan
    r = tp / (tp + fn) if (tp + fn) else np.nan
    return 2 * p * r / (p + r) if (p and r and (p + r)) else np.nan


def _boot_ci(cms, fn, n):
    rng = np.random.default_rng(SEED)
    vals = np.empty(BOOT)
    for b in range(BOOT):
        vals[b] = fn(cms[rng.integers(0, n, n)].sum(0))
    return np.nanpercentile(vals, 2.5), np.nanpercentile(vals, 97.5)


def metrics(cms):
    """Point metrics and CIs for one source's per-cell (n,2,2) array. Change is the positive class."""
    n = cms.shape[0]
    B = cms.sum(0).astype(float)
    tot = B.sum()
    tp, fp, fn, tn = B[1, 1], B[0, 1], B[1, 0], B[0, 0]
    diag = (cms[:, 0, 0] + cms[:, 1, 1]).astype(float)     # correct per cell
    totc = cms.sum((1, 2)).astype(float)
    ref_change = cms[:, 1, :].sum(1).astype(float)
    pred_change = cms[:, :, 1].sum(1).astype(float)
    ref_nc = cms[:, 0, :].sum(1).astype(float)
    pred_nc = cms[:, :, 0].sum(1).astype(float)
    tp_c = cms[:, 1, 1].astype(float)
    tn_c = cms[:, 0, 0].astype(float)

    def rc(y, x):
        r, se, lo, hi = cc.ratio_ci(y, x, n, N_FRAME)
        return r, lo, hi

    out = dict(
        n_cells=n, total_px=int(tot), valid_px=int(tot),
        OA=rc(diag, totc), baseline_OA=ref_nc.sum() / tot,
        change_precision=rc(tp_c, pred_change), change_recall=rc(tp_c, ref_change),
        nochange_precision=rc(tn_c, pred_nc), nochange_recall=rc(tn_c, ref_nc),
        change_support=int(B[1, :].sum()), nochange_support=int(B[0, :].sum()),
        pred_change_px=int(B[:, 1].sum()),
        kappa=(_kappa(B), *_boot_ci(cms, _kappa, n)),
        change_f1=(_f1_change(B), *_boot_ci(cms, _f1_change, n)),
    )
    return B, out


def render_cm(B, mt, source, path):
    """2x2 count heatmap in the PA/UA-margin style: cells coloured by row proportion, PA column with
    support, UA row, OA and kappa in the corner."""
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    B = B.astype(float)
    row = B.sum(1)
    col = B.sum(0)                                          # predicted support for UA
    with np.errstate(invalid="ignore"):
        rn = B / np.where(row[:, None] > 0, row[:, None], np.nan)
    pa = np.array([mt["nochange_recall"][0], mt["change_recall"][0]])
    ua = np.array([mt["nochange_precision"][0], mt["change_precision"][0]])
    sup = np.array([mt["nochange_support"], mt["change_support"]])
    oa, kappa = mt["OA"][0], mt["kappa"][0]
    blues, greens = plt.get_cmap("Blues"), plt.get_cmap("Greens")
    img = np.ones((3, 3, 4))
    for i in range(2):
        for j in range(2):
            img[i, j] = blues(rn[i, j] if np.isfinite(rn[i, j]) else 0.0)
        img[i, 2] = greens(pa[i] if np.isfinite(pa[i]) else 0.0)
    for j in range(2):
        img[2, j] = greens(ua[j] if np.isfinite(ua[j]) else 0.0)
    img[2, 2] = greens(oa if np.isfinite(oa) else 0.0)
    fig, ax = plt.subplots(figsize=(5.2, 4.8))
    ax.imshow(img, aspect="auto")

    def tc(v):
        return "white" if (np.isfinite(v) and v > 0.5) else "black"
    for i in range(2):
        for j in range(2):
            ax.text(j, i, f"{int(B[i, j]):,}", ha="center", va="center", fontsize=9, color=tc(rn[i, j]))
    for i in range(2):
        t = f"{pa[i] * 100:.0f}%" if np.isfinite(pa[i]) else "-"
        ax.text(2, i, f"{t}\nn={int(sup[i]):,}", ha="center", va="center", fontsize=7.5, color=tc(pa[i]))
    for j in range(2):
        t = f"{ua[j] * 100:.0f}%" if np.isfinite(ua[j]) else "-"
        ax.text(j, 2, f"{t}\nn={int(col[j]):,}", ha="center", va="center", fontsize=7.5, color=tc(ua[j]))
    ax.text(2, 2, f"OA {oa * 100:.0f}%\nκ {kappa:.2f}", ha="center", va="center", fontsize=8, color=tc(oa))
    ax.set_xticks(range(3)); ax.set_xticklabels(BIN_LABELS + ["PA"], fontsize=9)
    ax.set_yticks(range(3)); ax.set_yticklabels(BIN_LABELS + ["UA"], fontsize=9)
    ax.xaxis.tick_top(); ax.xaxis.set_label_position("top")
    ax.set_xlabel("model", fontsize=10); ax.set_ylabel("reference", fontsize=10)
    ax.axhline(1.5, color="0.4", lw=1.0); ax.axvline(1.5, color="0.4", lw=1.0)
    ax.set_xticks(np.arange(-0.5, 3, 1), minor=True)
    ax.set_yticks(np.arange(-0.5, 3, 1), minor=True)
    ax.grid(which="minor", color="white", lw=0.8); ax.tick_params(which="minor", length=0)
    ax.set_title(f"{source}  ·  binary change / no-change\ncells = counts; PA = recall, UA = precision, "
                 "Change is the positive class; n = reference support on PA, predicted support on UA",
                 fontsize=9, pad=22)
    fig.savefig(path, dpi=150, bbox_inches="tight")
    plt.close(fig)


def _caption(fig, text, width=118):
    import textwrap
    wrapped = "\n".join(textwrap.wrap(text, width))
    nlines = wrapped.count("\n") + 1
    fig.tight_layout(rect=[0, 0.03 + 0.05 * nlines, 1, 1])
    fig.text(0.5, 0.01, wrapped, ha="center", va="bottom", fontsize=8, color="0.35")


def _style(ax):
    ax.grid(False)
    for s in ("top", "right"):
        ax.spines[s].set_visible(False)


def fig_change_metrics(res, path):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    x = np.arange(len(SOURCES)); w = 0.26
    fig, ax = plt.subplots(figsize=(11, 5))
    for i, (key, lab) in enumerate([("change_precision", "UA (precision)"),
                                    ("change_recall", "PA (recall)"), ("change_f1", "F1")]):
        vals = [res[s][key][0] for s in SOURCES]
        lo = [res[s][key][0] - res[s][key][1] for s in SOURCES]
        hi = [res[s][key][2] - res[s][key][0] for s in SOURCES]
        ax.bar(x + (i - 1) * w, vals, w, yerr=[lo, hi], capsize=3, label=lab, edgecolor="white")
    ax.set_xticks(x); ax.set_xticklabels(SOURCES)
    ax.set_ylabel("Change-class metric"); ax.set_ylim(0, 1)
    ax.set_title("Binary Change-class metrics by source (Change = positive; 95% CIs)")
    ax.legend(fontsize=9, frameon=False)
    _style(ax)
    _caption(fig, "User's accuracy (precision), producer's accuracy (recall), and F1 of the Change "
                  "class for each classifier under the binary change / no-change collapse, pooled over "
                  f"the common {res[SOURCES[0]]['n_cells']} cells with 95 percent design-based CIs. "
                  "Change precision is near zero for every source: the classifiers flag far more change "
                  "than the interpreters mapped, so most predicted-change pixels are false. Recall is "
                  "higher but is inflated by that same over-prediction, so F1 stays low throughout.")
    fig.savefig(path, dpi=150, bbox_inches="tight")
    plt.close(fig)


def fig_overall(res, path):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    x = np.arange(len(SOURCES)); w = 0.38
    fig, ax = plt.subplots(figsize=(10, 5))
    oa = [res[s]["OA"][0] for s in SOURCES]
    oa_lo = [res[s]["OA"][0] - res[s]["OA"][1] for s in SOURCES]
    oa_hi = [res[s]["OA"][2] - res[s]["OA"][0] for s in SOURCES]
    ka = [res[s]["kappa"][0] for s in SOURCES]
    ax.bar(x - w / 2, oa, w, yerr=[oa_lo, oa_hi], capsize=3, label="OA", color="#4d4d4d", edgecolor="white")
    ax.bar(x + w / 2, ka, w, label="kappa", color="#7570b3", edgecolor="white")
    base = res[SOURCES[0]]["baseline_OA"]
    ax.axhline(base, ls="--", color="firebrick", lw=1.5, label=f"all-No-change baseline ({base:.3f})")
    ax.set_xticks(x); ax.set_xticklabels(SOURCES)
    ax.set_ylabel("value"); ax.set_ylim(0, 1)
    ax.set_title("Binary change / no-change: overall accuracy and kappa by source")
    ax.legend(fontsize=9, frameon=False)
    _style(ax)
    _caption(fig, "Overall accuracy and Cohen's kappa for each classifier under the binary change / "
                  f"no-change collapse, pooled over the common {res[SOURCES[0]]['n_cells']} cells. OA "
                  "is dominated by the ~98.5% No-change class and sits below the all-No-change baseline "
                  "(dashed) for every source, so labeling everything No-change beats every classifier. "
                  "Kappa, the agreement beyond chance, stays near zero, confirming little genuine "
                  "change-detection skill even at the binary level.")
    fig.savefig(path, dpi=150, bbox_inches="tight")
    plt.close(fig)


def write_note(res, n_cells, path):
    lines = [
        "# binary_change_no_change",
        "",
        "Binary change / no-change census confusion for the embedding variants (v2-v6) and spec_all. A "
        "further collapse of the 5-class scheme: No-change is the collapsed Stable class, and Change "
        "folds Harvest, Development, Insect/Disease, and Beaver. Change is the positive class. "
        "Generated by `scripts/build_binary_change.py`.",
        "",
        "## Basis",
        "",
        f"Reference: the adjudicated interpreted cell per location. Predictions: temporally-matched "
        f"per-bracket maps (spec_all from the spectral export, v2-v6 from the embedding export). All "
        f"six sources are scored on the same common {n_cells} cells, the cells spec_all classified "
        "(spec_all has 12 entirely-nodata rasters), so the confusion matrices are directly comparable. "
        "The reference collapse folds Other into Stable rather than dropping it, matching the other "
        "5-class runs.",
        "",
        "## Inference",
        "",
        "Design-based with the cell as the primary sampling unit: ratio-estimator CIs (FPC "
        f"sqrt(1 - n/N), N={N_FRAME:,}) for OA and the per-class recall and precision, and a cell-level "
        f"bootstrap (seed {SEED}, {BOOT} replicates) for kappa and F1.",
        "",
        "## Headline",
        "",
        f"{'source':9}{'OA':>8}{'baseline':>10}{'kappa':>8}{'Change UA':>11}{'Change PA':>11}{'Change F1':>11}",
    ]
    for s in SOURCES:
        r = res[s]
        lines.append(f"{s:9}{r['OA'][0]:>8.3f}{r['baseline_OA']:>10.3f}{r['kappa'][0]:>8.3f}"
                     f"{r['change_precision'][0]:>11.3f}{r['change_recall'][0]:>11.3f}"
                     f"{r['change_f1'][0]:>11.3f}")
    lines += [
        "",
        "OA is dominated by the ~98.5% No-change class and sits below the all-No-change baseline for "
        "every source, so read kappa and the Change-class UA/PA, not OA. Change precision (UA) is near "
        "zero everywhere: the classifiers over-map change, so most predicted-change pixels are false.",
        "",
        "## Outputs",
        "",
        "- `cm_<source>_counts.csv` and `cm_<source>.png`: 2x2 confusion, reference on rows, with PA/UA "
        "margins and OA/kappa.",
        "- `binary_metrics_long.csv`: per source, the overall metrics and the per-class (No-change, "
        "Change) precision and recall, with 95% CIs.",
        "- `compare_binary_change_metrics.png`, `compare_binary_overall.png`: cross-source comparisons.",
    ]
    with open(path, "w") as fh:
        fh.write("\n".join(lines) + "\n")


def main():
    os.makedirs(OUT, exist_ok=True)
    cells, mismatch = cc.select_by_truth(TRUTH)
    if mismatch:
        print("STOP: truth reviewer with no matching raster:", mismatch); raise SystemExit(1)
    cms_spec5, skipped, scored = sp5.build_census(cells, TRUTH)
    n = len(scored)
    print(f"common cell set (spec_all non-blank): {n}")

    per_cell = {"spec_all": to_binary(cms_spec5)}
    for v in ["v2", "v3", "v4", "v5", "v6"]:
        per_cell[v] = to_binary(sp5.build_embedding_census(scored, v))

    res, long_rows = {}, []
    print(f"\n{'source':9}{'OA':>8}{'baseline':>10}{'kappa':>8}{'ChgUA':>8}{'ChgPA':>8}{'ChgF1':>8}")
    for s in SOURCES:
        B, mt = metrics(per_cell[s])
        res[s] = mt
        pd.DataFrame(B.astype(int), index=BIN_LABELS, columns=BIN_LABELS).to_csv(
            os.path.join(OUT, f"cm_{s}_counts.csv"))
        render_cm(B, mt, s, os.path.join(OUT, f"cm_{s}.png"))
        # long rows
        long_rows.append(dict(source=s, scope="overall", cls="", metric="OA", estimate=round(mt["OA"][0], 5),
                              ci_lo=round(mt["OA"][1], 5), ci_hi=round(mt["OA"][2], 5), support=mt["valid_px"]))
        long_rows.append(dict(source=s, scope="overall", cls="", metric="baseline_OA",
                              estimate=round(mt["baseline_OA"], 5), ci_lo="", ci_hi="", support=mt["valid_px"]))
        long_rows.append(dict(source=s, scope="overall", cls="", metric="kappa", estimate=round(mt["kappa"][0], 5),
                              ci_lo=round(mt["kappa"][1], 5), ci_hi=round(mt["kappa"][2], 5), support=mt["valid_px"]))
        for cls, pk, rk, sk in [("No-change", "nochange_precision", "nochange_recall", "nochange_support"),
                                ("Change", "change_precision", "change_recall", "change_support")]:
            long_rows.append(dict(source=s, scope="class", cls=cls, metric="precision",
                                  estimate=round(mt[pk][0], 5), ci_lo=round(mt[pk][1], 5),
                                  ci_hi=round(mt[pk][2], 5), support=mt[sk]))
            long_rows.append(dict(source=s, scope="class", cls=cls, metric="recall",
                                  estimate=round(mt[rk][0], 5), ci_lo=round(mt[rk][1], 5),
                                  ci_hi=round(mt[rk][2], 5), support=mt[sk]))
            if cls == "Change":
                long_rows.append(dict(source=s, scope="class", cls=cls, metric="f1",
                                      estimate=round(mt["change_f1"][0], 5), ci_lo=round(mt["change_f1"][1], 5),
                                      ci_hi=round(mt["change_f1"][2], 5), support=mt[sk]))
        print(f"{s:9}{mt['OA'][0]:>8.3f}{mt['baseline_OA']:>10.3f}{mt['kappa'][0]:>8.3f}"
              f"{mt['change_precision'][0]:>8.3f}{mt['change_recall'][0]:>8.3f}{mt['change_f1'][0]:>8.3f}")

    pd.DataFrame(long_rows).to_csv(os.path.join(OUT, "binary_metrics_long.csv"), index=False)
    fig_change_metrics(res, os.path.join(OUT, "compare_binary_change_metrics.png"))
    fig_overall(res, os.path.join(OUT, "compare_binary_overall.png"))
    write_note(res, n, os.path.join(OUT, "note.md"))
    print(f"\nwrote {OUT}/ (6 matrices, binary_metrics_long.csv, 2 comparison figures, note.md)")


if __name__ == "__main__":
    main()
