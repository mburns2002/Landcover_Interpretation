#!/usr/bin/env python3
"""Build the thesis_materials compilation: every manuscript figure and table, in order.

Assembles a single markdown document that embeds each Chapter 2 and Chapter 3 figure with its
caption, renders each table from its source CSV as a markdown table, and gathers the supplementary
figures and tables at the end. Figure PNGs are copied into thesis_materials/figures so the folder is
a self-contained deliverable. Captions are transcribed from the curated caption files
(manuscript_formatting/figure_captions.md and figures/chapter3_captions.md); table data is read from
the source CSVs and never retyped.

outputs:
  thesis_materials/THESIS_FIGURES_AND_TABLES.md
  thesis_materials/figures/*.png (copied figure images)
"""

import csv
import os
import shutil

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
MF = os.path.join(ROOT, "manuscript_formatting")
FIGS = os.path.join(MF, "figures")
OUT = os.path.join(ROOT, "thesis_materials")
IMGOUT = os.path.join(OUT, "figures")

# one entry per figure. src paths are repo-relative. panels holds one or more images; the caption is
# shown once, below the panel(s). dest is the copied filename inside thesis_materials/figures.
FIG_CH2 = [
    dict(num="2.1", title="Study area", dest="fig_2_1_study_area.png",
         panels=["manuscript_formatting/figures/figure_study_area/figure1_study_area.png"],
         caption="Study area in the western Great Lakes region of the United States, spanning "
         "Wisconsin, Minnesota, and the Michigan Upper Peninsula, in EPSG:5070 (CONUS Albers, "
         "equal-area). Shows the study grid extent, the Great Lakes, the seven GLKN park units used "
         "here (each outlined and named), and the 180 interpreted reference cells (black squares), "
         "with a conterminous-United-States locator inset, a kilometer scale bar, and a north arrow. "
         "State and Great Lakes boundaries are from Natural Earth; the grid, park boundaries, and "
         "interpreted cells are from the Google Earth Engine exports."),
    dict(num="2.2", title="Study workflow", dest="fig_2_2_workflow.png",
         panels=["manuscript_formatting/figures/figure_2_2_workflow/figure_2_2_workflow.png"],
         caption="Overview of the study workflow, from reference data sources through feature "
         "construction, classification, and evaluation."),
    dict(num="2.3", title="Embedding feature configurations", dest="fig_2_3_embedding_configs.png",
         panels=["manuscript_formatting/figures/figure_embedding_configs/figure_2_3_embedding_configs.png"],
         caption="Construction of the five embedding feature configurations (v2 to v6) from the 2018 "
         "and 2020 AlphaEarth embedding fields."),
    dict(num="2.4", title="Overall accuracy across temporal brackets", dest="fig_2_4_oa_by_bracket.png",
         panels=["manuscript_formatting/figures/figure_2_4.png"],
         caption="Overall accuracy per source across the five NAIP brackets (2017-2019, 2018-2020, "
         "2019-2021, 2020-2022, 2021-2023), 10-class schema, adjudicated reference. The 2018-2020 "
         "bracket is the in-sample control (training window). Each bracket uses a disjoint 36-cell set "
         "(embeddings) so points are independent per-bracket assessments rather than a controlled "
         "transfer curve; spec_all uses 36, 36, 34, 32, and 30 cells across the brackets. Corresponds "
         "to Table 2.4."),
    dict(num="2.5", title="Per-cell 5-class macro-F1 by source", dest="fig_2_5_percell_f1.png",
         panels=["manuscript_formatting/figures/figure_2_5.png"],
         caption="Per-grid-cell macro-F1 under the 5-class collapse for each source on the common "
         "168-cell set, one point per cell, violin with the median (bar) and mean (diamond) marked. "
         "Macro-F1 is averaged over the classes present in the reference or the prediction for that "
         "cell."),
    dict(num="2.6", title="Per-cell F1 for the change classes", dest="fig_2_6_change_f1.png",
         panels=["manuscript_formatting/figures/figure_2_6.png"],
         caption="Per-cell F1 for each change class (Harvest, Development, Insect/Disease, Beaver) by "
         "source under the 5-class collapse, on the common 168-cell set, one point per contributing "
         "cell. A cell contributes to a class where that class is present in the reference or the "
         "prediction, so the contributing cell count differs across sources and is annotated."),
    dict(num="2.7", title="Area-weighted patch-size ECDF", dest="fig_2_7_patch_ecdf.png",
         panels=["manuscript_formatting/figures/figure_2_7.png"],
         caption="Area-weighted patch-size empirical cumulative distribution (cumulative fraction of "
         "class area by patch size, log axis), measured within the interpreted cell footprints for the "
         "adjudicated interpreted reference and each source's temporally-matched per-bracket "
         "prediction; patches from 8-connected labeling. Corresponds to Table 2.6."),
    dict(num="2.8", title="Moran's I by source", dest="fig_2_8_morans_i.png",
         panels=["manuscript_formatting/figures/figure_2_8.png"],
         caption="Moran's I per source (queen-contiguity spatial autocorrelation of the nominal class "
         "raster, read as a smoothness diagnostic), measured within the interpreted cell footprints "
         "for the adjudicated interpreted reference and each source's temporally-matched per-bracket "
         "prediction. Corresponds to Table 2.6."),
    dict(num="2.9", title="Classified-map speckle", dest="fig_2_9_speckle.png",
         panels=["manuscript_formatting/figures/figure_2_9.png"],
         caption="The same location (cell 31320, EPSG:5070) classified by each embedding configuration "
         "(v2 to v6), from the current 180-cell temporally-matched classifications, colored with the "
         "standard 10-class palette. Each panel is annotated with its neighbor-change value (fraction "
         "of horizontally-adjacent, both-valid pixel pairs whose class differs), computed over all 180 "
         "current cells: v2 0.085, v3 0.084, v4 0.155, v5 0.093, v6 0.801. Baseline-preserving "
         "configurations (v2, v3, v5) produce contiguous patches, v4 is grainier, and v6 is "
         "salt-and-pepper. A 1 km scale bar is on the v2 panel."),
    dict(num="2.10", title="Training-cap sensitivity for the change classes", dest="fig_2_10_changecap.png",
         panels=["manuscript_formatting/figures/figure_2_10.png"],
         caption="User's accuracy (UA) and producer's accuracy (PA) for the four change classes as the "
         "change-class training cap varies over 50, 100, 150, and 200 points (stable classes held at "
         "200), v2 embedding classifier, 10-class schema, pooled over 180 cells. Panel highlights "
         "beaver, whose small training pool (about 502 pixels) makes the cap a large fraction of the "
         "pool. Corresponds to Table 2.7."),
    dict(num="2.11", title="Per-class model F1 versus the inter-interpreter ceiling, 5-class",
         dest="fig_2_11_model_vs_interpreter.png",
         panels=["manuscript_formatting/figures/figure_2_11.png"],
         caption="Per-class F1 under the 5-class collapse for each prediction source (colored circle) "
         "against the adjudicated reference, next to the inter-interpreter agreement for the same class "
         "(grey diamond), each with a 95% bootstrap confidence interval. Model F1 uses a cluster (cell) "
         "bootstrap over the source's usable cells (v2 to v6 on 180 cells, spec_all on 168); the "
         "interpreter ceiling uses a cluster (pair) bootstrap over 72 pairs. One panel per source."),
    dict(num="2.12", title="Pooled confusion matrices, 5-class collapse", dest="fig_2_12_confusion",
         panels=["manuscript_formatting/figures/figure_2_12_candidates/confusion_v2.png",
                 "manuscript_formatting/figures/figure_2_12_candidates/confusion_specall.png"],
         caption="Pooled confusion matrices for the embedding variants and spec_all under the 5-class "
         "collapse; cells are raw pixel counts colored by row proportion, with a producer's accuracy "
         "(PA) column and reference support, a user's accuracy (UA) row and predicted support, and "
         "overall accuracy and kappa in the corner. Reference on rows, prediction on columns. Embedding "
         "matrices pool 180 cells; the spec_all matrix pools 168 cells. Representative panels shown here "
         "are v2 (embedding) and spec_all (spectral); the full figure has one panel per source."),
]

