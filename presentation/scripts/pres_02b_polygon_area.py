#!/usr/bin/env python3
"""pres_02b_polygon_area: total change-polygon area by agent, horizontal bars.

Secondary rarity figure. Four horizontal bars of total change-polygon area in km2 by agent, linear
scale, sorted descending, each labeled with its area and polygon count. No fitted lines, no log axis.

Data sources (all local CSVs, no Earth Engine):
  full span 2010-2020:  reports/GLKN_change_agents/glkn_polygon_area_by_agent_2010_2020.csv
                        (the Table 3.3 source; already aggregated per agent, no year column)
  restricted 2018-2020: reports/GLKN_change_agents/glkn_eda_changeagents_{2018,2019,2020}.csv summed
                        (the upstream per-year files carry a year attribute, so 2018-2020 is available)

The upstream carries a year attribute, so two variants are written: the full 2010-2020 span and a
2018-2020 span aligned with the 2018/2020 classification window. Both totals are printed to the
console. The 2018-2020 variant is summed across the separate per-year extraction, so it is on a
slightly different basis than the 2010-2020 aggregate; see the message.

sizing: 10 x 5.6 in, the content area of a 16:9 slide.

outputs (png only):
  presentation/figures/pres_02b_polygon_area.png            (2010-2020)
  presentation/figures/pres_02b_polygon_area_2018_2020.png  (2018-2020)
"""

import os

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

import slide_font
import pandas as pd

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
D = os.path.join(ROOT, "reports", "GLKN_change_agents")
OUT = os.path.join(ROOT, "presentation", "figures")

AGENT_DISPLAY = {"harvest": "Harvest", "development": "Development",
                 "beaver": "Beaver", "insect_disease_mort": "Insect/Disease"}
AGENT_COLOR = {"harvest": "yellow", "development": "red", "beaver": "orange",
               "insect_disease_mort": "#70A2DB"}


def _load_full():
    df = pd.read_csv(os.path.join(D, "glkn_polygon_area_by_agent_2010_2020.csv"))
    return {r.agent: (r.total_m2 / 1e6, int(r.n_polys)) for r in df.itertuples()}


def _load_2018_2020():
    agg = {}
    for y in (2018, 2019, 2020):
        df = pd.read_csv(os.path.join(D, f"glkn_eda_changeagents_{y}.csv"))
        for r in df.itertuples():
            km, n = agg.get(r.agent, (0.0, 0))
            agg[r.agent] = (km + r.total_m2 / 1e6, n + int(r.n_polys))
    return agg


def _plot(data, title, stem):
    rows = sorted(((AGENT_DISPLAY[a], km, n, AGENT_COLOR[a]) for a, (km, n) in data.items()),
                  key=lambda t: t[1], reverse=True)
    order = list(reversed(rows))   # ascending so the largest sits at the top
    y = range(len(order))

    plt.rcParams.update({"font.family": "sans-serif",
                         "font.sans-serif": ["Helvetica", "Arial", "DejaVu Sans"],
                         "font.size": 16, "axes.linewidth": 1.0})
    slide_font.use_spectral()
    fig, ax = plt.subplots(figsize=(10, 5.6))
    fig.subplots_adjust(left=0.16, right=0.97, top=0.88, bottom=0.15)
    ax.set_title(title, fontsize=19, fontweight="bold", pad=12)

    vals = [r[1] for r in order]
    ax.barh(list(y), vals, height=0.62, color=[r[3] for r in order],
            edgecolor="black", linewidth=0.9, zorder=3)
    ax.set_yticks(list(y))
    ax.set_yticklabels([r[0] for r in order], fontsize=16)
    ax.set_xlim(0, max(vals) * 1.32)
    off = max(vals) * 0.015
    for i, (_name, km, n, _c) in enumerate(order):
        ax.annotate(f"{km:,.1f} km$^2$  ({n:,} polygons)", (km, i), xytext=(off, 0),
                    textcoords="offset points", va="center", ha="left", fontsize=14)
    ax.set_xlabel("Total change-polygon area (km$^2$)", fontsize=18)
    ax.tick_params(axis="x", labelsize=14)
    ax.grid(False)
    for s in ("top", "right"):
        ax.spines[s].set_visible(False)

    os.makedirs(OUT, exist_ok=True)
    fig.savefig(os.path.join(OUT, f"{stem}.png"), dpi=300, bbox_inches="tight")
    plt.close(fig)
    print(f"wrote {stem}.png")


def main():
    full = _load_full()
    r2020 = _load_2018_2020()

    for label, data in [("2010-2020 (full)", full), ("2018-2020 (restricted)", r2020)]:
        print(f"total change-polygon area by agent, {label}:")
        for a in ("harvest", "development", "beaver", "insect_disease_mort"):
            km, n = data[a]
            print(f"  {AGENT_DISPLAY[a]:<16} {km:8.2f} km2   {n:6,} polygons")
        print(f"  {'sum':<16} {sum(v[0] for v in data.values()):8.2f} km2   "
              f"{sum(v[1] for v in data.values()):6,} polygons")

    _plot(full, "Total Change Area by Agent, 2010-2020", "pres_02b_polygon_area")
    _plot(r2020, "Total Change Area by Agent, 2018-2020", "pres_02b_polygon_area_2018_2020")


if __name__ == "__main__":
    main()
