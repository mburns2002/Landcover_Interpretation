#!/usr/bin/env python3
"""pres_07_speckle_locations: pres_07 (reference + every classification) for three more locations.

Reuses pres_07_speckle_with_ref.build_for_cell to render the same seven-panel figure (interpreted
reference, v2..v6, spec_all) for three additional cells, chosen for rich class variety (each holds all
four change classes) and spread across brackets. The pooled neighbor-change values are computed once and
shared, so all three figures agree with the primary pres_07 figure.

Outputs (PNG only), in a subfolder:
  presentation/figures/pres_07_speckle_with_ref_locations/pres_07_speckle_with_ref_cell<cell>_<bracket>.png
"""

import importlib.util
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
sys.path.insert(0, HERE)                              # slide_font
sys.path.insert(0, os.path.join(ROOT, "scripts"))    # compare_interpreters (pres_07's helper)

_spec = importlib.util.spec_from_file_location("P7", os.path.join(HERE, "pres_07_speckle_with_ref.py"))
P7 = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(P7)

OUT_DIR = os.path.join(ROOT, "presentation", "figures", "pres_07_speckle_with_ref_locations")
# (cell, bracket): each has all four change classes; spread over three brackets
LOCATIONS = [("04602", "2017_2019"), ("47961", "2018_2020"), ("07373", "2019_2021")]


def main():
    ref_paths, ncs = P7.prepare()
    for cell, bracket in LOCATIONS:
        out = os.path.join(OUT_DIR, f"pres_07_speckle_with_ref_cell{cell}_{bracket}.png")
        P7.build_for_cell(cell, bracket, ref_paths, ncs, out)


if __name__ == "__main__":
    main()