FIG_CH3 = [
    dict(num="3.1", title="Change-polygon size distribution by agent", dest="fig_3_1_polygon_size.png",
         panels=["manuscript_formatting/figures/figure_3_1_polygon_size_distribution.png"],
         caption="Distribution of GLKN change-polygon area by agent (log hectare axis), within the "
         "seven watersheds, 2010 through 2020. Facet labels give the polygon count per agent."),
    dict(num="3.2", title="Change detection rate by grid cell area", dest="fig_3_2_detection_rate",
         panels=["manuscript_formatting/figures/figure_3_2a_detection_rate_combined.png",
                 "manuscript_formatting/figures/figure_3_2b_detection_rate_by_agent.png"],
         caption="Change detection rate as a function of grid cell area, by agent, within the seven "
         "watersheds. The selected 112 px cell (11.29 km2) is marked. Detection rate increases with "
         "cell area for every agent, but harvest and development are detected far more often than "
         "beaver and insect and disease at every scale. Panel a is the combined-axes view, and panel b "
         "is the per-agent facets."),
    dict(num="3.3", title="Inter-interpreter per-class agreement, 5-class", dest="fig_3_3_agreement_forest.png",
         panels=["manuscript_formatting/figures/figure_3_3_agreement_forest_5class.png"],
         caption="Per-class inter-interpreter agreement F1 with 95% cluster bootstrap confidence "
         "intervals (five-class collapse), with reliability thresholds at 0.50 and 0.70. The change "
         "classes on which the classifiers of Chapter 2 performed worst are the same classes on which "
         "independent interpreters least agree."),
    dict(num="3.4", title="Geometry of inter-interpreter disagreement", dest="fig_3_4_disagreement_geometry.png",
         panels=["manuscript_formatting/figures/figure_3_4_disagreement_geometry.png"],
         caption="Geometry of inter-interpreter disagreement. The most contested class pairs by "
         "disagreeing pixels are dominated by forest-wetland and grass/shrub-wetland; the area-weighted "
         "distributions of contested-patch size and shape complexity show that the disagreed-upon area "
         "resides in large, geometrically complex zones rather than thin boundary strips. Panel A is "
         "the most contested class pairs, and panel B is the contested-patch area distribution."),
    dict(num="3.5", title="Conflicting training labels on shared ground", dest="fig_3_5_training_conflict.png",
         panels=["manuscript_formatting/figures/figure_3_5_training_conflict_overlay.png"],
         caption="Conflicting training labels on shared ground. In the largest grass/shrub versus "
         "wetland contested zones, both interpreters placed training points but assigned them to "
         "different classes, one labeling the ground grass/shrub and the other wetland. The "
         "disagreement is conceptual, residing in the interpreters' class assignments rather than in "
         "boundary delineation. The figure shows the top three contested patches. Reviewers are "
         "anonymized to letters."),
    dict(num="3.6", title="Recovery of agreement under spatial tolerance", dest="fig_3_6_spatial_tolerance.png",
         panels=["manuscript_formatting/figures/figure_3_6_spatial_tolerance.png"],
         caption="Recovery of inter-interpreter agreement under spatial tolerance. For each class, the "
         "net increase in agreement (above a heterogeneity null) when a match is allowed within a "
         "3-pixel or 5-pixel neighborhood. Boundary-driven disagreement recovers under tolerance; "
         "grass/shrub and wetland recover little, confirming that their disagreement concerns class "
         "identity rather than boundary placement."),
    dict(num="3.7", title="Sampling precision versus sample size", dest="fig_3_7_sd_vs_n.png",
         panels=["manuscript_formatting/figures/figure_3_7_sd_vs_n.png"],
         caption="Standard deviation of the sampled overall accuracy against sample size on log-log "
         "axes, one line per window size, one panel per variant, with a 1/sqrt(n) reference line. "
         "Precision improves as 1/sqrt(n), but each spatial window contributes less than its pixel "
         "count because of within-window autocorrelation."),
    dict(num="3.8", title="Design effect versus window size", dest="fig_3_8_design_effect.png",
         panels=["manuscript_formatting/figures/figure_3_8_design_effect_vs_W.png"],
         caption="Design effect (observed variance over the binomial variance expected under "
         "independent sampling) against window size, one line per variant. The design effect is large "
         "for the spatially coherent variants and near one for the fragmented variant, linking the "
         "spatial coherence documented in Chapter 2 to sampling efficiency."),
    dict(num="3.9", title="Class absence versus sample size", dest="fig_3_9_class_absence.png",
         panels=["manuscript_formatting/figures/figure_3_9_class_absence.png"],
         caption="Fraction of Monte Carlo iterations in which a class is entirely absent from the "
         "sample, against sample size (simple random), one line per class. The rare change classes are "
         "missed entirely at small sample sizes, where the common classes are always present."),
]

