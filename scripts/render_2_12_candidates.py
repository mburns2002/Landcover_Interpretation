"""Render the Figure 2.12 candidate confusion matrices for the manuscript using the shared clean
renderer (build_transfer_confusion.render_cm_png): descriptive title, caption band below the matrix,
and print-size fonts. The v2 panel is pooled over all grid cells (the five per-bracket matrices
summed, 180 cells), not the single 2018_2020 control bracket. Outputs go to
manuscript_formatting/figures/figure_2_12_candidates/.

Run: python scripts/render_2_12_candidates.py
"""

import os
import sys

import pandas as pd

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "scripts"))
import build_transfer_confusion as bmc

OUT = f"{ROOT}/manuscript_formatting/figures/figure_2_12_candidates"


def main():
    os.makedirs(OUT, exist_ok=True)

    # v2 pooled over all grid cells: sum the five per-bracket count matrices (180 cells)
    brackets = ["2017_2019", "2018_2020", "2019_2021", "2020_2022", "2021_2023"]
    v2 = sum(pd.read_csv(f"{ROOT}/reports/transfer_confusion_adjudicated/cm_v2_{b}.csv",
                         index_col=0).values for b in brackets)
    bmc.render_cm_png(v2, None, "v2", "pooled", f"{OUT}/cm_v2_allcells.png")
    print(f"v2 pooled over all cells: {int(v2.sum()):,} reference pixels")

    # spec_all pooled (already 168 cells)
    sp = pd.read_csv(f"{ROOT}/reports/spectral_composite_classified_maps/cm_specall_pooled.csv",
                     index_col=0).values
    bmc.render_cm_png(sp, None, "spec_all", "pooled", f"{OUT}/cm_specall_pooled.png")
    print(f"spec_all pooled: {int(sp.sum()):,} reference pixels")

    # 5-class pooled candidates (v2 and spec_all); k=5 is inferred from the matrix
    v2_5 = pd.read_csv(f"{ROOT}/reports/collapsed_5class_confusion/confusion_v2_counts.csv",
                       index_col=0).values
    bmc.render_cm_png(v2_5, None, "v2", "pooled", f"{OUT}/confusion_v2.png")
    sp_5 = pd.read_csv(f"{ROOT}/reports/spectral_composite_classified_maps/collapsed_5class/"
                       "confusion_specall_counts.csv", index_col=0).values
    bmc.render_cm_png(sp_5, None, "spec_all", "pooled", f"{OUT}/confusion_specall.png")

    # remove the superseded single-bracket v2 candidate if it lingers
    old = f"{OUT}/cm_v2_2018_2020.png"
    if os.path.exists(old):
        os.remove(old)
    print(f"wrote the four candidate confusion matrices -> {OUT}/")


if __name__ == "__main__":
    main()
