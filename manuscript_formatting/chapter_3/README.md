# Chapter 3 figures

GLKN change-analysis figures for Chapter 3 (the interpretation and validation-design chapter). Source
CSVs stay in `reports/GLKN_change_agents/`; the figures and their generating scripts live here.

## Figures
- `change_detection_rate_vs_cell_area_by_agent.{pdf,png}` and `..._combined.{pdf,png}` — detection
  rate (fraction of complete cells with change) vs grid cell area, per agent and combined. See
  `change_detection_rate_vs_cell_area_caption.md`. Made by `plot_change_detection_rate.R` (in this
  folder).
- `change_area_by_agent.png` and `change_count_by_agent.png` — total change area (hectares) and
  polygon count per agent by year (2017 to 2020), colored by the canonical class legend. Made by
  `scripts/glkn_change_agents_figure.py` (reads the CSVs in `reports/GLKN_change_agents/`, writes
  here).
- `polygon_size_distribution_by_agent.{pdf,png}` — per-agent histograms of polygon area (log-10
  hectare axis, free y), 2010 to 2020. Made by `plot_polygon_size_distribution.R` (in this folder).

## Regenerate
```bash
Rscript manuscript_formatting/chapter_3/plot_change_detection_rate.R
python scripts/glkn_change_agents_figure.py
```
