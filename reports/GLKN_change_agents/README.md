# GLKN_change_agents

Per-year exploratory summaries of the GLKN attributed change-agent polygons, one file per NAIP target
year (2017 to 2020). Source: the shared Google Drive folder `GLKN_GRID_CHANGE_ANALYSIS`, pulled
2026-07-26 (originals also in `data/raw/glkn/change_analysis/`).

## Files
`glkn_eda_changeagents_<year>.csv` — one row per change agent, with polygon-area statistics for that
year's attributed polygons.

## Columns
| column | meaning |
|---|---|
| `system:index` | Earth Engine row index |
| `agent` | change agent: `harvest`, `development`, `beaver`, `insect_disease_mort` |
| `n_polys` | number of attributed polygons |
| `total_m2` | total polygon area (square meters) |
| `mean_m2`, `median_m2`, `min_m2`, `max_m2` | per-polygon area statistics (square meters) |
| `year` | NAIP target year |
| `.geo` | geometry field, empty here (MultiPoint with no coordinates) |

These look like Earth Engine aggregation exports (area stats per agent per year), useful for
describing how much of each change type is present in the GLKN reference by year.
