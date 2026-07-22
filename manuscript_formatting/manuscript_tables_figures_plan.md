# Manuscript tables and figures: inventory and proposal

This is a PROPOSAL for the author to accept, edit, reorder, or override. It does not decide the
paper's structure. Every candidate table traces to a source CSV already in `reports/`; no numbers
were computed or hand-typed here, only read and rounded. Candidate figures point to figures already
rendered in `reports/`. Flagged issues (missing artifacts, inconsistent bases) are listed in the
final section and cross-referenced in `consistency_report.md`.

Deliverables in this folder:
- `manuscript_tables_figures_plan.md` (this file)
- `manuscript_tables.docx` (all candidate tables, styled, plus the draft captions as a second section)
- `tables/T*.csv` and `tables/S*.csv` (one tidy CSV per table; `_tidy.csv` where a wider long form exists)
- `figure_captions.md` (descriptive captions)
- `consistency_report.md` (label, cell-count, and basis inconsistencies)

## 1. Results artifacts found (inventory)

Format column: CSV = tidy or matrix CSV; PNG = rendered figure; TXT/MD = note or metrics text.

### Accuracy and confusion, embeddings and spectral
| Artifact | Contents | Format |
|---|---|---|
| `spectral_composite_classified_maps/comparison/overall_comparison.csv` | OA, macro-F1, mean IoU, kappa, n_cells, total_pixels per source (v2-v6, spec_all) x bracket + pooled; control flag | CSV |
| `spectral_composite_classified_maps/comparison/combined_metrics_long.csv` | per-class UA, PA, F1, IoU, support, cells_present per source x bracket + pooled | CSV |
| `transfer_confusion_adjudicated/transfer_metrics_long.csv` | same, embeddings only, per-bracket (no pooled row) | CSV |
| `transfer_confusion_adjudicated/cm_<v>_<bracket>.csv` | 25 count matrices, 10x10, reference on rows | CSV |
| `transfer_confusion_adjudicated/oa_by_bracket.png`, `oa_by_variant_bracket.csv` | OA by variant x bracket | PNG, CSV |
| `spectral_composite_classified_maps/cm_specall_<bracket>.csv`, `cm_specall_pooled.csv` | spectral count matrices, per-bracket + pooled (168) | CSV |
| `spectral_composite_classified_maps/spectral_metrics_long.csv` | spectral per-class metrics per bracket + pooled | CSV |
| `transfer_confusion/` (non-adjudicated) | earlier random-dedup counterpart of the adjudicated set | CSV, PNG |

### 5-class collapse
| Artifact | Contents | Format |
|---|---|---|
| `spectral_composite_classified_maps/collapsed_5class/comparison_collapsed.csv` | pooled 5-class OA, all-Stable baseline, kappa, macro-F1, mean IoU, all six sources on 168 cells | CSV |
| `spectral_composite_classified_maps/collapsed_5class/metrics_long.csv` | per-class 5-class metrics with design-based and bootstrap CIs (spec_all) | CSV |
| `collapsed_5class_confusion/metrics_long.csv` | design-based pooled 5-class metrics with CIs, embeddings | CSV |
| `collapsed_5class_confusion/confusion_<v>.png`, `confusion_<v>_counts.csv`, `_rownorm.csv` | pooled 5-class matrices, embeddings (180) | PNG, CSV |
| `transfer_confusion_adjudicated_5class/transfer_metrics_long.csv`, `cm_<v>_<bracket>.csv` | per-bracket 5-class metrics and matrices, fold-Other collapse | CSV |

