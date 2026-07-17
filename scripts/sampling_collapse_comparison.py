#!/usr/bin/env python3
"""Compare the 10-class and 5-class-collapse sampling runs side by side.

Reads reports/Case_ABCD_sampling/ (10-class) and reports/Case_ABCD_sampling_5class/ (Stable +
Harvest/Development/Insect-Disease/Beaver). The question: does collapsing the stable classes
improve convergence for the CHANGE classes? It should — each change stratum now gets n/5 instead
of n/10 (roughly double the allocation).

NOTE: macro-F1 changes meaning between schemes (it averages over 5 classes here, 10 there), so
the two are NOT comparable as levels — only as convergence behaviour (bias -> 0, SD shrinking).

Outputs (reports/Case_ABCD_sampling_5class/):
  - collapse_vs_10class.csv        side-by-side per variant x (n,W): OA/macro-F1 bias&SD,
                                   design effect, and change-class stratification efficiency
  - change_convergence.png         change-class stratified SD vs n, 5-class vs 10-class
  - collapse_summary.png           OA & macro-F1 SD, design effect: 5-class vs 10-class

Requires: pandas, numpy, matplotlib
"""

import os

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

D10 = "reports/Case_ABCD_sampling"
D5 = "reports/Case_ABCD_sampling_5class"
CHANGE = ["Harvest", "Development", "Insect/Disease", "Beaver"]
VERS = ["v2", "v3", "v4", "v5", "v6"]
VPAL = {"v2": "#1f77b4", "v3": "#2ca02c", "v4": "#9467bd", "v5": "#ff7f0e", "v6": "#d62728"}
LABELED_N = (20, 100, 500, 2000, 5000)


def _classic(ax):
    ax.grid(False)
    for s in ("top", "right"):
        ax.spines[s].set_visible(False)


def _nticks(ax, nv):
    nv = sorted(nv)
    ax.set_xticks(nv); ax.set_xticklabels([str(n) if n in LABELED_N else "" for n in nv])
    ax.minorticks_off()


