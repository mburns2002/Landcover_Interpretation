#!/usr/bin/env python3
"""Per-class inter-interpreter agreement with bootstrap confidence intervals.

For the double-interpreted cells (same location, two reviewers), pooled OA/kappa hide
the per-class picture. This reports, for each land cover class, the inter-interpreter
agreement F1 (= the balanced probability the two interpreters concur given one assigned
the class) and IoU, each with a 95% CI, plus a reliability tier.

Because pixels within a cell are spatially autocorrelated, the resampling unit is the
PAIR, not the pixel: a cluster (pair) bootstrap resamples the N pairs with replacement,
re-pools their confusion matrices, and recomputes each metric. This yields honest CIs
and flags the classes where the human reference itself is unreliable (e.g. Grass/Shrub,
Wetland) — evaluating any model against a single interpretation of those classes is
limited by that reference noise.

Outputs (reports/interpreter_agreement/):
  - per_class_agreement_ci.csv     machine-readable (point estimate + CI bounds)
  - per_class_agreement_table.md   manuscript markdown table
  - per_class_agreement_table.tex  manuscript LaTeX (booktabs)
  - per_class_agreement_forest.png forest plot of per-class F1 with CIs

Usage:
    python scripts/interpreter_class_ci.py
    python scripts/interpreter_class_ci.py --boot 5000 --seed 1

Requires: rasterio, numpy, pandas, matplotlib
"""

import argparse
import os
import sys

import numpy as np
import pandas as pd
import rasterio

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import compare_interpreters as CI  # reuse find_pairs / load_legend / confusion

OUT = "reports/interpreter_agreement"
HIGH, MOD = 0.70, 0.50  # reliability tier thresholds on F1


def per_class(cm):
    """Return (f1, iou) arrays over classes from a confusion matrix (rows=A, cols=B)."""
    tp = np.diag(cm).astype(float)
    row = cm.sum(1).astype(float)
    col = cm.sum(0).astype(float)
    with np.errstate(divide="ignore", invalid="ignore"):
        f1 = np.where((row + col) > 0, 2 * tp / (row + col), np.nan)
        iou = np.where((row + col - tp) > 0, tp / (row + col - tp), np.nan)
    return f1, iou


def overall(cm):
    tp = np.diag(cm).astype(float)
    row = cm.sum(1).astype(float)
    col = cm.sum(0).astype(float)
    tot = cm.sum()
    oa = tp.sum() / tot if tot else np.nan
    pe = (row * col).sum() / (tot * tot) if tot else np.nan
    kappa = (oa - pe) / (1 - pe) if tot and (1 - pe) else np.nan
    f1, iou = per_class(cm)
    pres = (row + col) > 0
    return dict(oa=oa, kappa=kappa,
                macro_f1=np.nanmean(f1[pres]) if pres.any() else np.nan,
                mean_iou=np.nanmean(iou[pres]) if pres.any() else np.nan)


def ci(samples):
    s = samples[~np.isnan(samples)]
    if s.size == 0:
        return (np.nan, np.nan)
    return (float(np.percentile(s, 2.5)), float(np.percentile(s, 97.5)))


