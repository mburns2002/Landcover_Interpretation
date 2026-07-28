#!/usr/bin/env python3
"""Grid-detail figure for the western Great Lakes manuscript.

Companion to the study-area figure (Figure 1). The main panel zooms into a dense block of the
sampling fishnet so the individual grid cells are visible: each cell is 112 pixels (30 m) to a
side, i.e. 3,360 m, and this is annotated on one cell. A handful of grid cell unique ids are
labeled, and the interpreted reference cells that fall in the block are filled. A locator inset
shows the whole study area with the full fishnet and marks the zoom window. Style, colors, scale
bar, and north arrow match the study-area figure; everything is EPSG:5070 (CONUS Albers,
equal-area).

Run: python scripts/build_grid_detail_figure.py
Requires: geopandas, matplotlib, shapely
"""

import os

import contextily as cx
import geopandas as gpd
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from matplotlib.lines import Line2D
from matplotlib.patches import Patch, Rectangle
from shapely.geometry import box

CRS = 5070
CELL_M = 3360.0                                            # 112 px * 30 m
WIN = 8                                                    # zoom window side, in cells
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
GLKN = f"{ROOT}/data/raw/glkn/GLKN_watershed_boundaries_7park_5070.shp"
GRID = f"{ROOT}/data/raw/glkn/grid_112_naip_brackets_5_11_26.csv"
CELLS = f"{ROOT}/exports/gee/interpreted_cells_by_bracket.csv"
NE = f"{ROOT}/data/raw/naturalearth"
OUT = f"{ROOT}/manuscript_formatting/figures/figure_grid_detail"

STATE = "#efece6"; STATE_EDGE = "#b9b3a7"                  # shared study-area palette
LAKE = "#cfe3ef"; LAKE_EDGE = "#9dc4d8"
GRIDLINE = "#5a5a5a"; INTERP = "#111111"; ZOOMBOX = "#d7191c"


def draw_scalebar(ax, length_m, n_seg=2, unit_div=1000, unit="km"):
    """Segmented scale bar with tick labels, drawn by hand (bottom-left), matching Figure 1."""
    xlim, ylim = ax.get_xlim(), ax.get_ylim()
    w, h = xlim[1] - xlim[0], ylim[1] - ylim[0]
    x0, y0 = xlim[0] + 0.04 * w, ylim[0] + 0.035 * h
    seg = length_m / n_seg
    bh = 0.014 * h
    for i in range(n_seg):
        ax.add_patch(Rectangle((x0 + i * seg, y0), seg, bh,
                               facecolor=("black" if i % 2 == 0 else "white"),
                               edgecolor="black", lw=0.8, zorder=11))
    for i in range(n_seg + 1):
        xt = x0 + i * seg
        ax.plot([xt, xt], [y0 + bh, y0 + bh + 0.011 * h], color="black", lw=0.8, zorder=11)
        ax.annotate(f"{i * seg / unit_div:g}", (xt, y0 + bh + 0.013 * h),
                    ha="center", va="bottom", fontsize=7, zorder=11)
    ax.annotate(unit, (x0 + length_m + 0.012 * w, y0 + bh / 2), va="center", ha="left",
                fontsize=7.5, zorder=11)


def north_arrow(ax, x=0.055, ytail=0.86, ytip=0.965):
    ax.annotate("N", xy=(x, ytip), xytext=(x, ytail), xycoords="axes fraction",
                ha="center", va="center", fontsize=12, fontweight="bold",
                arrowprops=dict(arrowstyle="-|>", color="black", linewidth=1.5))


def build_grid():
    df = pd.read_csv(GRID, dtype={"id": str})
    df["key"] = df.id.astype(str).str.zfill(5)
    geom = [box(l, b, r, t) for l, b, r, t in zip(df.left, df.bottom, df.right, df.top)]
    return gpd.GeoDataFrame(df, geometry=geom, crs=CRS)


def pick_window(grid, interp_keys):
    """Snap cell centers to integer grid indices and pick the WIN x WIN block that contains the
    most interpreted cells (tie-broken by total cell count), so the zoom shows real samples."""
    cx = (grid.left + grid.right).values / 2
    cy = (grid.top + grid.bottom).values / 2
    ix = np.rint((cx - cx.min()) / CELL_M).astype(int)
    iy = np.rint((cy - cy.min()) / CELL_M).astype(int)
    nx, ny = ix.max() + 1, iy.max() + 1
    tot = np.zeros((nx, ny), float)
    itp = np.zeros((nx, ny), float)
    is_i = grid.key.isin(interp_keys).values
    np.add.at(tot, (ix, iy), 1.0)
    np.add.at(itp, (ix, iy), is_i.astype(float))
    # sliding WIN x WIN sums via integral image
    def winsum(a):
        c = np.zeros((a.shape[0] + 1, a.shape[1] + 1))
        c[1:, 1:] = a.cumsum(0).cumsum(1)
        s = (c[WIN:, WIN:] - c[:-WIN, WIN:] - c[WIN:, :-WIN] + c[:-WIN, :-WIN])
        return s
    st, si = winsum(tot), winsum(itp)
    score = si * 1e6 + st                                 # interpreted cells first, then density
    bx, by = np.unravel_index(np.argmax(score), score.shape)
    sel = (ix >= bx) & (ix < bx + WIN) & (iy >= by) & (iy < by + WIN)
    return grid.iloc[sel].copy()


