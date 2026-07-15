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
- `per_class_agreement_ci.csv` + `per_class_agreement_table.md` / `.tex` +
  `per_class_agreement_forest.png` — **per-class F1 with bootstrap CIs** (manuscript table)
- `pairs/` — all 69 per-pair side-by-side figures (`<grid>_<revA>_vs_<revB>.png`:
  Reviewer A | Reviewer B | Agreement)
- `flagged_pairs/` — the 17 pairs below 0.70 agreement, rank-prefixed (`01_…` =
  lowest agreement) so they sort worst-first, matching `flagged_pairs_for_review.csv`
- `geometry/` — geometry of disagreement per **directed** class pair (see below)

Headline: mean per-pair agreement **0.77** (kappa 0.60). Reviewers agree on
Water/Forest/Agriculture; four boundaries drive ~68% of disagreement
(Forest↔Wetland, Agriculture↔Grass/Shrub, Grass/Shrub↔Forest, Grass/Shrub↔Wetland).

**Per-class reliability with CIs** (`scripts/interpreter_class_ci.py`): per-class F1 with
95% cluster (pair) bootstrap CIs — the resampling unit is the pair, not the pixel, since
pixels within a cell are autocorrelated. High: Water 0.92 (0.86–0.95), Forest 0.90
(0.88–0.91), Agriculture 0.78 (0.72–0.82). **Low (unreliable reference): Wetland 0.47
(0.37–0.55), Grass/Shrub 0.30 (0.23–0.36)**, plus the rare disturbance classes. Any model
scored against a single interpretation of Grass/Shrub or Wetland is bounded by reference
noise, not just model error, and should be reported with that caveat.

**Spatial-tolerance diagnostic** (`scripts/spatial_tolerance.py`): separates
boundary-misregistration disagreement from conceptual disagreement. Per class, agreement is
recomputed under relaxed matching (a pixel matches if its class appears anywhere in the k×k
neighborhood of the other reviewer's map), directionally (dilate B for A→B, dilate A for
B→A — asymmetric, reported separately, NOT a confusion matrix). The reported quantity is the
per-class **delta = relaxed − strict, above a heterogeneity null** (B's dilated masks shifted
3–5 px to estimate chance recovery from local class composition), with cluster (pair)
bootstrap CIs, all randomness `default_rng(42)`. Both k=3 and k=5 are run. **No relaxed
overall accuracy is produced — this is a diagnostic of where disagreement is edge-driven, not
a corrected accuracy.** Files: `spatial_tolerance_delta.csv`, `spatial_tolerance_delta.png`.

Findings (A→B): only **Development (+0.083) and Urban (+0.042)** recover significantly above
the null — small built features whose disagreement is boundary misregistration. **Grass/Shrub
(+0.013) and Wetland (+0.009) do not move above null** (CI includes 0) → conceptual
disagreement, independently confirming the training-conflict result. Forest/Agriculture/Water
go slightly negative (already ~0.9 strict; residual disagreement is scattered specks, and for
these dominant classes the heterogeneity null exceeds the observed recovery). Nothing keeps
climbing from 3×3 to 5×5 (every 5×5 delta ≤ its 3×3), so there is no gross (>1 px)
misregistration — the edge effects that exist are sub-pixel/one-pixel. The two directions are
asymmetric (e.g. Urban recovers A→B but not B→A), as expected.