# supplementary figures. sources for the Chapter 2 set live in reports/.
SUPP_FIG_CH2 = [
    dict(num="S2.1", title="Interpreter global confusion matrix", dest="fig_S2_1_interp_confusion.png",
         panels=["reports/interpreter_agreement/global_confusion_matrix.png"],
         caption="Pooled inter-interpreter confusion matrix over all double-interpreted pairs, raw "
         "pixel counts colored by row proportion, with a PA column (agreement given Reviewer A's label) "
         "and Reviewer A support, a UA row (agreement given Reviewer B's label) and Reviewer B support, "
         "and overall agreement and kappa in the corner. Both axes are interpreters, so there is no "
         "ground-truth reference and PA and UA are the two conditional agreement rates."),
    dict(num="S2.2", title="Class boundaries driving inter-interpreter disagreement",
         dest="fig_S2_2_boundary_disagreement.png",
         panels=["reports/interpreter_agreement/class_disagreement_top.png"],
         caption="Class boundaries ranked by their share of total inter-interpreter disagreement "
         "pixels."),
    dict(num="S2.3", title="Spectral-versus-embedding change-class comparison",
         dest="fig_S2_3_spectral_vs_embedding",
         panels=["reports/spectral_composite_classified_maps/comparison/compare_perclass_ua_pooled.png",
                 "reports/spectral_composite_classified_maps/comparison/compare_perclass_pa_pooled.png",
                 "reports/spectral_composite_classified_maps/comparison/compare_change_class_ua_by_bracket.png"],
         caption="Pooled change-class UA and PA comparison between spec_all and the embedding variants, "
         "10-class schema. Panels: pooled per-class UA, pooled per-class PA, and change-class UA by "
         "bracket."),
    dict(num="S2.4", title="Dedup-selection sensitivity", dest="fig_S2_4_dedup_sensitivity.png",
         panels=["reports/model_comparison/dedup_sensitivity_box.png"],
         caption="Distribution of overall accuracy per version across 100 random "
         "pick-one-interpretation-per-location draws, on the earlier 154-location snapshot. Corresponds "
         "to Table S2."),
    dict(num="S2.5", title="Tasseled Cap training-signal diagnostics", dest="fig_S2_5_tc_diagnostics",
         panels=["reports/TC_training/tc_delta_scatter.png",
                 "reports/TC_training/tc_mean_delta_heatmap.png",
                 "reports/TC_training/tc_lda_projection.png"],
         caption="Tasseled Cap change-space diagnostics of the training points: delta scatter, "
         "mean-delta class signature, and the linear-discriminant projection of class separability."),
    dict(num="S2.6", title="Reviewer directional over-assignment", dest="fig_S2_6_reviewer_overassignment.png",
         panels=["reports/interpreter_agreement/reviewer_overassignment_heatmap.png"],
         caption="Per-reviewer class over-assignment index (log2 ratio of pixels a reviewer claims for "
         "a class but the partner does not, versus the reverse) with 95% cluster (pair) bootstrap "
         "confidence intervals, over all 72 pairs."),
]

