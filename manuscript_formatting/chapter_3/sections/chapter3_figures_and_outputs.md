# Chapter 3 figures, tables, and numerical outputs (consolidation inventory)

Working inventory for drafting the Chapter 3 methods (sampling and validation design). This is a
consolidation of existing outputs, not a set of final exhibits. Figure and table numbers are not yet
assigned; items are referred to by descriptive label and repo-relative path. Nothing here is
recomputed; every number is quoted from the file named beside it.

## Scope and provenance (applies throughout)

- The study grid is the full three-state extent (MN, WI, and MI). The GLKN watersheds are the
  change-training source and a small fraction of the grid.
- The grid cell-size and polygon-size analyses are watershed-scoped. The only year window encoded in
  any current CSV is 2017 to 2020 (the per-year change-agent files). A 2010 to 2020 window is expected
  for the watershed-scoped analyses, but it is not carried in the grid or polygon exports, so it is
  asserted, not verified from the data. See the gaps list.
- Case ABCD reference is the adjudicated reviewer per location with temporally-matched per-bracket
  predictions as the map field. Its outputs are draws from designs whose properties are characterized,
  not accuracy estimates.
- The reliability analysis unit is the interpreter pair (72 double-interpreted cells, not
  de-duplicated). In the 5-class collapse, Unknown is excluded.

---

## Area 1: assessment-unit and reference-data design

### Grid cell-size analysis (nested grid, detection rate by cell size)

Source CSV: [`reports/GLKN_change_agents/glkn_grid_proportions_per_agent_5070_4agent.csv`](../../../reports/GLKN_change_agents/glkn_grid_proportions_per_agent_5070_4agent.csv).
Long format, one row per (cell size, agent): `cell_side_px`, `cell_side_m`, `agent`,
`n_cells_total`, `n_cells_complete`, `n_with_change`. EPSG:5070. This CSV **includes beaver** (all four
change agents: harvest, development, beaver, and insect_disease_mort).

Derived detection-rate table (five cell sizes, four agents), from
[`manuscript_formatting/tables/chapter3_table_detection_rate_by_cell_size.csv`](../tables/chapter3_table_detection_rate_by_cell_size.csv):

| Cell (px) | Side (m) | Area (km²) | Complete cells | Harvest % | Development % | Beaver % | Insect/Disease % |
|:--|--:|--:|--:|--:|--:|--:|--:|
| 224 | 6,720 | 45.16 | 166 | 72.9 | 51.8 | 23.5 | 7.8 |
| **112** | **3,360** | **11.29** | **664** | **59.9** | **31.5** | **9.3** | **2.9** |
| 56 | 1,680 | 2.82 | 2,656 | 38.7 | 14.6 | 3.0 | 1.2 |
| 28 | 840 | 0.71 | 10,624 | 21.6 | 5.8 | 0.9 | 0.5 |
| 14 | 420 | 0.18 | 42,496 | 12.2 | 2.3 | 0.3 | 0.2 |

Detection rate is `n_with_change / n_cells_complete`, the fraction of complete cells (fully within the
seven-watershed area of interest) containing at least one polygon of the agent. The 112 px cell
(11.29 km²) is the selected assessment unit. The absolute-count companion is
[`chapter3_table_complete_cell_counts_by_cell_size.csv`](../tables/chapter3_table_complete_cell_counts_by_cell_size.csv)
(same rows, columns `n_with_change` per agent alongside `n_cells_complete`).

Rendered tables (PNG plus editable DOCX, clean thesis style):
- [`chapter3_table_detection_rate_by_cell_size.png`](../tables/chapter3_table_detection_rate_by_cell_size.png) / `.docx`
- [`chapter3_table_complete_cell_counts_by_cell_size.png`](../tables/chapter3_table_complete_cell_counts_by_cell_size.png) / `.docx`

Derived figures:

- [`manuscript_formatting/chapter_3/change_detection_rate_vs_cell_area_by_agent.png`](../figures/change_detection_rate_vs_cell_area_by_agent.png) (and `.pdf`).
  Small multiples, one panel per change agent, plotting detection rate against grid cell area on a
  base-10 log x axis (0.18 to 45.16 km²) with a pixel secondary axis (14 to 224 px). The y axis is
  free per panel so the rare agents stay visible, and the dashed vertical line marks the selected
  112 px cell. Data basis: GLKN change polygons, seven-watershed AOI.