def tier(f1):
    if np.isnan(f1):
        return "n/a"
    return "High" if f1 >= HIGH else ("Moderate" if f1 >= MOD else "Low")


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--boot", type=int, default=2000, help="bootstrap replicates (default: 2000)")
    ap.add_argument("--seed", type=int, default=0)
    args = ap.parse_args()

    codes, names, colors = CI.load_legend()
    order = sorted(codes)
    pairs = CI.find_pairs()
    print(f"double-interpreted pairs: {len(pairs)}   classes: {len(order)}   boot: {args.boot}")

    # per-pair confusion matrices
    cms = []
    for (gid, samp, tgt), revs in sorted(pairs.items()):
        (revA, fA), (revB, fB) = revs[0], revs[1]
        with rasterio.open(fA) as s:
            a = s.read(1)
        with rasterio.open(fB) as s:
            b = s.read(1)
        if a.shape != b.shape:
            continue
        cm, _ = CI.confusion(a, b, order)
        cms.append(cm)
    stack = np.stack(cms)                     # (n_pairs, C, C)
    n = stack.shape[0]
    pooled = stack.sum(0)

    # point estimates
    f1_pt, iou_pt = per_class(pooled)
    support = (pooled.sum(0) + pooled.sum(1) - np.diag(pooled))     # union pixels per class
    n_pairs_cls = np.array([int(((stack[:, k, :].sum(1) + stack[:, :, k].sum(1)) > 0).sum())
                            for k in range(len(order))])            # pairs where class occurs
    ov_pt = overall(pooled)

    # cluster (pair) bootstrap
    rng = np.random.default_rng(args.seed)
    B = args.boot
    bf1 = np.full((B, len(order)), np.nan)
    biou = np.full((B, len(order)), np.nan)
    boa = np.full(B, np.nan); bk = np.full(B, np.nan)
    bmf1 = np.full(B, np.nan); bmiou = np.full(B, np.nan)
    for b in range(B):
        idx = rng.integers(0, n, n)
        cmb = stack[idx].sum(0)
        bf1[b], biou[b] = per_class(cmb)
        o = overall(cmb)
        boa[b], bk[b], bmf1[b], bmiou[b] = o["oa"], o["kappa"], o["macro_f1"], o["mean_iou"]

    # assemble per-class table (skip classes with no pixels at all, e.g. Fire)
    rows = []
    for k, c in enumerate(order):
        if support[k] == 0:
            continue
        f1lo, f1hi = ci(bf1[:, k])
        iolo, iohi = ci(biou[:, k])
        rows.append(dict(
            code=c, cls=names[c], n_pairs=int(n_pairs_cls[k]), support_px=int(support[k]),
            f1=round(float(f1_pt[k]), 3), f1_lo=round(f1lo, 3), f1_hi=round(f1hi, 3),
            iou=round(float(iou_pt[k]), 3), iou_lo=round(iolo, 3), iou_hi=round(iohi, 3),
            reliability=tier(f1_pt[k])))
    df = pd.DataFrame(rows).sort_values("f1", ascending=False).reset_index(drop=True)

    os.makedirs(OUT, exist_ok=True)
    df.to_csv(os.path.join(OUT, "per_class_agreement_ci.csv"), index=False)

    # overall summary (with CIs)
    summary = dict(
        overall_agreement=(round(ov_pt["oa"], 3), *[round(x, 3) for x in ci(boa)]),
        cohen_kappa=(round(ov_pt["kappa"], 3), *[round(x, 3) for x in ci(bk)]),
        macro_f1=(round(ov_pt["macro_f1"], 3), *[round(x, 3) for x in ci(bmf1)]),
        mean_iou=(round(ov_pt["mean_iou"], 3), *[round(x, 3) for x in ci(bmiou)]),
    )

    write_markdown(df, summary, n, B, os.path.join(OUT, "per_class_agreement_table.md"))
    write_latex(df, summary, n, B, os.path.join(OUT, "per_class_agreement_table.tex"))
    forest_plot(df, os.path.join(OUT, "per_class_agreement_forest.png"))

    print("\n" + "=" * 66)
    print(df.to_string(index=False))
    print("\noverall (point [95% CI]):")
    for k, (pt, lo, hi) in summary.items():
        print(f"  {k:18} {pt:.3f} [{lo:.3f}, {hi:.3f}]")
    print(f"\nreference-unreliable classes (F1 < {MOD}): "
          f"{', '.join(df[df.f1 < MOD].cls) or 'none'}")
    print(f"\noutputs -> {OUT}/")


def _fmt(pt, lo, hi):
    return f"{pt:.2f} ({lo:.2f}–{hi:.2f})"


def write_markdown(df, summary, n, B, path):
    lines = [
        f"# Inter-interpreter per-class agreement (n = {n} double-interpreted cells)",
        "",
        f"Point estimates with 95% cluster (pair) bootstrap CIs ({B} replicates). F1 is the",
        "balanced probability the two interpreters concur given one assigned the class.",
        "",
        "| Class | Pairs | Support (px) | F1 (95% CI) | IoU (95% CI) | Reliability |",
        "|-------|------:|-------------:|-------------|--------------|-------------|",
    ]
    for r in df.itertuples():
        lines.append(f"| {r.cls} | {r.n_pairs} | {r.support_px:,} | "
                     f"{_fmt(r.f1, r.f1_lo, r.f1_hi)} | {_fmt(r.iou, r.iou_lo, r.iou_hi)} | {r.reliability} |")
    lines += ["", "**Overall** (95% CI):", ""]
    label = {"overall_agreement": "Overall agreement", "cohen_kappa": "Cohen's κ",
             "macro_f1": "Macro F1", "mean_iou": "Mean IoU"}
    for k, (pt, lo, hi) in summary.items():
        lines.append(f"- {label[k]}: {_fmt(pt, lo, hi)}")
    lines += ["",
              "Reliability tiers on F1: High ≥ 0.70, Moderate 0.50–0.70, Low < 0.50. "
              "Low/Moderate classes (e.g. Grass/Shrub, Wetland) indicate the human reference "
              "is itself unreliable there, so model scores on those classes are bounded by "
              "reference noise, not only model error.", ""]
    with open(path, "w") as fh:
        fh.write("\n".join(lines))


