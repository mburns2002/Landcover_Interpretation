"""Re-render every confusion matrix in reports/ from its existing count CSV with the shared clean
style (descriptive title, caption band below the matrix, print-size fonts, American spelling) from
build_transfer_confusion.render_cm_png. This reads the stored count matrices, so it does not recompute
anything from rasters. The class count (5 or 10) is inferred from the matrix, which selects the labels.

Run: python scripts/rerender_confusion_matrices.py
"""

import glob
import os
import re
import sys

import pandas as pd

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "scripts"))
import build_transfer_confusion as bmc


def render(csv, variant, bracket, out):
    M = pd.read_csv(csv, index_col=0).values
    bmc.render_cm_png(M, None, variant, bracket, out)      # k (5 or 10) inferred from M
    return out


def main():
    R = os.path.join(ROOT, "reports")
    done = []

    # 10-class transfer matrices (adjudicated and the earlier non-adjudicated arm)
    for folder in ["transfer_confusion_adjudicated", "transfer_confusion",
                   "transfer_confusion_adjudicated_5class"]:
        for f in glob.glob(f"{R}/{folder}/cm_v*_*.csv"):
            m = re.search(r"cm_(v\d)_(\d{4}_\d{4})\.csv$", f)
            if m:
                done.append(render(f, m.group(1), m.group(2), f[:-4] + ".png"))

    # spectral 10-class (per bracket and pooled)
    for f in glob.glob(f"{R}/spectral_composite_classified_maps/cm_specall_*.csv"):
        m = re.search(r"cm_specall_(.+)\.csv$", f)
        done.append(render(f, "spec_all", m.group(1), f[:-4] + ".png"))

    # collapsed 5-class embeddings and spec_all (pooled)
    for f in glob.glob(f"{R}/collapsed_5class_confusion/confusion_v*_counts.csv"):
        m = re.search(r"confusion_(v\d)_counts\.csv$", f)
        done.append(render(f, m.group(1), "pooled", f.replace("_counts.csv", ".png")))
    f = f"{R}/spectral_composite_classified_maps/collapsed_5class/confusion_specall_counts.csv"
    if os.path.exists(f):
        done.append(render(f, "spec_all", "pooled", f.replace("_counts.csv", ".png")))

    # change-cap sensitivity matrices, 10-class and 5-class (pooled over 180 cells)
    for folder in ["sensitivity_changecap", "sensitivity_changecap_5class"]:
        for f in glob.glob(f"{R}/{folder}/cm_cap*_counts.csv"):
            m = re.search(r"cm_(cap\d+)_counts\.csv$", f)
            done.append(render(f, m.group(1), "pooled", f.replace("_counts.csv", ".png")))

    print(f"re-rendered {len(done)} confusion matrices")
    for p in sorted(done):
        print("  " + os.path.relpath(p, ROOT))


if __name__ == "__main__":
    main()
