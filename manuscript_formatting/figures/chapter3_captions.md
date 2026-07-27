# Chapter 3 figure captions (provisional 3.x numbering)

Working captions for the current Chapter 3 draft. The numbers are provisional, and a final renumber pass will follow. Captions are placed below each figure per OSU format. Source images are copied into this folder; the originals in reports/ and manuscript_formatting/chapter_3/ are left in place.

## Main text figures

### Figure 3.1
File: figure_3_1_polygon_size_distribution.png (vector: .pdf)

Distribution of GLKN change-polygon area by agent (log hectare axis), within the seven watersheds, 2010 through 2020. Facet labels give the polygon count per agent.

### Figure 3.2
Files: figure_3_2a_detection_rate_combined.png (vector: .pdf); figure_3_2b_detection_rate_by_agent.png (vector: .pdf)

Change detection rate as a function of grid cell area, by agent, within the seven watersheds. The selected 112 px cell (11.29 km2) is marked. Detection rate increases with cell area for every agent, but harvest and development are detected far more often than beaver and insect and disease at every scale. Two-panel figure: panel a is the combined-axes view, and panel b is the per-agent facets. The panels need manual assembly into one figure; they are not auto-composited.

### Figure 3.3
File: figure_3_3_agreement_forest_5class.png

Per-class inter-interpreter agreement F1 with 95% cluster bootstrap confidence intervals (five-class collapse), with reliability thresholds at 0.50 and 0.70. The change classes on which the classifiers of Chapter 2 performed worst are the same classes on which independent interpreters least agree.

### Figure 3.4
Files: figure_3_4a_contested_class_pairs.png; figure_3_4b_area_ecdf.png; figure_3_4c_shape_index_ecdf.png

Geometry of inter-interpreter disagreement. The most contested class pairs by disagreeing pixels are dominated by forest-wetland and grass/shrub-wetland; the area-weighted distributions of contested-patch size and shape complexity show that the disagreed-upon area resides in large, geometrically complex zones rather than thin boundary strips. Three-panel figure: panel a is the contested class pairs, panel b is the contested-patch area ECDF, and panel c is the shape-index ECDF. The panels need manual assembly into one figure; they are not auto-composited.

### Figure 3.5
File: figure_3_5_training_conflict_overlay.png

Conflicting training labels on shared ground. In the largest grass/shrub versus wetland contested zones, both interpreters placed training points but assigned them to different classes, one labeling the ground grass/shrub and the other wetland. The disagreement is conceptual, residing in the interpreters' class assignments rather than in boundary delineation.

### Figure 3.6
File: figure_3_6_spatial_tolerance.png

Recovery of inter-interpreter agreement under spatial tolerance. For each class, the net increase in agreement (above a heterogeneity null) when a match is allowed within a 3-pixel or 5-pixel neighborhood. Boundary-driven disagreement recovers under tolerance; grass/shrub and wetland recover little, confirming that their disagreement concerns class identity rather than boundary placement.

### Figure 3.7
File: figure_3_7_sd_vs_n.png

Standard deviation of the sampled overall accuracy against sample size on log-log axes, one line per window size, one panel per variant, with a 1/sqrt(n) reference line. Precision improves as 1/sqrt(n), but each spatial window contributes less than its pixel count because of within-window autocorrelation.

### Figure 3.8
File: figure_3_8_design_effect_vs_W.png

Design effect (observed variance over the binomial variance expected under independent sampling) against window size, one line per variant. The design effect is large for the spatially coherent variants and near one for the fragmented variant, linking the spatial coherence documented in Chapter 2 to sampling efficiency.

### Figure 3.9
File: figure_3_9_class_absence.png

Fraction of Monte Carlo iterations in which a class is entirely absent from the sample, against sample size (simple random), one line per class. The rare change classes are missed entirely at small sample sizes, where the common classes are always present.

## Supplementary figures

Provisional supplementary set; a final renumber pass will assign S numbers.

