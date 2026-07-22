# Methods and Results (draft)

*Working draft assembled from the analyses completed in this repository. Tables are generated from
the results CSVs and traceable to their source files; figures are the rendered outputs in `reports/`.
Prose is descriptive of what was done and what the numbers show. Sentences marked
`[Interpretation:]` are placeholders where the author's interpretation belongs and are not asserted
here. Literature and citations are out of scope for this draft.*

---

## 2. Methods

### 2.1 Study area and interpreted reference

The study area is the western Great Lakes region spanning Wisconsin, Minnesota, and Michigan. The
reference data are interpreted land-cover and change cells produced with the CKIT-RF interpreter
workflow: for each cell an analyst draws training polygons over high-resolution imagery, a per-cell
Random Forest is trained on those labels, and the result is a wall-to-wall classified raster on the
cell footprint (EPSG:5070, 10 m). The interpreted set used here is 180 cells (36 cells in each of
five NAIP acquisition brackets), of which 72 were independently interpreted by more than one
reviewer.

Where a cell was interpreted by more than one reviewer, a single interpretation per cell is selected
by adjudication, recorded in `exports/truth_selections.csv`, so each cell contributes exactly one
reference and none is double counted. The 72 multi-interpreted cells are also retained separately for
the inter-interpreter reliability analysis (Section 2.7), where each is scored as a reviewer pair.

The reference cells fall within the watersheds of seven park units of the National Park Service Great
Lakes Inventory and Monitoring Network (GLKN): Apostle Islands, Grand Portage, Isle Royale,
Mississippi National River and Recreation Area, Saint Croix, Sleeping Bear Dunes, and Voyageurs. Two
of the nine GLKN units, Indiana Dunes and Pictured Rocks, fall outside the study grid extent and are
not used. Figure 1 maps the study region, the grid extent, the park units,
and the interpreted cells.

[[FIG figure_study_area/figure1_study_area.png | Figure 1. Study area in the western Great Lakes region (Wisconsin, Minnesota, and the Michigan Upper Peninsula), EPSG:5070, showing the study grid extent, the Great Lakes, the seven GLKN park units, and the 180 interpreted reference cells, with a conterminous-US locator inset, scale bar, and north arrow.]]

### 2.2 Class schema and the 5-class collapse

The classification schema has 10 classes: Harvest, Development, Forest, Urban, Water, Agriculture,
Grass/Shrub, Wetland, Beaver, and Insect/Disease. The CKIT interpreter label identifiers are
crosswalked to this schema (0 to Water, 1 to Agriculture, 2 to Grass/Shrub, 3 to Forest, 4 to Urban,
5 to Wetland, 20 to Harvest, 30 to Development, 50 to Insect/Disease, 62 to Beaver). Two reference
values have no 10-class equivalent and are dropped: 10 (Unknown, an abstention) and 13 (Other,
no-change). Fire (40) carries no pixels in this reference set.

For change-focused analysis the schema is collapsed to five classes: Stable (the six no-change
classes pooled), Harvest, Development, Insect/Disease, and Beaver. The primary 5-class collapse
(used for the pooled comparison, the per-cell analyses, and the interpreter agreement) excludes
Unknown and Other. A second per-bracket 5-class product folds Other into Stable instead; the two
collapses are kept distinct and are not interchangeable (see the consistency report). Figure 1b shows
the 10-class schema and the 5-class collapse.

[[FIG figure_study_area/figure_class_schema.png | Figure 1b. Classification schema. Left, the 10-class schema grouped into the six no-change (stable) classes and the four change (disturbance) classes, each with its class code and legend color. Right, the 5-class collapse that folds the six stable classes into a single Stable class and keeps the four change classes.]]

### 2.3 Prediction sources: embedding variants and the spectral baseline

The embedding predictions are Random Forest classifications of AlphaEarth Foundations embeddings,
run in Google Earth Engine. Five embedding feature configurations are compared, distinguished by how
the base-year and paired-year embeddings and their change are combined (base year 2018, paired year
2020 in the training window, shifting per bracket in the temporally-matched runs):

- v2: base + delta (change from base to paired year).
- v3: base + paired year (both years stacked).
- v4: delta only.
- v5: base + dot product.
- v6: dot product only.

The spectral baseline (spec_all) is a Random Forest trained on 2018/2020 spectral composites drawn
from Sentinel-2, Landsat 8, and Sentinel-1 SAR raw bands and indices (50 bands). All six sources are
classified into the same 10-class schema on the same cell footprints, so the embedding-versus-
spectral comparison is like-for-like on the shared cells.

