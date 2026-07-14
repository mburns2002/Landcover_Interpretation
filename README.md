# Landcover_Interpretation

Tools and workflows for interpreting and classifying land cover from remote sensing
imagery. This project supports processing satellite/aerial imagery, extracting
features, training and applying classification models, and producing land cover maps.

## Overview

Land cover interpretation is the process of assigning each area of an image to a
category such as water, forest, cropland, urban, or bare soil. This repository
collects the code, notebooks, and configuration used to:

- ingest and preprocess imagery (reprojection, clipping, cloud masking, band math)
- compute spectral indices and other features (e.g. NDVI, NDWI)
- label and manage training samples
- train and evaluate classifiers
- generate and export classified land cover maps

## Project structure

```
Landcover_Interpretation/
├── data/
│   ├── raw/          # original, immutable imagery and reference data
│   ├── interim/      # intermediate processed data
│   └── processed/    # analysis-ready datasets
├── notebooks/        # exploratory and reporting Jupyter notebooks
├── src/              # reusable source code
├── models/           # trained model artifacts
├── outputs/          # maps, figures, and results
└── README.md
```

> Note: large data and output folders are ignored by git (see `.gitignore`).
> Keep only small samples or references under version control.

## Getting started

### Prerequisites

- Python 3.10+
- A geospatial stack such as `rasterio`, `numpy`, `geopandas`, `scikit-learn`,
  and `matplotlib`

### Setup

```bash
# clone the repository
git clone https://github.com/mburns2002/Landcover_Interpretation.git
cd Landcover_Interpretation

# create and activate a virtual environment
python -m venv .venv
source .venv/bin/activate        # windows: .venv\Scripts\activate

# install dependencies (once requirements.txt exists)
pip install -r requirements.txt
```

## Usage

Workflow steps will be documented here as the project develops, for example:

```bash
# example placeholder commands
python src/preprocess.py --input data/raw --output data/processed
python src/classify.py   --input data/processed --model models/rf.joblib
```

## Data

The Random Forest classified rasters (`rf_class_*.tif`, one per grid sample) live in
a shared Google Drive folder and are pulled into `data/raw/rf_class_maps/`. These
files are git-ignored, so each user fetches their own local copy.

### Fetching the classified rasters (recommended: authenticated rclone)

The public share link is subject to Google's per-link download quota and will fail
partway through ("too many accesses"). The reliable path is authenticated rclone:

```bash
# one-time setup
brew install rclone                                   # or https://rclone.org/downloads/
rclone config create gdrive drive scope drive.readonly
# ^ opens a browser: sign in with the account that has the folder, click Allow.
#   if interrupted, finish with:  rclone config reconnect gdrive:

# fetch (safe to re-run; skips files already present)
python scripts/fetch_rf_class_maps_rclone.py
```

This copies every `rf_class*.tif` and then recovers any files that Drive stored under
duplicate-named folders (which a normal copy walk skips) by fetching them via file ID.
Expected result: **224 / 224** rasters (~5 MB).

### Alternative: public link via gdown (no login, quota-limited)

```bash
pip install gdown
python scripts/fetch_rf_class_maps.py --pause 1.5     # re-run to resume after rate limits
```

### Model maps (AlphaEarth Foundations, from GEE)

The 10-class classified maps exported from Google Earth Engine act as the model
maps to compare against the interpreted RF results. Each version is exported by GEE
as multiple GeoTIFF tiles; they download into `data/raw/model_maps/<version>/`.

```bash
python scripts/fetch_model_maps.py            # all versions (v2-v6, ~1.9 GB)
python scripts/fetch_model_maps.py --list     # show sizes, download nothing
python scripts/fetch_model_maps.py --versions v6
```

These are 10 m resolution, `uint8`, EPSG:5070, class values 0–10 (0 = background /
no-data padding). They share resolution (10 m) and CRS (EPSG:5070) with the 223
Sentinel-2 interpreted maps, so those need no resampling to compare — only a class
crosswalk. The single Landsat interpreted grid (`Robert_grid_17800`) is 30 m and
would need resampling.

> Imagery source: Sentinel-2 (223 grids @ 10 m, 337×337) plus one Landsat grid
> (30 m, 113×113). Rasters are single-band `int32` class maps, CRS EPSG:5070.
> Target years span 2004–2022.

### Classification scheme

Pixel values are land cover / disturbance class codes, decoded via
`data/reference/label_lookup.csv`:

| Code | Class | Type | Code | Class | Type |
|-----:|-------|------|-----:|-------|------|
| 0 | Urban | stable | 10 | Unknown | disturbance |
| 1 | Agriculture | stable | 20 | Harvest | disturbance |
| 2 | Grass/Shrub | stable | 30 | Development | disturbance |
| 3 | Forest | stable | 40 | Fire | disturbance |
| 4 | Water | stable | 50 | Insect/Disease | disturbance |
| 5 | Wetland | stable | 62 | Beaver | disturbance |
| 13 | Other | stable | | | |

## Analysis & visualization

`scripts/inspect_and_plot.py` inspects and visualizes the classified rasters
(requires `rasterio numpy matplotlib pandas`):

```bash
# metadata + class histogram for one raster
python scripts/inspect_and_plot.py --stats data/raw/rf_class_maps/<grid>/<file>.tif

# class distribution across all rasters (writes outputs/class_distribution.csv)
python scripts/inspect_and_plot.py --stats-all

# labelled map of one raster  ->  outputs/<name>.png
python scripts/inspect_and_plot.py --plot data/raw/rf_class_maps/<grid>/<file>.tif

# montage of the first N maps  ->  outputs/montage_N.png
python scripts/inspect_and_plot.py --montage 9
```

