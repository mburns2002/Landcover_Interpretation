#!/usr/bin/env python3
"""pres_20_training_conflict_overlay: deck (Spectral) copy of manuscript Figure 3.5.

Same content and layout as scripts/training_polygon_overlay.py (the Grass/Shrub-versus-Wetland
training-label conflicts on shared ground, top three contested patches with the disagreement patch
outlined), but rendered in the presentation Spectral font at 300 dpi. It reuses that script's compute
step, so the panels and numbers match the manuscript figure exactly.

Run from the repo root: python presentation/scripts/pres_20_training_conflict_overlay.py
Output (PNG only for the Google Slides deck): presentation/figures/pres_20_training_conflict_overlay.png
"""

import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
sys.path.insert(0, HERE)                              # slide_font
sys.path.insert(0, os.path.join(ROOT, "scripts"))    # training_polygon_overlay (+ its helpers)

import slide_font
slide_font.use_spectral()                            # register Spectral before matplotlib renders

import training_polygon_overlay as T


def main():
    render, _df = T.compute()
    render_top, letter = T.anonymize_top3(render)
    out = os.path.join(ROOT, "presentation", "figures", "pres_20_training_conflict_overlay.png")
    T.make_render(render_top, letter, out, dpi=300)
    print(f"wrote {out}")


if __name__ == "__main__":
    main()