def main():
    m10 = pd.read_csv(os.path.join(D10, "metrics_by_n.csv"))
    m5 = pd.read_csv(os.path.join(D5, "metrics_by_n.csv"))
    de10 = pd.read_csv(os.path.join(D10, "design_effect.csv"))
    de5 = pd.read_csv(os.path.join(D5, "design_effect.csv"))
    ef10 = pd.read_csv(os.path.join(D10, "strat_efficiency.csv"))
    ef5 = pd.read_csv(os.path.join(D5, "strat_efficiency.csv"))
    n_values = sorted(m5.n.unique())

    # ---- side-by-side table (simple design for OA/macro-F1 SD; both designs' bias) ----
    rows = []
    for v in VERS:
        for W in sorted(m5.W.unique()):
            for n in n_values:
                rec = dict(version=v, W=W, n=n)
                for scheme, md in [("10", m10), ("5", m5)]:
                    a = md[(md.design == "simple") & (md.metric == "A_oa") &
                           (md.version == v) & (md.W == W) & (md.n == n)]
                    mf = md[(md.design == "simple") & (md.metric == "A_macrof1") &
                            (md.version == v) & (md.W == W) & (md.n == n)]
                    if len(a):
                        rec[f"oa_sd_{scheme}"] = float(a.sd.iloc[0]); rec[f"oa_bias_{scheme}"] = float(a.bias.iloc[0])
                    if len(mf):
                        rec[f"mf1_sd_{scheme}"] = float(mf.sd.iloc[0]); rec[f"mf1_bias_{scheme}"] = float(mf.bias.iloc[0])
                for scheme, de in [("10", de10), ("5", de5)]:
                    d = de[(de.version == v) & (de.W == W) & (de.n == n)]
                    if len(d):
                        rec[f"deff_{scheme}"] = float(d.design_effect.iloc[0])
                rows.append(rec)
    tab = pd.DataFrame(rows)
    tab.to_csv(os.path.join(D5, "collapse_vs_10class.csv"), index=False)

    # ---- change-class convergence: stratified SD of per-class F1, 5-class vs 10-class ----
    fig, axes = plt.subplots(1, len(CHANGE), figsize=(3.4 * len(CHANGE), 4), sharey=True)
    axes = np.atleast_1d(axes)
    for ax, cls in zip(axes, CHANGE):
        for scheme, ef, ls in [("10-class", ef10, "--"), ("5-class", ef5, "-")]:
            s = ef[(ef.version == "v2") & (ef.W == 1) & (ef.cls == cls)].sort_values("n")
            ax.plot(s.n, s.sd_strat, ls, marker="o", ms=4, color="#1f77b4" if scheme == "5-class" else "#d62728",
                    label=scheme)
        ax.set_xlabel("n (windows)"); ax.set_title(cls, fontsize=10)
        try:
            ax.set_xscale("log"); ax.set_yscale("log")
        except ValueError:
            pass
        _nticks(ax, n_values)
        if ax is axes[0]:
            ax.set_ylabel("stratified SD of per-class F1 (v2, W=1)")
        ax.legend(fontsize=8, frameon=False); _classic(ax)
    fig.suptitle("Does collapsing improve change-class convergence? Stratified SD of per-class F1 vs n\n"
                 "5-class doubles each change stratum (n/5 vs n/10) → converges FASTER at small n; but it "
                 "under-samples Stable (n/5 vs 6·n/10), so for the rarest classes (Development, Beaver) F1 "
                 "PRECISION suffers and 10-class passes it at large n. Recall gain vs precision cost. "
                 "Draws from a design, not accuracy estimates.", fontsize=9.5)
    fig.tight_layout(rect=[0, 0, 1, 0.9])
    fig.savefig(os.path.join(D5, "change_convergence.png"), dpi=140, bbox_inches="tight")
    plt.close(fig)

    # ---- summary: OA SD, macro-F1 SD, design effect (5 vs 10), lines per version ----
    fig, axes = plt.subplots(1, 3, figsize=(15, 4.6))
    # OA SD vs n (W=1), 5 vs 10
    for ax, (col, title) in zip(axes[:2], [("oa_sd", "OA SD (W=1)"), ("mf1_sd", "macro-F1 SD (W=1)")]):
        for v in VERS:
            s = tab[(tab.version == v) & (tab.W == 1)].sort_values("n")
            ax.plot(s.n, s[f"{col}_5"], "-", color=VPAL[v], label=f"{v} 5cl")
            ax.plot(s.n, s[f"{col}_10"], "--", color=VPAL[v], alpha=0.6)
        try:
            ax.set_xscale("log"); ax.set_yscale("log")
        except ValueError:
            pass
        _nticks(ax, n_values)
        ax.set_xlabel("n (windows)"); ax.set_ylabel(f"SD (solid=5-class, dashed=10-class)")
        ax.set_title(title); ax.legend(fontsize=6.5, frameon=False, ncol=2); _classic(ax)
    # design effect vs W, 5 vs 10 (mean over n)
    ax = axes[2]
    g5 = de5.groupby(["version", "W"]).design_effect.mean().reset_index()
    g10 = de10.groupby(["version", "W"]).design_effect.mean().reset_index()
    for v in VERS:
        ax.plot(g5[g5.version == v].W, g5[g5.version == v].design_effect, "-", color=VPAL[v], label=f"{v} 5cl")
        ax.plot(g10[g10.version == v].W, g10[g10.version == v].design_effect, "--", color=VPAL[v], alpha=0.6)
    ax.axhline(1, ls=":", color="k", lw=0.8); ax.set_xticks(sorted(de5.W.unique()))
    ax.set_xlabel("window size W"); ax.set_ylabel("design effect (solid=5-class, dashed=10-class)")
    ax.set_title("Design effect: 5-class vs 10-class"); ax.legend(fontsize=6.5, frameon=False, ncol=2); _classic(ax)
    fig.suptitle("5-class collapse vs 10-class: OA/macro-F1 precision and design effect "
                 "(macro-F1 not comparable as a level — 5 vs 10 classes)", fontsize=11)
    fig.tight_layout(rect=[0, 0, 1, 0.93])
    fig.savefig(os.path.join(D5, "collapse_summary.png"), dpi=140, bbox_inches="tight")
    plt.close(fig)

    # ---- console: change-class SD ratio (5-class / 10-class), small-n vs large-n regimes ----
    print("change-class stratified SD ratio (5-class / 10-class), v2 W=1  (<1 = 5-class better):")
    print(f"  {'class':16} {'n=50':>8} {'n=200':>8} {'n=5000':>8}")
    for cls in CHANGE:
        s5 = ef5[(ef5.version == "v2") & (ef5.W == 1) & (ef5.cls == cls)].set_index("n").sd_strat
        s10 = ef10[(ef10.version == "v2") & (ef10.W == 1) & (ef10.cls == cls)].set_index("n").sd_strat
        r = (s5 / s10).replace([np.inf, -np.inf], np.nan)
        print(f"  {cls:16} {r.get(50, np.nan):>8.2f} {r.get(200, np.nan):>8.2f} {r.get(5000, np.nan):>8.2f}")
    print("  -> 5-class wins at small n (allocation); 10-class catches/passes at large n for the rarest "
          "(Stable-stratum precision).")
    print(f"\noutputs -> {D5}/collapse_vs_10class.csv, change_convergence.png, collapse_summary.png")


if __name__ == "__main__":
    main()