Figures are written to `outputs/` (git-ignored). Across the 224 rasters, Forest
(~52%), Agriculture (~16%), and Wetland (~11%) dominate; disturbance classes are a
small fraction of pixels.

## Inter-interpreter agreement

Some grid cells were independently interpreted by two reviewers (matched on grid id +
sample + target year). `scripts/compare_interpreters.py` compares each such pair
pixel-for-pixel (identical footprint, no reprojection) and reports overall agreement,
per-class F1/IoU, macro-F1, mean IoU, and Cohen's kappa, plus a
Reviewer A | Reviewer B | Agreement figure per pair.

```bash
python scripts/compare_interpreters.py               # all pairs
python scripts/compare_interpreters.py --limit 6     # quick preview
python scripts/compare_interpreters.py --no-figures  # metrics only
```

Outputs go to `outputs/interpreter_agreement/` (per-pair PNGs, `per_pair_metrics.csv`,
`by_reviewer_pair.csv`, pooled confusion matrix, `global_metrics.txt`).

Across the 69 double-labeled cells, mean per-pair agreement is 0.77 (kappa 0.60).
Reviewers agree strongly on unambiguous classes (Water 0.90, Forest 0.89,
Agriculture 0.83 on the confusion diagonal) and diverge on transitional/disturbance
classes (Grass/Shrub, Wetland, Development, Insect/Disease, Beaver) — e.g. one
reviewer's Insect/Disease is called Forest by the other 71% of the time. Agreement
also varies by reviewer pairing (mina-robert 0.87 highest; bekka-mina 0.72 lowest).

`scripts/disagreement_summary.py` post-processes those results into (a) the class
boundaries driving the most disagreement and (b) the lowest-agreement pairs flagged
for manual review:

```bash
python scripts/disagreement_summary.py --worst 12 --flag-below 0.70
```

It writes `class_disagreement_ranked.csv`, `per_class_contested.csv`,
`class_disagreement_top.png`, `lowest_agreement_pairs.csv`, and
`flagged_pairs_for_review.csv`. Just four boundaries account for ~68% of all
disagreement: Forest↔Wetland (22%), Agriculture↔Grass/Shrub (17%),
Grass/Shrub↔Forest (14%), and Grass/Shrub↔Wetland (14%). 17 pairs fall below 0.70
overall agreement (worst: grid 10333 bekka-vs-mina, 0.48).

To browse every pair figure in VSCode, `scripts/pairs_contact_sheet.py` stacks them
into paginated overview PNGs (sorted lowest-agreement first), or opens an arrow-key
browser:

```bash
python scripts/pairs_contact_sheet.py                 # all pairs -> montage_page_*.png
python scripts/pairs_contact_sheet.py --flagged-below 0.70   # -> montage_flagged_page_*.png
python scripts/pairs_contact_sheet.py --interactive   # Left/Right arrows, q to quit
```

Open the resulting `montage_page_*.png` in VSCode's image viewer and scroll.

## Interpreted vs. model comparison

`scripts/compare_interpreted_vs_model.py` compares each interpreted Sentinel-2 cell
against the AlphaEarth model maps. Per cell it stitches the model tiles, clips to the
cell frame (both 10 m / EPSG:5070, nearest-neighbour, no resampling), crosswalks both
to the common 10-class scheme, and computes a confusion matrix with per-class
precision/recall/F1/IoU plus overall accuracy, macro-F1, mean IoU, and Cohen's kappa.
It also renders an Interpreted | Model | Agreement figure per cell.

```bash
python scripts/compare_interpreted_vs_model.py               # all cells, v2-v6
python scripts/compare_interpreted_vs_model.py --versions v2 # one version
python scripts/compare_interpreted_vs_model.py --targets 2019 # date-aligned subset
python scripts/compare_interpreted_vs_model.py --limit 6     # quick preview
python scripts/compare_interpreted_vs_model.py --no-figures  # metrics only
```

**De-duplication:** some locations were labeled by multiple reviewers. By default the
comparison keeps one randomly-chosen interpretation per location (grid + sample +
target), seeded for reproducibility (`--seed`), so a location is never double-counted.
Use `--keep-duplicates` for the old every-raster behavior. De-duplication trims the
all-years set from 223 rasters to 154 locations (and the 2019 subset from 41 to 30);
pooled metrics barely change (v2 OA 0.651 -> 0.657), confirming the double-counting
was not materially biasing results.

**Date alignment:** the model maps are a 2018-2020 composite (bracket year 2019).
Only interpreted cells with target year 2019 share that optical window, so
`--targets 2019` restricts the comparison to the temporally-matched cells (30 after
de-dup) and writes to `outputs/comparison_<version>_target2019/`. Doing so raises
agreement for every smooth version (e.g. v2 OA 0.66 -> 0.72; v4 gains the most).

Outputs go to `outputs/comparison_<version>/` (per-cell PNGs, confusion matrix,
`per_cell_metrics.csv`, `global_metrics.txt`) plus `outputs/comparison_summary_by_version.csv`.

Model versions v2-v5 are spatially-smooth classifiers; v6 is the speckly dot-product
classifier (reported via a per-version "neighbor-change" value: ~0.08 smooth, ~0.83
per-pixel). Pooled over all 223 cells, agreement is strongest for v2 (OA 0.65,
kappa 0.52) and lowest for the v6 dot-product map (OA 0.19). Stable classes agree
well (Water F1 0.93, Forest 0.79, Agriculture 0.78); small disturbance classes
(harvest, development, insect/disease, beaver) largely get absorbed into the
dominant stable classes by the model.

## License

No license specified yet. Add a `LICENSE` file to define usage terms.

## Contact

Maintained by [@mburns2002](https://github.com/mburns2002).
