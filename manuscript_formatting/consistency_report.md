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

## B. Two different 5-class collapses

There are two 5-class collapse rules in the repository, and they do not produce the same pooled
numbers.

- Exclude rule (drops Unknown and Other): used by `collapsed_5class/comparison_collapsed.csv`
  (Table 4), `model_per_class_ci_5class.csv` (Table 7), `per_cell_f1_5class` (Table 10),
  `per_cell_change_f1` (Table 11), and the interpreter 5-class agreement (Table 6).
- Fold rule (folds Other into Stable, drops Unknown and Fire): used by
  `transfer_confusion_adjudicated_5class/` (the per-bracket 5-class matrices).
- Consequence: the pooled 5-class OA in Table 4 is not a re-aggregation of the per-bracket 5-class
  matrices, and Table S4 (design-based CIs from `collapsed_5class_confusion/metrics_long.csv`) may
  rest on a different collapse and cell set than Table 4. Confirm which collapse each 5-class number
  uses before combining Table 4 and Table S4 in one statement.
- Action for the author: pick one 5-class collapse as the manuscript standard (the exclude rule is
  the more widely used here) and state it once in Methods; footnote any table that uses the other.

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
- The adjudicated 10-class results (`transfer_confusion_adjudicated/`) and the combined comparison
  (`comparison/`) are the current basis and are what Tables 1 to 3 use.

## G. Rounding applied (stated for the record)

- Accuracy-like quantities (OA, kappa, macro-F1, mean IoU, per-class UA, PA, F1, IoU, agreement F1,
  and their CI bounds) are rounded to 3 decimals.
- Patch sizes are rounded to 2 decimals (hectares); Moran's I to 2 decimals (mean) and 3 (std).
- Support and predicted-pixel counts are integers, comma-grouped in the docx.
- No value was altered beyond rounding. Where a source stored fewer decimals, the stored value is
  used as is (for example the dedup and design-CI CSVs).
