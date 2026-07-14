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

> Imagery source: Sentinel-2. Document the classification scheme / land cover legend,
> target years, and grid definitions here as they are finalized.

## License

No license specified yet. Add a `LICENSE` file to define usage terms.

## Contact

Maintained by [@mburns2002](https://github.com/mburns2002).
