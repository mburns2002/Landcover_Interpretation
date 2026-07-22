# Draft figure captions

Descriptive captions for the candidate figures, drawn from existing rendered figures in `reports/`.
Captions state what each figure shows, its data basis (cells, sources, brackets, pooled or
per-bracket), the metric, and essential method detail. They do not assert findings or conclusions;
interpretive sentences are left to the author. Each caption names the source PNG for traceability.
Variant labels are v2 to v6 (AlphaEarth embedding feature sets) and spec_all (spectral composite).
The 5-class collapse is Stable, Harvest, Development, Insect/Disease, and Beaver.

## Main-text candidate figures

### Figure 1. Study area
Study area in the western Great Lakes region of the United States, spanning Wisconsin, Minnesota, and
the Michigan Upper Peninsula, in EPSG:5070 (CONUS Albers, equal-area). Shows the study grid extent,
the Great Lakes, the seven GLKN park units used here (each outlined and named), and the 180
interpreted reference cells (black squares), with a conterminous-United-States locator inset, a
kilometer scale bar, and a north arrow. State and Great Lakes boundaries are from Natural Earth; the
grid, park boundaries, and interpreted cells are from the Google Earth Engine exports. Source:
`manuscript_formatting/figure_study_area/figure1_study_area.png` (and `.pdf`). Full caption in
`manuscript_formatting/figure_study_area/figure1_caption.md`. A class-schema panel (10-class and 5-class collapse) is not
yet included and could be added as a second panel if wanted.

### Figure 1b. Classification schema
The 10-class classification schema and its 5-class collapse. Left, the 10 classes grouped into the six
no-change (stable) classes and the four change (disturbance) classes, each with its class code and
legend color. Right, the 5-class collapse that folds the six stable classes into a single Stable class
and keeps the four change classes. Colors are the project class legend. Source:
`manuscript_formatting/figure_study_area/figure_class_schema.png` (and `.pdf`). Full caption in
`manuscript_formatting/figure_study_area/figure_class_schema_caption.md`. Can serve as Figure 1b (paired with the study
area) or a standalone methods figure.

### Figure 2. Overall accuracy by prediction source
Overall accuracy, Cohen's kappa, macro-F1, and mean IoU for the six prediction sources (embedding
variants v2 to v6 and the spectral spec_all classifier), 10-class schema, pooled across the five
NAIP brackets against the adjudicated interpreted reference. Embedding variants are scored on 180
cells and spec_all on 168 cells. Bars are grouped by metric. Source:
`reports/spectral_composite_classified_maps/comparison/compare_overall_metrics.png`. Corresponds to
Table 1.

### Figure 3. Overall accuracy across temporal brackets
Overall accuracy per source across the five NAIP brackets (2017-2019, 2018-2020, 2019-2021,
2020-2022, 2021-2023), 10-class schema, adjudicated reference. The 2018-2020 bracket is the
in-sample control (training window). Each bracket uses a disjoint 36-cell set (embeddings) so points
are independent per-bracket assessments rather than a controlled transfer curve; spec_all uses 36,
36, 34, 32, and 30 cells across the brackets. Source:
`reports/transfer_confusion_adjudicated/oa_by_bracket.png`. Corresponds to Table 2.

### Figure 4. Pooled confusion matrices, 5-class collapse
Pooled confusion matrices for the embedding variants and spec_all under the 5-class collapse,
cells are raw pixel counts colored by row proportion, with a producer's accuracy (PA) column and
reference support, a user's accuracy (UA) row and predicted support, and overall accuracy and kappa
in the corner. Reference on rows, prediction on columns. Embedding matrices pool 180 cells
(`reports/collapsed_5class_confusion/confusion_v2.png` through `confusion_v6.png`); the spec_all
matrix pools 168 cells (`reports/spectral_composite_classified_maps/collapsed_5class/confusion_specall.png`).
Unknown and Other reference pixels are dropped in this collapse. Corresponds to Table 4.

### Figure 5. Per-class confusion, 10-class, representative sources
Per-class confusion matrices for a representative smooth embedding variant (v2) and spec_all,
10-class schema, in the count-plus-PA/UA style (raw counts colored by row proportion, PA column with
reference support, UA row with predicted support, overall accuracy and kappa in the corner).
FLAGGED BASIS: the embedding matrices are per-bracket, not pooled, so this figure uses the
in-sample control bracket 2018-2020, 36 cells
(`reports/transfer_confusion_adjudicated/cm_v2_2018_2020.png`); the spec_all matrix is pooled over
168 cells (`reports/spectral_composite_classified_maps/cm_specall_pooled.png`). No pooled 10-class
embedding confusion matrix exists in the repository, so the two panels are on different bases and
should not be read as like-for-like; see the consistency report.

### Figure 6. Inter-interpreter per-class agreement, 10-class
Forest plot of per-class inter-interpreter agreement F1 with 95% cluster (pair) bootstrap confidence
intervals, 10-class schema, over the 72 double-interpreted cells. Each dot is the pooled point
estimate and its bar is the confidence interval; dashed vertical lines mark the Low, Moderate, and
High reliability thresholds at 0.50 and 0.70. F1 is the balanced probability that two interpreters
concur given one assigned the class. Source:
`reports/interpreter_agreement/per_class_agreement_forest.png`. Corresponds to Table 5.

### Figure 7. Inter-interpreter per-class agreement, 5-class collapse
Forest plot of per-class inter-interpreter agreement F1 with 95% cluster (pair) bootstrap confidence
intervals under the 5-class collapse, over the 72 double-interpreted cells, same method and
thresholds as Figure 6. Source:
`reports/interpreter_agreement/per_class_agreement_forest_5class.png`. Corresponds to Table 6.

