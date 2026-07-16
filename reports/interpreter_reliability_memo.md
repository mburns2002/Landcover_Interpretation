# Inter-interpreter reliability of the CKIT-RF land cover interpretations

*Methods-and-results memo. All figures/tables referenced live under
`reports/interpreter_agreement/`; analysis scripts under `scripts/`.*

## Summary

Seventy-two grid cells were independently interpreted by two reviewers each (a later batch added three bekka-robert pairs and turned one existing mina-peter cell into a mina/peter/robert triple, currently scored as its mina-peter pair). Pooled
agreement is moderate (overall agreement 0.77, Cohen's κ 0.66), but this masks a strong
per-class split: reviewers agree on unambiguous cover (Water, Forest, Agriculture; F1 ≥ 0.78)
and diverge sharply on transitional and disturbance classes (Grass/Shrub F1 0.30, Wetland
0.47). Five diagnostics establish that the low-agreement classes reflect **genuine conceptual
disagreement in the reference, not mapping noise or misregistration**: (i) the disagreement is
concentrated on four class boundaries; (ii) by area it occurs in large, irregular mosaic zones
rather than thin edges; (iii) for the largest Grass/Shrub↔Wetland zones, both reviewers placed
*conflicting training labels* on the same ground; (iv) reviewers carry systematic,
directional class-assignment biases; and (v) a spatial-tolerance test shows the Grass/Shrub and
Wetland disagreement does not recover under a one-pixel tolerance, whereas only small built
classes (Urban, Development) do. The practical implication: model accuracy reported against a
single interpretation of Grass/Shrub or Wetland is bounded by reference noise, not model error,
and should be reported with that caveat.

## Data and setup

Each of the 72 double-interpreted cells is a Sentinel-2 grid cell (10 m, EPSG:5070, ~337 × 337
px) labeled by two of five reviewers (ash, bekka, mina, peter, robert). Reviewers drew training
polygons; every pixel inside a polygon became a labeled training sample (`samples_generated`
sidecars), and a Random Forest produced the wall-to-wall classification (`rf_class` raster) used
here. Cells were matched on grid + sample + target year, so the two interpretations share an
identical footprint and are compared pixel-for-pixel with no reprojection. The land cover legend
has 13 classes (stable: Urban, Agriculture, Grass/Shrub, Forest, Water, Wetland, Other;
disturbance: Harvest, Development, Fire, Insect/Disease, Beaver, Unknown; Fire is absent from the
data). **No de-duplication is applied — the replicate pairs are the unit of analysis.**

## Diagnostic 1 — Per-class agreement with confidence intervals

*Script: `interpreter_class_ci.py`. Table: `per_class_agreement_table.{md,tex}`; figure:
`per_class_agreement_forest.png`.*

For each pair a confusion matrix was formed (rows = reviewer A, cols = reviewer B, alphabetical);
per class we report the symmetric agreement F1 = 2·TP / (row + col), i.e. the balanced probability
that the two interpreters concur given one assigned the class. Because pixels within a cell are
spatially autocorrelated, uncertainty is a **cluster (pair) bootstrap** (2000 replicates; the
resampling unit is the pair, not the pixel).

| Class | F1 (95% CI) | Tier |
|-------|-------------|------|
| Water | 0.92 (0.86–0.95) | High |
| Forest | 0.90 (0.88–0.91) | High |
| Agriculture | 0.78 (0.72–0.82) | High |
| Harvest | 0.70 (0.60–0.76) | Moderate |
| Urban | 0.60 (0.53–0.68) | Moderate |
| Wetland | 0.47 (0.37–0.55) | **Low** |
| Grass/Shrub | 0.30 (0.23–0.36) | **Low** |
| Development | 0.28 (0.02–0.46) | Low |
| Insect/Disease | 0.23 (0.01–0.49) | Low |
| Beaver | 0.08 (0.00–0.21) | Low |
| Unknown | 0.00 (0.00–0.00) | Low |

Overall agreement 0.77 (0.74–0.80); Cohen's κ 0.66 (0.62–0.70); macro-F1 0.47 (0.43–0.51). CIs
widen appropriately for the rare disturbance classes, so their low reliability is not over-claimed
on thin samples.

## Diagnostic 2 — Where the disagreement lives (class boundaries and geometry)

*Scripts: `disagreement_summary.py`, `disagreement_geometry.py`,
`disagreement_geometry_bysize.py`. Figures: `class_disagreement_top.png`,
`geometry/area_ecdf_focus.png`, `geometry/shape_index_area_weighted_ecdf.png`,
`geometry/gs_wetland_top10.png`.*

Four undirected boundaries account for ~68% of all disagreeing pixels: Forest↔Wetland (22%),
Agriculture↔Grass/Shrub (17%), Grass/Shrub↔Forest (14%), Grass/Shrub↔Wetland (14%).

Disagreement patches (per directed class pair, 8-connected labeling; area, 4-connected perimeter,
and shape index P/(2√(πA))) show two regimes. **By count** it is pixel-edge speckle: of 255,985
disagreement patches, 93% are ≤ 1 px wide and 99% ≤ 2 px (median width 0.5 px), and the pooled
shape index (~1.13–1.20) is essentially the single-pixel value (a 1×1 patch has shape index 1.128).
**By area** the picture inverts. Weighting by area rather than patch count, the patches that hold
the disagreement (≥ 0.1 ha, carrying 55–83% of disagreement area) have area-weighted median shape
index 3.7–6.1 and extent (area / bounding-box area) ≈ 0.42 — elongated, crenulated, not compact.
For the worst boundary, Grass/Shrub↔Wetland, the ten largest disagreement patches are 30–120 ha,
3–7 px wide, shape index 6–12, extent ~0.3: **large, irregular mosaic zones**, not thin margin
ribbons and not compact interior blocks.

## Diagnostic 3 — Are the largest disagreements training conflicts or extrapolation?

*Script: `training_polygon_overlay.py`. Table: `geometry/gs_wetland_training_overlay.csv`;
figure: `geometry/gs_wetland_training_overlay.png`.*

For the six cells containing the ten largest Grass/Shrub↔Wetland patches, both reviewers'
training points were overlaid on each patch and the distance from the patch to each reviewer's
nearest training was measured. Six of ten patches are **direct training conflicts** — both
reviewers placed training inside the zone (0 m) but with different classes (e.g. the 121 ha patch:
one reviewer trained Grass/Shrub, the other Wetland). Three are one-sided (only one reviewer
trained there; the other's RF extrapolated, nearest training 79–685 m away) and one is pure
extrapolation (neither trained in the zone). The largest disagreements are therefore
**encoded in the training labels**, not artifacts of the Random Forest.

## Diagnostic 4 — Systematic directional reviewer bias

*Script: `reviewer_directional_asymmetry.py`. Figure: `reviewer_overassignment_heatmap.png`;
tables: `reviewer_class_overassignment.csv`, `reviewer_directed_classpairs.csv`.*

Pooling the directed confusion per reviewer (in pixels/area), we computed an over-assignment index
log₂[(pixels where R claims class C and the partner does not + 1) / (reverse + 1)], with cluster
(pair) bootstrap CIs. Several reviewers systematically over-assign classes (95% CI excludes 0):
mina over-assigns Agriculture (+1.97) and Water (+1.75); bekka over-assigns Insect/Disease (+6.46),
Harvest (+1.76), and Urban (+1.55); ash over-assigns Water (+2.75). On the Grass/Shrub↔Wetland
boundary specifically there is a reviewer "wetness" axis: robert (+2.85) and, mildly, bekka/mina
(+0.28/+0.19) lean Wetland, while ash (+0.63) and peter (+1.64) lean Grass/Shrub. Disagreement on
these boundaries is thus partly a reproducible difference in how individual reviewers apply the
class definitions. *Caveat:* the index is relative to comparison partners, and the co-labeling
graph is unbalanced (bekka and mina share 22 of the 72 pairs), so paired reviewers' indices are two
views of the same contrast; rare-class extremes (Beaver, Unknown) are unstable.

## Diagnostic 5 — Edge-driven vs conceptual disagreement (spatial tolerance)

*Script: `spatial_tolerance.py`. Figure: `spatial_tolerance_delta.png`; table:
`spatial_tolerance_delta.csv`.*

Per class we recomputed agreement under relaxed matching (a pixel matches if its class appears in
the k×k neighborhood of the other reviewer's map), directionally (dilate B for A→B, dilate A for
B→A). The reported quantity is the per-class **recovery above a heterogeneity null** — (relaxed −
strict) minus the same quantity computed against the other map translated 3–5 px, which estimates
chance recovery from local class composition — with cluster (pair) bootstrap CIs, at k = 3 and
k = 5. *This is a diagnostic of where disagreement is edge-driven; no relaxed overall accuracy is
computed.* Only Development (+0.083) and Urban (+0.042) recover significantly above the null (small
built features whose disagreement is one-pixel boundary misregistration). Grass/Shrub (+0.013) and
Wetland (+0.009) do **not** move above the null — their disagreement is conceptual, not
registration. No class keeps climbing from 3×3 to 5×5 (every 5×5 recovery ≤ its 3×3), so there is
no gross (> 1 px) misregistration.

## Synthesis

The five diagnostics converge. Reviewers reliably agree on Water, Forest, and Agriculture, and the
residual disagreement there is scattered single-pixel edge speckle. The unreliable classes —
Grass/Shrub and Wetland above all — disagree in large, irregular mosaic zones (Diagnostic 2) that
carry conflicting training labels (Diagnostic 3), reflect systematic reviewer-level class-definition
axes (Diagnostic 4), and do not recover under spatial tolerance (Diagnostic 5). This is conceptual
disagreement about ambiguous, hydrologically-transitional ground (wet meadow vs. emergent wetland;
sparse grass/shrub vs. wetland margin), not mapping error.

## Implications for model evaluation

A classifier scored against a single interpretation inherits this reference noise class-by-class.
On Water/Forest/Agriculture the reference is trustworthy (F1 ≥ 0.78) and model error is
interpretable. On Grass/Shrub and Wetland the two-interpreter ceiling is only 0.30 and 0.47, so a
model cannot exceed that agreement against either interpretation regardless of quality; per-class
metrics for these classes should be reported with the inter-interpreter F1 alongside, and
whole-map accuracy should not be read as a single number that mixes reliable and unreliable classes.

## Reproducibility and limitations

All statistics use cluster (pair) bootstraps (2000 replicates) so uncertainty reflects the 69
independent cells, not autocorrelated pixels; all randomness uses `numpy.default_rng(42)`. The
analysis is intentionally not de-duplicated. Limitations: (a) the reviewer-bias index is relative
and confounded by unbalanced pairing (Diagnostic 4); a joint model of reviewer class-propensity on
the co-labeling graph would remove this. (b) The spatial-tolerance null uses wrap-around
translation, a minor edge approximation. (c) Rare disturbance classes (Beaver, Insect/Disease,
Development, Unknown) have small pixel support and correspondingly wide CIs; their point estimates
should be treated as indicative.