### Interpreter reference reliability
| Artifact | Contents | Format |
|---|---|---|
| `interpreter_agreement/per_class_agreement_ci.csv` (+ `_5class.csv`) | per-class agreement F1, IoU, 95% pair-bootstrap CIs, reliability tier | CSV |
| `interpreter_agreement/per_class_agreement_forest.png` (+ `_5class.png`) | forest plots of the above | PNG |
| `interpreter_agreement/global_confusion_matrix.csv`/`.png` | pooled interpreter-vs-interpreter confusion | CSV, PNG |
| `interpreter_agreement/per_pair_metrics.csv`, `by_reviewer_pair.csv`, `class_disagreement_ranked.csv`, `per_class_contested.csv` | pair-level and boundary-level agreement | CSV |
| `interpreter_agreement/spatial_tolerance_delta.csv`/`.png` | edge-driven versus conceptual disagreement diagnostic | CSV, PNG |
| `interpreter_agreement/reviewer_class_overassignment.csv`, `reviewer_directed_classpairs.csv` | reviewer directional bias | CSV |
| `interpreter_agreement/geometry/*`, `change_change_conflicts/*`, `change_stable_conflicts/*` | disagreement geometry and change-type conflicts | CSV, PNG |

### Model versus interpreter, per-cell, spatial, sensitivity
| Artifact | Contents | Format |
|---|---|---|
| `model_vs_interpreter_5class/model_per_class_ci_5class.csv`, `forest_5class_<src>.png` | per-class model F1 vs interpreter ceiling, 5-class, cell-bootstrap CIs | CSV, PNG |
| `per_cell_f1_5class/per_cell_f1_summary.csv`, `per_cell_f1_allsources.csv`, violins | per-cell 5-class macro-F1 by source | CSV, PNG |
| `per_cell_change_f1/change_f1_summary.csv`, `per_cell_change_f1.csv`, violins/heatmap | per-cell change-class F1 by source | CSV, PNG |
| `spatial_structure/spatial_structure_summary.csv` (+ `with_spec_all/`) | mean patch, median-by-area, Moran's I per source | CSV, PNG |
| `spatial_structure/patch_size_by_class.csv` | per-class patch statistics | CSV |
| `sensitivity_changecap/sensitivity_metrics_long.csv` (+ `_5class`) | change-cap sensitivity, per-class UA/PA/F1, predicted pixels, train ceiling | CSV, PNG |
| `model_comparison/model_speckle.csv`, `dedup_sensitivity_summary.csv` | speckle and dedup robustness | CSV, PNG |
| `binary_change_no_change/*` | binary change-vs-no-change confusion and metrics | CSV, PNG |
| `window_sampling_by_approach/Case_*/window_sampling_metrics.csv` | window-aggregation sampling sweep | CSV, PNG |
| `Case_ABCD_sampling/`, `Case_ABCD_sampling_5class/` | sampling-design study | CSV, PNG |
| `TC_training/*` | Tasseled Cap training-signal diagnostics | PNG |

## 2. MAIN-TEXT tables (Chapter 2 numbering, see renumber_manifest.md)

Built (tidy CSV + docx). Numbered in the thesis per-chapter scheme.

| New | Old | Table | File |
|---|---|---|---|
| Table 2.1 | Table 2.1 | Ten-class classification schema | tables/schema_table/table_2_1_schema.csv/.docx |
| Table 2.2 | Table 2.2 | Embedding configurations (not present; see flags) | none |
| Table 2.3 | Table 1 | Pooled overall accuracy by source (10-class) | tables/table_2_3.csv |
| Table 2.4 | Table 2 | Overall accuracy by source and bracket (10-class) | tables/table_2_4.csv |
| Table 2.5 | Table 3 | Per-class F1 by source (10-class, pooled) | tables/table_2_5.csv |
| Table 2.6 | Table 9 | Spatial-structure diagnostics by source | tables/table_2_6.csv |
| Table 2.7 | Table 8 | Training-cap sensitivity, change classes | tables/table_2_7.csv |
| Table 2.8 | Table 5 | Inter-interpreter reliability, 10-class (may move to Ch. 3) | tables/table_2_8.csv |

Kept but not assigned a Chapter 2 number (the 5-class results appear as figures 2.5, 2.6, 2.11, 2.12):