# Chapter 3 supplementary figures already sit in manuscript_formatting/figures as figure_S_*.png.
SUPP_FIG_CH3 = [
    ("figure_S_agreement_forest_10class.png", "Per-class inter-interpreter agreement F1 with 95% "
     "cluster bootstrap confidence intervals, ten-class schema, with reliability thresholds at 0.50 "
     "and 0.70."),
    ("figure_S_reviewer_overassignment.png", "Heatmap of per-reviewer class over-assignment "
     "(diagnostic D4), showing which classes each reviewer claims more or less than partners. "
     "Reviewers are anonymized to letters."),
    ("figure_S_bias_vs_n.png", "Mean sampled overall accuracy minus the census against sample size "
     "(v2, W=3), comparing simple random, stratified weighted, and stratified unweighted designs."),
    ("figure_S_strat_efficiency.png", "Per-class ratio of stratified to simple-random sampling "
     "standard deviation (v2, W=1, largest n); below one means stratification reduces variance for "
     "that class."),
    ("figure_S_d_corr_vs_n.png", "Approach D per-class correlation of map versus reference area "
     "proportions against sample size (v2, W=5, simple random), one line per class."),
    ("figure_S_variant_comparison.png", "Cross-variant comparison of the sampling-design metrics."),
    ("figure_S_variant_separation_scatter.png", "Scatter of variant separation from the "
     "sampling-design experiment."),
    ("figure_S_sd_vs_n_5class.png", "Standard deviation of sampled overall accuracy against sample "
     "size (log-log), per window size and variant, five-class collapse."),
    ("figure_S_bias_vs_n_5class.png", "Bias of sampled overall accuracy against sample size, "
     "five-class collapse."),
    ("figure_S_design_effect_vs_W_5class.png", "Design effect against window size, per variant, "
     "five-class collapse."),
    ("figure_S_strat_efficiency_5class.png", "Per-class stratification efficiency, five-class "
     "collapse."),
    ("figure_S_class_absence_5class.png", "Fraction of iterations in which a class is entirely absent "
     "against sample size, five-class collapse."),
    ("figure_S_d_corr_vs_n_5class.png", "Approach D per-class proportion correlation against sample "
     "size, five-class collapse."),
    ("figure_S_change_convergence_5class.png", "Convergence of the change-class estimates with sample "
     "size, five-class collapse."),
    ("figure_S_collapse_summary_5class.png", "Summary of the five-class collapse sampling-design "
     "results."),
    ("figure_S_recall_precision_convergence_5class.png", "Convergence of per-class recall and "
     "precision with sample size, five-class collapse."),
]

