# Renumbering manifest (Chapter 2 per-chapter scheme)

Labeling pass only. No numeric values changed. Old sequential numbers map to the thesis per-chapter
numbers below. Analysis scripts and their raw outputs in `reports/` are not renamed; only the
manuscript-side files under `manuscript_formatting/` are renamed, and the captions, docx, and plan are
relabeled.

## Tables (main text)

| Old | New | Content | Old file | New file |
|-----|-----|---------|----------|----------|
| Table 2.1 | Table 2.1 | Ten-class classification schema | tables/schema_table/table_2_1_schema.docx/.csv | unchanged (already 2.1) |
| Table 2.2 | Table 2.2 | Embedding configurations table | not present | flagged, see below |
| Table 1 | Table 2.3 | Pooled accuracy by source (10-class) | tables/T1.csv | tables/table_2_3.csv |
| Table 2 | Table 2.4 | Accuracy by source and bracket (10-class) | tables/T2.csv, T2_tidy.csv | tables/table_2_4.csv, table_2_4_tidy.csv |
| Table 3 | Table 2.5 | Per-class F1 by source (10-class) | tables/T3.csv | tables/table_2_5.csv |
| Table 9 | Table 2.6 | Spatial-structure diagnostics | tables/T9.csv | tables/table_2_6.csv |
| Table 8 | Table 2.7 | Training-cap sensitivity (change classes) | tables/T8.csv | tables/table_2_7.csv |
| Table 5 | Table 2.8 | Inter-interpreter reliability (10-class) | tables/T5.csv | tables/table_2_8.csv |

## Figures (main text)

| Old | New | Content | Source (raw output, not renamed) |
|-----|-----|---------|----------------------------------|
| study-area map | Figure 2.1 | Study area | figures/figure_study_area/figure1_study_area.png (file kept, author regenerating separately; number 2.1 assigned in captions) |
| workflow diagram | Figure 2.2 | Study workflow | figures/figure_2_2_workflow/ (already 2.2) |
| embedding schematic | Figure 2.3 | Embedding configurations | figures/figure_embedding_configs/figure_2_3_embedding_configs (already 2.3) |
| Figure 3 | Figure 2.4 | Accuracy across brackets | reports/transfer_confusion_adjudicated/oa_by_bracket.png |
| Figure 11 | Figure 2.5 | Per-cell 5-class macro-F1 | reports/per_cell_f1_5class/f1_violin_common.png |
| Figure 12 | Figure 2.6 | Per-class change-class F1 | reports/per_cell_change_f1/change_f1_violins.png |
| Figure 9a | Figure 2.7 | Area-weighted patch-size ECDF | reports/spatial_structure/with_spec_all/patch_size_ecdf_area_weighted.png |
| Figure 9b | Figure 2.8 | Moran's I by source | reports/spatial_structure/with_spec_all/morans_i_by_source.png |
| Figure 10 | Figure 2.9 | Neighbor-change map detail | reports/model_comparison/model_speckle_crops.png |
| Figure 13 | Figure 2.10 | Change-class UA/PA vs training cap | reports/sensitivity_changecap/change_classes_ua_pa_vs_cap.png |
| Figure 8 | Figure 2.11 | Model-vs-interpreter reliability ceiling | reports/model_vs_interpreter_5class/forest_5class_*.png |
| Figure 4/5 | Figure 2.12 | Confusion matrices (pooled) | reports/collapsed_5class_confusion/, spectral collapsed |

## Structural notes and flags (author to resolve)