- [`manuscript_formatting/chapter_3/change_detection_rate_vs_cell_area_combined.png`](../figures/change_detection_rate_vs_cell_area_combined.png) (and `.pdf`).
  The four agents on one shared set of axes, one colored line and points per agent, colorblind-safe
  palette, with the 112 px cell marked. Same axes and data basis as the per-agent panels.
- Linear-axis companions of both figures:
  [`change_detection_rate_vs_cell_area_by_agent_linear.png`](../figures/change_detection_rate_vs_cell_area_by_agent_linear.png)
  and [`change_detection_rate_vs_cell_area_combined_linear.png`](../figures/change_detection_rate_vs_cell_area_combined_linear.png)
  (each with `.pdf`). Same data on a linear rather than log x axis; only the endpoint and selected-cell
  ticks are labeled (14, 112, and 224 px) since the smaller cells crowd the origin on a linear scale.
- Full caption: [`change_detection_rate_vs_cell_area_caption.md`](../figures/change_detection_rate_vs_cell_area_caption.md).

### Per-agent polygon-size summary

Source CSV: [`reports/GLKN_change_agents/glkn_polygon_area_by_agent_2010_2020.csv`](../../../reports/GLKN_change_agents/glkn_polygon_area_by_agent_2010_2020.csv).
One row per agent with `n_polys`, `min_m2`, `median_m2`, `mean_m2`, `sd_m2`, `max_m2`, and `total_m2`.
Watershed-scoped, 2010 to 2020, all four agents including beaver. Rendered table
[`manuscript_formatting/tables/chapter3_table_polygon_size_by_agent.csv`](../tables/chapter3_table_polygon_size_by_agent.csv)
(areas converted to hectares, total to square kilometers):

| Agent | N polygons | Min (ha) | Median (ha) | Mean (ha) | SD (ha) | Max (ha) | Total (km²) |
|:--|--:|--:|--:|--:|--:|--:|--:|
| Harvest | 7,032 | 0.80 | 2.36 | 7.65 | 13.27 | 221.69 | 537.81 |
| Development | 2,360 | 0.80 | 1.52 | 2.78 | 3.96 | 47.01 | 65.52 |
| Beaver | 678 | 0.80 | 1.30 | 1.88 | 2.49 | 48.93 | 12.74 |
| Insect/Disease | 99 | 0.81 | 1.47 | 2.76 | 7.72 | 77.62 | 2.74 |

Insect and disease rests on few polygons (99), so its distribution statistics are based on limited
data. Rendered PNG and DOCX:
[`chapter3_table_polygon_size_by_agent.png`](../tables/chapter3_table_polygon_size_by_agent.png).

Per-polygon histogram data:
[`reports/GLKN_change_agents/glkn_histograms_by_agent_2010_2020.csv`](../../../reports/GLKN_change_agents/glkn_histograms_by_agent_2010_2020.csv),
one row per polygon with `agent`, `area_ha`, `area_m2`, `log10_area_ha`, and `year` (10,169 polygons,
all four agents, 2010 to 2020). Derived figure:

- [`manuscript_formatting/chapter_3/polygon_size_distribution_by_agent.png`](../figures/polygon_size_distribution_by_agent.png)
  (and `.pdf`). One facet per change agent, histogram of polygon area on a log-10 hectare axis with a
  free y axis, facet labels carrying the per-agent polygon count. Data basis: GLKN change polygons,
  seven-watershed AOI, 2010 to 2020.

### GLKN dataset EDA (per-year agent counts and polygon areas)

Source: [`reports/GLKN_change_agents/glkn_eda_changeagents_2017.csv`](../../../reports/GLKN_change_agents/glkn_eda_changeagents_2017.csv)
through `..._2020.csv` (one file per year). Columns per file: `agent`, `n_polys`, `min_m2`,
`median_m2`, `mean_m2`, `max_m2`, `total_m2`, `year`. One row per agent per year, all four agents
present including beaver. Supporting figures:

