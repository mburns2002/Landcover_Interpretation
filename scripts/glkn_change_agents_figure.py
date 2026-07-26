#!/usr/bin/env python3
"""Two figures from the GLKN per-year change-agent EDA CSVs: total change area (hectares) and
polygon count per agent across the NAIP target years 2017 to 2020. Bars are colored by the canonical
class legend (harvest, development, beaver, insect/disease), grouped by year.

Reads reports/GLKN_change_agents/glkn_eda_changeagents_<year>.csv; writes change_area_by_agent.png
and change_count_by_agent.png next to them.

Run: python scripts/glkn_change_agents_figure.py
Requires: pandas, matplotlib
"""

import glob
import os
import sys
import textwrap

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import compare_interpreted_vs_model as C

DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                   "reports", "GLKN_change_agents")

# change agent (as written in the CSV) -> canonical class code, for the legend color and display name
AGENT_CLASS = {"harvest": 1, "development": 2, "beaver": 9, "insect_disease_mort": 10}
DISPLAY = {"harvest": "Harvest", "development": "Development", "beaver": "Beaver",
           "insect_disease_mort": "Insect/Disease"}
ORDER = ["harvest", "development", "beaver", "insect_disease_mort"]


def load():
    frames = [pd.read_csv(f) for f in sorted(glob.glob(os.path.join(DIR, "glkn_eda_changeagents_*.csv")))]
    df = pd.concat(frames, ignore_index=True)
    df["year"] = df["year"].astype(int)
    return df


def caption(fig, text, width=112):
    wrapped = "\n".join(textwrap.wrap(text, width))
    nlines = wrapped.count("\n") + 1
    fig.tight_layout(rect=[0, 0.03 + 0.03 * nlines, 1, 1])
    fig.text(0.5, 0.012, wrapped, ha="center", va="bottom", fontsize=9, color="0.3")


def grouped_bar(df, value_col, transform, ylabel, title, cap, out):
    colors = C.load_mappings()[2]                          # canonical class legend {code: color}
    years = sorted(df["year"].unique())
    x = np.arange(len(years))
    w = 0.8 / len(ORDER)                                   # bars share 0.8 of each year slot
    fig, ax = plt.subplots(figsize=(9, 5.5))
    for i, agent in enumerate(ORDER):
        vals = []
        for y in years:
            row = df[(df.year == y) & (df.agent == agent)]
            vals.append(transform(float(row[value_col].iloc[0])) if len(row) else 0.0)
        ax.bar(x + (i - (len(ORDER) - 1) / 2) * w, vals, w, label=DISPLAY[agent],
               color=colors[AGENT_CLASS[agent]], edgecolor="0.3", linewidth=0.6, zorder=3)
    ax.set_xticks(x)
    ax.set_xticklabels([str(y) for y in years], fontsize=11)
    ax.tick_params(axis="y", labelsize=11)
    ax.set_xlabel("NAIP Target Year", fontsize=12)
    ax.set_ylabel(ylabel, fontsize=12)
    ax.set_title(title, fontsize=15, fontweight="bold", pad=14)
    ax.grid(False)
    for s in ("top", "right"):
        ax.spines[s].set_visible(False)
    ax.legend(fontsize=11, frameon=False)
    caption(fig, cap)
    fig.savefig(out, dpi=300, bbox_inches="tight")
    plt.close(fig)
    print(f"wrote {out}")


def main():
    df = load()
    grouped_bar(
        df, "total_m2", lambda m2: m2 / 1e4,               # square meters -> hectares
        "Total Change Area (ha)",
        "GLKN Change-Agent Area by Year",
        "Total area of GLKN attributed change-agent polygons per year (2017 to 2020), one bar per "
        "change agent, colored by the canonical class legend. Area is summed over all attributed "
        "polygons for that agent and year and converted to hectares.",
        os.path.join(DIR, "change_area_by_agent.png"))
    grouped_bar(
        df, "n_polys", lambda n: n,
        "Number of Polygons",
        "GLKN Change-Agent Polygon Count by Year",
        "Count of GLKN attributed change-agent polygons per year (2017 to 2020), one bar per change "
        "agent, colored by the canonical class legend.",
        os.path.join(DIR, "change_count_by_agent.png"))


if __name__ == "__main__":
    main()