- `figure_S_agreement_forest_10class.png`: Per-class inter-interpreter agreement F1 with 95% cluster bootstrap confidence intervals, ten-class schema, with reliability thresholds at 0.50 and 0.70.
- `figure_S_reviewer_overassignment.png`: Heatmap of per-reviewer class over-assignment (diagnostic D4), showing which classes each reviewer claims more or less than partners.
- `figure_S_bias_vs_n.png`: Mean sampled overall accuracy minus the census against sample size (v2, W=3), comparing simple random, stratified weighted, and stratified unweighted designs.
- `figure_S_strat_efficiency.png`: Per-class ratio of stratified to simple-random sampling standard deviation (v2, W=1, largest n); below one means stratification reduces variance for that class.
- `figure_S_d_corr_vs_n.png`: Approach D per-class correlation of map versus reference area proportions against sample size (v2, W=5, simple random), one line per class.
- `figure_S_variant_comparison.png`: Cross-variant comparison of the sampling-design metrics.
- `figure_S_variant_separation_scatter.png`: Scatter of variant separation from the sampling-design experiment.
- `figure_S_sd_vs_n_5class.png`: Standard deviation of sampled overall accuracy against sample size (log-log), per window size and variant, five-class collapse.
- `figure_S_bias_vs_n_5class.png`: Bias of sampled overall accuracy against sample size, five-class collapse.
- `figure_S_design_effect_vs_W_5class.png`: Design effect against window size, per variant, five-class collapse.
- `figure_S_strat_efficiency_5class.png`: Per-class stratification efficiency, five-class collapse.
- `figure_S_class_absence_5class.png`: Fraction of iterations in which a class is entirely absent against sample size, five-class collapse.
- `figure_S_d_corr_vs_n_5class.png`: Approach D per-class proportion correlation against sample size, five-class collapse.
- `figure_S_change_convergence_5class.png`: Convergence of the change-class estimates with sample size, five-class collapse.
- `figure_S_collapse_summary_5class.png`: Summary of the five-class collapse sampling-design results.
- `figure_S_recall_precision_convergence_5class.png`: Convergence of per-class recall and precision with sample size, five-class collapse.

## Report

### Copies made (source -> destination)

- `manuscript_formatting/chapter_3/figures/polygon_size_distribution_by_agent.png` -> `manuscript_formatting/figures/figure_3_1_polygon_size_distribution.png`
- `manuscript_formatting/chapter_3/figures/polygon_size_distribution_by_agent.pdf` -> `manuscript_formatting/figures/figure_3_1_polygon_size_distribution.pdf`
- `reports/interpreter_agreement/per_class_agreement_forest_5class.png` -> `manuscript_formatting/figures/figure_3_3_agreement_forest_5class.png`
- `reports/interpreter_agreement/geometry/gs_wetland_training_overlay.png` -> `manuscript_formatting/figures/figure_3_5_training_conflict_overlay.png`
- `reports/interpreter_agreement/spatial_tolerance_delta.png` -> `manuscript_formatting/figures/figure_3_6_spatial_tolerance.png`
- `reports/Case_ABCD_sampling/sd_vs_n_OA.png` -> `manuscript_formatting/figures/figure_3_7_sd_vs_n.png`
- `reports/Case_ABCD_sampling/design_effect_vs_W.png` -> `manuscript_formatting/figures/figure_3_8_design_effect_vs_W.png`
- `reports/Case_ABCD_sampling/class_absence.png` -> `manuscript_formatting/figures/figure_3_9_class_absence.png`
- `manuscript_formatting/chapter_3/figures/change_detection_rate_vs_cell_area_combined.png` -> `manuscript_formatting/figures/figure_3_2a_detection_rate_combined.png`
- `manuscript_formatting/chapter_3/figures/change_detection_rate_vs_cell_area_combined.pdf` -> `manuscript_formatting/figures/figure_3_2a_detection_rate_combined.pdf`
- `manuscript_formatting/chapter_3/figures/change_detection_rate_vs_cell_area_by_agent.png` -> `manuscript_formatting/figures/figure_3_2b_detection_rate_by_agent.png`
- `manuscript_formatting/chapter_3/figures/change_detection_rate_vs_cell_area_by_agent.pdf` -> `manuscript_formatting/figures/figure_3_2b_detection_rate_by_agent.pdf`
- `reports/interpreter_agreement/class_disagreement_top.png` -> `manuscript_formatting/figures/figure_3_4a_contested_class_pairs.png`
- `reports/interpreter_agreement/geometry/area_ecdf_focus.png` -> `manuscript_formatting/figures/figure_3_4b_area_ecdf.png`
- `reports/interpreter_agreement/geometry/shape_index_area_weighted_ecdf.png` -> `manuscript_formatting/figures/figure_3_4c_shape_index_ecdf.png`
- `reports/interpreter_agreement/per_class_agreement_forest.png` -> `manuscript_formatting/figures/figure_S_agreement_forest_10class.png`
- `reports/interpreter_agreement/reviewer_overassignment_heatmap.png` -> `manuscript_formatting/figures/figure_S_reviewer_overassignment.png`
- `reports/Case_ABCD_sampling/bias_vs_n_OA.png` -> `manuscript_formatting/figures/figure_S_bias_vs_n.png`
- `reports/Case_ABCD_sampling/strat_efficiency.png` -> `manuscript_formatting/figures/figure_S_strat_efficiency.png`
- `reports/Case_ABCD_sampling/d_corr_vs_n.png` -> `manuscript_formatting/figures/figure_S_d_corr_vs_n.png`
- `reports/Case_ABCD_sampling/variant_comparison.png` -> `manuscript_formatting/figures/figure_S_variant_comparison.png`
- `reports/Case_ABCD_sampling/variant_separation_scatter.png` -> `manuscript_formatting/figures/figure_S_variant_separation_scatter.png`
- `reports/Case_ABCD_sampling_5class/sd_vs_n_OA.png` -> `manuscript_formatting/figures/figure_S_sd_vs_n_5class.png`
- `reports/Case_ABCD_sampling_5class/bias_vs_n_OA.png` -> `manuscript_formatting/figures/figure_S_bias_vs_n_5class.png`
- `reports/Case_ABCD_sampling_5class/design_effect_vs_W.png` -> `manuscript_formatting/figures/figure_S_design_effect_vs_W_5class.png`
- `reports/Case_ABCD_sampling_5class/strat_efficiency.png` -> `manuscript_formatting/figures/figure_S_strat_efficiency_5class.png`
- `reports/Case_ABCD_sampling_5class/class_absence.png` -> `manuscript_formatting/figures/figure_S_class_absence_5class.png`
- `reports/Case_ABCD_sampling_5class/d_corr_vs_n.png` -> `manuscript_formatting/figures/figure_S_d_corr_vs_n_5class.png`
- `reports/Case_ABCD_sampling_5class/change_convergence.png` -> `manuscript_formatting/figures/figure_S_change_convergence_5class.png`
- `reports/Case_ABCD_sampling_5class/collapse_summary.png` -> `manuscript_formatting/figures/figure_S_collapse_summary_5class.png`
- `reports/Case_ABCD_sampling_5class/recall_precision_convergence.png` -> `manuscript_formatting/figures/figure_S_recall_precision_convergence_5class.png`