- [`manuscript_formatting/chapter_3/change_area_by_agent.png`](../figures/change_area_by_agent.png).
  Grouped bar chart of total change-agent polygon area (hectares) per agent by year (2017 to 2020),
  colored by the canonical class legend.
- [`manuscript_formatting/chapter_3/change_count_by_agent.png`](../figures/change_count_by_agent.png).
  Grouped bar chart of polygon count per agent by year (2017 to 2020), same coloring.

The state scope of the EDA (MN and WI only, versus a three-state MN, WI, and MI version) is not
encoded in these files, so it cannot be confirmed from the data here.

### Key numbers (Area 1, all quoted from the CSVs above)

- Selected assessment unit: 112 px, 3,360 m, 11.29 km², with 664 complete cells.
- Detection rate at 112 px: harvest 59.9%, development 31.5%, beaver 9.3%, insect and disease 2.9%.
- Complete cells with change at 112 px: harvest 398, development 209, beaver 62, insect and disease 19,
  of 664 complete cells.
- Polygon counts 2010 to 2020: harvest 7,032, development 2,360, beaver 678, insect and disease 99.
- Total change area 2010 to 2020: harvest 537.81 km², development 65.52 km², beaver 12.74 km²,
  insect and disease 2.74 km².
- Per-year EDA counts 2017 to 2020 (a subset window): harvest 1,347, development 775, beaver 53,
  insect and disease 30.

### Missing, to generate, or to rerun (Area 1)

- Year window: the polygon-size and histogram products are 2010 to 2020 (watershed-scoped), and the
  grid CSV is labeled 2010 to 2020 by assertion (it carries no year field). The per-year EDA files are
  2017 to 2020, a subset. Confirm the grid CSV window and carry the year in the file.
- Complete-cell count at 112 px reads 664 in the current CSV. Reconcile against the earlier grid doc
  value of 575.
- EDA state scope (MN and WI versus three-state MN, WI, and MI). Confirm which was exported.

---

## Area 2: sampling-design characterization (Case ABCD)

Monte Carlo sampling-design experiment. These are draws from designs whose statistical properties are
characterized, not accuracy estimates. Reference:
[`reports/Case_ABCD_sampling/reference.txt`](../../../reports/Case_ABCD_sampling/reference.txt) records the
adjudicated reviewer per location, per-bracket predictions as the map field, and
`numpy.SeedSequence(42)`. A full description of the population, the two designs (simple random and
stratified Horvitz-Thompson), and the four approaches (A per-pixel, B dominant pair, C plurality, D
proportions) is in [`reports/Case_ABCD_sampling/README.md`](../../../reports/Case_ABCD_sampling/README.md).

### Found figures (10-class, `reports/Case_ABCD_sampling/`)

- [`sd_vs_n_OA.png`](../../../reports/Case_ABCD_sampling/sd_vs_n_OA.png). Standard deviation of the sampled
  overall accuracy (approach A, simple random) against sample size n on log-log axes, one line per
  window size W, one panel per variant v2 to v6, with a 1/sqrt(n) reference line.
- [`bias_vs_n_OA.png`](../../../reports/Case_ABCD_sampling/bias_vs_n_OA.png). Mean sampled OA minus census OA
  against n for v2 at W=3, comparing simple random, stratified weighted, and stratified unweighted.
- [`design_effect_vs_W.png`](../../../reports/Case_ABCD_sampling/design_effect_vs_W.png). Design effect
  (observed variance over binomial variance) against window size W, one line per variant, averaged
  over n.
- [`strat_efficiency.png`](../../../reports/Case_ABCD_sampling/strat_efficiency.png). Per-class ratio of
  stratified to simple-random standard deviation for v2 at W=1 and the largest n.
- [`class_absence.png`](../../../reports/Case_ABCD_sampling/class_absence.png). Fraction of Monte Carlo
  iterations in which a class is entirely absent from the sample against n (simple random, v2, W=1),
  one line per class.
