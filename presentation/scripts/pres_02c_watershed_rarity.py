#!/usr/bin/env python3
"""pres_02c_watershed_rarity: how little of the GLKN watersheds is mapped change, by change type.

Companion to pres_02_rarity, but on an AREA basis with the seven GLKN park watersheds as the universe
(instead of reference-pixel counts). Panel A is a single horizontal stacked bar of the whole watershed
area: unchanged land in grey plus the four change classes in their palette colors. Because attributed
change polygons cover only about 2.9% of the watershed area, the change segments are a thin sliver at
the right, so Panel B zooms into just that sliver, broken out by change type and labeled directly with
area (km2) and percentage of the total watershed area. Linear scale throughout, no log axis.

Data sources (all local, no Earth Engine):
  change-polygon area by agent, 2010-2020:
      reports/GLKN_change_agents/glkn_polygon_area_by_agent_2010_2020.csv  (total_m2 per agent)
  total watershed area (denominator):
      data/raw/glkn/GLKN_watershed_boundaries_7park_5070.shp  (7 park watersheds, EPSG:5070; the
      full watershed extent as extracted, matching the watershed-scoped polygon totals)

Both totals and the change fraction are printed to the console.

sizing: 11 x 6 in, near the content area of a 16:9 slide.

output (png only):
  presentation/figures/pres_02c_watershed_rarity.png
"""

import os

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

import slide_font
from matplotlib.patches import ConnectionPatch
import geopandas as gpd
import pandas as pd

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
AREA_CSV = os.path.join(ROOT, "reports", "GLKN_change_agents", "glkn_polygon_area_by_agent_2010_2020.csv")
WSHED = os.path.join(ROOT, "data", "raw", "glkn", "GLKN_watershed_boundaries_7park_5070.shp")
OUT = os.path.join(ROOT, "presentation", "figures")

# canonical 10-class palette colors for the four change classes; unchanged land folds to grey
AGENT_DISPLAY = {"harvest": "Harvest", "development": "Development",
                 "beaver": "Beaver", "insect_disease_mort": "Insect/Disease"}
AGENT_COLOR = {"harvest": "yellow", "development": "red", "beaver": "orange",
               "insect_disease_mort": "#70A2DB"}
UNCHANGED_COLOR = "#BDBDBD"


def _pct(x):
    return f"{x:.2f}%" if x >= 0.1 else f"{x:.3f}%"


