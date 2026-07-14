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

- `comparison_summary_by_version.csv` — OA / macro-F1 / mean IoU / kappa per version
- `v2_global_confusion_matrix.png`, `v2_global_metrics.txt` — best-agreeing version

Headline: agreement is strongest for v2 (OA 0.65, kappa 0.52) and lowest for the
v6 dot-product map (OA 0.19). Stable classes agree well (Water F1 0.93, Forest 0.79,
Agriculture 0.78); small disturbance classes get absorbed into stable classes.

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