- [`d_corr_vs_n.png`](../../../reports/Case_ABCD_sampling/d_corr_vs_n.png). Approach D per-class correlation of
  map versus reference area proportions against n (v2, W=5, simple random), one line per class.
- [`variant_comparison.png`](../../../reports/Case_ABCD_sampling/variant_comparison.png) and
  [`variant_separation_scatter.png`](../../../reports/Case_ABCD_sampling/variant_separation_scatter.png).
  Cross-variant comparison panels (from `scripts/sampling_variant_comparison.py`).

### Found figures (5-class collapse, `reports/Case_ABCD_sampling_5class/`)

Same core set as above (`sd_vs_n_OA.png`, `bias_vs_n_OA.png`, `design_effect_vs_W.png`,
`strat_efficiency.png`, `class_absence.png`, `d_corr_vs_n.png`), plus the collapse-specific panels:

- [`change_convergence.png`](../../../reports/Case_ABCD_sampling_5class/change_convergence.png),
  [`collapse_summary.png`](../../../reports/Case_ABCD_sampling_5class/collapse_summary.png), and
  [`recall_precision_convergence.png`](../../../reports/Case_ABCD_sampling_5class/recall_precision_convergence.png)
  (from `scripts/sampling_collapse_comparison.py`).

### Found tables

Present in both `reports/Case_ABCD_sampling/` and `reports/Case_ABCD_sampling_5class/`:
`census.csv`, `metrics_by_n.csv`, `per_class_metrics.csv`, `class_absence.csv`, `stratum_ceiling.csv`,
`stratum_realized.csv`, `design_effect.csv`, `strat_efficiency.csv`, `d_correlation.csv`,
`reference.txt`. The 5-class folder additionally has `exclusion.txt`, `collapse_vs_10class.csv`, and
`collapsed_kappa.csv`.

- `census.csv`: full-population OA, kappa, and macro-F1 per version, W, and approach. One row per
  (version, W, approach).
- `metrics_by_n.csv`: sampled-estimate summary (census, mean, sd, bias, and 2.5 and 97.5 percentiles)
  per design, version, W, n, and metric. Large; described, not rendered.
- `per_class_metrics.csv`: per-class recall, precision, and F1 sampled versus census, per design,
  version, W, n, and class. Large; described, not rendered.
- `design_effect.csv`, `strat_efficiency.csv`, `class_absence.csv`, `stratum_ceiling.csv`,
  `stratum_realized.csv`, `d_correlation.csv`: the per-figure supporting tables named for each plot
  above.

### Key numbers (Area 2, quoted from the README and the 5-class outputs)

- Precision scales as 1/sqrt(n); each window is worth less than its pixel count. The design effect is
  large for the spatially coherent variants v2 to v5 and near 1 for the near-independent v6
  (`reports/Case_ABCD_sampling/README.md`).
- Simple random misses the rare change classes at small n; only the weighted stratified estimator
  returns to the census, and the unweighted stratified estimator stays biased (README).
- 5-class collapse OA and kappa, [`collapsed_kappa.csv`](../../../reports/Case_ABCD_sampling_5class/collapsed_kappa.csv):
  v2 OA 0.883, kappa 0.025; v3 0.806, 0.010; v4 0.941, 0.059; v5 0.767, 0.007; v6 0.750, 0.006.
- 5-class exclusion, [`exclusion.txt`](../../../reports/Case_ABCD_sampling_5class/exclusion.txt): Unknown
  excluded, 4,139 pixels, 0.0202% of 20,443,094 reference pixels.

### Missing, to generate, or to rerun (Area 2)

- None evident. Both the 10-class and 5-class output sets, including the expected tables and plots,
  are present.

---

## Area 3: reference reliability (inter-interpreter, five diagnostics)

Outputs under [`reports/interpreter_agreement/`](../../../reports/interpreter_agreement/). The unit is the
interpreter pair over 72 double-interpreted cells (8,178,653 pooled valid pixels,
[`global_metrics.txt`](../../../reports/interpreter_agreement/global_metrics.txt)); pairs are not
de-duplicated.

### D1: per-class agreement