def main():
    os.makedirs(OUT, exist_ok=True)
    grid = build_grid()
    cells = pd.read_csv(CELLS, dtype=str)
    interp_keys = set(cells.cell_id.str.zfill(5))
    grid["interp"] = grid.key.isin(interp_keys)

    zoom = pick_window(grid, interp_keys)
    n_i = int(zoom.interp.sum())
    zx0, zy0, zx1, zy1 = zoom.total_bounds
    print(f"zoom block: {len(zoom)} cells ({n_i} interpreted), bounds {zoom.total_bounds.round(0)}")

    # context layers, all reprojected to 5070
    parks = gpd.read_file(GLKN).to_crs(CRS)
    states = gpd.read_file(f"{NE}/ne_50m_admin_1_states_provinces_lakes.shp").to_crs(CRS)
    states = states[states.admin.isin(["United States of America", "Canada"])].copy()
    lakes = gpd.read_file(f"{NE}/ne_50m_lakes.shp").to_crs(CRS)

    fig = plt.figure(figsize=(7.5, 6.9))
    gs = fig.add_gridspec(2, 1, height_ratios=[6.0, 0.7], hspace=0.02)
    ax = fig.add_subplot(gs[0])
    axleg = fig.add_subplot(gs[1]); axleg.axis("off")

    pad = 0.08 * max(zx1 - zx0, zy1 - zy0)
    xlim = (zx0 - pad, zx1 + pad)
    ylim = (zy0 - pad * 3.2, zy1 + pad)                   # clear strip below the grid: cell label + scale bar

    # slightly transparent shaded-relief basemap so the underlying landscape shows through the grid;
    # limits are set first so contextily fetches tiles for the zoom window, then warps them to 5070
    ax.set_xlim(*xlim); ax.set_ylim(*ylim); ax.set_aspect("equal")
    cx.add_basemap(ax, crs=f"EPSG:{CRS}", source=cx.providers.Esri.WorldShadedRelief,
                   alpha=0.85, attribution=False, zorder=0)
    viewbox = box(xlim[0], ylim[0], xlim[1], ylim[1])
    park_in_view = bool(parks.boundary.intersects(viewbox).any())
    parks.boundary.plot(ax=ax, color="#7a7266", linewidth=1.0, linestyle=(0, (4, 2)), zorder=3)
    zoom.boundary.plot(ax=ax, color=GRIDLINE, linewidth=0.7, zorder=5)
    zoom[zoom.interp].plot(ax=ax, facecolor=INTERP, edgecolor=INTERP, linewidth=0.5,
                           alpha=0.62, zorder=6)

    # label a spread of grid unique ids: every interpreted cell, plus a few plain cells
    zs = zoom.sort_values(["top", "left"], ascending=[False, True]).reset_index(drop=True)
    plain = zs[~zs.interp]
    label_rows = pd.concat([zs[zs.interp], plain.iloc[:: max(1, len(plain) // 6)]]).drop_duplicates("key")
    ckey = lambda l, t: (int(round(l)), int(round(t)))
    is_interp = {ckey(r.left, r.top): bool(r.interp) for r in zs.itertuples()}
    labeled = {ckey(r.left, r.top) for r in label_rows.itertuples()}
    for r in label_rows.itertuples():
        cxx = (r.left + r.right) / 2; cyy = (r.top + r.bottom) / 2
        ax.annotate(str(r.id), (cxx, cyy), ha="center", va="center", fontsize=6.2,
                    color="white" if r.interp else "#333333",
                    fontweight="bold" if r.interp else "normal", zorder=8)

    # dimension callout: an interior plain cell whose 8 neighbors and its below cell are all plain and
    # unlabeled, so the arrow and its label land on empty ground; nearest to top-center wins
    lefts = sorted(zoom.left.unique()); tops = sorted(zoom.top.unique(), reverse=True)
    cc, cr = lefts[len(lefts) // 2], tops[1] if len(tops) > 2 else tops[0]
    def clear(r):
        k = ckey(r.left, r.top)
        below = (k[0], k[1] - int(round(CELL_M)))
        if below not in is_interp or is_interp[below] or below in labeled:
            return False
        for dx in (-1, 0, 1):
            for dy in (-1, 0, 1):
                nb = (k[0] + dx * int(round(CELL_M)), k[1] + dy * int(round(CELL_M)))
                if is_interp.get(nb) or nb in labeled:
                    return False
        return True
    inner = plain[plain.left.isin(lefts[1:-1]) & plain.top.isin(tops[1:-1])]
    cand = inner[inner.apply(clear, axis=1)] if len(inner) else inner
    pool = cand if len(cand) else inner if len(inner) else plain
    pool = pool.assign(d=(pool.left - cc).abs() + (pool.top - cr).abs())
    dc = pool.sort_values("d").iloc[0]
    # outline the representative cell and draw a width arrow inside it (no on-grid text); the label
    # goes in the clear strip below the grid so it never crosses grid lines
    ax.add_patch(Rectangle((dc.left, dc.bottom), CELL_M, CELL_M, facecolor="none",
                           edgecolor="#000000", linewidth=1.6, zorder=7))
    y_arrow = dc.bottom + 0.5 * CELL_M
    ax.annotate("", xy=(dc.left + 0.08 * CELL_M, y_arrow), xytext=(dc.right - 0.08 * CELL_M, y_arrow),
                arrowprops=dict(arrowstyle="<|-|>", color="#000000", lw=1.3), zorder=9)
    ax.annotate("each grid cell = 112 px (30 m) = 3,360 m per side",
                (0.5, zy0 - 0.62 * CELL_M), xycoords=("axes fraction", "data"),
                ha="center", va="center", fontsize=8, fontweight="bold", zorder=9)

    ax.set_xlim(*xlim); ax.set_ylim(*ylim); ax.set_aspect("equal")
    ax.set_xticks([]); ax.set_yticks([])
    for sp in ax.spines.values():
        sp.set_edgecolor("#888888")
    draw_scalebar(ax, length_m=10000, n_seg=2)
    north_arrow(ax, x=0.028)

    # locator inset (top-right): whole study area, full fishnet, zoom window marked
    axin = ax.inset_axes([0.66, 0.60, 0.335, 0.38])
    gminx, gminy, gmaxx, gmaxy = grid.total_bounds
    ib = box(gminx, gminy, gmaxx, gmaxy).buffer(0.05 * (gmaxx - gminx))
    states.clip(ib).plot(ax=axin, facecolor=STATE, edgecolor=STATE_EDGE, linewidth=0.3, zorder=1)
    lakes.clip(ib).plot(ax=axin, facecolor=LAKE, edgecolor=LAKE_EDGE, linewidth=0.2, zorder=2)
    grid.boundary.plot(ax=axin, color=GRIDLINE, linewidth=0.06, alpha=0.7, zorder=3)
    axin.add_patch(Rectangle((xlim[0], ylim[0]), xlim[1] - xlim[0], ylim[1] - ylim[0],
                             facecolor="none", edgecolor=ZOOMBOX, linewidth=1.4, zorder=6))
    axin.set_xlim(gminx - 0.04 * (gmaxx - gminx), gmaxx + 0.04 * (gmaxx - gminx))
    axin.set_ylim(gminy - 0.04 * (gmaxy - gminy), gmaxy + 0.04 * (gmaxy - gminy))
    axin.set_aspect("equal"); axin.set_xticks([]); axin.set_yticks([])
    axin.set_facecolor("white")
    for sp in axin.spines.values():
        sp.set_edgecolor("#888888")

    handles = [
        Patch(facecolor="none", edgecolor=GRIDLINE, linewidth=0.8, label="Fishnet grid cell (3,360 m)"),
        Line2D([], [], marker="s", ls="", markerfacecolor=INTERP, markeredgecolor=INTERP,
               markersize=6, alpha=0.85, label=f"Interpreted reference cell (n = {n_i} shown)"),
        Line2D([], [], color=ZOOMBOX, lw=1.4, label="Zoom window (see inset)"),
    ]
    if park_in_view:
        handles.insert(2, Line2D([], [], color="#7a7266", lw=1.0, ls=(0, (4, 2)),
                                 label="GLKN park watershed boundary"))
    axleg.legend(handles=handles, loc="center", ncol=2, fontsize=7.4, frameon=False,
                 handlelength=1.7, columnspacing=1.8)

    png = f"{OUT}/figure_grid_detail.png"
    pdf = f"{OUT}/figure_grid_detail.pdf"
    fig.savefig(png, dpi=300, bbox_inches="tight")
    fig.savefig(pdf, bbox_inches="tight")
    plt.close(fig)
    print(f"wrote {png} and {pdf}")


if __name__ == "__main__":
    main()