# tables. each renders from its source CSV. missing entry marks a table that was not built.
TAB_CH2 = [
    dict(num="2.1", title="Ten-class classification schema",
         csv="manuscript_formatting/tables/schema_table/table_2_1_schema.csv",
         caption="The ten-class classification schema: class code, class name, change or stable type, "
         "and definition."),
    dict(num="2.2", title="Embedding configurations", csv=None,
         caption="Not built as a table; the embedding configurations are shown in Figure 2.3."),
    dict(num="2.3", title="Pooled overall accuracy by source (10-class)",
         csv="manuscript_formatting/tables/table_2_3.csv",
         caption="Pooled overall accuracy, Cohen's kappa, macro-F1, and mean IoU by source (10-class "
         "schema), pooled across the five NAIP brackets against the adjudicated reference. Embedding "
         "variants on 180 cells, spec_all on 168."),
    dict(num="2.4", title="Overall accuracy by source and bracket (10-class)",
         csv="manuscript_formatting/tables/table_2_4.csv",
         caption="Overall accuracy by source and NAIP bracket (10-class schema), with the 2018-2020 "
         "in-sample control marked and a pooled column. Companion to Figure 2.4."),
    dict(num="2.5", title="Per-class F1 by source (10-class, pooled)",
         csv="manuscript_formatting/tables/table_2_5.csv",
         caption="Per-class F1 by source (10-class schema, pooled) with per-class reference support on "
         "the embedding (180-cell) and spectral (168-cell) bases."),
    dict(num="2.6", title="Spatial-structure diagnostics by source",
         csv="manuscript_formatting/tables/table_2_6.csv",
         caption="Spatial-structure diagnostics by source: patch count, mean patch size, "
         "median-by-area patch size, and Moran's I (mean and standard deviation), within the "
         "interpreted cell footprints. Companion to Figures 2.7 and 2.8."),
    dict(num="2.7", title="Training-cap sensitivity, change classes",
         csv="manuscript_formatting/tables/table_2_7.csv",
         caption="Training-cap sensitivity for the change classes: UA, PA, and F1 as the change-class "
         "training cap varies (50, 100, 150, and 200 points), with training ceiling and support. "
         "Companion to Figure 2.10."),
    dict(num="2.8", title="Inter-interpreter reliability, 10-class",
         csv="manuscript_formatting/tables/table_2_8.csv",
         caption="Inter-interpreter reliability by class (10-class schema): agreement F1 and IoU with "
         "95% cluster (pair) bootstrap confidence intervals and a reliability tier, over the 72 "
         "double-interpreted cells."),
]

