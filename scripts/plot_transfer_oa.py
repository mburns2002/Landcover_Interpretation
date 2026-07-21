#!/usr/bin/env python3
"""Overall-accuracy-by-bracket summary for the temporal-transferability experiment.

Reads reports/transfer_confusion/transfer_metrics_long.csv and renders one figure with the NAIP
bracket (time period) on the x axis and each variant's OA on the y axis, plus a wide table CSV.
The 2018_2020 bracket is the in-sample control and is marked. The brackets use disjoint cell sets,
so the lines are five independent assessments, not a controlled transfer curve; the caption says so.

Outputs -> reports/transfer_confusion/oa_by_bracket.png, oa_by_variant_bracket.csv
"""

import os

import argparse

import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import pandas as pd

BRACKETS = ["2017_2019", "2018_2020", "2019_2021", "2020_2022", "2021_2023"]
CONTROL = "2018_2020"
VARIANTS = ["v2", "v3", "v4", "v5", "v6"]
VPAL = {"v2": "#1f77b4", "v3": "#2ca02c", "v4": "#9467bd", "v5": "#ff7f0e", "v6": "#d62728"}


def _caption(fig, text, top=1.0, width=125):
    import textwrap
    wrapped = "\n".join(textwrap.wrap(text, width))
    nlines = wrapped.count("\n") + 1
    fig.tight_layout(rect=[0, 0.02 + 0.035 * nlines, 1, top])
    fig.text(0.5, 0.01, wrapped, ha="center", va="bottom", fontsize=8, color="0.35")


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--dir", default="reports/transfer_confusion",
                    help="transfer confusion folder to read/write (default: reports/transfer_confusion)")
    DIR = ap.parse_args().dir
    long = pd.read_csv(os.path.join(DIR, "transfer_metrics_long.csv"))
    # oa is repeated on every class row, so one value per (variant, bracket)
    oa = (long.groupby(["variant", "bracket"]).OA.first().unstack("bracket")
          .reindex(index=VARIANTS, columns=BRACKETS))
    oa.round(4).to_csv(os.path.join(DIR, "oa_by_variant_bracket.csv"))

    x = range(len(BRACKETS))
    xlabels = [b.replace("_", "–") for b in BRACKETS]     # en-dash for the year range
    fig, ax = plt.subplots(figsize=(9, 5.6))

    # shade the in-sample control bracket
    ci = BRACKETS.index(CONTROL)
    ax.axvspan(ci - 0.5, ci + 0.5, color="0.92", zorder=0)
    ax.text(ci, 0.03, "in-sample\ncontrol", ha="center", va="bottom", fontsize=8, color="0.4")

    for v in VARIANTS:
        ax.plot(x, oa.loc[v].to_numpy(), "-o", color=VPAL[v], lw=2, ms=6, label=v, zorder=3)
        for xi, val in zip(x, oa.loc[v].to_numpy()):       # value labels
            ax.annotate(f"{val:.2f}", (xi, val), textcoords="offset points", xytext=(0, 7),
                        ha="center", fontsize=6.5, color=VPAL[v])

    ax.set_xticks(list(x)); ax.set_xticklabels(xlabels)
    # fit the y-axis to the data with headroom, so the collapsed run (OA near 1) is not clipped
    ax.set_ylim(0, min(1.0, np.ceil(float(np.nanmax(oa.to_numpy())) * 10) / 10 + 0.05))
    ax.set_xlabel("NAIP bracket (time period)")
    ax.set_ylabel("overall accuracy (OA)")
    ax.set_title("Classifier temporal transferability: OA by variant and bracket\n"
                 "RF trained once on 2018/2020; applied to five brackets on disjoint cell sets "
                 "(36 cells each)",
                 fontsize=9.5)
    ax.legend(frameon=False, ncol=5, loc="lower center", bbox_to_anchor=(0.5, -0.26))
    ax.grid(False)
    for s in ("top", "right"):
        ax.spines[s].set_visible(False)
    _caption(fig, "Overall accuracy of each RF variant (v2 to v6) when the single classifier "
             "trained on the 2018/2020 embeddings is applied to five NAIP brackets, with the time "
             "period on the x axis and OA on the y axis. Each colored line is one variant, dots "
             "carry the OA value, and the shaded 2018-2020 column marks the in-sample control. The "
             "five brackets use disjoint cell sets of 36 cells each, so read the points as five "
             "independent assessments, and not as a controlled transfer curve.")
    fig.savefig(os.path.join(DIR, "oa_by_bracket.png"), dpi=150, bbox_inches="tight")
    plt.close(fig)

    print("OA by variant (rows) and bracket (cols):")
    print(oa.round(3).to_string())
    print(f"\nwrote {DIR}/oa_by_bracket.png and oa_by_variant_bracket.csv")


if __name__ == "__main__":
    main()