### Combine decisions

- Figure 3.2: FLAGGED for manual assembly. Copied as two panels, `figure_3_2a_detection_rate_combined.png` (combined-axes view) and `figure_3_2b_detection_rate_by_agent.png` (per-agent facets). Not auto-composited, since the two source figures carry their own titles and axes and a clean single figure needs panel relabeling. Assemble manually as panels a and b under one caption.
- Figure 3.4: FLAGGED for manual assembly. Copied as three panels, `figure_3_4a_contested_class_pairs.png`, `figure_3_4b_area_ecdf.png`, and `figure_3_4c_shape_index_ecdf.png`. Not auto-composited, for the same reason. Assemble manually as panels a, b, and c under one caption.

### Supplementary figures (source -> destination)

- `reports/interpreter_agreement/per_class_agreement_forest.png` -> `manuscript_formatting/figures/figure_S_agreement_forest_10class.png`
- `reports/interpreter_agreement/reviewer_overassignment_heatmap.png` -> `manuscript_formatting/figures/figure_S_reviewer_overassignment.png`
- `reports/Case_ABCD_sampling/bias_vs_n_OA.png` -> `manuscript_formatting/figures/figure_S_bias_vs_n.png`
- `reports/Case_ABCD_sampling/strat_efficiency.png` -> `manuscript_formatting/figures/figure_S_strat_efficiency.png`
- `reports/Case_ABCD_sampling/d_corr_vs_n.png` -> `manuscript_formatting/figures/figure_S_d_corr_vs_n.png`
- `reports/Case_ABCD_sampling/variant_comparison.png` -> `manuscript_formatting/figures/figure_S_variant_comparison.png`
- `reports/Case_ABCD_sampling/variant_separation_scatter.png` -> `manuscript_formatting/figures/figure_S_variant_separation_scatter.png`
- `reports/Case_ABCD_sampling_5class/sd_vs_n_OA.png` -> `manuscript_formatting/figures/figure_S_sd_vs_n_5class.png`
- `reports/Case_ABCD_sampling_5class/bias_vs_n_OA.png` -> `manuscript_formatting/figures/figure_S_bias_vs_n_5class.png`
- `reports/Case_ABCD_sampling_5class/design_effect_vs_W.png` -> `manuscript_formatting/figures/figure_S_design_effect_vs_W_5class.png`
- `reports/Case_ABCD_sampling_5class/strat_efficiency.png` -> `manuscript_formatting/figures/figure_S_strat_efficiency_5class.png`
- `reports/Case_ABCD_sampling_5class/class_absence.png` -> `manuscript_formatting/figures/figure_S_class_absence_5class.png`
- `reports/Case_ABCD_sampling_5class/d_corr_vs_n.png` -> `manuscript_formatting/figures/figure_S_d_corr_vs_n_5class.png`
- `reports/Case_ABCD_sampling_5class/change_convergence.png` -> `manuscript_formatting/figures/figure_S_change_convergence_5class.png`
- `reports/Case_ABCD_sampling_5class/collapse_summary.png` -> `manuscript_formatting/figures/figure_S_collapse_summary_5class.png`
- `reports/Case_ABCD_sampling_5class/recall_precision_convergence.png` -> `manuscript_formatting/figures/figure_S_recall_precision_convergence_5class.png`

### Missing sources

- None. Every source named in the mapping was found.