| Old | Table | File |
|---|---|---|
| Table 4 | Pooled accuracy by source (5-class collapse) | tables/T4.csv |
| Table 6 | Inter-interpreter per-class agreement, 5-class | tables/T6.csv |
| Table 7 | Model F1 vs interpreter ceiling (5-class) | tables/T7.csv |
| Table 10 | Per-cell 5-class macro-F1 by source | tables/T10.csv |
| Table 11 | Mean per-cell F1 by change class and source | tables/T11.csv |

## 3. Proposed SUPPLEMENTARY tables

Built: S1-S4. Proposed but not yet built: S5+ (source CSVs named for the author to request).

| ID | Table | Source CSV | Status |
|---|---|---|---|
| S1 | Full per-class UA/PA/F1/IoU/support by source (10-class, pooled) | combined_metrics_long.csv | built |
| S2 | Dedup-selection sensitivity of OA | dedup_sensitivity_summary.csv | built |
| S3 | Map speckle (neighbor-change) by variant | model_speckle.csv | built |
| S4 | Design-based pooled 5-class metrics (point + CI in source) | collapsed_5class_confusion/metrics_long.csv | built |
| S5 | Per-bracket per-class metrics, all sources | combined_metrics_long.csv | proposed |
| S6 | Reviewer directional over-assignment index | reviewer_class_overassignment.csv | proposed |
| S7 | Spatial-tolerance delta (edge vs conceptual disagreement) | spatial_tolerance_delta.csv | proposed |
| S8 | Change/stable and change/change conflict totals | change_stable_conflicts, change_change_conflicts | proposed |
| S9 | Window-aggregation sampling sweep (OA/kappa vs W) | window_sampling_metrics.csv | proposed |
| S10 | Per-class patch-size statistics | patch_size_by_class.csv | proposed |
| S11 | Binary change-vs-no-change accuracy | binary_change_no_change | proposed |

## 4. Proposed figures

See `figure_captions.md` for full descriptive captions and `renumber_manifest.md` for the old-to-new
mapping. Chapter 2 main figures: 2.1 study area, 2.2 workflow, 2.3 embedding configurations, 2.4 OA by
bracket, 2.5 per-cell F1 violins, 2.6 change-class per-cell F1, 2.7 area-weighted patch-size ECDF, 2.8
Moran's I, 2.9 speckle crops, 2.10 change-cap sensitivity, 2.11 model-vs-interpreter forests, 2.12
pooled confusion matrices. Flagged (number pending): classification schema (former 1b), overall
accuracy bars (former 2), interpreter agreement forests (former 6 and 7), mean patch size per class
(former 9 panel B). Supplementary: S1 interpreter global confusion, S2 boundary disagreement, S3
spectral-vs-embedding change comparison, S4 dedup sensitivity, S5 Tasseled Cap diagnostics, S6
reviewer over-assignment, S7 top-disagreement panels.

## 5. Flagged issues (see consistency_report.md)

1. 168 versus 180 cells. Embedding pooled metrics use 180 cells; spec_all uses 168 (12 blank spec_all
   rasters). Tables 2.3 to 2.5 keep both sources on their native bases and label N; the 5-class tables
   (former Tables 4, 7, 10, 11, now unassigned) use the common 168-cell set. This must not be mixed
   silently within one comparison.
2. Two different 5-class collapses: RESOLVED. A single canonical collapse (Other folds into Stable,
   Unknown excluded) is now used everywhere; see consistency_report.md item B.
3. No pooled 10-class embedding confusion matrix exists (embeddings are per-bracket only), so
   Figure 2.12 mixes a per-bracket embedding panel with a pooled spectral panel. Flagged, not
   reconciled.
4. Superseded arm. `model_comparison/` and `model_comparison_2018_2020/` reflect an earlier
   154-location snapshot with random dedup; the current reference set is 180 locations with
   adjudication. Only S2 and S3 draw from that arm, and both are labeled as the earlier snapshot.
5. Structural renumbering flags: Figure 9 split into 2.7 and 2.8 with panel B unassigned, old Figure 4
   and Figure 5 both map to 2.12, and no Table 2.2 exists. See renumber_manifest.md.