TAB_CH3 = [
    dict(num="3.1", title="Change detection rate by cell size",
         csv="manuscript_formatting/chapter_3/tables/chapter3_table_detection_rate_by_cell_size.csv",
         caption="Change detection rate (percent of complete cells containing at least one polygon of "
         "the agent) by grid cell size and change agent, seven-watershed AOI, EPSG:5070. The 112 px "
         "cell (11.29 km2) is the selected assessment unit."),
    dict(num="3.2", title="Complete-cell counts by cell size",
         csv="manuscript_formatting/chapter_3/tables/chapter3_table_complete_cell_counts_by_cell_size.csv",
         caption="Complete-cell counts and per-agent counts of cells with change, by grid cell size "
         "(the absolute-count companion to the detection-rate table)."),
    dict(num="3.3", title="Change-polygon size statistics by agent",
         csv="manuscript_formatting/chapter_3/tables/chapter3_table_polygon_size_by_agent.csv",
         caption="GLKN change-polygon size statistics by agent: polygon count, minimum, median, mean, "
         "standard deviation, and maximum area (hectares), and total area (km2), 2010 to 2020."),
    dict(num="3.4", title="Inter-interpreter agreement, 5-class",
         csv="manuscript_formatting/chapter_3/tables/chapter3_table_interpreter_agreement_5class.csv",
         caption="Per-class inter-interpreter agreement (5-class collapse): agreement F1 and IoU with "
         "95% cluster bootstrap confidence intervals and a reliability tier, over the double-interpreted "
         "cells (Unknown excluded)."),
]

SUPP_TAB_CH2 = [
    dict(num="S1", title="Full per-class metrics by source (10-class, pooled)",
         csv="manuscript_formatting/tables/S1.csv",
         caption="Full per-class UA, PA, F1, IoU, support, and cells-present by source (10-class "
         "schema, pooled)."),
    dict(num="S2", title="Dedup-selection sensitivity of OA",
         csv="manuscript_formatting/tables/S2.csv",
         caption="Overall accuracy and macro-F1 sensitivity across 100 random "
         "pick-one-interpretation-per-location draws, per version, on the earlier 154-location "
         "snapshot."),
    dict(num="S3", title="Map speckle (neighbor-change) by variant",
         csv="manuscript_formatting/tables/S3.csv",
         caption="Map speckle by source: neighbor-change (fraction of adjacent valid pixel pairs whose "
         "class differs), pooled overall accuracy, and valid pixel-pair count."),
    dict(num="S4", title="Design-based pooled 5-class metrics",
         csv="manuscript_formatting/tables/S4.csv",
         caption="Design-based pooled 5-class metrics by source: overall accuracy, kappa, macro-F1, "
         "mean IoU, and the all-Stable baseline overall accuracy."),
]


def _copy(src_rel, dest_name):
    # copy a repo-relative image into thesis_materials/figures, return the markdown-relative path
    src = os.path.join(ROOT, src_rel)
    if not os.path.isfile(src):
        print(f"WARN missing figure source: {src_rel}")
        return None
    shutil.copy2(src, os.path.join(IMGOUT, dest_name))
    return f"figures/{dest_name}"


def _fig_block(entry, label):
    # emit a figure heading, its panel image(s), and the caption. multi-panel entries get a, b, c tags
    lines = [f"#### {label} {entry['num']}. {entry['title']}", ""]
    panels = entry["panels"]
    multi = len(panels) > 1
    for i, src_rel in enumerate(panels):
        suffix = f"_{chr(97 + i)}" if multi else ""
        base = entry["dest"]
        stem = base[:-4] if base.endswith(".png") else base
        dest = f"{stem}{suffix}.png"
        rel = _copy(src_rel, dest)
        tag = f" (panel {chr(97 + i)})" if multi else ""
        if rel:
            lines.append(f"![{label} {entry['num']}{tag}]({rel})")
        else:
            lines.append(f"*(figure file not found: {src_rel})*")
        lines.append("")
    lines.append(f"*{label} {entry['num']}. {entry['caption']}*")
    lines.append("")
    return "\n".join(lines)


