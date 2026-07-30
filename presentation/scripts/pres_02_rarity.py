#!/usr/bin/env python3
"""pres_02_rarity: total change area by agent across the seven GLKN watersheds.

Defense-slide figure. One horizontal bar per change agent (harvest, development, beaver, and
insect/disease mortality) showing total mapped change area in km2, sorted descending, each bar
labeled directly with its area and polygon count. The point is the wide span between the most and
least common agent, and that all change together is a small fraction of the landscape. Two versions
are written, one log x axis and one linear x axis, so the presenter can pick.

All values are read from the source data. Agent areas and polygon counts come from the Table 3.3 CSV;
the total seven-watershed area is computed from the GLKN watershed boundary shapefile (EPSG:5070,
equal-area, so geometry area in square meters divides to km2). Nothing is hard-coded.

sizing: 10 x 5.6 in, the content area of a 16:9 slide (not full bleed).

outputs (png only):
  presentation/figures/pres_02_rarity.png (log x axis, primary)
  presentation/figures/pres_02_rarity_linear.png (linear x axis, alternative)
"""

import os

import geopandas as gpd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.transforms as mtransforms
import pandas as pd

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
CSV = os.path.join(ROOT, "manuscript_formatting", "chapter_3", "tables",
                   "chapter3_table_polygon_size_by_agent.csv")
SHP = os.path.join(ROOT, "data", "raw", "glkn", "GLKN_watershed_boundaries_7park_5070.shp")
LEGEND = os.path.join(ROOT, "data", "reference", "model_maps_10class_legend.csv")
OUT = os.path.join(ROOT, "presentation", "figures")

# change agent (as written in the polygon CSV) -> canonical 10-class code, for the shared palette
AGENT_CLASS = {"harvest": 1, "development": 2, "beaver": 9, "insect_disease_mort": 10}


def load_data():
    df = pd.read_csv(CSV)
    # keep only the four change agents, in case the CSV ever carries extra rows
    df = df[df["agent"].isin(AGENT_CLASS)].copy()
    df = df.sort_values("total_km2", ascending=False).reset_index(drop=True)

    leg = pd.read_csv(LEGEND).set_index("code")
    df["code"] = df["agent"].map(AGENT_CLASS)
    df["color"] = df["code"].map(leg["color"])
    df["label"] = df["code"].map(leg["display_name"])

    watershed_km2 = gpd.read_file(SHP).geometry.area.sum() / 1e6
    return df, watershed_km2


def _diagnostics(df, watershed_km2):
    total_change = df["total_km2"].sum()
    ratio = df["total_km2"].max() / df["total_km2"].min()
    print("change-agent totals (sorted descending):")
    for r in df.itertuples():
        print(f"  {r.label:<16} {r.total_km2:>8.2f} km2   {int(r.n_polys):>6,} polygons   color={r.color}")
    print(f"total change area:      {total_change:8.2f} km2")
    print(f"seven-watershed area:   {watershed_km2:8.2f} km2  (from {os.path.basename(SHP)})")
    print(f"change as fraction:     {100 * total_change / watershed_km2:.2f} % of the landscape")
    print(f"top-to-bottom ratio:    {ratio:.1f}x  ({df.label.iloc[0]} vs {df.label.iloc[-1]})")
    return total_change, ratio


def _style():
    plt.rcParams.update({
        "font.family": "sans-serif",
        "font.sans-serif": ["Helvetica", "Arial", "DejaVu Sans"],
        "font.size": 16,          # base, legible when projected
        "axes.linewidth": 1.0,
    })


def _bars(ax, df):
    # ascending y so the largest agent sits at the top, colored by the shared class palette
    order = df.iloc[::-1].reset_index(drop=True)
    y = range(len(order))
    ax.barh(list(y), order["total_km2"], height=0.62,
            color=order["color"], edgecolor="black", linewidth=0.9, zorder=3)
    ax.set_yticks(list(y))
    ax.set_yticklabels(order["label"], fontsize=16)
    ax.tick_params(axis="x", labelsize=15)
    for s in ("top", "right"):
        ax.spines[s].set_visible(False)
    ax.grid(False)
    return order


