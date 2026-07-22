# Consistency report

Label, cell-count, and basis inconsistencies found while formatting the existing results into
manuscript tables and captions. Each item is for the author to resolve; nothing here was silently
reconciled. Items are ordered by how much they affect cross-table comparison.

## A. Cell-count bases (168 versus 180)

The evaluation cell set is not uniform across tables, for documented reasons.

- Embedding variants v2 to v6 are scored on 180 cells (pooled). Spec_all is scored on 168 cells,
  since 12 spec_all prediction rasters are entirely nodata in the out-of-sample brackets
  (2019-2021: 2 cells; 2020-2022: 4; 2021-2023: 6). This is stated in
  `spectral_composite_classified_maps/note.md`.
- Tables 1, 2, and 3 (10-class) keep each source on its native basis and label N explicitly (180 for
  embeddings, 168 for spec_all). The per-class support in Table 3 is therefore given twice, once for
  the 180-cell embedding pool and once for the 168-cell spec_all pool.
- Tables 4, 7, 10, and 11 (5-class) use the common 168-cell set for all six sources, so within those
  tables the basis is uniform.
- Action for the author: when a single sentence compares an embedding number from a 180-cell table
  with a spec_all number, note the different N, or restrict to the common set. Do not mix 168 and 180
  silently inside one claim.

## B. Two different 5-class collapses (RESOLVED)

Status: resolved. The 5-class collapse now has a single canonical definition, applied consistently
across the whole analysis.

Canonical 5-class collapse (the only correct definition):
- Stable = {forest, urban, water, agriculture, grass/shrub, wetland}, plus Harvest = {1},
  Development = {2}, Insect/Disease = {10}, and Beaver = {9}.
- Reference-only handling of the two non-schema CKIT labels: Other (CKIT 13) folds into Stable, and
  Unknown (CKIT 10) is excluded (dropped). Fire (CKIT 40) is absent and excluded. This differs from
  the 10-class analysis, which excludes both Other and Unknown, since Other has no 10-class home; under
  the 5-class collapse Other is a stable land-cover state and becomes Stable.

Resolution: the collapse is defined once in `scripts/collapsed_5class_confusion.py` as
`collapse_reference` (CKIT to 5-class) and `collapse_prediction` (10-class to 5-class), built on
`_REF_COLLAPSE` and `_MODEL_COLLAPSE`. Every 5-class script now imports these. The scripts that had
previously excluded Other were corrected to fold it into Stable: `per_cell_f1_5class.py` (Table 10),
`per_cell_change_f1.py` (Table 11), `model_class_ci_5class.py` (Table 7), and `interpreter_class_ci.py`
(Table 6). The scripts that were already canonical are unchanged: `spectral_collapsed_5class.py`
(Table 4), `collapsed_5class_confusion.py` (Table S4), `build_transfer_confusion_5class.py`, and the
changecap and disagreement figures. Table 4 and Table S4 were verified byte-identical after
regeneration.

Numeric effect (small, as expected): across the 180 adjudicated reference cells, 33,978 Other pixels
in 25 cells moved from excluded to Stable, and 4,139 Unknown pixels in 10 cells stayed excluded. Per
source, the Stable reference support rose by 33,978 pixels for the embeddings (180 cells) and by
32,938 for spec_all (168 cells, since 1,040 Other pixels fall in the 12 blank spec_all cells). Pooled
per-class F1 and per-cell F1 were unchanged to three decimals, since Stable already dominates. The
inter-interpreter Stable support (72 pairs) rose by 28,519 pixels with F1 unchanged at 0.993.

## C. No pooled 10-class embedding confusion matrix

The embedding confusion matrices are per-bracket only (25 matrices, no pooled matrix), by design, so
the pooled 10-class accuracy in Table 1 has no single matching confusion-matrix figure for the
embeddings. Spec_all does have a pooled 10-class matrix (168 cells). Figure 5 therefore pairs a
per-bracket embedding matrix (the in-sample control 2018-2020, 36 cells) with a pooled spec_all
matrix (168 cells); these are different bases. Action: either accept the mixed-basis figure with the
caption caveat, or add a pooled 10-class embedding matrix if one is wanted.

## D. Interpreter agreement basis (72 pairs) versus model evaluation (180/168 cells)

The inter-interpreter agreement tables (T5, T6) and figures are computed on the 72 double-interpreted
cells, scored as 72 reviewer pairs. This is a different and smaller basis than the 180-cell (168 for
spec_all) model evaluation. That is expected, since agreement needs two interpretations of the same
cell, but the two Ns should not be conflated. The model-versus-interpreter figure (T7, Figure 8)
deliberately overlays the two bases and labels each, which is the intended use.

## E. Class-name drift between model and interpreter outputs

- The 10-class model CSVs use short lowercase codes: `ag`, `grass_shrub`, `insect_disease`, and
  `development` versus `urban`. The interpreter confusion CSV uses display names: Agriculture,
  Grass/Shrub, Insect/Disease, and both Urban and Development. All manuscript tables here map to the
  display names (Agriculture, Grass/Shrub, Insect/Disease, Urban, Development) for consistency.
- The interpreter global confusion matrix carries 13 legend classes (adds Unknown, Other, and Fire),
  while the model 10-class schema excludes Unknown (10), Other (13), and Fire (40, zero pixels). This
  is the intended schema difference, not an error, but the two figures list different class sets, so
  a reader comparing them should be told the interpreter figure is on the full CKIT legend.
- Action: adopt one display-name set in the manuscript (the 10 names used in these tables) and note
  the three extra legend classes only where the interpreter figures appear.

## F. Adjudicated versus earlier (superseded) results

- The current reference is 180 locations with adjudication (`exports/truth_selections.csv`). The
  `model_comparison/` and `model_comparison_2018_2020/` folders reflect an earlier 154-location
  snapshot with random dedup and are superseded for headline accuracy. Only Tables S2 and S3 draw
  from that arm, and both are labeled as the earlier snapshot. Do not quote a 154-basis number next
  to a 180-basis number without saying so.
- Figure 2.9 (classified-map speckle) was regenerated from the current 180-cell pipeline, so it no
  longer draws from the superseded arm. Table S3 (map speckle) still holds the earlier-snapshot
  neighbor-change values and is on a different basis than Figure 2.9 until regenerated.
- The adjudicated 10-class results (`transfer_confusion_adjudicated/`) and the combined comparison
  (`comparison/`) are the current basis and are what Tables 2.3 to 2.5 use.

## G. Rounding applied (stated for the record)

- Accuracy-like quantities (OA, kappa, macro-F1, mean IoU, per-class UA, PA, F1, IoU, agreement F1,
  and their CI bounds) are rounded to 3 decimals.
- Patch sizes are rounded to 2 decimals (hectares); Moran's I to 2 decimals (mean) and 3 (std).
- Support and predicted-pixel counts are integers, comma-grouped in the docx.
- No value was altered beyond rounding. Where a source stored fewer decimals, the stored value is
  used as is (for example the dedup and design-CI CSVs).
