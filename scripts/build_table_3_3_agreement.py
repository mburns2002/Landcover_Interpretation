#!/usr/bin/env python3
"""Table 3.3: per-class inter-interpreter agreement (five-class collapse), rendered in the shared
Chapter 3 table style (tidy csv, png, and editable docx) using the helpers in build_chapter3_tables.
Data source: reports/interpreter_agreement/per_class_agreement_ci_5class.csv (the same numbers behind
figure 3.3). Caption goes below the table.

Run: python scripts/build_table_3_3_agreement.py
Requires: pandas, matplotlib, python-docx
"""

import os
import sys

import pandas as pd

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import build_chapter3_tables as bt

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CSV = os.path.join(REPO, "reports", "interpreter_agreement", "per_class_agreement_ci_5class.csv")


def ci(val, lo, hi):
    # point estimate with its 95% confidence interval, two decimals
    return f"{val:.2f} ({lo:.2f}–{hi:.2f})"


def main():
    df = pd.read_csv(CSV)
    headers = ["Class", "Pairs", "Support\n(px)", "F1\n(95% CI)", "IoU\n(95% CI)", "Reliability"]
    aligns = ["l", "r", "r", "l", "l", "l"]
    rows, tidy = [], []
    for r in df.itertuples():
        rows.append([r.cls, f"{int(r.n_pairs):,}", f"{int(r.support_px):,}",
                     ci(r.f1, r.f1_lo, r.f1_hi), ci(r.iou, r.iou_lo, r.iou_hi), r.reliability])
        tidy.append({"class": r.cls, "n_pairs": int(r.n_pairs), "support_px": int(r.support_px),
                     "f1": r.f1, "f1_lo": r.f1_lo, "f1_hi": r.f1_hi,
                     "iou": r.iou, "iou_lo": r.iou_lo, "iou_hi": r.iou_hi, "reliability": r.reliability})
    foot = ("F1 between independent interpreters over the 72 double-interpreted cells, with 95% "
            "cluster bootstrap confidence intervals and IoU, and the reliability tier (thresholds at "
            "0.50 and 0.70). Interpreters agree almost perfectly on stable land and well on harvest, "
            "but poorly on development, insect and disease, and beaver.")
    bt.emit("chapter3_table_interpreter_agreement_5class",
            "Per-Class Inter-Interpreter Agreement, Five-Class Collapse", None, None,
            headers, rows, aligns, pd.DataFrame(tidy), footnote=foot)


if __name__ == "__main__":
    main()