def _bar_labels(ax, order, mult=None, add=None):
    # direct label at each bar end: area and polygon count. log axes offset multiplicatively,
    # linear axes offset by a fixed amount
    for i, r in enumerate(order.itertuples()):
        x = r.total_km2 * mult if mult is not None else r.total_km2 + add
        ax.text(x, i, f"{r.total_km2:,.1f} km$^2$  ({int(r.n_polys):,} polygons)",
                va="center", ha="left", fontsize=15)


def make_log(df, watershed_km2, total_change, ratio):
    _style()
    fig, ax = plt.subplots(figsize=(10, 5.6))
    fig.subplots_adjust(left=0.18, right=0.97, top=0.90, bottom=0.15)
    order = _bars(ax, df)
    ax.set_xscale("log")
    ax.set_xlim(1, 40000)
    _bar_labels(ax, order, mult=1.15)
    ax.set_xlabel("Total mapped change area (km$^2$, log scale)", fontsize=18)

    # single reference: the whole seven-watershed area, so all change reads as a small sliver
    ax.axvline(watershed_km2, color="0.35", linestyle="--", linewidth=1.4, zorder=2)
    tb = mtransforms.blended_transform_factory(ax.transData, ax.transAxes)
    ax.text(watershed_km2, 1.02, f"seven-watershed area\n{watershed_km2:,.0f} km$^2$",
            transform=tb, ha="center", va="bottom", fontsize=14, color="0.35")

    # the rarity gradient, stated as the measured ratio, and the combined-change fraction
    ax.text(0.66, 0.30,
            f"{df.label.iloc[0]} covers ~{ratio:.0f}x\nthe {df.label.iloc[-1]} area",
            transform=ax.transAxes, ha="center", va="center", fontsize=15)
    ax.text(0.66, 0.12,
            f"all change combined = {total_change:,.0f} km$^2$\n({100 * total_change / watershed_km2:.1f}% of the landscape)",
            transform=ax.transAxes, ha="center", va="center", fontsize=14, color="0.35")

    _save(fig, "pres_02_rarity")


def make_linear(df, watershed_km2, total_change, ratio):
    _style()
    fig, ax = plt.subplots(figsize=(10, 5.6))
    fig.subplots_adjust(left=0.18, right=0.97, top=0.90, bottom=0.15)
    order = _bars(ax, df)
    ax.set_xlim(0, df["total_km2"].max() * 1.75)
    _bar_labels(ax, order, add=df["total_km2"].max() * 0.02)
    ax.set_xlabel("Total mapped change area (km$^2$)", fontsize=18)

    # placed in the open lower-right, clear of the harvest bar at top
    ax.text(0.97, 0.50,
            f"{df.label.iloc[0]} covers ~{ratio:.0f}x the {df.label.iloc[-1]} area",
            transform=ax.transAxes, ha="right", va="top", fontsize=15)
    # the seven-watershed total is far off this scale, so it is stated as text rather than drawn
    ax.text(0.97, 0.34,
            f"seven-watershed area = {watershed_km2:,.0f} km$^2$ (off scale)\n"
            f"all change combined = {total_change:,.0f} km$^2$, "
            f"{100 * total_change / watershed_km2:.1f}% of the landscape",
            transform=ax.transAxes, ha="right", va="top", fontsize=14, color="0.35")

    _save(fig, "pres_02_rarity_linear")


def _save(fig, stem):
    # pngs only, per the presentation figures convention
    os.makedirs(OUT, exist_ok=True)
    fig.savefig(os.path.join(OUT, f"{stem}.png"), dpi=300, bbox_inches="tight")
    plt.close(fig)
    print(f"wrote {stem}.png")


def main():
    df, watershed_km2 = load_data()
    total_change, ratio = _diagnostics(df, watershed_km2)
    make_log(df, watershed_km2, total_change, ratio)
    make_linear(df, watershed_km2, total_change, ratio)


if __name__ == "__main__":
    main()
