# interpreted_cells_by_bracket.csv

Companion note for the GEE upload listing which CKIT-RF grid cells are interpreted for which NAIP bracket.

## Source

The classified interpretation rasters under `data/raw/rf_class_maps/`, one file per reviewer, cell, and bracket. Filenames were parsed with the pattern `reviewer_<name>_grid_<id>_sample_<n>_sensor_<sensor>_target_<year>_opt_<y1>_<y2>`. 254 rasters were found and parsed; no filename failed to parse.

## Bracket mapping

The `opt_<y1>_<y2>` field is the NAIP bracket, and it already uses the requested string form, so the mapping to the five in-scope brackets is the identity:

| source `opt_` field | bracket | matching target year |
|---|---|---|
| opt_2017_2019 | 2017_2019 | 2018 |
| opt_2018_2020 | 2018_2020 | 2019 |
| opt_2019_2021 | 2019_2021 | 2020 |
| opt_2020_2022 | 2020_2022 | 2021 |
| opt_2021_2023 | 2021_2023 | 2022 |

The bracket brackets the target year by plus or minus one, consistent with a NAIP acquisition window centered on the interpreted year.

## cell_id transformation

`cell_id` is the `grid_<id>` value converted to an integer, then zero-padded to a width-5 string (`str(int(id)).zfill(5)`), so it joins cleanly against the GEE asset `grid_112_naip_brackets_5_11_26`. The source ids are already width-5 numeric strings, so the transformation is effectively a no-op here, yet it is applied defensively so that an integer-typed or unpadded source would normalize identically. An unpadded or integer id would produce a silent zero-match join in GEE, so the padding is retained.

## Summary

- Total unique cells: 180
- Total rows (one per cell and bracket): 180

| bracket | unique cells | double-interpreted (collapsed) |
|---|---|---|
| 2017_2019 | 36 | 20 |
| 2018_2020 | 36 | 12 |
| 2019_2021 | 36 | 20 |
| 2020_2022 | 36 | 10 |
| 2021_2023 | 36 | 10 |

The brackets are balanced at 36 cells each.

## Cross-bracket overlap

Cells interpreted for all five brackets: **0**. Distribution of brackets per cell: {1: 180}. Every cell is interpreted for exactly one bracket, so the per-bracket cell sets are disjoint. A cross-bracket transferability comparison therefore runs on different cells per bracket, not a shared panel, so differences across brackets confound the classifier's temporal transfer with the differing cell composition. This is worth weighing before the GEE runs.

## Double interpretation

A subset of cells is interpreted by two reviewers for agreement measurement. Following the requirement, each such cell is listed once per bracket, so the CSV collapses that multiplicity. The collapsed counts per bracket are in the table above, and total 72 double-interpreted (cell, bracket) pairs.

## Records excluded

The following records fall outside the five in-scope brackets and are excluded from the CSV:

- `rf_class_reviewer_Robert_grid_17800_sample_16_sensor_Landsat_target_2004_opt_2003_2005_epsg5070.tif` (bracket 2003_2005, sensor Landsat, target 2004). This is the only record on a non-NAIP-bracket window and the only Landsat record, so it is out of scope for this experiment.

## Flagged ids (kept, not dropped)

- 65 cell ids exceed the 21561-cell study count (max `53151`). The interpretation records draw ids from a larger tiling than the 21561 active cells, so an id above 21561 is not by itself malformed, and grid membership cannot be confirmed from the records alone. These ids are retained; verify them against `grid_112_naip_brackets_5_11_26` in GEE, where a non-member id will simply fail to join. The ids: 22691, 22823, 23240, 23753, 24192, 24360, 24381, 25072, 25092, 26752, 26973, 28412, 28522, 29142, 29490, 29513, 29781, 30292, 30392, 30591, 31320, 32460, 32631, 32780, 34023, 34240, 35012, 35493, 36361, 36882, 37243, 39193, 39322, 39563, 40091, 40890, 41261, 42180, 42291, 43442, 43520, 44751, 44811, 45391, 45833, 46291, 46571, 47523, 47893, 47961, 48221, 48422, 48671, 48680, 48740, 48800, 49610, 50520, 50721, 50981, 51040, 51183, 51391, 52172, 53151.
