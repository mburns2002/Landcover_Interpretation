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

Describe the imagery sources, dates, resolution, and classification scheme here
(e.g. Sentinel-2, Landsat, NAIP; and the land cover legend used).

## License

No license specified yet. Add a `LICENSE` file to define usage terms.

## Contact

Maintained by [@mburns2002](https://github.com/mburns2002).