- Tables: [`per_class_agreement_table.md`](../../../reports/interpreter_agreement/per_class_agreement_table.md)
  and `.tex` (10-class), [`per_class_agreement_table_5class.md`](../../../reports/interpreter_agreement/per_class_agreement_table_5class.md)
  and `.tex` (5-class). Underlying CIs in `per_class_agreement_ci.csv` and
  `per_class_agreement_ci_5class.csv`. A row is a class with its pairs, support pixels, F1 and IoU
  point estimates with 95% cluster (pair) bootstrap CIs, and a reliability tier.
- Figures: [`per_class_agreement_forest.png`](../../../reports/interpreter_agreement/per_class_agreement_forest.png)
  (10-class) and [`per_class_agreement_forest_5class.png`](../../../reports/interpreter_agreement/per_class_agreement_forest_5class.png)
  (5-class). Forest plots of per-class agreement F1 with 95% CIs, dashed reliability thresholds at
  0.50 and 0.70. Data basis: 72 pairs.

5-class per-class agreement (small, rendered inline from `per_class_agreement_table_5class.md`):

| Class | Pairs | Support (px) | F1 (95% CI) | Reliability |
|:--|--:|--:|:--|:--|
| Stable | 72 | 8,087,379 | 0.99 (0.99–1.00) | High |
| Harvest | 35 | 124,641 | 0.75 (0.63–0.82) | High |
| Development | 27 | 9,288 | 0.29 (0.03–0.47) | Low |
| Insect/Disease | 19 | 56,257 | 0.23 (0.00–0.47) | Low |
| Beaver | 15 | 8,828 | 0.08 (0.00–0.21) | Low |

### D2: disagreement geometry

- [`class_disagreement_top.png`](../../../reports/interpreter_agreement/class_disagreement_top.png). The most
  contested class pairs by disagreeing pixels, from
  [`class_disagreement_ranked.csv`](../../../reports/interpreter_agreement/class_disagreement_ranked.csv)
  (columns `class_a`, `class_b`, `disagree_px`, `pct_of_all_disagreement`; top pair Forest versus
  Wetland at 21.76% of all disagreement).
- [`geometry/area_ecdf_focus.png`](../../../reports/interpreter_agreement/geometry/area_ecdf_focus.png).
  Empirical CDF of contested-patch area.
- [`geometry/shape_index_area_weighted_ecdf.png`](../../../reports/interpreter_agreement/geometry/shape_index_area_weighted_ecdf.png).
  Area-weighted empirical CDF of patch shape index.
- [`geometry/gs_wetland_top10.png`](../../../reports/interpreter_agreement/geometry/gs_wetland_top10.png) with
  [`gs_wetland_top10.csv`](../../../reports/interpreter_agreement/geometry/gs_wetland_top10.csv) (columns
  `cell_id`, `lid`, `area_px`, `area_ha`, `shape_index`, `width_px`, `extent`). The ten largest
  grass/shrub versus wetland contested patches.

### D3: training-conflict overlay

- [`geometry/gs_wetland_training_overlay.png`](../../../reports/interpreter_agreement/geometry/gs_wetland_training_overlay.png)
  with [`gs_wetland_training_overlay.csv`](../../../reports/interpreter_agreement/geometry/gs_wetland_training_overlay.csv)
  (columns include `rank`, `cell_id`, `area_ha`, `reviewer_a`, `a_pts_in_zone`, `a_classes_in_zone`,
  `reviewer_b`, `b_pts_in_zone`, `b_classes_in_zone`, `category`). Training points falling inside the
  grass/shrub versus wetland contested zones, per reviewer, with the conflicting class labels.

### D4: reviewer directional bias

- [`reviewer_overassignment_heatmap.png`](../../../reports/interpreter_agreement/reviewer_overassignment_heatmap.png).
  Heatmap of per-reviewer class over-assignment.
- [`reviewer_class_overassignment.csv`](../../../reports/interpreter_agreement/reviewer_class_overassignment.csv)
  (columns `reviewer`, `cls`, `code`, `claim_self_ha`, `claim_partner_ha`, `log2_index`, `ci_lo`,
  `ci_hi`, `significant`, `n_pairs`). One row per reviewer and class: how much of a class a reviewer
  claims relative to partners, with a log2 index and CI.