1. Figure 9 held three panels (A area-weighted ECDF, B mean patch size, C Moran's I). The mapping
   splits it: 9a area-weighted ECDF becomes Figure 2.7 and 9b Moran's I becomes Figure 2.8. Panel B
   (mean patch size per class) is not assigned a Chapter 2 number and is flagged.
2. Figure 4/5 both map to Figure 2.12. Old Figure 4 was the pooled 5-class confusion matrices and old
   Figure 5 was the per-class 10-class confusion. Figure 2.12 is set to the pooled confusion. Confirm
   whether 2.12 combines both or Figure 5 is cut.
3. Table 2.2 (embedding configurations table) does not exist as a table. The embedding configurations
   are conveyed by Figure 2.3 (the schematic). Confirm whether a Table 2.2 is wanted.
4. Table 2.8 (inter-interpreter reliability) is renumbered 2.8 for now, but the inter-interpreter
   measurement belongs to Chapter 3; only the reliability-ceiling comparison (Figure 2.11) stays in
   Chapter 2. Final home of this table is undecided.

## Not in the Chapter 2 numbering (kept, not renumbered)

Tables (were main, now unassigned; all 5-class):
- Table 4 (pooled accuracy, 5-class collapse) -> tables/T4.csv
- Table 6 (inter-interpreter, 5-class) -> tables/T6.csv
- Table 7 (model vs interpreter, 5-class) -> tables/T7.csv, T7_tidy.csv
- Table 10 (per-cell 5-class macro-F1) -> tables/T10.csv
- Table 11 (per-cell change-class F1) -> tables/T11.csv, T11_tidy.csv

The 5-class results appear in the main text as figures (2.5, 2.6, 2.11, 2.12), so these five tables
are kept and flagged rather than given a Chapter 2 number.

Figures (were main, now unassigned):
- Figure 1b (classification schema) -> figures/figure_study_area/figure_class_schema.png
- Figure 2 (overall accuracy bars) -> reports/.../compare_overall_metrics.png
- Figure 6 (inter-interpreter agreement, 10-class) -> reports/.../per_class_agreement_forest.png
- Figure 7 (inter-interpreter agreement, 5-class) -> reports/.../per_class_agreement_forest_5class.png

## Supplementary (keep S-prefix, no per-chapter S-scheme given)

Tables: S1 (full per-class UA/PA long), S2 (dedup 100-draw robustness), S3 (speckle), S4 (design-based
5-class CIs). Figures: S1 to S7 as in figure_captions.md. Reported as-is.

## Cross-references updated (mapped -> mapped)

- Figure 2.4 caption: "Corresponds to Table 2" -> "Table 2.4".
- Figures 2.7 and 2.8 captions: "Corresponds to Table 9" -> "Table 2.6".
- Figure 2.10 caption: "Corresponds to Table 8" -> "Table 2.7".
- Table 2.4 tidy CSV and note unchanged in content.

Cross-references pointing to unassigned tables (Figures 2.5, 2.6, 2.11, 2.12) are reworded to name the
former table and note it is unassigned, rather than pointing at a Chapter 2 number that does not exist.

## Prose draft references (FLAGGED, not edited this pass)

The drafted section `sections/Methods_and_Results_draft.src.md` is being rewritten separately against
the new numbers, so it is not edited here. It carries old exhibit references that the rewrite must
update: the `[[TABLE ...]]` placeholders and the "Table N" and "Figure N" labels. To keep the render
pipeline runnable in the meantime, `render_methods_results.py` now aliases the six renamed table ids
(T1, T2, T3, T5, T8, T9) to their new files, so an unedited `[[TABLE T3]]` still resolves. The
placeholder-to-file mapping for the rewrite:

- `[[TABLE T1]]` -> table_2_3, `[[TABLE T2]]` -> table_2_4, `[[TABLE T3]]` -> table_2_5,
  `[[TABLE T9]]` -> table_2_6, `[[TABLE T8]]` -> table_2_7, `[[TABLE T5]]` -> table_2_8.
- `[[TABLE T4]]`, `[[TABLE T6]]`, `[[TABLE T7]]`, `[[TABLE T10]]`, `[[TABLE T11]]`, `[[TABLE S1..S4]]`
  are unchanged (flagged or supplementary).

Figure and table number labels inside the prose ("Figure 1" to "Figure 13", "Table 1" to "Table 11",
"Figure 9a/9b/1b") are left as-is for the prose rewrite; use the tables above to map them. The rendered
draft under `sections/draft/` is now stale with respect to the new numbers and should be regenerated
after the prose rewrite.