def write_latex(df, summary, n, B, path):
    L = [
        "% Inter-interpreter per-class agreement. Requires \\usepackage{booktabs}.",
        "\\begin{table}[t]", "\\centering",
        f"\\caption{{Inter-interpreter per-class agreement across the {n} double-interpreted "
        f"cells. Values are point estimates with 95\\% cluster (pair) bootstrap confidence "
        f"intervals ({B} replicates). F1 is the balanced probability that the two interpreters "
        f"concur given one assigned the class; low values indicate an unreliable reference.}}",
        "\\label{tab:interpreter_agreement}",
        "\\begin{tabular}{lrrccl}", "\\toprule",
        "Class & Pairs & Support (px) & F1 (95\\% CI) & IoU (95\\% CI) & Reliability \\\\",
        "\\midrule",
    ]
    for r in df.itertuples():
        L.append(f"{r.cls} & {r.n_pairs} & {r.support_px:,} & "
                 f"{r.f1:.2f} ({r.f1_lo:.2f}--{r.f1_hi:.2f}) & "
                 f"{r.iou:.2f} ({r.iou_lo:.2f}--{r.iou_hi:.2f}) & {r.reliability} \\\\")
    L += ["\\midrule"]
    oa = summary["overall_agreement"]; kp = summary["cohen_kappa"]; mf = summary["macro_f1"]
    L.append(f"\\multicolumn{{6}}{{l}}{{Overall agreement {oa[0]:.2f} "
             f"({oa[1]:.2f}--{oa[2]:.2f}); Cohen's $\\kappa$ {kp[0]:.2f} "
             f"({kp[1]:.2f}--{kp[2]:.2f}); macro-F1 {mf[0]:.2f} ({mf[1]:.2f}--{mf[2]:.2f})}} \\\\")
    L += ["\\bottomrule", "\\end{tabular}", "\\end{table}", ""]
    with open(path, "w") as fh:
        fh.write("\n".join(L))


def _caption(fig, text, top=1.0, width=125):
    import textwrap
    wrapped = "\n".join(textwrap.wrap(text, width))
    nlines = wrapped.count("\n") + 1
    fig.tight_layout(rect=[0, 0.02 + 0.035 * nlines, 1, top])
    fig.text(0.5, 0.01, wrapped, ha="center", va="bottom", fontsize=8, color="0.35")


def forest_plot(df, path):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    d = df.iloc[::-1]  # lowest F1 at bottom-up -> plot ascending
    color = {"High": "#2ca02c", "Moderate": "#ff7f0e", "Low": "#d62728", "n/a": "gray"}
    y = np.arange(len(d))
    fig, ax = plt.subplots(figsize=(8, 0.45 * len(d) + 1.5))
    for i, r in enumerate(d.itertuples()):
        ax.plot([r.f1_lo, r.f1_hi], [i, i], color=color[r.reliability], lw=2, zorder=1)
        ax.scatter(r.f1, i, color=color[r.reliability], s=45, zorder=2)
    ax.set_yticks(y); ax.set_yticklabels([f"{r.cls} (n={r.n_pairs})" for r in d.itertuples()])
    ax.axvline(HIGH, ls="--", lw=0.8, color="gray"); ax.axvline(MOD, ls="--", lw=0.8, color="gray")
    ax.set_xlabel("inter-interpreter F1 (95% CI)")
    ax.set_xlim(0, 1)
    ax.set_title("Per-class inter-interpreter agreement\n(dashed: Low/Moderate/High thresholds)")
    from matplotlib.patches import Patch
    ax.legend(handles=[Patch(color=color[t], label=t) for t in ["High", "Moderate", "Low"]],
              loc="lower right", fontsize=8)
    _caption(fig, "Forest plot of per-class inter-interpreter agreement F1 for each land-cover "
                  "class, where each dot is the pooled point estimate and its horizontal bar is "
                  "the 95% cluster (pair) bootstrap confidence interval. F1 is the balanced "
                  "probability that the two interpreters concur given one assigned the class, and "
                  "the dashed vertical lines mark the Low, Moderate, and High reliability "
                  "thresholds at 0.50 and 0.70. Dots colored orange or red identify classes such "
                  "as Grass/Shrub and Wetland where the human reference itself is unreliable.")
    fig.savefig(path, dpi=150, bbox_inches="tight")
    plt.close(fig)


if __name__ == "__main__":
    main()
