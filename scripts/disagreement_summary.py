#!/usr/bin/env python3
"""Summarize inter-interpreter disagreement from the comparison outputs.

Reads the artifacts written by ``compare_interpreters.py`` and produces:
  (a) which class boundaries drive the most reviewer disagreement, from the pooled
      confusion matrix (symmetric off-diagonal pixel counts); and
  (b) the specific reviewer pairs with the lowest agreement, flagged for manual review.

Run ``compare_interpreters.py`` first. Outputs land next to its results.

Usage:
    python scripts/disagreement_summary.py
    python scripts/disagreement_summary.py --worst 15 --flag-below 0.70
"""

import argparse
import os

import numpy as np
import pandas as pd

DIR = "outputs/interpreter_agreement"


def class_disagreement(cm_csv):
    """Rank unordered class pairs by pooled disagreement pixels."""
    cm = pd.read_csv(cm_csv, index_col=0)
    labels = list(cm.index)
    M = cm.to_numpy()
    total = M.sum()
    disagree_total = total - np.trace(M)

    # per class-pair (i<j): pixels where the two reviewers split between class i and j
    rows = []
    n = len(labels)
    for i in range(n):
        for j in range(i + 1, n):
            px = int(M[i, j] + M[j, i])
            if px:
                rows.append(dict(class_a=labels[i], class_b=labels[j], disagree_px=px,
                                 pct_of_all_disagreement=round(100 * px / disagree_total, 2)))
    pair_df = pd.DataFrame(rows).sort_values("disagree_px", ascending=False).reset_index(drop=True)

    # per class: how often a reviewer's label of this class is contested
    per_class = []
    for i, lab in enumerate(labels):
        involved = int(M[i, :].sum() + M[:, i].sum())          # pixels labeled this class by either
        agreed = int(2 * M[i, i])                              # both agreed
        contested = involved - agreed
        support = int(M[i, :].sum() + M[:, i].sum() - M[i, i])  # union support
        per_class.append(dict(cls=lab, union_px=support,
                              self_agreement=round(M[i, i] / M[i, :].sum(), 3) if M[i, :].sum() else float("nan"),
                              contested_px=contested))
    class_df = pd.DataFrame(per_class).sort_values("contested_px", ascending=False).reset_index(drop=True)
    return pair_df, class_df, int(disagree_total), int(total)


def _caption(fig, text, top=1.0, width=125):
    import textwrap
    wrapped = "\n".join(textwrap.wrap(text, width))
    nlines = wrapped.count("\n") + 1
    fig.tight_layout(rect=[0, 0.02 + 0.035 * nlines, 1, top])
    fig.text(0.5, 0.01, wrapped, ha="center", va="bottom", fontsize=8, color="0.35")


def plot_top_pairs(pair_df, out_path, top=12):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    d = pair_df.head(top).iloc[::-1]
    labels = [f"{a} ↔ {b}" for a, b in zip(d.class_a, d.class_b)]
    fig, ax = plt.subplots(figsize=(9, 0.45 * len(d) + 1.5))
    ax.barh(labels, d.pct_of_all_disagreement, color="#d62728")
    ax.set_xlabel("% of all reviewer-disagreement pixels")
    ax.set_title(f"Top {top} class boundaries driving reviewer disagreement")
    for y, v in enumerate(d.pct_of_all_disagreement):
        ax.text(v + 0.2, y, f"{v:.1f}%", va="center", fontsize=8)
    _caption(fig, "Horizontal bars rank the unordered class-boundary pairs that drive the most "
                  "disagreement between reviewers, pooled over all reviewer pairs. Each bar's "
                  "length is that boundary's share of all reviewer-disagreement pixels, with the "
                  "percentage annotated at the bar tip and the longest bars at the top. Read it to "
                  "see which pairs of land-cover classes, such as Grass/Shrub versus Wetland, "
                  "account for the bulk of inter-interpreter disagreement.")
    fig.savefig(out_path, dpi=140, bbox_inches="tight")
    plt.close(fig)


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--worst", type=int, default=10, help="how many lowest-agreement pairs to flag")
    ap.add_argument("--flag-below", type=float, default=0.70,
                    help="also flag every pair with overall agreement below this (default: 0.70)")
    args = ap.parse_args()

    cm_csv = os.path.join(DIR, "global_confusion_matrix.csv")
    pair_csv = os.path.join(DIR, "per_pair_metrics.csv")
    if not (os.path.exists(cm_csv) and os.path.exists(pair_csv)):
        raise SystemExit("missing comparison outputs; run scripts/compare_interpreters.py first.")

    # (a) class-boundary disagreement
    pair_df, class_df, disagree_total, total = class_disagreement(cm_csv)
    pair_df.to_csv(os.path.join(DIR, "class_disagreement_ranked.csv"), index=False)
    class_df.to_csv(os.path.join(DIR, "per_class_contested.csv"), index=False)
    plot_top_pairs(pair_df, os.path.join(DIR, "class_disagreement_top.png"))

    print(f"(a) CLASS-BOUNDARY DISAGREEMENT  ({disagree_total:,} disagreeing px of {total:,} total)")
    print("    top class pairs driving disagreement:")
    print(pair_df.head(10).to_string(index=False))
    print("\n    most-contested classes (low self-agreement, high contested px):")
    print(class_df.to_string(index=False))

    # (b) lowest-agreement pairs
    pairs = pd.read_csv(pair_csv).sort_values(["overall_agreement", "kappa"])
    worst = pairs.head(args.worst)
    flagged = pairs[pairs.overall_agreement < args.flag_below]
    cols = ["grid", "sample", "target", "revA", "revB", "overall_agreement", "kappa", "macro_f1", "n_valid"]
    worst[cols].to_csv(os.path.join(DIR, "lowest_agreement_pairs.csv"), index=False)
    flagged[cols].to_csv(os.path.join(DIR, "flagged_pairs_for_review.csv"), index=False)

    print(f"\n(b) LOWEST-AGREEMENT PAIRS (bottom {args.worst}):")
    print(worst[cols].to_string(index=False))
    print(f"\n    {len(flagged)} pair(s) below agreement {args.flag_below} flagged -> "
          f"{DIR}/flagged_pairs_for_review.csv")
    print(f"    (open the matching outputs/interpreter_agreement/<grid>_<revA>_vs_<revB>.png to review)")

    print(f"\nwrote: class_disagreement_ranked.csv, per_class_contested.csv, "
          f"class_disagreement_top.png, lowest_agreement_pairs.csv, flagged_pairs_for_review.csv")


if __name__ == "__main__":
    main()