### 2.4 Temporal transferability design

A single classifier is trained once on the 2018/2020 window and applied to five NAIP brackets:
2017-2019, 2018-2020, 2019-2021, 2020-2022, and 2021-2023. The 2018-2020 bracket is the in-sample
control (its own year window). The five brackets use disjoint 36-cell sets with no cell shared across
brackets, so a bracket-to-bracket difference confounds temporal transfer with the differing cell
composition and landscape difficulty. The per-bracket results are therefore five independent
assessments rather than a controlled transfer curve, and the pooled numbers, or a same-bracket
comparison, are the like-for-like readings. The embedding predictions cover all 180 cells; spec_all
covers 168, since 12 spec_all rasters are entirely nodata in the out-of-sample brackets.

### 2.5 Accuracy assessment

For each source, bracket, and pooling, a confusion matrix is built with the interpreted reference on
rows and the prediction on columns, counting only pixels where both carry a valid class. From each
matrix we report overall accuracy (OA), Cohen's kappa, macro-F1, and mean IoU, and per class the
user's accuracy (UA, precision), producer's accuracy (PA, recall), F1, IoU, and reference support
(pixel count). Because pixels within a cell are spatially autocorrelated, per-class metrics also
carry a design-aware low-support flag that fires when a class appears in fewer than five cells or has
under 100 reference pixels, since a large pixel count concentrated in one or two cells is still only
one or two independent observations.

### 2.6 Inter-interpreter reference reliability

The 72 double-interpreted cells are used to quantify how reliable the reference itself is, per class.
For each reviewer pair a pixel-for-pixel confusion matrix is built on the shared footprint, and per
class the agreement F1 (the balanced probability that the two interpreters concur given one assigned
the class) is computed, both for the 10-class schema and the 5-class collapse. Confidence intervals
use a cluster (pair) bootstrap: the resampling unit is the pair, not the pixel, so within-cell
autocorrelation is respected. Classes are assigned a reliability tier on F1 (High at or above 0.70,
Moderate 0.50 to 0.70, Low below 0.50).

Two supporting diagnostics separate the kinds of disagreement. A spatial-tolerance analysis recomputes
per-class agreement under relaxed neighborhood matching, above a heterogeneity null, to isolate
boundary-misregistration disagreement from conceptual disagreement. A directional-asymmetry analysis
pools the directed reviewer confusion per class and reports an over-assignment index with pair-bootstrap
CIs, to test whether reviewers carry systematic class leanings.

### 2.7 Model accuracy against the reliability ceiling

To place model accuracy against reference reliability, each source's per-class F1 under the 5-class
collapse is computed against the adjudicated reference, pooled over the source's usable cells, with a
cluster (cell) bootstrap. These model F1 values are shown alongside the inter-interpreter agreement
F1 for the same class (the reliability ceiling from Section 2.6), so the gap between a source and the
human ceiling is visible per class.

### 2.8 Per-cell analyses

Beyond pooled metrics, each grid cell is treated as one sample. For every source and cell, the 5-class
confusion is built and the cell's macro-F1 is the mean of the per-class F1 over the classes present in
the reference or the prediction for that cell. A per-class version restricts to each change class and
reports its per-cell F1 distribution. The six sources are compared on the common set of cells usable
for all six (168 cells); each source is also summarized on its own full usable set, which differs in N
and is not a head-to-head ranking.

### 2.9 Spatial-structure diagnostics

Spatial coherence is measured within the interpreted cell footprints, so the reference sets the scale.
Per source we report the mean patch size and the area-weighted median patch size from 8-connected
component labeling, and Moran's I (queen contiguity) of the class raster as a smoothness diagnostic
(class codes are nominal, so this is read as spatial smoothness, not autocorrelation of a meaningful
variable). A complementary neighbor-change metric measures the fraction of horizontally-adjacent,
both-valid pixel pairs whose class differs, over the full rasters.

### 2.10 Training-cap sensitivity

To probe the sensitivity of the rare change classes to training size, a v2 classifier is trained with
the four change classes capped at 50, 100, 150, and 200 training points (stable classes held at 200)
and applied per bracket, pooled over the 180 cells. Per change class we report UA, PA, F1, predicted
pixel count, reference support, and the total unique-training-pixel ceiling, since the cap constrains
the small-pool classes (Beaver about 502 pixels, Insect/Disease about 662) far more than the
large-pool classes (Harvest about 18,800, Development about 8,500).

