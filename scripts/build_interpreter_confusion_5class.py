#!/usr/bin/env python3
"""Five-class inter-interpreter confusion matrix, collapsed from the 10-class version.

Reads reports/interpreter_agreement/global_confusion_matrix.csv (the pooled interpreter-vs-interpreter
counts) and collapses it to the canonical 5-class scheme: the six stable classes plus Other fold into
Stable, the four change classes are kept, and Unknown (and the all-zero Fire) are dropped. The result
is rendered with the same PA/UA renderer used for the 10-class matrix.

Outputs:
  reports/interpreter_agreement/global_confusion_matrix_5class.png
  reports/interpreter_agreement/global_confusion_matrix_5class.csv
"""

import importlib.util
import os

import numpy as np
import pandas as pd

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SRC = f"{ROOT}/reports/interpreter_agreement/global_confusion_matrix.csv"
OUT_PNG = f"{ROOT}/reports/interpreter_agreement/global_confusion_matrix_5class.png"
OUT_CSV = f"{ROOT}/reports/interpreter_agreement/global_confusion_matrix_5class.csv"

# 5-class group index (order Stable, Harvest, Development, Insect/Disease, Beaver)
STABLE = {"Urban", "Agriculture", "Grass/Shrub", "Forest", "Water", "Wetland", "Other"}
DROP = {"Unknown", "Fire"}
CHANGE = {"Harvest": 1, "Development": 2, "Insect/Disease": 3, "Beaver": 4}
NAMES5 = {0: "Stable", 1: "Harvest", 2: "Development", 3: "Insect/Disease", 4: "Beaver"}


def _group(name):
    if name in DROP:
        return None
    if name in STABLE:
        return 0
    return CHANGE[name]


def main():
    df = pd.read_csv(SRC, index_col=0)
    cm5 = np.zeros((5, 5), dtype=np.int64)
    for ri in df.index:
        gi = _group(ri)
        if gi is None:
            continue
        for cj in df.columns:
            gj = _group(cj)
            if gj is None:
                continue
            cm5[gi, gj] += int(df.loc[ri, cj])

    # diagnostics
    tp = np.diag(cm5).sum()
    tot = cm5.sum()
    row = cm5.sum(1)
    col = cm5.sum(0)
    oa = tp / tot
    pe = (row * col).sum() / (tot * tot)
    kappa = (oa - pe) / (1 - pe)
    print("collapsed 5-class inter-interpreter confusion (rows Reviewer A, cols Reviewer B):")
    print(pd.DataFrame(cm5, index=[NAMES5[i] for i in range(5)],
                       columns=[NAMES5[i] for i in range(5)]).to_string())
    print(f"\npooled overall agreement: {oa:.4f}   kappa: {kappa:.4f}   pixels: {tot:,}")
    pd.DataFrame(cm5, index=[NAMES5[i] for i in range(5)],
                 columns=[NAMES5[i] for i in range(5)]).to_csv(OUT_CSV)

    # render with the same PA/UA style as the 10-class matrix
    spec = importlib.util.spec_from_file_location("CI", f"{ROOT}/scripts/compare_interpreters.py")
    CI = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(CI)
    CI.plot_confusion(cm5, list(NAMES5), NAMES5, OUT_PNG, title="Inter-Interpreter Agreement")
    print(f"wrote {OUT_PNG} and {OUT_CSV}")


if __name__ == "__main__":
    main()
