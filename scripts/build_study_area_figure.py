#!/usr/bin/env python3
"""Study-area figure (Figure 1) for the western Great Lakes manuscript.

Maps the analysis region in EPSG:5070 (CONUS Albers, equal-area): neighboring states and provinces
for context, the Great Lakes, the study grid extent, the seven GLKN park watershed boundaries, and
the interpreted reference cells. A locator inset places the region within North America, and a scale
bar and north arrow are added. Inputs are the GEE grid export, the GLKN watershed shapefile, the
interpreted-cell list, and Natural Earth context layers; all are reprojected to EPSG:5070.

Run: python scripts/build_study_area_figure.py
Requires: geopandas, matplotlib, matplotlib-scalebar, shapely
"""

import os

import geopandas as gpd
import matplotlib.pyplot as plt
import pandas as pd
from matplotlib.lines import Line2D
from matplotlib.patches import Patch, Rectangle
from matplotlib_scalebar.scalebar import ScaleBar
from shapely.geometry import box

CRS = 5070
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
GLKN = f"{ROOT}/data/raw/glkn/GLKN_watershed_boundaries_7park_5070.shp"
GRID = f"{ROOT}/data/raw/glkn/grid_112_naip_brackets_5_11_26.csv"
CELLS = f"{ROOT}/exports/gee/interpreted_cells_by_bracket.csv"
NE = f"{ROOT}/data/raw/naturalearth"
OUT = f"{ROOT}/figure_study_area"

# park code to full name for the legend
PARK_NAME = {
    "apis": "Apostle Islands National Lakeshore",
    "grpo": "Grand Portage National Monument",
    "isro": "Isle Royale National Park",
    "miss": "Mississippi National River and Recreation Area",
    "sacn": "Saint Croix National Scenic Riverway",
    "slbe": "Sleeping Bear Dunes National Lakeshore",
    "voya": "Voyageurs National Park",
}
# qualitative palette, seven parks, colorblind aware and avoiding lake blue
PARK_COLOR = {
    "voya": "#882255", "apis": "#D55E00", "grpo": "#009E73", "miss": "#CC79A7",
    "sacn": "#E69F00", "slbe": "#7B3294", "isro": "#8C564B",
}
STATE_LABELS = ["Minnesota", "Wisconsin", "Michigan"]


def build_grid():
    df = pd.read_csv(GRID, dtype={"id": str})
    df["key"] = df.id.astype(str).str.zfill(5)                 # zero-padded 5-digit join key
    geom = [box(l, b, r, t) for l, b, r, t in zip(df.left, df.bottom, df.right, df.top)]
    return gpd.GeoDataFrame(df, geometry=geom, crs=CRS)


