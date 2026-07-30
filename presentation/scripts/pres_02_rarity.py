#!/usr/bin/env python3
"""pres_02_rarity: how rare change is in the reference, by reference-pixel count.

Primary rarity figure. Panel A is a single horizontal stacked bar of every reference pixel on the
180-cell embedding basis, with the stable share in grey and the four change classes in their class
palette colors. Because change is about 1.6% of pixels, the change segments are a thin sliver at the
right, so Panel B is a zoomed companion showing only the change portion broken out by class, with each
class labeled directly (outside the bar) by pixel count and percentage of the grand total. Linear scale
throughout, no log axis, no fitted lines.

Data source: manuscript_formatting/tables/table_2_5.csv, the per-class reference support behind
Table 2.5, column "Support (emb, 180)" (the 180-cell embedding basis). The change total percentage is
checked against the complement of the all-Stable baseline overall accuracy in Table S4
(manuscript_formatting/tables/S4.csv); the check is printed to the console.

sizing: 11 x 6 in, near the content area of a 16:9 slide.

output (png only):
  presentation/figures/pres_02_rarity.png
"""

import os

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import ConnectionPatch
import pandas as pd

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
T25 = os.path.join(ROOT, "manuscript_formatting", "tables", "table_2_5.csv")
S4 = os.path.join(ROOT, "manuscript_formatting", "tables", "S4.csv")
OUT = os.path.join(ROOT, "presentation", "figures")

# canonical 10-class palette colors for the four change classes; stable folds to grey
CHANGE = ["Harvest", "Insect/Disease", "Development", "Beaver"]   # will re-sort by count, descending
CLASS_COLOR = {"Harvest": "yellow", "Development": "red", "Beaver": "orange", "Insect/Disease": "#70A2DB"}
STABLE_COLOR = "#BDBDBD"


def _pct(x):
    return f"{x:.2f}%" if x >= 0.1 else f"{x:.3f}%"


def main():
    df = pd.read_csv(T25)
    sup = dict(zip(df["Class"], df["Support (emb, 180)"].astype(int)))
    total = sum(sup.values())
    change = {c: sup[c] for c in CHANGE}
    change_total = sum(change.values())
    stable_total = total - change_total
    order = sorted(change, key=change.get, reverse=True)   # descending by pixel count

    # diagnostics
    print("reference pixels on the 180-cell embedding basis (Table 2.5 support):")
    for c in order:
        print(f"  {c:<16} {change[c]:>10,} px  {100*change[c]/total:.3f}% of all")
    print(f"  {'change total':<16} {change_total:>10,} px  {100*change_total/total:.3f}% of all")
    print(f"  {'stable total':<16} {stable_total:>10,} px  {100*stable_total/total:.3f}% of all")
    print(f"  {'grand total':<16} {total:>10,} px")

    base = float(pd.read_csv(S4)["baseline_OA"].iloc[0])
    change_frac = change_total / total
    print(f"\nchange fraction = {change_frac:.5f} ({100*change_frac:.3f}%)")
    print(f"1 - S4 all-Stable baseline_OA ({base}) = {1 - base:.5f} ({100*(1 - base):.3f}%)")
    ok = abs(change_frac - (1 - base)) < 0.001
    print(f"match within rounding: {'YES' if ok else 'NO'}  "
          f"(exact stable fraction {stable_total/total:.5f} rounds to baseline {round(stable_total/total, 3)})")

    plt.rcParams.update({"font.family": "sans-serif",
                         "font.sans-serif": ["Helvetica", "Arial", "DejaVu Sans"],
                         "font.size": 16, "axes.linewidth": 1.0})
    fig, (axA, axB) = plt.subplots(2, 1, figsize=(11, 6), gridspec_kw=dict(height_ratios=[1, 1.5]))
    fig.subplots_adjust(left=0.06, right=0.97, top=0.86, bottom=0.13, hspace=0.9)
    axA.set_title("Change Classes Are 1.6% of Reference Pixels", fontsize=19, fontweight="bold", pad=12)

    # ---- panel A: full stacked bar (stable grey + change sliver) ----
    axA.barh(0, stable_total, color=STABLE_COLOR, edgecolor="black", linewidth=0.8, height=0.6)
    cum = stable_total
    for c in order:
        axA.barh(0, change[c], left=cum, color=CLASS_COLOR[c], edgecolor="black", linewidth=0.8, height=0.6)
        cum += change[c]
    axA.set_xlim(0, total)
    axA.set_ylim(-0.5, 0.5)
    axA.set_yticks([])
    axA.set_xticks([0, 5e6, 10e6, 15e6, 20e6])
    axA.set_xticklabels(["0", "5M", "10M", "15M", "20M"], fontsize=13)
    for s in ("top", "right", "left"):
        axA.spines[s].set_visible(False)
    axA.text(stable_total / 2, 0, f"Stable\n{stable_total:,} px  (98.4%)", ha="center", va="center",
             fontsize=15, color="0.15")
    axA.annotate(f"Change: {change_total:,} px  (1.6%)", xy=(stable_total + change_total / 2, 0.30),
                 xytext=(total, 0.95), ha="right", va="bottom", fontsize=14, color="0.1",
                 arrowprops=dict(arrowstyle="-", color="0.4", lw=1.0))
    axA.set_xlabel("Reference pixels, all 180 cells", fontsize=15, loc="left")

    # ---- panel B: zoomed change-only stacked bar ----
    cumb = 0.0
    centers = {}
    for c in order:
        axB.barh(0, change[c], left=cumb, color=CLASS_COLOR[c], edgecolor="black", linewidth=0.8, height=0.55)
        centers[c] = cumb + change[c] / 2
        cumb += change[c]
    axB.set_xlim(0, change_total * 1.34)
    axB.set_ylim(-2.4, 0.9)
    axB.set_yticks([])
    axB.set_xticks([0, 1e5, 2e5, 3e5])
    axB.set_xticklabels(["0", "100k", "200k", "300k"], fontsize=13)
    for s in ("top", "right", "left"):
        axB.spines[s].set_visible(False)
    axB.set_xlabel("Change-class reference pixels (zoom of the 1.6% sliver)", fontsize=15, loc="left")

    # direct labels outside each segment; the two tiny classes go to the right margin with leaders
    xr = change_total * 1.06
    lab = {
        "Harvest": (centers["Harvest"], -1.05, "center", -0.28),
        "Insect/Disease": (centers["Insect/Disease"], -1.05, "center", -0.28),
        "Beaver": (xr, -0.35, "left", -0.12),
        "Development": (xr, -1.5, "left", -0.12),
    }
    for c in order:
        lx, ly, ha, yanchor = lab[c]
        axB.annotate(f"{c}\n{change[c]:,} px  ({_pct(100*change[c]/total)})",
                     xy=(centers[c], yanchor), xytext=(lx, ly), ha=ha, va="top",
                     fontsize=13.5, color="0.1", arrowprops=dict(arrowstyle="-", color="0.5", lw=0.9))

    # zoom funnel connecting the change sliver in A to the full width of B
    for xa, xb in [(stable_total, 0), (total, change_total)]:
        con = ConnectionPatch(xyA=(xa, -0.30), coordsA=axA.transData, xyB=(xb, 0.30),
                              coordsB=axB.transData, color="0.7", lw=1.0, linestyle=(0, (4, 3)))
        fig.add_artist(con)

    os.makedirs(OUT, exist_ok=True)
    fig.savefig(os.path.join(OUT, "pres_02_rarity.png"), dpi=300, bbox_inches="tight")
    plt.close(fig)
    print("\nwrote pres_02_rarity.png")


if __name__ == "__main__":
    main()