- [`reviewer_directed_classpairs.csv`](../../../reports/interpreter_agreement/reviewer_directed_classpairs.csv)
  (columns `reviewer`, `says`, `partner_says`, `px_R_over`, `px_partner_over`, `area_R_over_ha`,
  `log2_ratio`). Directed class-pair over-assignment per reviewer.

### D5: spatial tolerance

- [`spatial_tolerance_delta.png`](../../../reports/interpreter_agreement/spatial_tolerance_delta.png) with
  [`spatial_tolerance_delta.csv`](../../../reports/interpreter_agreement/spatial_tolerance_delta.csv). Per class
  and direction (AtoB, BtoA), strict versus relaxed agreement at 3-pixel and 5-pixel tolerance, the
  raw delta, a null delta, and the net delta with CI. Columns `direction`, `cls`, `code`, `denom_px`,
  `strict_3`, `relaxed_3`, `delta_3`, `null_delta_3`, `delta_net_3`, `net_lo_3`, `net_hi_3`, and the
  matching `_5` set.

### Supporting outputs (not one of the five diagnostics)

- [`global_confusion_matrix.png`](../../../reports/interpreter_agreement/global_confusion_matrix.png) and
  `.csv`: pooled inter-interpreter confusion over all pairs.
- `global_metrics.txt`, `per_pair_metrics.csv`, `by_reviewer_pair.csv`, `lowest_agreement_pairs.csv`,
  `flagged_pairs_for_review.csv`, `per_class_contested.csv`.
- Per-pair rendered comparisons in `pairs/` (about 70 PNGs), `flagged_pairs/` (17 PNGs), and
  `change_stable_conflicts/examples/` and `change_change_conflicts/` supporting CSVs and summaries.

### Key numbers (Area 3, quoted from `global_metrics.txt` and the D1 tables)

- 72 multi-reviewer pairs, 8,178,653 pooled valid pixels.
- Pooled overall agreement 0.7747, pooled Cohen's kappa 0.6675, pooled macro F1 0.4796, pooled mean
  IoU 0.3703.
- 10-class per-class F1 tiers: High are Water 0.92, Forest 0.90, Agriculture 0.78, and Harvest 0.75;
  Moderate is Urban 0.61; Low are Wetland 0.47, Other 0.45, Grass/Shrub 0.29, Development 0.28,
  Insect/Disease 0.23, Beaver 0.08, and Unknown 0.00.
- 5-class per-class F1: Stable 0.99 (High), Harvest 0.75 (High), Development 0.29, Insect/Disease 0.23,
  and Beaver 0.08 (Low).

### Missing, to generate, or to rerun (Area 3)

- None evident. All five diagnostics (D1 through D5), including the expected tables and figures, are
  present.

---

## Gaps and reruns (punch list)

1. **Polygon-size summary with SD (Area 1). Resolved.** `glkn_polygon_area_by_agent_2010_2020.csv`
   (with `sd_m2` and all four agents including beaver) is now in the repo, and the polygon-size table
   carries median and standard deviation.
2. **Polygon histogram data (Area 1). Resolved.** `glkn_histograms_by_agent_2010_2020.csv` is now in
   the repo, and the polygon-size distribution figure is derived from it.
3. **Year window (Area 1).** The polygon-size and histogram products are 2010 to 2020. The grid CSV is
   labeled 2010 to 2020 by assertion but carries no year field, and the per-year EDA files are 2017 to
   2020 (a subset). Confirm the grid CSV window and carry the year in the file.
4. **575 versus 664 complete cells at 112 px (Area 1).** The current grid CSV reports 664 complete
   cells at 112 px; an earlier grid doc reported 575. Reconcile.
5. **EDA state scope (Area 1).** Confirm whether the change-agent EDA is MN and WI only or the
   three-state MN, WI, and MI version. The state is not encoded in the current EDA files.
6. **Grid CSV provenance (Area 1).** The grid CSV carries no year or state column, so window and scope
   cannot be verified from the file itself.
7. **Areas 2 and 3.** No missing items identified; both output sets are complete.
