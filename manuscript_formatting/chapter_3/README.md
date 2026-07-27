# Chapter 3

GLKN change-analysis outputs for Chapter 3 (the interpretation and validation-design chapter). Source
CSVs stay in `reports/GLKN_change_agents/`; the deliverables live here, organized into subfolders.

## Layout
- `figures/` — the rendered figures (PNG and PDF) and the figure caption md.
- `tables/` — the Chapter 3 tables (each as a tidy CSV, a PNG, and an editable DOCX).
- `sections/` — `chapter3_figures_and_outputs.md`, the working consolidation inventory for drafting.
- `plot_change_detection_rate.R` and `plot_polygon_size_distribution.R` — the R figure generators
  (the Python generators live in `scripts/`).

## Figures (`figures/`)
- `change_detection_rate_vs_cell_area_by_agent.{pdf,png}` and `..._combined.{pdf,png}`, plus their
  `_linear` companions — detection rate (fraction of complete cells with change) vs grid cell area,
  per agent and combined, on log and linear x axes. See `change_detection_rate_vs_cell_area_caption.md`.
  Made by `plot_change_detection_rate.R`.
- `change_area_by_agent.png` and `change_count_by_agent.png` — total change area (hectares) and
  polygon count per agent by year (2017 to 2020), colored by the canonical class legend. Made by
  `scripts/glkn_change_agents_figure.py`.
- `polygon_size_distribution_by_agent.{pdf,png}` — per-agent histograms of polygon area (log-10
  hectare axis, free y), 2010 to 2020. Made by `plot_polygon_size_distribution.R`.

## Tables (`tables/`)
`chapter3_table_detection_rate_by_cell_size`, `chapter3_table_complete_cell_counts_by_cell_size`, and
`chapter3_table_polygon_size_by_agent`. Made by `scripts/build_chapter3_tables.py`.

## Regenerate
```bash
Rscript manuscript_formatting/chapter_3/plot_change_detection_rate.R
Rscript manuscript_formatting/chapter_3/plot_polygon_size_distribution.R
python scripts/glkn_change_agents_figure.py
python scripts/build_chapter3_tables.py
```
