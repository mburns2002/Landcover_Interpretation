# Chapter 2 figure collection report

Copy-and-rename pass that collected the Chapter 2 data figures from their `reports/` sources into
`manuscript_formatting/figures/` under the thesis 2.x filenames, per `renumber_manifest.md`. Copies
were made with `shutil.copy2` (bytes preserved, no re-encoding) by
`scripts/collect_chapter2_figures.py`. The `reports/` originals were not moved, deleted, or altered;
`git status reports/` shows no changes, and every copy was verified byte-identical to its source.

## Straight copies (source -> destination)

| Figure | Source | Destination |
|--------|--------|-------------|
| 2.4 | reports/transfer_confusion_adjudicated/oa_by_bracket.png | figures/figure_2_4.png |
| 2.5 | reports/per_cell_f1_5class/f1_violin_common.png | figures/figure_2_5.png |
| 2.6 | reports/per_cell_change_f1/change_f1_violins.png | figures/figure_2_6.png |
| 2.7 | reports/spatial_structure/with_spec_all/patch_size_ecdf_area_weighted.png | figures/figure_2_7.png |
| 2.8 | reports/spatial_structure/with_spec_all/morans_i_by_source.png | figures/figure_2_8.png |
| 2.10 | reports/sensitivity_changecap/change_classes_ua_pa_vs_cap.png | figures/figure_2_10.png |

## Figure 2.9 (speckle crops), handled

A regenerated current-pipeline crop already existed at
`manuscript_formatting/figures/figure_2_9_speckle_crops.png` (from the prior regeneration task), so it
was used and confirmed present. It was copied to the clean name `figures/figure_2_9.png`. The stale
154-location snapshot (`reports/model_comparison/model_speckle_crops.png`) was NOT promoted and was not
copied. No `figure_2_9_STALE_do_not_use.png` was needed.

## Figure 2.11 (reliability ceiling), handled

The manifest source is a wildcard (one panel per source). The representative panel is v4, matching the
draft (`forest_5class_v4.png`), copied to `figures/figure_2_11.png`. The full per-source set (v2, v3,
v4, v5, v6, and spec_all) was copied into `figures/figure_2_11_all_sources/`, keeping the original
`forest_5class_<source>.png` names.

## Figure 2.12 (confusion matrices), unresolved

Not assembled. The manifest flags 2.12's composition as unresolved (per-bracket embedding versus
pooled spectral basis, and old Figures 4 and 5 both mapping to 2.12). No `figure_2_12.png` was created.
The draft-referenced candidate confusion panels were copied into `figures/figure_2_12_candidates/` for
the composition decision:

- cm_v2_2018_2020.png (10-class v2, per-bracket in-sample control)
- cm_specall_pooled.png (10-class spec_all, pooled)
- confusion_v2.png (5-class v2, pooled)
- confusion_specall.png (5-class spec_all, pooled)

Figure 2.12 still needs a same-bracket, single-basis source decision before a final panel is built.

## Status per figure number (2.1 to 2.12)

| Figure | Status | File |
|--------|--------|------|
| 2.1 | present (schematic, being generated separately) | figures/figure_study_area/figure1_study_area.png |
| 2.2 | present (schematic) | figures/figure_2_2_workflow/figure_2_2_workflow.png |
| 2.3 | present (schematic) | figures/figure_embedding_configs/figure_2_3_embedding_configs.png |
| 2.4 | present, clean | figures/figure_2_4.png |
| 2.5 | present, clean | figures/figure_2_5.png |
| 2.6 | present, clean | figures/figure_2_6.png |
| 2.7 | present, clean | figures/figure_2_7.png |
| 2.8 | present, clean | figures/figure_2_8.png |
| 2.9 | present, clean (current pipeline; stale not promoted) | figures/figure_2_9.png |
| 2.10 | present, clean | figures/figure_2_10.png |
| 2.11 | present, clean (v4 representative; full set in figure_2_11_all_sources/) | figures/figure_2_11.png |
| 2.12 | UNRESOLVED, no final file; candidates collected | figures/figure_2_12_candidates/ |

All six data figures targeted for a straight copy are present as clean `figure_2_x.png` files, plus
2.9 and 2.11. The three schematics (2.1, 2.2, 2.3) are present in their own folders and are being
generated separately, so they were not renamed to flat `figure_2_x.png` here. Nothing in 2.4 to 2.11
is missing; only 2.12 is flagged as unresolved.
