#!/usr/bin/env python3
"""pres_15_embedding_ops_version_5: symbolic equations with abstract embedding textures (smoother).

Same as version_4 but the embeddings are smoother/more continuous (more low-frequency content and
bilinear display) so they read like a true embedding rather than fine noise.

Two operation equations, each on its own row:
  Delta        emb(2018) - emb(2020) = delta output   (red-white-blue, still 64 dimensions -> a stack)
  Dot product  emb(2018) . emb(2020) = dot output     (a single black-and-white value)

Geometry: data units == inches on the background axes (set_position([0,0,1,1])); the textured squares
are their own image axes placed in figure-fraction coordinates.
Output (PNG only): presentation/figures/pres_15_embedding_ops_version_5.png
"""

import os

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

import slide_font
import numpy as np
from matplotlib.cm import ScalarMappable
from matplotlib.colors import Normalize, TwoSlopeNorm
from matplotlib.patches import Circle, FancyArrowPatch, Rectangle
slide_font.use_spectral()

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
OUT = os.path.join(ROOT, "presentation", "figures")

DARK = "#1a1a1a"
EMB_EDGE, EMB_BACK = "#0072B2", "#dbe9f4"
OUT_EDGE, OUT_BACK = "#555555", "#ededed"

FIG_W, FIG_H = 12.0, 5.6
LABEL_FS, BODY_FS, SUB_FS = 18, 14, 12

# geometry (data units == inches)
DELTA_CY, DOT_CY = 3.9, 1.45
S_EMB, N_EMB, OFF = 0.9, 4, 0.14                 # embedding / delta stacks
BBOX = S_EMB + (N_EMB - 1) * OFF
COL = {"a": 1.5, "op": 2.75, "b": 4.0, "eq": 5.25, "out": 6.5}
ANN_X = 7.5

N = 240
INTERP = "bilinear"                              # soft display (no hard pixel grid)


def _textures():
    rng = np.random.default_rng(7)

    def fnoise(beta=2.1):                                           # 1/f noise: organic structure at all scales
        white = rng.normal(size=(N, N))
        f = np.fft.fftfreq(N)
        fx, fy = np.meshgrid(f, f)
        r = np.hypot(fx, fy)
        r[0, 0] = 1.0
        img = np.real(np.fft.ifft2(np.fft.fft2(white) / r ** (beta / 2)))
        return (img - img.min()) / (np.ptp(img) + 1e-9)

    def emb():                                                     # smooth, continuous colorful terrain
        base = np.stack([fnoise(3.2) for _ in range(3)], -1)       # strong low-frequency -> smooth regions
        return np.clip((base - 0.5) * 1.5 + 0.5, 0, 1)

    e18 = emb()
    change = np.stack([fnoise(2.8) for _ in range(3)], -1) - 0.5    # smooth organic year-to-year change
    e20 = np.clip(e18 + 0.16 * change, 0, 1)

    d = (e20 - e18).mean(axis=2)                                    # organic signed delta (smooth, no blocks)
    dot = (e18 * e20).sum(axis=2) / 3.0                            # per-pixel similarity, grayscale
    m = 1.7 * float(np.max(np.abs(d))) or 1.0                       # soft: change reads medium red/blue, not dark
    delta_rgba = ScalarMappable(norm=TwoSlopeNorm(vcenter=0.0, vmin=-m, vmax=m),
                                cmap=plt.get_cmap("RdBu")).to_rgba(d)
    dot_rgba = ScalarMappable(norm=Normalize(dot.min(), dot.max()),
                              cmap=plt.get_cmap("gray")).to_rgba(dot)
    return e18, e20, delta_rgba, dot_rgba


def _imgsq(fig, cx, cy, s, tex, edge):
    ax = fig.add_axes([(cx - s / 2) / FIG_W, (cy - s / 2) / FIG_H, s / FIG_W, s / FIG_H])
    ax.imshow(tex, interpolation=INTERP, aspect="auto")
    ax.set_xticks([])
    ax.set_yticks([])
    for sp in ax.spines.values():
        sp.set_edgecolor(edge)
        sp.set_linewidth(1.3)