def _md_table(csv_rel):
    # render a source CSV as a github markdown table, values passed through unchanged
    path = os.path.join(ROOT, csv_rel)
    with open(path, newline="") as fh:
        rows = list(csv.reader(fh))
    if not rows:
        return "*(empty table)*\n"
    head = rows[0]
    out = ["| " + " | ".join(head) + " |", "| " + " | ".join(["---"] * len(head)) + " |"]
    for r in rows[1:]:
        r = r + [""] * (len(head) - len(r))
        out.append("| " + " | ".join(cell.replace("|", "\\|") for cell in r) + " |")
    return "\n".join(out) + "\n"


def _tab_block(entry, label):
    lines = [f"#### {label} {entry['num']}. {entry['title']}", ""]
    if entry.get("csv"):
        lines.append(_md_table(entry["csv"]))
    lines.append(f"*{label} {entry['num']}. {entry['caption']}*")
    lines.append("")
    return "\n".join(lines)


def main():
    os.makedirs(IMGOUT, exist_ok=True)
    md = []
    md.append("# GLKN Land-Cover Interpretation: Thesis Figures and Tables")
    md.append("")
    md.append("Compiled figures and tables for the thesis, in manuscript order, each with its caption. "
              "Chapter 2 covers land-cover classification from AlphaEarth embedding configurations, and "
              "Chapter 3 covers the interpretation reliability and validation-sampling design. "
              "Supplementary figures and tables follow at the end. Figure images are copied into "
              "`figures/` so this folder is self-contained; table values are read from the source CSVs "
              "in `manuscript_formatting/`. Generated by `scripts/build_thesis_materials.py`.")
    md.append("")

    md.append("## Chapter 2")
    md.append("")
    md.append("### Chapter 2 figures")
    md.append("")
    for e in FIG_CH2:
        md.append(_fig_block(e, "Figure"))
    md.append("### Chapter 2 tables")
    md.append("")
    for e in TAB_CH2:
        md.append(_tab_block(e, "Table"))

    md.append("## Chapter 3")
    md.append("")
    md.append("### Chapter 3 figures")
    md.append("")
    for e in FIG_CH3:
        md.append(_fig_block(e, "Figure"))
    md.append("### Chapter 3 tables")
    md.append("")
    for e in TAB_CH3:
        md.append(_tab_block(e, "Table"))

    md.append("## Supplementary figures")
    md.append("")
    md.append("Supplementary numbering is provisional and grouped by chapter (S2.x for Chapter 2, S3.x "
              "for Chapter 3); a final renumber pass will follow.")
    md.append("")
    md.append("### Chapter 2 supplementary figures")
    md.append("")
    for e in SUPP_FIG_CH2:
        md.append(_fig_block(e, "Figure"))
    md.append("### Chapter 3 supplementary figures")
    md.append("")
    for i, (fname, cap) in enumerate(SUPP_FIG_CH3, start=1):
        num = f"S3.{i}"
        rel = _copy(os.path.join("manuscript_formatting", "figures", fname), f"fig_{num.replace('.', '_')}_{fname}")
        md.append(f"#### Figure {num}")
        md.append("")
        md.append(f"![Figure {num}]({rel})" if rel else f"*(figure file not found: {fname})*")
        md.append("")
        md.append(f"*Figure {num}. {cap}*")
        md.append("")

    md.append("## Supplementary tables")
    md.append("")
    md.append("### Chapter 2 supplementary tables")
    md.append("")
    for e in SUPP_TAB_CH2:
        md.append(_tab_block(e, "Table"))

    with open(os.path.join(OUT, "THESIS_FIGURES_AND_TABLES.md"), "w") as fh:
        fh.write("\n".join(md).rstrip() + "\n")

    n_fig = len(FIG_CH2) + len(FIG_CH3) + len(SUPP_FIG_CH2) + len(SUPP_FIG_CH3)
    n_tab = len([t for t in TAB_CH2 if t.get("csv")]) + len(TAB_CH3) + len(SUPP_TAB_CH2)
    print(f"wrote {OUT}/THESIS_FIGURES_AND_TABLES.md")
    print(f"figures embedded: {n_fig}, tables rendered: {n_tab}")
    print(f"images copied into {IMGOUT}")


if __name__ == "__main__":
    main()