### 2.11 Software and reproducibility

All analyses are scripted (`scripts/`) and their curated outputs, with rendered figures and per-figure
captions, are in `reports/`. Confusion matrices, metric tables, and figures regenerate from the raw
predictions and the adjudicated reference; the raw prediction and sample sidecars are fetched from
cloud storage and are not committed.

---

## 3. Results

### 3.1 Overall accuracy by prediction source

Pooled over the five brackets, overall accuracy separates the smooth context-preserving embeddings
from the change-only and dot-product configurations (Table 1, Figure 2). Among the embeddings, v2
attains the highest pooled OA (0.659) and v6 the lowest (0.130); the spectral baseline spec_all sits
at 0.588 on its 168-cell pool. Kappa, macro-F1, and mean IoU follow the same ordering.
`[Interpretation: relate the v2/v3/v5 versus v4/v6 split to the context-preserving versus
change-only feature design.]`

[[TABLE T1]]

[[FIG reports/spectral_composite_classified_maps/comparison/compare_overall_metrics.png | Figure 2. Overall accuracy, kappa, macro-F1, and mean IoU by prediction source (10-class schema, pooled; embeddings on 180 cells, spec_all on 168).]]

### 3.2 Accuracy across temporal brackets

Overall accuracy by source and bracket is shown in Table 2 and Figure 3, with the 2018-2020 in-sample
control marked. The brackets use disjoint cell sets, so these are five independent assessments rather
than a transfer curve. `[Interpretation: comment on which sources hold up off the training window and
which do not, keeping the disjoint-cell caveat in view.]`

[[TABLE T2]]

[[FIG reports/transfer_confusion_adjudicated/oa_by_bracket.png | Figure 3. Overall accuracy per source across the five NAIP brackets (10-class schema, adjudicated reference; 2018-2020 is the in-sample control).]]

### 3.3 Per-class accuracy, 10-class schema

Per-class F1, pooled, is given in Table 3, with per-class UA, PA, F1, IoU, and support for every
source in the supplementary long table (Table S1). Reference support is reported per class, and is
low for the rare change classes, so their per-class numbers rest on little data.
`[Interpretation: identify the classes that drive the aggregate differences.]`

[[TABLE T3]]

[[FIG reports/transfer_confusion_adjudicated/cm_v2_2018_2020.png | Figure 5a. Per-class confusion for v2, in-sample control bracket 2018-2020 (10-class, 36 cells; raw counts colored by row proportion, PA column and UA row, OA and kappa in the corner). See the consistency report on the per-bracket versus pooled basis.]]

[[FIG reports/spectral_composite_classified_maps/cm_specall_pooled.png | Figure 5b. Per-class confusion for spec_all, pooled (10-class, 168 cells).]]

### 3.4 Change-focused accuracy under the 5-class collapse

Under the 5-class collapse on the common 168-cell set, overall accuracy is high for every source
because the landscape is stable-dominated (the all-Stable baseline OA is 0.985), so kappa and
macro-F1 carry the change signal (Table 4, Figure 4). The pooled 5-class OA is highest for v4 (0.897)
and lowest for v6 (0.602). `[Interpretation: contrast the 5-class OA ordering with the 10-class
ordering in Table 1, noting the role of the stable-dominated baseline and of v4's behavior when the
change classes are folded.]`

[[TABLE T4]]

[[FIG reports/collapsed_5class_confusion/confusion_v2.png | Figure 4a. Pooled 5-class confusion for v2 (180 cells).]]

[[FIG reports/spectral_composite_classified_maps/collapsed_5class/confusion_specall.png | Figure 4b. Pooled 5-class confusion for spec_all (168 cells).]]

### 3.5 Reliability of the interpreted reference

Inter-interpreter agreement over the 72 double-interpreted cells sets a per-class reliability ceiling
(Tables 5 and 6, Figures 6 and 7). Mean per-pair overall agreement is 0.77 (kappa 0.60). In the
5-class collapse, interpreters agree almost perfectly on Stable (F1 0.993) and well on Harvest (0.749),
and fall to Low reliability on Development (0.295), Insect/Disease (0.229), and Beaver (0.077). In the
10-class schema, Water, Forest, and Agriculture are High reliability while Grass/Shrub and Wetland are
Low. `[Interpretation: state the consequence for model evaluation on the Low-reliability classes.]`

