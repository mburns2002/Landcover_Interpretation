# Reports

Curated summary artifacts so results are viewable on GitHub without regenerating
them. The full per-cell/per-pair figures live in `outputs/` (git-ignored); rerun the
scripts in `scripts/` to reproduce everything.

## interpreter_agreement/ — inter-interpreter agreement

Same grid cell independently labeled by two reviewers (69 pairs).
Source: `scripts/compare_interpreters.py` + `scripts/disagreement_summary.py`.

- `per_pair_metrics.csv` — one row per reviewer pair (agreement, F1, IoU, kappa)
- `by_reviewer_pair.csv` — mean agreement grouped by reviewer pairing
- `class_disagreement_ranked.csv` — class boundaries ranked by disagreement pixels
- `per_class_contested.csv` — per-class self-agreement and contested pixels
- `lowest_agreement_pairs.csv` / `flagged_pairs_for_review.csv` — pairs to review
- `global_metrics.txt` — pooled metrics
- `global_confusion_matrix.png`, `class_disagreement_top.png` — key figures

Headline: mean per-pair agreement **0.77** (kappa 0.60). Reviewers agree on
Water/Forest/Agriculture; four boundaries drive ~68% of disagreement
(Forest↔Wetland, Agriculture↔Grass/Shrub, Grass/Shrub↔Forest, Grass/Shrub↔Wetland).

## model_comparison/ — interpreted vs. AlphaEarth model maps

Each interpreted Sentinel-2 cell vs. the model maps (v2–v6).
Source: `scripts/compare_interpreted_vs_model.py`.

- `comparison_summary_by_version.csv` — OA / macro-F1 / mean IoU / kappa per version (all target years)
- `v2_global_confusion_matrix.png`, `v2_global_metrics.txt` — best-agreeing version
- `comparison_summary_by_version_target2019.csv` — **date-aligned** run (see below)
- `v2_target2019_confusion_matrix.png`, `v2_target2019_metrics.txt`

Headline (de-duplicated, all years): agreement is strongest for v2 (OA 0.66,
kappa 0.53) and lowest for the v6 dot-product map (OA 0.19). Stable classes agree
well (Water, Forest, Agriculture); small disturbance classes get absorbed into
stable classes.

### De-duplication of repeated locations

Some locations were interpreted by multiple reviewers. The comparison de-duplicates
by default — keeping one randomly-chosen interpretation per location (grid + sample +
target), seeded for reproducibility — so no location is double-counted. This trims the
all-years set from 223 rasters to **154 locations** (and the 2019 subset from 41 to
**30**). Pooled metrics barely change (v2 OA 0.651 → 0.657), so the earlier
double-counting was not materially biasing the numbers. All figures below reflect the
de-duplicated runs.

### Date alignment (target year 2019)

The model maps are a 2018–2020 GEE composite (bracket year 2019). Only interpreted
cells with **target year 2019** share that exact optical window (2018–2020); other
target years use offset windows and are temporally misaligned. Restricting to the 30
date-aligned, de-duplicated cells (`--targets 2019`) raises agreement for every smooth
version:

| version | OA (all years) | OA (2019) | ΔOA |
|---------|:---:|:---:|:---:|
| v2 | 0.66 | 0.72 | +0.06 |
| v3 | 0.61 | 0.69 | +0.09 |
| v4 | 0.51 | 0.64 | +0.13 |
| v5 | 0.56 | 0.64 | +0.07 |
| v6 | 0.19 | 0.19 | +0.01 |

Temporal mismatch was inflating disagreement (v4 gains the most, +0.13). v6 is
unchanged because its per-pixel speckle dominates regardless of date.

### Model-map spatial speckle (`scripts/model_speckle.py`)

`neighbor_change` = fraction of horizontally-adjacent, both-valid pixel pairs whose
class differs, computed over the **full rasters** (~2.43 billion pairs each; low =
smooth patches, high = per-pixel speckle). See `model_speckle.csv` and plots
`model_speckle_bar.png`, `model_speckle_vs_accuracy.png`, `model_speckle_crops.png`.

| version | neighbor_change | character |
|---------|:---:|-----------|
| v2 | 0.075 | smooth |
| v3 | 0.077 | smooth |
| v5 | 0.091 | smooth |
| v4 | 0.135 | mostly smooth |
| v6 | 0.781 | speckly (dot-product) |

Speckle is inversely related to agreement with the interpretations: the smooth maps
(v2/v3/v5) score highest, the speckly v6 lowest — so v6's low OA partly reflects its
per-pixel format, not only its accuracy.

### Spatial structure — patch size & Moran's I (`scripts/spatial_structure.py`)

`neighbor_change` separates v6 but not v2/v3/v5. Two richer diagnostics, computed on
both the model maps and the interpreted cells (measured within the same cell
footprints, so the interpretations set the reference scale):

- **mean patch size per class** — 8-connected component labeling on each class mask.
- **Moran's I** — spatial autocorrelation of the class raster (queen contiguity).
  (Class codes are nominal, so read this as a smoothness diagnostic, not autocorrelation
  of a meaningful variable.)

Files: `spatial_structure_summary.csv`, `patch_size_by_class.csv`, and plots
`patch_size_ecdf.png`, `patch_size_hist_smallmultiples.png`,
`mean_patch_size_by_class.png`, `morans_i_by_source.png`.

| source | mean patch (ha) | Moran's I |
|--------|:---:|:---:|
| **interpreted (ref)** | **0.79** | **0.75** |
| v2 | 1.13 | 0.82 |
| v3 | 1.18 | 0.82 |
| v4 | 0.42 | 0.71 |
| v5 | 0.97 | 0.81 |
| v6 | 0.024 | 0.09 |

Patch size (unlike neighbor_change) discriminates the smooth variants: ordered by
grain, v6 (speckle) < v4 (fragmented) < **interpreted** < v5 < v2 < v3 (over-smoothed).
v5 is closest to the interpreted scale; v2/v3 over-smooth the large classes most
(Water patches 6–8 ha vs. the interpreted 2.2 ha; Agriculture ~5 ha vs. ~1 ha). Moran's I
mainly isolates v6 (0.09) and mildly v4 (0.71); v2/v3/v5 cluster near 0.82.
