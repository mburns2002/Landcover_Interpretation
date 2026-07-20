# Reports

Curated summary artifacts so results are viewable on GitHub without regenerating
them. The full per-cell/per-pair figures live in `outputs/` (git-ignored); rerun the
scripts in `scripts/` to reproduce everything.

Every `.png` here has an explanation rendered directly beneath the figure (title, axes,
metric definition, why it exists, how to interpret) — visible when you open the image.
The same text is also embedded in the PNG metadata (read with `exiftool <file>` or
`from PIL import Image; Image.open(p).text["Description"]`). Regenerating a figure
overwrites it without the caption; re-apply with `python scripts/annotate_figures.py`
(idempotent — a `Captioned` flag prevents stacking).

## Embedding variants (v2–v6)

The model maps `v2`–`v6` are one Random Forest classified on different AlphaEarth embedding feature
sets. From the Earth Engine definition below, **2018 is the base year**: read `img2018` as the
base-year embedding and `img2020` as the paired-year embedding (here the 2018/2020 training window),
`delta` as the change between them, and `dot` as the dot-product feature. In the temporally-matched
runs the base and paired years shift per NAIP bracket, so "2018/2020" generalizes to
"base/paired year".

```js
var variants = {
  v2: { img: img2018.addBands(delta) },    // 2018 + delta
  v3: { img: img2018.addBands(img2020) },  // 2018 + 2020
  v4: { img: delta },                      // delta only
  v5: { img: img2018.addBands(dot) },      // 2018 + dot
  v6: { img: dot },                        // dot only
};
```

| variant | embedding features (base = 2018, paired = 2020) | note |
|---|---|---|
| v2 | base + delta | smooth, most faithful to abundance |
| v3 | base + paired | smooth |
| v4 | delta only | mostly smooth, overfits the base/paired window (poor temporal transfer) |
| v5 | base + dot | smooth |
| v6 | dot only | speckly per-pixel (dot-product); low autocorrelation, weak abundance signal |

## interpreter_agreement/ — inter-interpreter agreement

The interpreted set is **180 locations** (108 single-reviewer, 72 multi-reviewer: 71 double plus
one mina/peter/robert triple), 36 cells per NAIP bracket across 2017_2019–2021_2023. Inter-
interpreter agreement scores the 72 multi-reviewer cells as 72 pairs (the triple as its first
mina-peter pair).
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
- `pairs/` — all 72 per-pair side-by-side figures (`<grid>_<revA>_vs_<revB>.png`:
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
all 72 pairs, the full directed confusion is pooled per reviewer in pixels (area, not patch
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
features being mapped). No de-duplication — the 72 replicate pairs are the point.
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

**Change/change type conflicts** (`scripts/interpreter_change_change_conflicts.py`, in
`change_change_conflicts/`): pixels where both reviewers called change but disagreed on which
change type. Change classes in the RF scheme are Harvest (20), Development (30), Insect/Disease
(50), Beaver (62); Fire (40) has zero pixels. **Unknown (10) is excluded** — it is unattributed
disturbance, so Unknown-vs-Harvest is one reviewer declining to attribute, not a type conflict;
Unknown-vs-change is reported separately. Across the 72 double-interpreted cells, 8-connected
patches are labeled per cell. Files: `change_change_pixels_long.csv` (one row per cell × reviewer
pair × directed class pair), `ordered_pairs.csv` (directed and symmetrized change-class pair
totals), `change_change_patches.csv` (one row per connected patch), `summary.txt`.

Findings: this is **small, as expected** — change is ~1.5% of pixels and most change-class
disagreement goes to *stable* classes, not to other change classes. **Total conflict is 2,551 px
= 25.5 ha across all pairs: 0.14% of all disagreement and 1.30% of all change-labeled pixels.**
Only 16 of 72 cells carry any. It is overwhelmingly scattered single pixels (748 patches, median
1 px, max 2.45 ha). Symmetrized, **Insect/Disease↔Beaver dominates (15.5 ha)** — and a single
cell (grid 10333, bekka vs mina) holds 1,548 of those 1,549 px — followed by Harvest↔Insect/
Disease (8.2 ha); all others are <1.1 ha. Unknown-vs-change is a separate 519 px (5.2 ha).
Reviewer A/B ordering is alphabetical and arbitrary, so the directed counts carry no meaning on
their own; the symmetrized totals are the reviewer-order-independent numbers.

**Change/stable conflicts** (`scripts/interpreter_change_stable_conflicts.py`, in
`change_stable_conflicts/`): the counterpart, pixels where one reviewer called an attributed change
class and the other called a stable class (either direction). Stable classes are Urban (0),
Agriculture (1), Grass/Shrub (2), Forest (3), Water (4), Wetland (5), Other (13); change classes as
above. **Unknown (10) is excluded** and Unknown-vs-stable reported separately. Same file set as the
change/change folder (`change_stable_pixels_long.csv` with extra `stable_class`/`change_class`
columns, `ordered_pairs.csv`, `change_stable_patches.csv`, `summary.txt`, `COLUMNS.md`).

Findings: this is **the dominant form of change-class disagreement, ~43x the change/change count**.
**Total conflict is 110,265 px = 1,102.7 ha: 5.99% of all disagreement, but 55.98% of all
change-labeled pixels** — so when interpreters disagree about change, it is overwhelmingly one
seeing disturbance where the other sees stable cover, not a dispute over the change type. 55 of 72
cells carry some. Patches are larger than in the change/change case (16,447 patches, median 2 px,
max 16.4 ha). Symmetrized, the biggest confusions are **Forest↔Insect/Disease (396 ha) and
Forest↔Harvest (241 ha)**, then Grass/Shrub↔Harvest (118 ha), Wetland↔Harvest (74 ha), and
Agriculture↔Harvest (48 ha): the question of whether a stand is disturbed or stable forest, or
whether cleared/senescing vegetation is harvest or stable. Unknown-vs-stable is a separate 4,557 px
(45.6 ha). `examples/` renders the 10 largest disagreements (`scripts/plot_change_stable_examples.py`): the two reviewers' cells side by side in the RF interpreted colours with the disagreed area outlined, e.g. rank 1 is cell 20941 where bekka mapped 117 ha of Insect/Disease that mina mapped as Forest.

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
target), seeded for reproducibility — so no location is double-counted. Pooled metrics
barely change under de-duplication (v2 OA 0.651 → 0.657), so the earlier double-counting
was not materially biasing the numbers.