[[TABLE T6]]

[[FIG reports/interpreter_agreement/per_class_agreement_forest_5class.png | Figure 7. Inter-interpreter per-class agreement F1 with 95% cluster (pair) bootstrap CIs, 5-class collapse, 72 pairs.]]

The full 10-class agreement table (Table 5) and its forest plot (Figure 6) are reported in the
supplement-adjacent material; the pooled interpreter confusion matrix is Figure S1.

### 3.6 Model accuracy against the reliability ceiling

Placing each source's per-class 5-class F1 next to the inter-interpreter ceiling shows the two
regimes per class (Table 7, Figure 8). On Stable the sources approach the ceiling (v4 0.947 versus
0.993). On Harvest the best source reaches 0.146 (v4) against a ceiling of 0.749, a large gap. On
Development, Insect/Disease, and Beaver both the sources and the ceiling are low.
`[Interpretation: distinguish the reducible gap on Harvest from the reference-limited classes.]`

[[TABLE T7]]

[[FIG reports/model_vs_interpreter_5class/forest_5class_v4.png | Figure 8. Per-class F1 for v4 (colored) against the inter-interpreter ceiling (grey), 5-class collapse, with 95% bootstrap CIs. One panel per source in reports/model_vs_interpreter_5class/.]]

### 3.7 Per-cell distributions

The per-cell macro-F1 distributions (Table 10, Figure 11) and the per-class change-class F1
distributions (Table 11, Figure 12) summarize how each source does cell by cell rather than in the
pool. `[Interpretation: note where a distribution spikes at zero for a change class and what that
indicates about commission or omission.]`

[[TABLE T10]]

[[FIG reports/per_cell_f1_5class/f1_violin_common.png | Figure 11. Per-cell 5-class macro-F1 by source on the common 168-cell set, median (bar) and mean (diamond) marked.]]

[[TABLE T11]]

[[FIG reports/per_cell_change_f1/change_f1_violins.png | Figure 12. Per-cell F1 for the four change classes by source (5-class collapse, common set; contributing cell counts annotated).]]

### 3.8 Spatial structure and speckle

The spatial-structure diagnostics (Table 9, Figure 9) and the neighbor-change speckle metric (Table
S3, Figure 10) characterize the maps' spatial coherence. The interpreted reference has a mean patch
size of 0.79 ha and Moran's I 0.75; among the sources, v6 is the outlier (mean patch 0.02 ha, Moran's
I 0.08, neighbor-change 0.781), consistent with its per-pixel dot-product format, while v2, v3, and
v5 cluster near the reference scale. `[Interpretation: connect the spatial-structure ordering to the
accuracy ordering and to the point that similar aggregate accuracy can hide different spatial
predictions.]`

[[TABLE T9]]

[[FIG reports/spatial_structure/with_spec_all/patch_size_ecdf_area_weighted.png | Figure 9a. Area-weighted patch-size ECDF by source (within interpreted footprints).]]

[[FIG reports/spatial_structure/with_spec_all/morans_i_by_source.png | Figure 9b. Moran's I by source.]]

[[FIG reports/model_comparison/model_speckle_crops.png | Figure 10. Cropped classified-map detail per embedding variant illustrating the neighbor-change speckle metric.]]

### 3.9 Training-cap sensitivity for the change classes

Table 8 and Figure 13 report how the change-class metrics move as the training cap varies from 50 to
200 points, with the training ceiling per class given so the cap is read relative to the available
pool. `[Interpretation: state, for Beaver and Insect/Disease especially, whether lower caps trade
commission for recall or simply relabel, per the interpretive guardrail in the analysis note.]`

[[TABLE T8]]

[[FIG reports/sensitivity_changecap/change_classes_ua_pa_vs_cap.png | Figure 13. User's and producer's accuracy for the four change classes versus the training cap (v2, 10-class, 180 cells).]]

### 3.10 Robustness

The choice of which reviewer represents a multi-interpreted cell was tested by repeating the
pick-one-per-location draw 100 times on the earlier snapshot; the version ordering is stable (Table
S2). Map speckle by variant is reported in Table S3.

[[TABLE S2]]

---

*End of draft. Sections marked `[Interpretation:]` and the missing study-area figure (Figure 1) are
left for the author. See `manuscript_tables_figures_plan.md` for the full candidate set and
`consistency_report.md` for the basis caveats that any combined statement must respect.*