def main():
    os.makedirs(OUT, exist_ok=True)

    grid = build_grid()
    cells = pd.read_csv(CELLS, dtype=str)
    keep = set(cells.cell_id)
    interp = grid[grid.key.isin(keep)].copy()                  # interpreted cells, verified below
    n_join = len(interp)
    print(f"interpreted-cell join: {n_join} of {len(keep)} expected")
    if n_join != len(keep):
        raise SystemExit(f"STOP: join produced {n_join}, expected {len(keep)}; check key padding.")

    footprint = grid.geometry.union_all()                      # study grid extent as one polygon
    parks = gpd.read_file(GLKN).to_crs(CRS)

    states = gpd.read_file(f"{NE}/ne_50m_admin_1_states_provinces_lakes.shp").to_crs(CRS)
    states_na = states[states.admin.isin(["United States of America", "Canada"])].copy()
    lakes = gpd.read_file(f"{NE}/ne_50m_lakes.shp").to_crs(CRS)
    countries = gpd.read_file(f"{NE}/ne_110m_admin_0_countries.shp").to_crs(CRS)

    # main-map extent from the grid and parks, padded
    minx, miny, maxx, maxy = grid.total_bounds
    pminx, pminy, pmaxx, pmaxy = parks.total_bounds
    minx, miny = min(minx, pminx), min(miny, pminy)
    maxx, maxy = max(maxx, pmaxx), max(maxy, pmaxy)
    padx, pady = 0.06 * (maxx - minx), 0.06 * (maxy - miny)
    xlim = (minx - padx, maxx + padx)
    ylim = (miny - pady, maxy + pady)

    # map on top, external legend strip below (keeps double-column width, frees the data area)
    fig = plt.figure(figsize=(7.5, 6.7))
    gs = fig.add_gridspec(2, 1, height_ratios=[6.0, 1.15], hspace=0.02)
    ax = fig.add_subplot(gs[0])
    axleg = fig.add_subplot(gs[1]); axleg.axis("off")

    # back to front: states, lakes, grid extent, parks, interpreted cells
    states_na.plot(ax=ax, facecolor="#efece6", edgecolor="#b9b3a7", linewidth=0.5, zorder=1)
    lakes.plot(ax=ax, facecolor="#cfe3ef", edgecolor="#9dc4d8", linewidth=0.3, zorder=2)
    gpd.GeoSeries([footprint], crs=CRS).plot(ax=ax, facecolor="#000000", alpha=0.04,
                                             edgecolor="#555555", linewidth=0.9, zorder=3)
    for code, sub in parks.groupby("park"):
        sub.plot(ax=ax, facecolor=PARK_COLOR[code], edgecolor=PARK_COLOR[code],
                 alpha=0.45, linewidth=1.1, zorder=4)
        sub.boundary.plot(ax=ax, color=PARK_COLOR[code], linewidth=1.1, zorder=5)
    interp.plot(ax=ax, facecolor="#111111", edgecolor="#111111", linewidth=0.2, zorder=6)

    # state name labels, placed at the representative point of the in-frame part of each state
    # (so Michigan labels in the Upper Peninsula rather than the off-frame Lower Peninsula)
    extent_box = box(xlim[0], ylim[0], xlim[1], ylim[1])
    for nm in STATE_LABELS:
        s = states_na[states_na.name == nm]
        if len(s):
            clipped = s.geometry.union_all().intersection(extent_box)
            if not clipped.is_empty:
                c = clipped.representative_point()
                ax.annotate(nm, (c.x, c.y), fontsize=8, color="#6b6459", ha="center",
                            style="italic", zorder=7)

    ax.set_xlim(*xlim); ax.set_ylim(*ylim)
    ax.set_aspect("equal")
    ax.set_xticks([]); ax.set_yticks([])
    for sp in ax.spines.values():
        sp.set_edgecolor("#888888")

    # scale bar (5070 units are meters; auto-labels in km at this range)
    ax.add_artist(ScaleBar(1, units="m", location="lower left", box_alpha=0.7,
                           length_fraction=0.22, font_properties={"size": 7}))
    # north arrow, placed over open water so it covers no layer
    ax.annotate("N", xy=(0.58, 0.96), xytext=(0.58, 0.85), xycoords="axes fraction",
                ha="center", va="center", fontsize=11, fontweight="bold",
                arrowprops=dict(arrowstyle="-|>", color="black", linewidth=1.4))

    # external legend strip below the map: parks (full names) plus the grid and cell layers
    handles = [Patch(facecolor=PARK_COLOR[c], edgecolor=PARK_COLOR[c], alpha=0.6,
                     label=PARK_NAME[c]) for c in sorted(PARK_NAME)]
    handles += [Patch(facecolor="#000000", alpha=0.06, edgecolor="#555555",
                      label="Study grid extent"),
                Line2D([], [], marker="s", ls="", markerfacecolor="#111111",
                       markeredgecolor="#111111", markersize=6,
                       label=f"Interpreted cells (n = {n_join})"),
                Patch(facecolor="#cfe3ef", edgecolor="#9dc4d8", label="Great Lakes")]
    axleg.legend(handles=handles, loc="center", ncol=2, fontsize=7.2, frameon=False,
                 handlelength=1.4, columnspacing=1.6, title="GLKN park units and map layers",
                 title_fontsize=8)

    # locator inset over Lake Superior (top-right), data-free, with the main-map extent marked
    axin = ax.inset_axes([0.775, 0.62, 0.225, 0.36])
    na = countries[countries.NAME.isin(["United States of America", "Canada", "Mexico"])]
    na.plot(ax=axin, facecolor="#f2efe9", edgecolor="#b9b3a7", linewidth=0.4)
    axin.add_patch(Rectangle((xlim[0], ylim[0]), xlim[1] - xlim[0], ylim[1] - ylim[0],
                             facecolor="none", edgecolor="#d7191c", linewidth=1.3, zorder=5))
    axin.set_xlim(-2.3e6, 2.6e6); axin.set_ylim(2.0e5, 3.4e6)
    axin.set_aspect("equal")
    axin.set_xticks([]); axin.set_yticks([])
    axin.set_facecolor("white")
    for sp in axin.spines.values():
        sp.set_edgecolor("#888888")
    png = f"{OUT}/figure1_study_area.png"
    pdf = f"{OUT}/figure1_study_area.pdf"
    fig.savefig(png, dpi=300, bbox_inches="tight")
    fig.savefig(pdf, bbox_inches="tight")                     # vector version
    plt.close(fig)

    w, h = fig.get_size_inches()
    print(f"wrote {png} and {pdf}")
    print(f"figure size: {w:.2f} x {h:.2f} in, 300 dpi (png), vector (pdf)")
    return n_join, (w, h)


if __name__ == "__main__":
    main()