def _stack(fig, bg, cx, cy, tex, edge, back):
    """Overlapping stack: back layers as plain offset squares, front layer as the texture."""
    bl = (cx - BBOX / 2, cy - BBOX / 2)
    for i in range(N_EMB - 1, 0, -1):
        bg.add_patch(Rectangle((bl[0] + i * OFF, bl[1] + i * OFF), S_EMB, S_EMB, facecolor=back,
                               edgecolor=edge, linewidth=1.2, zorder=3 + (N_EMB - 1 - i)))
    _imgsq(fig, bl[0] + S_EMB / 2, bl[1] + S_EMB / 2, S_EMB, tex, edge)


def _sign(bg, x, y, s, fs):
    bg.text(x, y, s, ha="center", va="center", fontsize=fs, fontweight="bold", color=DARK, zorder=6)


def _oplabel(bg, name, sub, cy):
    bg.text(ANN_X, cy + 0.12, name, ha="left", va="bottom", fontsize=LABEL_FS, fontweight="bold",
            color=DARK, zorder=6)
    bg.text(ANN_X, cy - 0.14, sub, ha="left", va="top", fontsize=SUB_FS, color="0.4", style="italic",
            zorder=6)


def main():
    e18, e20, delta_rgba, dot_rgba = _textures()

    fig = plt.figure(figsize=(FIG_W, FIG_H))
    bg = fig.add_axes([0, 0, 1, 1])
    bg.set_xlim(0, FIG_W)
    bg.set_ylim(0, FIG_H)
    bg.axis("off")

    bg.text((COL["a"] + COL["b"]) / 2, DELTA_CY + BBOX / 2 + 0.5, "AlphaEarth Embeddings",
            ha="center", va="bottom", fontsize=16, fontweight="bold", color=DARK, zorder=6)
    for col, yr in (("a", "2018"), ("b", "2020")):
        bg.text(COL[col], DELTA_CY + BBOX / 2 + 0.14, yr, ha="center", va="bottom", fontsize=LABEL_FS,
                fontweight="bold", color=DARK, zorder=6)

    # delta row: emb - emb = delta stack (64 dimensions)
    _stack(fig, bg, COL["a"], DELTA_CY, e18, EMB_EDGE, EMB_BACK)
    _stack(fig, bg, COL["b"], DELTA_CY, e20, EMB_EDGE, EMB_BACK)
    _sign(bg, COL["op"], DELTA_CY, "−", 40)
    _sign(bg, COL["eq"], DELTA_CY, "=", 34)
    _stack(fig, bg, COL["out"], DELTA_CY, delta_rgba, OUT_EDGE, OUT_BACK)
    bg.text(COL["out"], DELTA_CY - BBOX / 2 - 0.16, "64 dimensions", ha="center", va="top",
            fontsize=SUB_FS, color="0.35", zorder=6)
    _oplabel(bg, "Delta", "elementwise difference", DELTA_CY)

    # dot row: emb . emb = single grayscale value
    _stack(fig, bg, COL["a"], DOT_CY, e18, EMB_EDGE, EMB_BACK)
    _stack(fig, bg, COL["b"], DOT_CY, e20, EMB_EDGE, EMB_BACK)
    bg.add_patch(Circle((COL["op"], DOT_CY), 0.1, facecolor=DARK, edgecolor="none", zorder=6))
    _sign(bg, COL["eq"], DOT_CY, "=", 34)
    _imgsq(fig, COL["out"], DOT_CY, S_EMB, dot_rgba, OUT_EDGE)
    bg.text(COL["out"], DOT_CY - S_EMB / 2 - 0.16, "cosine similarity (−1 to 1)", ha="center",
            va="top", fontsize=SUB_FS, color="0.35", zorder=6)
    _oplabel(bg, "Dot product", "similarity between the years", DOT_CY)

    os.makedirs(OUT, exist_ok=True)
    fig.savefig(os.path.join(OUT, "pres_15_embedding_ops_version_5.png"), dpi=300)
    plt.close(fig)
    print("wrote pres_15_embedding_ops_version_5.png")


if __name__ == "__main__":
    main()
