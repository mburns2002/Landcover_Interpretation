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

## 2. Proposed MAIN-TEXT tables

Built (tidy CSV + docx). Author decides inclusion.

| ID | Table | Rationale | Source CSV |
|---|---|---|---|
| T1 | Pooled overall accuracy by source (10-class) | Headline accuracy comparison, one row per source | overall_comparison.csv |
| T2 | Overall accuracy by source and bracket (10-class) | Temporal-transfer summary with the in-sample control marked | overall_comparison.csv |
| T3 | Per-class F1 by source (10-class, pooled) | Where each source succeeds or fails per class | combined_metrics_long.csv |
| T4 | Pooled accuracy by source (5-class collapse) | Change-focused accuracy, all six sources on one basis | comparison_collapsed.csv |
| T5 | Inter-interpreter per-class agreement, 10-class | Reference-reliability ceiling per class | per_class_agreement_ci.csv |
| T6 | Inter-interpreter per-class agreement, 5-class | Reference-reliability ceiling, collapsed | per_class_agreement_ci_5class.csv |
| T7 | Model F1 vs interpreter ceiling (5-class) | Ties model accuracy to reference reliability | model_per_class_ci_5class.csv + interpreter CI |
| T8 | Training-cap sensitivity, change classes | Sensitivity of the rare change classes to training size | sensitivity_metrics_long.csv |
| T9 | Spatial-structure diagnostics by source | Spatial coherence beyond aggregate accuracy | with_spec_all/spatial_structure_summary.csv |
| T10 | Per-cell 5-class macro-F1 by source | Per-cell distribution summary | per_cell_f1_summary.csv |
| T11 | Mean per-cell F1 by change class and source | Per-cell change-class summary | change_f1_summary.csv |

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

See `figure_captions.md` for full descriptive captions. Main: F1 study area (TO CREATE), F2 overall
accuracy bars, F3 OA by bracket, F4 pooled 5-class confusion, F5 per-class 10-class confusion
(representative), F6 and F7 interpreter agreement forests, F8 model vs interpreter forests, F9
spatial structure, F10 speckle crops, F11 per-cell F1 violins, F12 change-class per-cell F1, F13
change-cap sensitivity. Supplementary: S1 interpreter global confusion, S2 boundary disagreement, S3
spectral-vs-embedding change comparison, S4 dedup sensitivity, S5 Tasseled Cap diagnostics, S6
reviewer over-assignment, S7 top-disagreement panels.

## 5. Flagged issues (see consistency_report.md)

1. 168 versus 180 cells. Embedding pooled metrics use 180 cells; spec_all uses 168 (12 blank spec_all
   rasters). Tables 1 to 3 keep both sources on their native bases and label N; the 5-class Tables 4,
   7, 10, and 11 use the common 168-cell set. This must not be mixed silently within one comparison.
2. Two different 5-class collapses. The pooled comparison (Table 4) drops Unknown and Other; the
   per-bracket 5-class matrices fold Other into Stable. The pooled OA values therefore differ from a
   re-aggregation of the per-bracket matrices. Table 4 and Table S4 may sit on different bases.
3. No pooled 10-class embedding confusion matrix exists (embeddings are per-bracket only), so Figure 5
   mixes a per-bracket embedding panel with a pooled spectral panel. Flagged, not reconciled.
4. Superseded arm. `model_comparison/` and `model_comparison_2018_2020/` reflect an earlier
   154-location snapshot with random dedup; the current reference set is 180 locations with
   adjudication. Only S2 and S3 draw from that arm, and both are labeled as the earlier snapshot.
5. Missing study-area and schema figure (Figure 1). Not found in the repository.