**These cached outputs reflect an earlier 154-location snapshot** (223 rasters, 30 with target
year 2019). The current interpreted set is **180 locations** (253 rasters, 36 with target 2019).
This all-years, static-mosaic arm is temporally mismatched for the off-2019 cells and is
superseded by `model_comparison_2018_2020/` (date-aligned) and `transfer_confusion/` (per-bracket
matched), so it has not been regenerated on the newer cells; treat its numbers as the original
baseline, not the current reference.

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
target years use offset windows and are temporally misaligned. Restricting to the
date-aligned, de-duplicated cells (`--targets 2019`; 30 in this earlier snapshot, 36 in
the current data) raises agreement for every smooth version:

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
footprints, so the interpretations set the reference scale). Regenerated on the current
basis: the interpreted source is the **adjudicated** reviewer per location
(`truth_selections.csv`) and the model source is each cell's **temporally-matched
per-bracket prediction** (`--truth exports/truth_selections.csv --preds
data/raw/transfer_predictions`; see `reference.txt`).

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
| v2 | 1.10 | 0.82 |
| v3 | 1.22 | 0.82 |
| v4 | 0.37 | 0.67 |
| v5 | 1.00 | 0.82 |
| v6 | 0.022 | 0.08 |

Patch size (unlike neighbor_change) discriminates the smooth variants: ordered by
grain, v6 (speckle) < v4 (fragmented) < **interpreted** < v5 < v2 < v3 (over-smoothed).
v5 is closest to the interpreted scale; v2/v3 over-smooth the large classes most. Moran's I
mainly isolates v6 (0.08) and now more clearly v4 (0.67, down from 0.71 on the static mosaic):
v4's off-year matched predictions are more fragmented than its 2018/2020 map, consistent with its
poor temporal transfer. v2/v3/v5 cluster near 0.82. The interpreted reference barely changes from
the earlier static/random-dedup basis (0.79 ha, Moran's I 0.75), since only 72 of 180 cells switch
reviewer; the structural ordering is unchanged.

## window_sampling_by_approach/ — per-approach window sampling (grouping)

The four per-approach folders below (`Case_A/B/C/D_window_sampling/`) are grouped here. They
sweep window size W over the exhaustive tiling per approach and use the static v2-v6 mosaic
reference; the unified sampling-design study is `Case_ABCD_sampling/`.

## window_sampling_by_approach/Case_B_window_sampling/ — Approach B window sampling

Implements Approach B (dominant pixel-pair per window) from Robert's window-sampling
framework (`disturbance_uncertainty/docs/window_sampling_methods.md`), adapted from binary to
our 10-class scheme. Source: `scripts/window_sampling_approachB.py`. Reference = interpreted
cells (deduped, one per location, seed 42, all target years); map field = model v2–v6. Each
cell is tiled EXHAUSTIVELY with non-overlapping W×W windows (not random sequential adsorption —
our cells are complete frame enumerations, so tiling gives inclusion probabilities known by
construction); partial edge windows are dropped and the discarded pixels reported. Per window,
all W² valid (map, ref) pairs are tallied over the 10×10 combinations and the single most
frequent one is the window's one contribution to the confusion matrix. **Tie rule
substitution:** Robert's binary preference (1,1)>(0,0)>(1,0)>(0,1) does not generalize, so ties
break by lowest map code then lowest reference code. W ∈ {1,3,5,7,9}; **W=1 reproduces the
per-pixel `compare_interpreted_vs_model.py` confusion exactly (asserted, PASS for all five
versions)** before proceeding.

- `window_sampling_metrics.csv` — version × W: OA, macro-F1, mean IoU, kappa, n_windows,
  windows_per_cell, edge-discard
- `window_sampling_confusion.csv` — long-format confusion (version, W, ref, map, count)
- `window_sampling_metrics.png` — metrics vs W per version, with windows/cell

As W grows, dominant-pair aggregation removes minority within-window disagreement, so agreement
rises monotonically for the smooth versions (v2 OA 0.66→0.74, κ 0.53→0.62 from W=1→9); the
speckly v6 barely benefits (OA 0.19→0.24, saturating by W=5 — no dominant pair in per-pixel
noise). This is a diagnostic of how within-window aggregation changes the assessment, not a
better accuracy: the per-window design keeps inclusion probabilities exact but effective sample
size falls as ~1/W² (windows per cell 113,576 → 1,369 from W=1 to W=9; edge discard ≤ 2.4%).

## window_sampling_by_approach/Case_C_window_sampling/ — Approach C window sampling

Implements Approach C (independent per-field label per window) from Robert's window-sampling
framework, adapted to our 10-class scheme. Source: `scripts/window_sampling_approachC.py`. Same
setup as Case B (interpreted reference vs. model v2–v6, deduped seed 42 all years, exhaustive
non-overlapping W×W tiling, W ∈ {1,3,5,7,9}). Approach C labels each field independently and
compares. **Deviation from source:** Robert thresholds each field at >50% (a binary majority);
with 10 classes a window often has no majority class, so we use PLURALITY — the most frequent
class in the map field and in the reference field — recorded as (plurality_map, plurality_ref),
one sample per window. Ties: lowest class code (consistent with B). **W=1 is identical to B at
W=1 and to the per-pixel confusion (asserted C == B == per-pixel, PASS for all versions);** the
internal B recomputation also matches Case_B exactly.

- `window_sampling_metrics.csv` — version × W: OA, macro-F1, mean IoU, kappa, n_windows,
  `frac_map_majority`, `frac_ref_majority` (share of windows whose plurality was a true >50%
  majority), `n_bne`/`frac_bne` (windows where B ≠ C), windows_per_cell, edge-discard
- `window_sampling_confusion.csv` — long-format confusion for C
- `window_sampling_metrics.png` — metrics / majority share / B≠C vs W

Key results. C climbs with W more slowly than B (v2 OA 0.66→0.69 vs B's 0.66→0.74) because C
records a disagreement whenever the two fields' pluralities differ, even when the most common
pair agrees. The **reference field almost always has a true majority** (0.93 even at W=9 — the
interpretations are spatially smooth), so plurality is a faithful summary of the reference. The
**map majority share depends on the version**: v2–v5 stay ~0.90–0.98, but **v6 collapses to 0.19
(W=3) → 0.04 (W=9)** — its per-pixel speckle means a window rarely has any dominant class, so the
v6 Approach-C label is a weak window summary and its v6 metrics must be read with that caveat.
B≠C grows with W and isolates within-window heterogeneity: ~7% of windows at W=9 for the smooth
versions, but **~15% for v6** (0.11 at W=3 → 0.15 at W=9), where B and C most often diverge.

## window_sampling_by_approach/Case_D_window_sampling/ — Approach D window sampling (per class)

Implements Approach D (proportional agreement scatter) from Robert's framework, **per class**
rather than collapsed to binary. Source: `scripts/window_sampling_approachD.py`. Same setup as
Case B/C (interpreted reference vs. model v2–v6, deduped seed 42 all years, exhaustive
non-overlapping tiling). For each class c and window, prop_map = fraction of the window's
jointly-valid pixels that are class c in the map, prop_ref = same in the reference; the pair is
plotted against the 1:1 line. **No confusion matrix / no OA by design** — a continuous view of
whether each variant carries the right class abundance in the right area. W ∈ {3,5,7,9} (W=1 is
degenerate). **Windows where both proportions are 0 are dropped and counted** (rare classes are
heavily zero-inflated — e.g. v6 Development 42% dropped, Insect/Disease 30%); each panel is
annotated with the retained window count.

- `window_sampling_metrics.csv` — version × W × class: n_retained, n_dropped, frac_dropped,
  rmse (to 1:1), mae, bias (prop_map − prop_ref), corr (Pearson)
- `prop_scatter_<version>.png` — 10 classes (rows) × W (cols) proportional-agreement densities
- `tightness_vs_W.png` — RMSE-to-1:1 vs W, per class, lines per version

Reading it: RMSE-to-1:1 falls with W for every class and variant — the models carry roughly the
right class abundance but misplace pixels locally, so aggregating to larger windows tightens the
scatter onto 1:1. v2/v3/v5 track tightest for the stable classes (Water RMSE 0.16 at W=9); **v4
is the abundance outlier** for Water/Urban/Agriculture (RMSE 0.37–0.42 at W=9). v6 is the worst
for Forest (0.54, bias −0.38 — it under-represents forest abundance). Caveat on v6's *low* RMSE
for the rare disturbance classes: its Pearson corr is ≈0 there, i.e. its per-pixel speckle gives
diffuse, near-constant proportions that don't track the reference — the low RMSE reflects uniform
smallness, not agreement, and should be read with the corr column, not on its own.

## window_sampling_by_approach/Case_A_window_sampling/ — Approach A as a design experiment

Approach A (pixel-level enumeration) from Robert's framework, run as a DESIGN EXPERIMENT, not
another aggregation scheme. Source: `scripts/window_sampling_approachA.py`. Under the exhaustive
tiling used for B/C/D, A collapses to the per-pixel comparison at any W, so it only becomes
informative under SAMPLING. Setup: interpreted reference vs. model v2–v6, de-duplicated one
interpretation per location (seed 42, all target years); the cells are a simple random sample
from the grid_112_naip_brackets frame, so the cell is the primary sampling unit. Within each
cell, n windows of size W×W are placed at random (RSA, reject overlaps), all W² pixels enumerated
and pooled into a confusion matrix — one draw. Sweep n ∈ {1,2,5,10,25,50}, W ∈ {1,3,5,7,9}, 200
draws each; per draw record OA, macro-F1, kappa; compare the sampling distribution to the census
(we have every pixel, so the census is the known truth). **These are draws from a design whose
properties we characterize — NOT accuracy estimates.**

(Note: the deduped set is now 180 cells, not the 154 in the original spec, because 30 newly
pulled interpreted cells — 26 bekka singletons on new grids — are part of the same frame sample.
The design conclusions are identical either way.)

- `approachA_design.csv` — version × n × W: census, mean/SD/2.5-97.5 pct of each metric, bias,
  mean pixels, binomial SD, design effect, SD ratio, effective sample size
- `sd_vs_cost.png` — SD(OA) vs pixels sampled per cell (n·W²), one line per W, per version
- `design_effect_vs_W.png` — design effect vs W (+ information retained per pixel)
- `bias_vs_W.png` — mean sampled OA − census OA vs W (unbiasedness check)

Findings. **Bias ≈ 0 at all W** (max |bias| 0.005) — random window placement recovers the census.
**Precision is not set by pixel count:** (n=50, W=1) and (n=2, W=5) both touch 50 pixels/cell but
W=1 is far more precise, because pixels within a window are autocorrelated. **Design effect** (the
cost of that autocorrelation) is ~0.8–0.95 at W=1 (≈ independent) and climbs steeply to ~28–32 at
W=9 for the smooth versions — a 9×9 window's 81 pixels carry only ~3 independent pixels' worth of
information. The **speckly v6 pays far less** (deff ~8 at W=9) because adjacent pixels are not
autocorrelated. Effective sample size (N / deff) makes the tradeoff legible: at equal pixels
interpreted, **many small windows beat a few large ones** — decisively for smooth maps, marginally
for v6.

## Case_ABCD_sampling/ — sampling experiment against known truth

A/B/C/D under two sampling designs, measured against the exhaustive-tiling census (which is
the known truth — we have every pixel). Source: `scripts/sampling_experiment_ABCD.py --truth
exports/truth_selections.csv --preds data/raw/transfer_predictions`. Separate from
`window_sampling_by_approach/Case_{A,B,C,D}_window_sampling/` (those are the census). **Draws from
designs whose properties we characterize — NOT accuracy estimates.** Setup: interpreted reference
vs. model v2–v6, one interpretation per location from the **adjudicated truth set**
(`truth_selections.csv`, `notebooks/adjudicate_truth.ipynb`), all years, 180 cells; the sampling
randomness stays seed 42 (`reference.txt`). The map field is now the **temporally-matched
per-bracket prediction** for each cell (`pred_<bracket>_cell*.tif`, the same maps used in
`transfer_confusion/`), so every cell is compared against the classifier applied to its own NAIP
bracket, not the single 2018/2020 mosaic. cell = primary sampling unit, pixels within a cell =
census. Population = the exhaustive

Effect of the temporal matching on the census (10-class, W=1): the sampling-design conclusions
(design effect, stratification efficiency, class absence) are unchanged, but the census accuracy
now reflects temporal transfer. **v4 drops sharply, OA 0.509 → 0.245 (kappa 0.32 → 0.12) and v6
0.188 → 0.130**, since their 2018/2020 overfit does not carry to the other brackets and each cell
is now scored against its own-bracket prediction; v2 (0.66), v3 (0.61 → 0.64), and v5 (0.57 →
0.59) barely move. The static mosaic had masked v4's transfer failure by comparing its 2018/2020
map against off-year references. The 5-class collapse shifts the same way (v4 OA 0.940 → 0.894,
v6 0.749 → 0.596; kappa still ~0 for every variant, so no change-detection skill either way).
non-overlapping W×W tiling windows with a jointly-valid center; sampling draws n distinct
(non-overlapping) windows. W ∈ {1,3,5,7,9}; n ∈ {20,50,100,200,500,1000,2000,5000} total across
the frame; 100 iterations per (n, W, design); seeds from base 42. **W=1 collapses A=B=C —
asserted (verified for all five versions).**

- `stratum_ceiling.csv` — windows per center reference class per W (the ceiling that bounds
  each class; Beaver ~0.05%, ~10k windows)
- `census.csv` — the truth (A/B/C OA/kappa/macro-F1) per version × W
- `metrics_by_n.csv` — bias/SD/2.5-97.5 pct vs census, per design × version × W × n × metric
  (incl. weighted `A_oa_wtd`, `C_frac_majority`)
- `class_absence.csv` / `class_absence.png` — fraction of iterations each class is absent
- `stratum_realized.csv` — realized equal allocation and shortfall per stratum, plus the
  **finite-population correction**: `stratum_ceiling` (N_h), `sampling_fraction` (n_h/N_h) and
  `fpc_sd_factor` = sqrt((N_h−n_h)/(N_h−1)) per stratum × n
- `per_class_metrics.csv` — per-class **recall** (producer's), **precision** (user's) and F1 vs n,
  per design × version × W (design-consistent weighted; mean/SD/bias vs census)
- `design_effect.csv` / `design_effect_vs_W.png` — deff and effective sample size
- `strat_efficiency.csv` / `strat_efficiency.png` — SD_stratified / SD_simple per class
- `d_correlation.csv` / `d_corr_vs_n.png` — Approach D per-class correlation (leads; rmse/bias alongside)
- `sd_vs_n_OA.png`, `bias_vs_n_OA.png`

Findings. **Design 1 (simple random) fails for rare classes at small budgets**, documented:
at n=20, W=1, Development is entirely absent in 78% of iterations, Insect/Disease 66%, Harvest
58%; all classes appear by n≈1000. **Design 2 (stratified, equal allocation)** deliberately
oversamples rare classes — so the **unweighted** estimate is biased (OA off by ~-0.19 from the
census at n=5000), while the **Horvitz-Thompson weighted** estimate recovers the census (bias
~-0.0004). **Design effect ≈ 1 at W=1** (verified — simple random per-pixel is binomial) and
climbs steeply (~38-47 at W=9 for smooth versions, ~10 for the speckly v6). **Stratification
efficiency** shows the crossover: it helps the rare classes enormously (Beaver SD ratio ~0.14,
Development ~0.18, Insect/Disease ~0.27) and hurts the common classes (Forest ~1.9, Agriculture
~1.35), because equal allocation starves them — the crossover sits around Grass/Shrub–Water. 

**Cross-variant differences the strategies expose** (`scripts/sampling_variant_comparison.py`, `variant_comparison.png`): the sampling designs discriminate the classifier variants. (1) Design effect separates the dot-product v6 (~10 at W=9) from the smooth v2-v5 (~38-47) — v6's per-pixel errors are spatially independent, so windows waste ~4x less information. (2) Approach D proportion correlation orders their quality: v2≈v3≈v5 track abundance well (Water 0.97, Agriculture 0.87), v4 is intermediate (Water 0.56, Urban 0.18), and v6 is near zero everywhere (Water 0.07, Urban -0.05) — it carries almost no class-abundance signal. (3) v6's speckle makes rare classes less often absent under simple random (spurious presence, not signal); v4 is idiosyncratic (rarely predicts Beaver, over-predicts Urban). The stratification crossover holds across all variants.  collapses this to two axes — abundance-weighted Approach D correlation (x) vs design effect at W=9 (y): v2/v3/v5 cluster upper-right (coherent, faithful), v4 upper-middle, and v6 sits isolated bottom-left (dot-product: no abundance signal, low autocorrelation).

## Case_ABCD_sampling_5class/ — sampling experiment under a 5-class collapse

The sampling experiment (as `Case_ABCD_sampling/`) rerun under a **5-class collapse**: all stable
classes merged into **Stable** (urban/agriculture/grass-shrub/forest/water/wetland/other), the
four change classes kept distinct (Harvest, Development, Insect/Disease, Beaver). Source:
`scripts/sampling_experiment_ABCD.py --collapse --truth exports/truth_selections.csv --preds
data/raw/transfer_predictions`. The reference points are the **adjudicated interpretation per
location** (`truth_selections.csv`, `notebooks/adjudicate_truth.ipynb`) and the map field is the
**temporally-matched per-bracket prediction** per cell (as in `Case_ABCD_sampling/`); the sampling
randomness stays seed 42 (`reference.txt` records both). **Unknown (unattributed change, no model
equivalent)
is excluded** — a substantive exclusion, not a technicality: dropping observed-but-unattributed
disturbance makes the Stable stratum marginally purer than the landscape. Excluded Unknown pixels
under the adjudicated reference: **4,139 (0.020% of the frame)** — still marginal, though larger
than the 1,823 (0.009%) under the random pick, since the adjudicated reviewers label more Unknown
in aggregate (`exclusion.txt`). Fire (40) has zero pixels. Census, ceilings, and all bias
comparisons are recomputed under the 5-class scheme (the 10-class census does not transfer). W=1
A=B=C verified. Files mirror the 10-class folder (`census.csv`, `stratum_ceiling.csv`,
`metrics_by_n.csv`, …) plus the comparison below.

Under the temporally-matched map field the collapsed census is v2 OA 0.872 / kappa 0.044, v3 0.828
/ 0.021, v4 0.894 / 0.074, v5 0.793 / 0.014, v6 0.596 / 0.005 — **kappa is still ~0 for every
variant, so no change-detection skill either way**, and the temporally-sensitive variants drop
(v4 OA 0.940 → 0.894, v6 0.749 → 0.596) just as in the 10-class matrix. The design-effect and
stratification findings are unchanged. Both this folder and `Case_ABCD_sampling/` now use the
adjudicated reference and the matched per-bracket map field; the `sampling_collapse_comparison.py`
outputs (which compare the two) will pick this up on their next run.

Collapsed census (v2, W=1): OA 0.883 but kappa 0.03 — Stable dominance (**~98.5%** of center
pixels) inflates OA while revealing little change skill. Stratum ceiling: Stable 98.5%, Harvest
1.1%, Insect/Disease 0.29%, Development 0.07%, Beaver 0.05% — the four change strata are what
constrain the design.

**Comparison to the 10-class run** (`scripts/sampling_collapse_comparison.py`,
`collapse_vs_10class.csv`, `change_convergence.png`, `collapse_summary.png`,
`recall_precision_convergence.png`, `collapsed_kappa.csv`): equal allocation now
gives each change stratum n/5 (vs n/10). The question — does collapsing improve change-class
convergence? — has a **crossover** answer: 5-class converges FASTER at small n (Development SD
ratio 0.63, Insect/Disease 0.58 at n=50), but for the rarest classes (Development, Beaver) the
10-class scheme **catches up and passes at large n** (Development ratio 1.80 at n=5000). Mechanism:
collapsing doubles the change-stratum allocation (helps recall) but under-samples Stable (n/5 vs
6·n/10), degrading change-class F1 **precision** (false positives live in the stable background) —
recall gain vs precision cost. Also: **design effect increases** under the collapse (OA now
dominated by the highly-autocorrelated Stable class, lifting even v6 from ~10 to ~23 at W=9), and
**macro-F1 is not comparable as a level** between schemes (it averages 5 classes here, 10 there) —
only its convergence behaviour is.

**Recall vs precision — shown, not inferred from F1** (`recall_precision_convergence.png`,
`per_class_metrics.csv`). Splitting the F1 crossover into its two components confirms the
mechanism directly. Stratified SD ratio (5-class / 10-class, v2, W=1): **recall is estimated
better under collapse at every n** (ratio ~0.69–0.84 across all four change classes — the
allocation benefit), while **precision degrades at large n** for the rarest classes (Development
1.97×, Harvest 1.57×, Beaver 1.15× the 10-class SD at n=5000). The F1 crossover is genuinely a
recall gain traded against a precision loss, not a single effect read off F1.

**Finite-population correction — verified and quantified** (`stratum_realized.csv`, columns
`sampling_fraction`/`fpc_sd_factor`). The FPC is applied *implicitly*: the reported SDs are the
empirical spread of without-replacement Monte-Carlo draws, so a fully-sampled stratum
contributes zero variance by construction. Its magnitude is now visible. At n=5000, W=1, the
constraining change strata sit at sampling fractions of Beaver 9.9% (5-class) / 5.0% (10-class),
Development 6.9% / 3.4%, giving FPC SD factors of ~0.95 (5-class) vs ~0.97–0.98 (10-class). The
**5-class arm's fraction is higher** (double allocation into a stratum of the same ceiling), so
its FPC reduces variance *more* — the **opposite** direction to the observed crossover. The FPC
therefore cannot manufacture the crossover; it slightly counteracts it, confirming the crossover
is a genuine allocation/precision effect.

**Collapsed-scheme kappa across all variants, stated plainly** (`collapsed_kappa.csv`). At W=1,
collapsed-census kappa is v2 0.025, v3 0.010, v4 0.059, v5 0.007, v6 0.006 — **~0.06 at most**.
Once stable-class discrimination is removed from the metric, every model variant (v2–v6) has
**essentially no change-detection skill**: the high collapsed OA (0.75–0.94) is carried entirely
by agreement on the ~98.5% Stable background, not by detecting Harvest/Development/Insect-
Disease/Beaver. This is a substantive result about the maps, not an artefact of the collapse.

## variant_difference_maps/ — pairwise difference maps between model variants

Pairwise comparison of the four smooth classified variants (v2, v3, v4, v5). **v6 is excluded**:
its per-pixel dot-product speckle makes every comparison read as noise. That leaves six unordered
pairs, each in its own subfolder (`v2_vs_v3/` ...); by convention the lower version number is A.
Source: `scripts/variant_difference_maps.py`. The mosaic is 72,577 × 48,386 at 10 m (EPSG:5070,
two horizontal tiles); v2–v5 share the grid exactly, so windows are read directly with no
resampling.

Per pixel, in the 10-class model scheme (1/2/9/10 change, 3–8 stable), each pixel is one of:
agree (rendered in that class's colour), stable/stable mismatch (grey), A-change/B-stable
(magenta), B-change/A-stable (cyan; kept distinct from the former — different findings), or
change/change mismatch (red). Background (either map 0) is black.

Per pair: `difference_map.png` (full-map overview at **160 m blocks**, each block coloured by its
**majority composition**: whichever wins between total agreement and total disagreement across its
256 underlying pixels, then the leading category, with agreement shown in muted class colours.
This has no priority bias, so a mostly-agreeing block reads as the landscape and only genuinely
disagreement-dominated blocks read as disagreement, which is why the smooth v2/v3/v5 pairs now
look mostly like the landscape while the v4 pairs look genuinely contested. The four saturated
disagreement categories are legended in the map; every muted agree class has its own swatch in a
row beneath the map), `category_stats.csv`
(pixel count and area per category, **computed at full 10 m resolution from windowed reads, not
from the render**), `cat5_change_pairs.csv` (change/change by directed change-class pair),
`cat3_Achange_by_class.csv` / `cat4_Bchange_by_class.csv` (by the detecting variant's change
class), `zoom_topNN_*.png` (the 10 largest change-involved disagreement patches), and
`overlay_topNN_*.png` (the 5 largest such patches intersecting an interpreted cell, as
variant A | variant B | interpreted reference), and `overlay_cellNN_gridID.png` (5 cell-sized
3-panel examples: the interpreted cells with the most in-cell A/B change-involved disagreement,
cropped to the cell extent so the interpreted reference fills its panel rather than sitting as a
 speck inside a large patch crop). `pairs_summary.csv` collects all six. A second overview, `difference_map_change.png`, is a **change-focused recolour** of the same block render: all stable classes read as one medium gray (water slightly darker) and colour is reserved for the agreed change classes (Harvest, Development, Beaver, Insect/Disease) and the three change-involved disagreement categories, so change stands out against a gray stable landscape. Regenerable from the cached grids with `--plots-only`.

`cell_all_variants/` holds 6-panel figures (`cellNN_gridID.png`), one per interpreted cell: all five variants (v2-v6, including v6 here so its speckle is visible) plus the interpreted reference, every panel cropped to the cell's ~3.4 km extent. Cells are ranked by how much the four smooth variants (v2-v5) disagree inside the cell, so the top cells surface the sharpest inter-variant conflicts (for example cell 51040: v2/v3/v5 and the human all call a lake Water, v4 calls the whole lake Urban, v6 is pure per-pixel noise). Built by `python scripts/variant_difference_maps.py --cell-panels` (windowed reads, no streaming; `--cell-panels-n` sets the count, default 20).

**Patch definition.** Change-involved disagreement (categories 3+4+5) is 8-connected-labeled on
an **80 m grid** where each block carries its exact full-resolution cat-3/4/5 pixel count, so
component areas are exact. A block counts toward a patch only if it is **≥25% dense** in
change-involved disagreement; without that floor the disagreement is so extensive that
8-connectivity merges the whole diffuse field into one mosaic-spanning blob. Crops are capped at
2.5 km so a sprawling patch never forces a multi-gigabyte read; the very largest patches are
shown centred on their bounding box at the cap.

Findings: the variants are **far from interchangeable for change**, and **v4 is the outlier**.
Agreement is 82–86% among {v2, v3, v5} but collapses to **47% (v4_vs_v5), 51% (v3_vs_v4), 56%
(v2_vs_v4)** — every v4 pair also carries 7–8 million ha of stable/stable mismatch, i.e. v4
assigns the *stable* classes very differently. The change-involved disagreement is dominated by
one-directional over-calling: v5 flags change over millions of ha the others call stable
(v5-change/v4-stable 4.98 M ha, v5-change/v2-stable 3.34 M ha), and it is a **pervasive
contiguous field, not discrete features** (the full-map renders show it flooding the landscape).
change/change mismatches are comparatively small (33k–204k ha). Of each pair's 10 largest
change-involved patches, **6–9 of 10 intersect an interpreted cell** (recorded per pair in
`notes.txt`), so the interpreted overlays are populated rather than empty. Interpreted cells used:
180 (de-duplicated, seed 42).

## collapsed_5class_confusion/ — census confusion under the 5-class collapse

Full confusion matrix per variant under the 5-class collapsed scheme, as a **census** over the
interpreted cells (every valid pixel counted), not a sampling experiment. Scheme: Stable (urban,
agriculture, grass/shrub, forest, water, wetland, other) plus the four change classes kept
distinct (Harvest, Development, Insect/Disease, Beaver). Unknown (10) is excluded; Fire (40) is
empty. The collapse is applied after the crosswalk to both reference and model. Reference =
interpreted cells de-duplicated to one per location (numpy `default_rng` seed 42), all target
years. Variants **v2–v6 including v6** — the collapse is exactly the condition under which its
per-pixel behaviour might change, so excluding it would beg the question.
Source: `scripts/collapsed_5class_confusion.py`.

Files: `confusion_<v>_counts.csv` / `_rownorm.csv` (raw and row-normalized 5×5, reference on rows
so the row-normalized diagonal is producer's accuracy), `confusion_<v>_rownorm.png` (heatmap, no
gridlines), `metrics_long.csv` (every metric × variant × class with ratio-estimator and bootstrap
CIs and support), `summary_by_variant.md` / `.tex` (per-variant headline table, booktabs),
`summary.txt`.

CIs are design-based with the **cell as the primary sampling unit**: ratio estimators across
cells (variance from the between-cell variance, FPC √(1 − n/N), N = 21,561) for the ratio-form
metrics (OA, per-class recall/precision/IoU), cross-checked with a cell-level bootstrap (seed 42,
2000 replicates) which also covers the non-ratio metrics (F1, macro-F1, mean IoU, kappa). The two
agree closely; for the rarest classes the normal-approximation ratio CI can dip below 0 while the
bootstrap stays positive, which is why the cross-check is reported. **Cell count is 180, not the
154 the plan named** — the data now holds 36 cells/year × 5 years (2018–2022), all overlapping
the model; the FPC is 0.996 either way, so the CIs are unaffected.

Headline (stated plainly): **OA is dominated by the ~98.5% Stable class and every variant's OA is
below the all-Stable baseline of 0.985** — labeling everything Stable beats every model — with
**kappa ≈ 0** (v2 0.884 / κ 0.025, v3 0.807 / 0.009, v4 0.941 / 0.063, v5 0.767 / 0.007, v6 0.750
/ 0.007). So under the collapse the maps carry almost no change-detection information; v4's higher
OA is just closer agreement on Stable, not skill. The row-normalized matrices show why: change
classes overwhelmingly map to Stable (Harvest 0.78→Stable, Development 0.89→Stable for v2), and
Stable leaks to Beaver (1.35 M px for v2), so change-class precision is near zero (Beaver 0.002,
Development 0.007). macro-F1 here (~0.18–0.22) averages 5 classes versus 10 in the 10-class
matrices and is **not comparable as a level**.

## model_comparison_2018_2020/ — interpreted vs model, temporally matched cells

Rerun of the interpreted-vs-model comparison on **only the temporally matched cells**, and the
version that **supersedes the all-years runs for the model-comparison arm**. The model maps v2-v6
are classified from 2018 and 2020 embeddings, so only interpreted cells with target year 2019
carry the matching NAIP bracket (2018-2020); target 2018 brackets 2017-2019, 2021 brackets
2020-2022, etc. Filtering to target 2019 and de-duplicating (numpy `default_rng` seed 42) gives
**36 cells** (the plan named 30; the data has grown), all confirmed at bracket 2018-2020
(`cells.csv`). Variants v2-v6. Source: `scripts/model_comparison_2018_2020.py`. The existing
`model_comparison/` all-years outputs are left untouched.

Per variant, both schemes: 10-class and 5-class collapsed confusion (raw + row-normalized CSVs,
row-normalized heatmap figures with no gridlines), OA / macro-F1 / mean IoU / kappa, and per-class
precision/recall/F1/IoU/support. Files: `confusion_<scheme>_<v>_counts.csv` / `_rownorm.csv` /
`_rownorm.png`, `metrics_long.csv`, `summary_by_variant.md` / `.tex`, `summary.txt`, `cells.csv`.

**Inference.** Target year is a property of the cell (it follows from NAIP availability), not of
the random draw, so if interpreters worked a randomized list the target-2019 subset is a
probability sample of the **2018/2020-eligible subpopulation**, which is narrower than the full
21,561-cell frame. That subpopulation is estimated at ~4,312 cells (sample proportion of 2019
cells), and the ratio-estimator FPC uses it, not 21,561 (numerically 0.996 either way). CIs use
the cell as the primary sampling unit, cross-checked with a cell-level bootstrap (seed 42). **With
n=36 the intervals are wide and are reported, not suppressed.** Per-class metrics are **design-aware
flagged**: scored only if the class has ≥100 px AND appears in ≥3 cells; `cells_present` is in
`metrics_long.csv`. Here every change class clears both (Harvest 18 cells, Development 10,
Insect/Disease 8, Beaver 5), so none are suppressed, but Beaver rests on 5 cells with very wide CIs.

Findings: **temporal matching matters.** On the matched cells the 10-class metrics are meaningfully
better than the collapsed/all-years views: v2 OA 0.72, kappa 0.59 (v3 0.70/0.57, v5 0.65/0.51,
v4 0.64/0.46, and the speckly **v6 collapses to 0.19/0.08**). But that kappa is stable-class skill:
the row-normalized 10-class matrix shows change classes revert to the stable class they resemble
(Harvest 0.63→Forest, Insect/Disease 0.70→Forest, Beaver 0.39→Wetland). The **5-class collapse
confirms the census story on these cells too** — every variant's OA (0.69-0.94) is below the
all-Stable baseline 0.979 with kappa ≈ 0 (v4 highest at 0.157). One bright spot: **Harvest
precision reaches 0.54 (0.28-0.71) for v2**, far above its near-zero all-years value, so temporal
matching does recover some Harvest signal. macro-F1 averages 5 vs 10 classes across the two schemes
and is not comparable as a level, nor with the earlier all-years matrices.

## transfer_confusion/ — temporal-transferability confusion matrices

Per-class confusion matrices and accuracy for the classifier temporal-transferability experiment.
A Random Forest trained once on 2018/2020 AlphaEarth embeddings was applied to five NAIP brackets
(2017_2019, 2018_2020, 2019_2021, 2020_2022, 2021_2023), restricted to the CKIT-RF interpreted
cells for each bracket (36 disjoint cells per bracket). 2018_2020 is the in-sample control.
Source: `scripts/build_transfer_confusion.py`, predictions fetched by
`scripts/fetch_transfer_predictions.py` (Drive, git-ignored). The GEE predictions carry 5 bands
(band1=v2 ... band5=v6, values 1-10); the CKIT reference is remapped through the crosswalk
(0->4, 1->6, 2->7, 3->3, 4->5, 5->8, 20->1, 30->2, 50->10, 62->9), and reference values 10
(unknown) and 13 (other_no_change) are dropped.

Files: `cm_<variant>_<bracket>.csv` (25 matrices, 10x10 raw counts, reference on rows so the
diagonal is producer's accuracy, prediction on columns), `cm_<variant>_<bracket>.png` (25 heatmaps,
cells coloured by row proportion with raw counts, a producer's-accuracy column with support, a
user's-accuracy row, and OA and kappa in the corner), `transfer_metrics_long.csv` (one row per
variant x bracket x class with per-class precision/recall/F1/IoU/support/cells_present/low_support,
the aggregate OA/macro-F1/mean IoU/kappa repeated on each row, and a `control` flag), and `note.md`.
`oa_by_bracket.png` and `oa_by_variant_bracket.csv` summarize OA at a glance: time period on the x
axis, OA on the y axis, one line per variant, with the in-sample 2018_2020 control shaded.

**Alignment held.** Each prediction was pinned to its reference grid via `ckit_cell_grids.csv`;
the script asserts equal CRS, width, height, and transform (atol 1e-6) per pair before comparing.
All 180 pairs matched, so **0 were skipped** for grid mismatch, band count, or missing reference,
and no reference carried an unmapped value.

**Double interpretation:** 72 cells have two reviewers' references. One reference per cell is used,
chosen at random with a fixed seed (`numpy.default_rng(42)`, drawn in sorted cell-id order), so it
is reproducible.

**Disjoint-cell caveat (stated in the note):** the five brackets use disjoint cell sets, so a
bracket-to-bracket difference confounds temporal transfer with the differing cell composition and
landscape difficulty. These are five independent assessments, not a controlled transfer curve, and
the 2018_2020 control is scored on its own 36 cells, not a shared baseline.

Findings: **v2 and v3 transfer best, v4 collapses out-of-sample, v6 is poor everywhere.** v2 OA is
0.72 in-sample (kappa 0.60) and 0.60-0.72 across the transfer brackets (kappa 0.46-0.59). v4 scores
0.64 in-sample but drops to 0.07-0.29 on the transfer brackets (kappa 0.01-0.18), so it overfits
the 2018/2020 window and does not carry to other years. v6 stays at OA 0.07-0.19 throughout. As
elsewhere, the aggregate metrics are dominated by the abundant stable classes; per-class change
metrics are weak and rest on thin support. Support is reported per class with a design-aware
`low_support` flag (a class in fewer than 5 cells or under 100 px), since pixels within a cell are
autocorrelated. Beaver in 2019_2021 (613 px, 4 cells) is the one flagged case, and its 0.69 recall
sits against a 0.0007 precision, so its number should not be trusted. macro-F1 here averages 10
classes and is not comparable as a level with the collapsed matrices.

## transfer_confusion_adjudicated/ — same analysis, adjudicated reference

The transfer confusion rerun with the **adjudicated truth reference** instead of the random pick:
for each multi-interpreted location the reviewer chosen in `exports/truth_selections.csv`
(`notebooks/adjudicate_truth.ipynb`) is used, and the single-interpreted cells are unchanged.
Built with `python scripts/build_transfer_confusion.py --truth exports/truth_selections.csv`;
`scripts/plot_transfer_oa.py --dir reports/transfer_confusion_adjudicated` adds the OA figure.
All 180 pairs matched (0 skipped, 0 unmapped, 0 truth/raster mismatches). Same file set as
`transfer_confusion/`.

Finding: **the adjudication barely moves the aggregate metrics.** Every OA shifts by at most
0.007 versus the random-reference version (for example v2 2017_2019 0.645 -> 0.651, v4 2017_2019
0.087 -> 0.084), and the story is unchanged: v2/v3/v5 transfer, v4 collapses out-of-sample, v6 is
poor throughout. This is expected, since only 72 of 180 cells change reference and the two
reviewers of a location agree on roughly three quarters of pixels, so which reviewer is chosen is
a small perturbation on the pooled matrices. The adjudicated version is the one to cite going
forward; the random-reference `transfer_confusion/` is kept for comparison.