**Directional asymmetry / reviewer bias** (`scripts/reviewer_directional_asymmetry.py`):
tests whether the top-10 "mina=Wetland vs partner=Grass/Shrub" direction generalizes. Across
all 69 pairs, the full directed confusion is pooled per reviewer in pixels (area, not patch
count); the over-assignment index = log2((px R claims class C, partner doesn't + 1)/(px
partner claims C, R doesn't + 1)), with cluster (pair) bootstrap CIs (seed 42). Files:
`reviewer_class_overassignment.csv`, `reviewer_directed_classpairs.csv`,
`reviewer_overassignment_heatmap.png`.

Directional asymmetry **does generalize** — reviewers carry systematic class leanings (95% CI
excludes 0): **mina over-assigns Agriculture (+1.97) and Water (+1.75); bekka over-assigns
Insect/Disease (+6.46), Harvest (+1.76), Urban (+1.55); ash over-assigns Water (+2.75)**. On
the Grass/Shrub↔Wetland boundary specifically there is a reviewer "wetness" axis: robert
(+2.85) and bekka/mina (mild, +0.28/+0.19) lean Wetland, while ash (+0.63) and peter (+1.64)
lean Grass/Shrub — so the top-10 pattern was mina (mildly wet) meeting ash (GS-leaning), not
mina being the extreme. Caveat: the index is relative to comparison partners and the pairing
graph is unbalanced (bekka↔mina share 22 pairs), so paired reviewers' indices are two views of
the same contrast (mina +Agriculture mirrors bekka −Agriculture). Rare-class extremes
(Beaver, Unknown) are unstable and mostly not significant.

**Geometry of disagreement** (`scripts/disagreement_geometry.py`, in `geometry/`): per
DIRECTED class pair (reviewer_a said A, reviewer_b said B — direction kept, not
symmetrized), the per-cell disagreement mask is 8-connected-labeled and each patch is
measured for area, 4-connected perimeter (single pixel = 4), perimeter/area, and shape
index P/(2√(πA)). Agreement areas get the same geometry as a reference (the size of the
features being mapped). No de-duplication — the 69 replicate pairs are the point.
Files: `patch_geometry.csv` (one row per patch: cell_id, reviewer_a/b, class_a/b, patch_id,
area_px, area_ha, perimeter, pa_ratio, shape_index, width_px, touches_edge, kind),
`patchpair_summary.csv` (per pair × {all, interior}: n, area median/IQR, shape median,
fraction of disagreement area < / ≥ 0.1 ha), `width_distribution.csv`, and ECDF plots
`area_ecdf_focus.png`, `shape_index_ecdf_focus.png`, `width_ecdf.png`.

Findings: disagreement is overwhelmingly a thin-ribbon phenomenon at the resolution limit
— **93% of disagreement patches are ≤ 1 px wide, 99% ≤ 2 px** (median width 0.5 px) — and
disagreement patches are consistently smaller than the agreed features of the same classes
(disagreement ECDF sits left of the agreement reference). By *area* it flips: only ~17–45%
of disagreement area is in sub-0.1 ha patches for the major boundaries, so a minority of
larger patches holds most of the disagreed area. Traps handled: border-touching patches are
flagged and summaries reported with/without them (they barely move the distributions), and
the per-patch pixel width is reported to make the resolution-limit share explicit. Shape
index clusters ~1.13–1.20 (compact to slightly crenulated), consistent with boundary slivers.

**Area-weighted / size-conditional** (`scripts/disagreement_geometry_bysize.py`): the pooled
shape index ~1.13–1.20 is an artifact of single-pixel specks (a 1×1 patch has shape index
1.128). Weighting by area and conditioning on size overturns the "thin ribbon" reading for
the patches that hold the area. For **≥0.1 ha patches**, shape index rises to count-median
~2.2 and **area-weighted median ~3.7–6.1**, extent (area / bbox area) is ~0.42 (elongated,
not compact), and area-weighted width is ~2–3 px. For **Grass/Shrub↔Wetland**, the 10 largest
disagreement patches are **30–120 ha**, 3–7 px wide, shape index **6–12**, extent ~0.3 — and
the render (`gs_wetland_top10.png`) shows they are **large, irregular, mosaic-like zones**
where one reviewer mapped Grass/Shrub and the other Wetland across whole landscape units, not
thin margin ribbons and not compact interior blocks. So the disagreement has two regimes:
pixel-edge speckle (most of the count) and systematic large-area class-definition differences
(most of the area). Files: `size_conditional_summary.csv`, `gs_wetland_top10.csv`,
`shape_index_area_weighted_ecdf.png`, `gs_wetland_top10.png`.

**Training-label check** (`scripts/training_polygon_overlay.py`): for the cells holding the
10 largest GS↔Wetland patches, both reviewers' interpreter training data (the
`samples_generated` point sidecars — dense pixels from the drawn training polygons, with a
`class`/`labelId`) is overlaid on each patch to test whether the disagreement is a training
conflict or model extrapolation. Result: **6 of 10 are direct training conflicts** — both
reviewers placed training *inside* the zone (0 m) but labeled it differently (e.g. the 121 ha
patch: bekka trained Grass/Shrub, mina trained Wetland); **3 are one-sided** (only one reviewer
trained there, the other's nearest training 79–685 m away, so its RF extrapolated); **1 is pure
extrapolation** (neither trained in the zone). So the biggest GS↔Wetland disagreements are
genuine, encoded-in-the-labels class-definition conflicts over wet-meadow/wetland transitional
ground, not model noise. Files: `gs_wetland_training_overlay.csv` (per patch: points-in-zone
and nearest-training distance per reviewer, class breakdown, category),
`gs_wetland_training_overlay.png` (training points over the side-by-side maps, patch outlined).
Source `samples_generated` shapefiles are fetched via rclone into `data/raw/samples_generated/`
(git-ignored).

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

### Selection sensitivity (`scripts/dedup_sensitivity.py`)

Many locations were interpreted by two reviewers; the comparison keeps one. This test
repeats the "pick one interpretation per location" draw 100 times with different random
selections and reports the metric distribution per version (`dedup_sensitivity_runs.csv`,
`dedup_sensitivity_summary.csv`, `dedup_sensitivity_box.png`). The result is a robustness
check: the choice barely matters.

| version | OA mean ± std | OA range (min–max) |
|---------|:---:|:---:|
| v2 | 0.657 ± 0.002 | 0.652–0.661 |
| v3 | 0.606 ± 0.002 | 0.602–0.610 |
| v4 | 0.507 ± 0.002 | 0.502–0.512 |
| v5 | 0.564 ± 0.002 | 0.560–0.568 |
| v6 | 0.186 ± 0.000 | 0.185–0.187 |

Across 100 random selections the OA range per version is ≈0.01 and the version ranking
(v2 > v3 > v5 > v4 > v6) never changes — so the arbitrary choice of which reviewer's
interpretation is used at each double-labeled location does not affect the conclusions.

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
