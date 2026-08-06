#!/usr/bin/env python3
"""pres_change_disagreement_maps: deck (Spectral) maps of the largest change-vs-stable disagreements.

Deck versions of reports/interpreter_agreement/change_stable_conflicts/examples/: for each of the top
contested cells, the two reviewers' interpreted maps side by side with the disagreed area (one called
the stable class, the other the paired change class) outlined. Reuses plot_change_stable_examples's
legend/pairing/colorize helpers so the maps match the report, but rendered in the presentation font.

Run from the repo root: python presentation/scripts/pres_change_disagreement_maps.py
Output (PNG only), in presentation/figures/change_disagreement/.
"""

import os
import sys

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import Patch
import numpy as np
import pandas as pd
import rasterio

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
sys.path.insert(0, HERE)                              # slide_font
sys.path.insert(0, os.path.join(ROOT, "scripts"))    # plot_change_stable_examples
import slide_font
import plot_change_stable_examples as CSE

OUT_DIR = os.path.join(ROOT, "presentation", "figures", "change_disagreement")
N_TOP = 4


def main():
    slide_font.use_spectral()
    os.makedirs(OUT_DIR, exist_ok=True)
    code2name, code2rgb, name2code = CSE.load_legend()
    idx = CSE.pair_index()
    df = pd.read_csv(CSE.LONG_CSV, dtype={"grid": str, "sample": str, "target": str})
    top = df.sort_values("area_ha", ascending=False).head(N_TOP).reset_index(drop=True)

    # anonymize reviewers to stable letters (sorted by name), no names on the figures; keep a key file
    shown = sorted({r for row in top.itertuples() for r in (row.revA, row.revB)})
    letter = {rev: chr(ord("A") + i) for i, rev in enumerate(shown)}
    pd.DataFrame([{"letter": lt, "reviewer": rev} for rev, lt in letter.items()]).to_csv(
        os.path.join(OUT_DIR, "reviewer_letter_key.csv"), index=False)

    for rank, row in top.iterrows():
        paths = idx.get((row.grid, row["sample"], row.target), {})
        if row.revA not in paths or row.revB not in paths:
            print(f"  missing raster for {row.grid} {row.revA}/{row.revB}; skip")
            continue
        with rasterio.open(paths[row.revA]) as ds:
            a = ds.read(1)
        with rasterio.open(paths[row.revB]) as ds:
            b = ds.read(1)
        if a.shape != b.shape:
            print(f"  shape mismatch {row.grid}; skip")
            continue
        sc, cc = name2code[row.stable_class], name2code[row.change_class]
        conflict = ((a == sc) & (b == cc)) | ((a == cc) & (b == sc))

        fig, axes = plt.subplots(1, 2, figsize=(11, 6.2))
        for ax, arr, rev in [(axes[0], a, row.revA), (axes[1], b, row.revB)]:
            ax.imshow(CSE.colorize(arr, code2rgb), interpolation="nearest")
            ax.contour(conflict.astype(float), levels=[0.5], colors="black", linewidths=1.8)
            ax.set_title(f"Reviewer {letter[rev]}", fontsize=15, fontweight="bold")   # anonymized
            ax.set_xticks([]); ax.set_yticks([])

        present = sorted(set(np.unique(a)).union(np.unique(b)) & set(code2name))
        handles = [Patch(facecolor=code2rgb[c], edgecolor="0.4", label=code2name[c]) for c in present]
        handles.append(Patch(facecolor="none", edgecolor="black", label="disagreed area (outlined)"))
        fig.legend(handles=handles, loc="lower center", ncol=min(7, len(handles)), fontsize=11,
                   frameon=False, bbox_to_anchor=(0.5, 0.05))
        km = a.shape[1] * 10 / 1000
        fig.suptitle(f"Interpreters Split on Change: {row.stable_class} vs {row.change_class}  "
                     f"(Cell {row.grid}, {row.area_ha:.0f} ha)", fontsize=16, fontweight="bold", y=0.98)
        fig.text(0.5, 0.005, "Two reviewers' interpreted maps of the same cell; the outline marks pixels "
                 "one called stable and the other called the paired change class.",
                 ha="center", va="bottom", fontsize=10, color="0.35")
        fig.subplots_adjust(left=0.02, right=0.98, top=0.90, bottom=0.16, wspace=0.04)

        out = os.path.join(OUT_DIR, f"change_disagreement_map_rank{rank + 1:02d}_grid{row.grid}_"
                           f"{row.stable_class}_vs_{row.change_class}.png".replace("/", "-"))
        fig.savefig(out, dpi=300, bbox_inches="tight")
        plt.close(fig)
        print(f"  wrote {os.path.basename(out)}")


if __name__ == "__main__":
    main()