def main():
    df = pd.read_csv(AREA_CSV)
    change_km2 = {r.agent: r.total_m2 / 1e6 for r in df.itertuples()}       # km2 per agent
    change_total = sum(change_km2.values())

    wshed = gpd.read_file(WSHED)                                            # EPSG:5070, area in m2
    total = float(wshed.geometry.area.sum()) / 1e6                         # total watershed area, km2
    unchanged = total - change_total
    order = sorted(change_km2, key=change_km2.get, reverse=True)           # descending by area

    # diagnostics
    print(f"total GLKN watershed area (7 parks) = {total:,.1f} km2")
    for a in order:
        print(f"  {AGENT_DISPLAY[a]:<16} {change_km2[a]:8.2f} km2   {100*change_km2[a]/total:.3f}% of watersheds")
    print(f"  {'change total':<16} {change_total:8.2f} km2   {100*change_total/total:.3f}% of watersheds")
    print(f"  {'unchanged':<16} {unchanged:8.2f} km2   {100*unchanged/total:.3f}% of watersheds")

    plt.rcParams.update({"font.family": "sans-serif",
                         "font.sans-serif": ["Helvetica", "Arial", "DejaVu Sans"],
                         "font.size": 16, "axes.linewidth": 1.0})
    slide_font.use_spectral()
    fig, (axA, axB) = plt.subplots(2, 1, figsize=(11, 6), gridspec_kw=dict(height_ratios=[1, 1.5]))
    fig.subplots_adjust(left=0.06, right=0.97, top=0.86, bottom=0.13, hspace=0.9)
    axA.set_title("Change Polygons Cover 2.9% of the GLKN Watersheds", fontsize=19,
                  fontweight="bold", pad=12)

    # ---- panel A: full watershed bar (unchanged grey + change sliver) ----
    axA.barh(0, unchanged, color=UNCHANGED_COLOR, edgecolor="black", linewidth=0.8, height=0.6)
    cum = unchanged
    for c in order:
        axA.barh(0, change_km2[c], left=cum, color=AGENT_COLOR[c], edgecolor="black",
                 linewidth=0.8, height=0.6)
        cum += change_km2[c]
    axA.set_xlim(0, total)
    axA.set_ylim(-0.5, 0.5)
    axA.set_yticks([])
    axA.set_xticks([0, 5e3, 10e3, 15e3, 20e3])
    axA.set_xticklabels(["0", "5k", "10k", "15k", "20k"], fontsize=13)
    for s in ("top", "right", "left"):
        axA.spines[s].set_visible(False)
    axA.text(unchanged / 2, 0, f"Unchanged\n{unchanged:,.0f} km$^2$  (97.1%)", ha="center",
             va="center", fontsize=15, color="0.15")
    axA.annotate(f"Change: {change_total:,.0f} km$^2$  (2.9%)",
                 xy=(unchanged + change_total / 2, 0.30), xytext=(total, 0.95), ha="right",
                 va="bottom", fontsize=14, color="0.1",
                 arrowprops=dict(arrowstyle="-", color="0.4", lw=1.0))
    axA.set_xlabel("GLKN watershed area (km$^2$)", fontsize=15, loc="left")

    # ---- panel B: zoomed change-only stacked bar ----
    cumb = 0.0
    centers = {}
    for c in order:
        axB.barh(0, change_km2[c], left=cumb, color=AGENT_COLOR[c], edgecolor="black",
                 linewidth=0.8, height=0.55)
        centers[c] = cumb + change_km2[c] / 2
        cumb += change_km2[c]
    axB.set_xlim(0, change_total * 1.34)
    axB.set_ylim(-3.2, 0.9)
    axB.set_yticks([])
    axB.set_xticks([0, 200, 400, 600])
    axB.set_xticklabels(["0", "200", "400", "600"], fontsize=13)
    for s in ("top", "right", "left"):
        axB.spines[s].set_visible(False)
    axB.set_xlabel("Change-polygon area (km$^2$)", fontsize=15, loc="left")

    # direct labels; the three tiny classes go to the right margin with elbow leaders (never cross text)
    xr = change_total * 1.06
    lab = {
        "harvest": (centers["harvest"], -1.1, "center", -0.28),
        "development": (xr, -0.4, "left", -0.12),
        "beaver": (xr, -1.5, "left", -0.12),
        "insect_disease_mort": (xr, -2.6, "left", -0.12),
    }
    for a in order:
        name = AGENT_DISPLAY[a]
        lx, ly, ha, yanchor = lab[a]
        txt = f"{name}\n{change_km2[a]:,.1f} km$^2$  ({_pct(100*change_km2[a]/total)})"
        if a in ("development", "beaver", "insect_disease_mort"):
            axB.text(lx, ly, txt, ha=ha, va="top", fontsize=12.5, color="0.1")
            sx = centers[a]
            axB.plot([sx, sx, lx - change_total * 0.015], [yanchor, ly + 0.06, ly + 0.06],
                     color="0.5", lw=0.9, zorder=1, solid_capstyle="round", solid_joinstyle="round")
        else:
            axB.annotate(txt, xy=(centers[a], yanchor), xytext=(lx, ly), ha=ha, va="top",
                         fontsize=12.5, color="0.1", arrowprops=dict(arrowstyle="-", color="0.5", lw=0.9))

    # zoom funnel connecting the change sliver in A to the full width of B
    for xa, xb in [(unchanged, 0), (total, change_total)]:
        con = ConnectionPatch(xyA=(xa, -0.30), coordsA=axA.transData, xyB=(xb, 0.30),
                              coordsB=axB.transData, color="0.7", lw=1.0, linestyle=(0, (4, 3)))
        fig.add_artist(con)

    os.makedirs(OUT, exist_ok=True)
    fig.savefig(os.path.join(OUT, "pres_02c_watershed_rarity.png"), dpi=300, bbox_inches="tight")
    plt.close(fig)
    print("\nwrote pres_02c_watershed_rarity.png")


if __name__ == "__main__":
    main()