### Figure 8. Per-class model F1 versus the inter-interpreter ceiling, 5-class
Per-class F1 under the 5-class collapse for each prediction source (colored circle) against the
adjudicated reference, next to the inter-interpreter agreement for the same class (grey diamond),
each with a 95% bootstrap confidence interval. Model F1 uses a cluster (cell) bootstrap over the
source's usable cells (v2 to v6 on 180 cells, spec_all on 168); the interpreter ceiling uses a
cluster (pair) bootstrap over 72 pairs. One panel per source. Sources:
`reports/model_vs_interpreter_5class/forest_5class_v2.png` through `forest_5class_v6.png` and
`forest_5class_spec_all.png`. Corresponds to Table 7.

### Figure 9. Spatial structure by source
Spatial-structure diagnostics measured within the interpreted cell footprints. Panel A, area-
weighted patch-size ECDF (cumulative fraction of class area by patch size, log axis); panel B, mean
patch size per class; panel C, Moran's I per source. Sources are the adjudicated interpreted
reference and each source's temporally-matched per-bracket prediction; patches from 8-connected
labeling; Moran's I is queen-contiguity autocorrelation of the nominal class raster, read as a
smoothness diagnostic. Sources:
`reports/spatial_structure/with_spec_all/patch_size_ecdf_area_weighted.png`,
`mean_patch_size_by_class.png`, and `morans_i_by_source.png`. Corresponds to Table 9.

### Figure 10. Model-map speckle
Cropped detail of each embedding variant's classified map at a common location, illustrating the
per-pixel character captured by the neighbor-change metric (fraction of horizontally-adjacent,
both-valid pixel pairs whose class differs, over the full rasters). Source:
`reports/model_comparison/model_speckle_crops.png`. Corresponds to Table S3.

### Figure 11. Per-cell 5-class macro-F1 by source
Per-grid-cell macro-F1 under the 5-class collapse for each source on the common 168-cell set, one
point per cell, violin with the median (bar) and mean (diamond) marked. Macro-F1 is averaged over
the classes present in the reference or the prediction for that cell. Source:
`reports/per_cell_f1_5class/f1_violin_common.png`. Corresponds to Table 10.

### Figure 12. Per-cell F1 for the change classes
Per-cell F1 for each change class (Harvest, Development, Insect/Disease, Beaver) by source under the
5-class collapse, on the common 168-cell set, one point per contributing cell. A cell contributes to
a class where that class is present in the reference or the prediction, so the contributing cell
count differs across sources and is annotated. Source:
`reports/per_cell_change_f1/change_f1_violins.png`. Corresponds to Table 11.

### Figure 13. Training-cap sensitivity for the change classes
User's accuracy (UA) and producer's accuracy (PA) for the four change classes as the change-class
training cap varies over 50, 100, 150, and 200 points (stable classes held at 200), v2 embedding
classifier, 10-class schema, pooled over 180 cells. Panel highlights beaver, whose small training
pool (about 502 pixels) makes the cap a large fraction of the pool. Sources:
`reports/sensitivity_changecap/change_classes_ua_pa_vs_cap.png` and `beaver_headline.png`.
Corresponds to Table 8.

## Supplementary candidate figures

### Figure S1. Interpreter global confusion matrix
Pooled inter-interpreter confusion matrix over all double-interpreted pairs, raw pixel counts
colored by row proportion, with a PA column (agreement given Reviewer A's label) and Reviewer A
support, a UA row (agreement given Reviewer B's label) and Reviewer B support, and overall agreement
and kappa in the corner. Both axes are interpreters, so there is no ground-truth reference and PA and
UA are the two conditional agreement rates. Source:
`reports/interpreter_agreement/global_confusion_matrix.png`.

### Figure S2. Class boundaries driving inter-interpreter disagreement
Class boundaries ranked by their share of total inter-interpreter disagreement pixels. Source:
`reports/interpreter_agreement/class_disagreement_top.png`.

### Figure S3. Spectral-versus-embedding change-class comparison
Pooled change-class UA and PA comparison between spec_all and the embedding variants, 10-class
schema. Sources: `reports/spectral_composite_classified_maps/comparison/compare_perclass_ua_pooled.png`,
`compare_perclass_pa_pooled.png`, and `compare_change_class_ua_by_bracket.png`.

### Figure S4. Dedup-selection sensitivity
Distribution of overall accuracy per version across 100 random pick-one-interpretation-per-location
draws, on the earlier 154-location snapshot. Source:
`reports/model_comparison/dedup_sensitivity_box.png`. Corresponds to Table S2.

### Figure S5. Tasseled Cap training-signal diagnostics
Tasseled Cap change-space diagnostics of the training points: delta scatter, mean-delta class
signature, and the linear-discriminant projection of class separability. Sources:
`reports/TC_training/tc_delta_scatter.png`, `tc_mean_delta_heatmap.png`, and `tc_lda_projection.png`.

### Figure S6. Reviewer directional over-assignment
Per-reviewer class over-assignment index (log2 ratio of pixels a reviewer claims for a class but the
partner does not, versus the reverse) with 95% cluster (pair) bootstrap confidence intervals, over
all 72 pairs. Source: `reports/interpreter_agreement/reviewer_overassignment_heatmap.png`.

### Figure S7. Top-disagreement map panels
Representative cell panels showing the interpreted reference and the prediction maps at the cells
where a given source disagrees most with the reference, with an agree/disagree panel. Sources under
`reports/spectral_composite_classified_maps/comparison/top_disagreement_maps/` and
`reports/model_vs_interpreter_5class/` (per-source disagreement panels).
