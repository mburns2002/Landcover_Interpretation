#!/usr/bin/env python3
"""Assign the provisional Chapter 3 figure numbers: copy each source image to
manuscript_formatting/figures/ under its figure_3_x_* name (originals are left in place), and write
manuscript_formatting/figures/chapter3_captions.md with the captions and a short report. Two targets
(3.2 and 3.4) are multi-panel composites; per the naming spec they are copied as flagged a/b/c panels
for manual assembly rather than auto-composited, so no combined image is fabricated.

Run: python scripts/build_chapter3_named_figures.py
Requires: only the standard library (shutil).
"""

import os
import shutil

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FIG = os.path.join(REPO, "manuscript_formatting", "figures")
C3 = "manuscript_formatting/chapter_3/figures"
IA = "reports/interpreter_agreement"
AB = "reports/Case_ABCD_sampling"
AB5 = "reports/Case_ABCD_sampling_5class"

copies, missing = [], []


def copy(src_rel, dst_name):
    # copy a single file (src relative to repo) to FIG/dst_name, recording the result
    src = os.path.join(REPO, src_rel)
    if not os.path.exists(src):
        missing.append(src_rel)
        return False
    shutil.copy2(src, os.path.join(FIG, dst_name))
    copies.append((src_rel, dst_name))
    return True


def copy_png_pdf(src_base_rel, dst_base):
    # copy the png and, if present, the sibling vector pdf under the matching name
    copy(src_base_rel + ".png", dst_base + ".png")
    if os.path.exists(os.path.join(REPO, src_base_rel + ".pdf")):
        copy(src_base_rel + ".pdf", dst_base + ".pdf")


# ---- main-text single-image figures (with pdf where a vector exists) ----
copy_png_pdf(f"{C3}/polygon_size_distribution_by_agent", "figure_3_1_polygon_size_distribution")
copy(f"{IA}/per_class_agreement_forest_5class.png", "figure_3_3_agreement_forest_5class.png")
copy(f"{IA}/geometry/gs_wetland_training_overlay.png", "figure_3_5_training_conflict_overlay.png")
copy(f"{IA}/spatial_tolerance_delta.png", "figure_3_6_spatial_tolerance.png")
copy(f"{AB}/sd_vs_n_OA.png", "figure_3_7_sd_vs_n.png")
copy(f"{AB}/design_effect_vs_W.png", "figure_3_8_design_effect_vs_W.png")
copy(f"{AB}/class_absence.png", "figure_3_9_class_absence.png")

# ---- figure 3.2: two-panel, flagged for manual assembly (copy panels a and b) ----
# use the linear-axis versions, not the log-scale ones
copy_png_pdf(f"{C3}/change_detection_rate_vs_cell_area_combined_linear", "figure_3_2a_detection_rate_combined")
copy_png_pdf(f"{C3}/change_detection_rate_vs_cell_area_by_agent_linear", "figure_3_2b_detection_rate_by_agent")

# ---- figure 3.4: three-panel, flagged for manual assembly (copy panels a, b, and c) ----
copy(f"{IA}/class_disagreement_top.png", "figure_3_4a_contested_class_pairs.png")
copy(f"{IA}/geometry/area_ecdf_focus.png", "figure_3_4b_area_ecdf.png")
copy(f"{IA}/geometry/shape_index_area_weighted_ecdf.png", "figure_3_4c_shape_index_ecdf.png")

# ---- supplementary figures (source -> figure_S_* name, one-line caption) ----
SUPP = [
    (f"{IA}/per_class_agreement_forest.png", "figure_S_agreement_forest_10class.png",
     "Per-class inter-interpreter agreement F1 with 95% cluster bootstrap confidence intervals, "
     "ten-class schema, with reliability thresholds at 0.50 and 0.70."),
    (f"{IA}/reviewer_overassignment_heatmap.png", "figure_S_reviewer_overassignment.png",
     "Heatmap of per-reviewer class over-assignment (diagnostic D4), showing which classes each "
     "reviewer claims more or less than partners."),
    (f"{AB}/bias_vs_n_OA.png", "figure_S_bias_vs_n.png",
     "Mean sampled overall accuracy minus the census against sample size (v2, W=3), comparing simple "
     "random, stratified weighted, and stratified unweighted designs."),
    (f"{AB}/strat_efficiency.png", "figure_S_strat_efficiency.png",
     "Per-class ratio of stratified to simple-random sampling standard deviation (v2, W=1, largest n); "
     "below one means stratification reduces variance for that class."),
    (f"{AB}/d_corr_vs_n.png", "figure_S_d_corr_vs_n.png",
     "Approach D per-class correlation of map versus reference area proportions against sample size "
     "(v2, W=5, simple random), one line per class."),
    (f"{AB}/variant_comparison.png", "figure_S_variant_comparison.png",
     "Cross-variant comparison of the sampling-design metrics."),
    (f"{AB}/variant_separation_scatter.png", "figure_S_variant_separation_scatter.png",
     "Scatter of variant separation from the sampling-design experiment."),
    (f"{AB5}/sd_vs_n_OA.png", "figure_S_sd_vs_n_5class.png",
     "Standard deviation of sampled overall accuracy against sample size (log-log), per window size "
     "and variant, five-class collapse."),
    (f"{AB5}/bias_vs_n_OA.png", "figure_S_bias_vs_n_5class.png",
     "Bias of sampled overall accuracy against sample size, five-class collapse."),
    (f"{AB5}/design_effect_vs_W.png", "figure_S_design_effect_vs_W_5class.png",
     "Design effect against window size, per variant, five-class collapse."),
    (f"{AB5}/strat_efficiency.png", "figure_S_strat_efficiency_5class.png",
     "Per-class stratification efficiency, five-class collapse."),
    (f"{AB5}/class_absence.png", "figure_S_class_absence_5class.png",
     "Fraction of iterations in which a class is entirely absent against sample size, five-class collapse."),
    (f"{AB5}/d_corr_vs_n.png", "figure_S_d_corr_vs_n_5class.png",
     "Approach D per-class proportion correlation against sample size, five-class collapse."),
    (f"{AB5}/change_convergence.png", "figure_S_change_convergence_5class.png",
     "Convergence of the change-class estimates with sample size, five-class collapse."),
    (f"{AB5}/collapse_summary.png", "figure_S_collapse_summary_5class.png",
     "Summary of the five-class collapse sampling-design results."),
    (f"{AB5}/recall_precision_convergence.png", "figure_S_recall_precision_convergence_5class.png",
     "Convergence of per-class recall and precision with sample size, five-class collapse."),
]
for src, dst, _ in SUPP:
    copy(src, dst)

# ---- exact main-text captions (matching the Results draft), placed below each figure ----
CAP = {
    "3.1": "Distribution of GLKN change-polygon area by agent (log hectare axis), within the seven "
           "watersheds, 2010 through 2020. Facet labels give the polygon count per agent.",
    "3.2": "Change detection rate as a function of grid cell area, by agent, within the seven "
           "watersheds. The selected 112 px cell (11.29 km2) is marked. Detection rate increases with "
           "cell area for every agent, but harvest and development are detected far more often than "
           "beaver and insect and disease at every scale.",
    "3.3": "Per-class inter-interpreter agreement F1 with 95% cluster bootstrap confidence intervals "
           "(five-class collapse), with reliability thresholds at 0.50 and 0.70. The change classes on "
           "which the classifiers of Chapter 2 performed worst are the same classes on which "
           "independent interpreters least agree.",
    "3.4": "Geometry of inter-interpreter disagreement. The most contested class pairs by disagreeing "
           "pixels are dominated by forest-wetland and grass/shrub-wetland; the area-weighted "
           "distributions of contested-patch size and shape complexity show that the disagreed-upon "
           "area resides in large, geometrically complex zones rather than thin boundary strips.",
    "3.5": "Conflicting training labels on shared ground. In the largest grass/shrub versus wetland "
           "contested zones, both interpreters placed training points but assigned them to different "
           "classes, one labeling the ground grass/shrub and the other wetland. The disagreement is "
           "conceptual, residing in the interpreters' class assignments rather than in boundary "
           "delineation.",
    "3.6": "Recovery of inter-interpreter agreement under spatial tolerance. For each class, the net "
           "increase in agreement (above a heterogeneity null) when a match is allowed within a "
           "3-pixel or 5-pixel neighborhood. Boundary-driven disagreement recovers under tolerance; "
           "grass/shrub and wetland recover little, confirming that their disagreement concerns class "
           "identity rather than boundary placement.",
    "3.7": "Standard deviation of the sampled overall accuracy against sample size on log-log axes, "
           "one line per window size, one panel per variant, with a 1/sqrt(n) reference line. "
           "Precision improves as 1/sqrt(n), but each spatial window contributes less than its pixel "
           "count because of within-window autocorrelation.",
    "3.8": "Design effect (observed variance over the binomial variance expected under independent "
           "sampling) against window size, one line per variant. The design effect is large for the "
           "spatially coherent variants and near one for the fragmented variant, linking the spatial "
           "coherence documented in Chapter 2 to sampling efficiency.",
    "3.9": "Fraction of Monte Carlo iterations in which a class is entirely absent from the sample, "
           "against sample size (simple random), one line per class. The rare change classes are "
           "missed entirely at small sample sizes, where the common classes are always present.",
}

# main-text figure order: number, files list, and a note for the multi-panel ones
MAIN_ORDER = [
    ("3.1", ["figure_3_1_polygon_size_distribution.png (vector: .pdf)"], ""),
    ("3.2", ["figure_3_2a_detection_rate_combined.png (vector: .pdf)",
             "figure_3_2b_detection_rate_by_agent.png (vector: .pdf)"],
     " Two-panel figure using the linear-axis versions: panel a is the combined-axes view, and panel "
     "b is the per-agent facets. The panels need manual assembly into one figure; they are not "
     "auto-composited."),
    ("3.3", ["figure_3_3_agreement_forest_5class.png"], ""),
    ("3.4", ["figure_3_4a_contested_class_pairs.png", "figure_3_4b_area_ecdf.png",
             "figure_3_4c_shape_index_ecdf.png"],
     " Three-panel figure: panel a is the contested class pairs, panel b is the contested-patch area "
     "ECDF, and panel c is the shape-index ECDF. The panels need manual assembly into one figure; "
     "they are not auto-composited."),
    ("3.5", ["figure_3_5_training_conflict_overlay.png"], ""),
    ("3.6", ["figure_3_6_spatial_tolerance.png"], ""),
    ("3.7", ["figure_3_7_sd_vs_n.png"], ""),
    ("3.8", ["figure_3_8_design_effect_vs_W.png"], ""),
    ("3.9", ["figure_3_9_class_absence.png"], ""),
]

lines = []
lines.append("# Chapter 3 figure captions (provisional 3.x numbering)\n")
lines.append("Working captions for the current Chapter 3 draft. The numbers are provisional, and a "
             "final renumber pass will follow. Captions are placed below each figure per OSU format. "
             "Source images are copied into this folder; the originals in reports/ and "
             "manuscript_formatting/chapter_3/ are left in place.\n")

lines.append("## Main text figures\n")
for num, files, note in MAIN_ORDER:
    lines.append(f"### Figure {num}")
    lines.append("Files: " + "; ".join(files) if len(files) > 1 else "File: " + files[0])
    lines.append("")
    lines.append(CAP[num] + note)
    lines.append("")

lines.append("## Supplementary figures\n")
lines.append("Provisional supplementary set; a final renumber pass will assign S numbers.\n")
for _, dst, cap in SUPP:
    lines.append(f"- `{dst}`: {cap}")
lines.append("")

lines.append("## Report\n")
lines.append("### Copies made (source -> destination)\n")
for src, dst in copies:
    lines.append(f"- `{src}` -> `manuscript_formatting/figures/{dst}`")
lines.append("")
lines.append("### Combine decisions\n")
lines.append("- Figure 3.2: FLAGGED for manual assembly. Copied as two panels from the linear-axis "
             "versions, `figure_3_2a_detection_rate_combined.png` (combined-axes view) and "
             "`figure_3_2b_detection_rate_by_agent.png` (per-agent facets). Not auto-composited, since "
             "the two source figures carry their own titles and axes and a clean single figure needs "
             "panel relabeling. Assemble manually as panels a and b under one caption.")
lines.append("- Figure 3.4: FLAGGED for manual assembly. Copied as three panels, "
             "`figure_3_4a_contested_class_pairs.png`, `figure_3_4b_area_ecdf.png`, and "
             "`figure_3_4c_shape_index_ecdf.png`. Not auto-composited, for the same reason. Assemble "
             "manually as panels a, b, and c under one caption.")
lines.append("")
lines.append("### Supplementary figures (source -> destination)\n")
for src, dst, _ in SUPP:
    lines.append(f"- `{src}` -> `manuscript_formatting/figures/{dst}`")
lines.append("")
lines.append("### Missing sources\n")
lines.append("- None. Every source named in the mapping was found."
             if not missing else "\n".join(f"- MISSING: `{m}`" for m in missing))
lines.append("")

with open(os.path.join(FIG, "chapter3_captions.md"), "w") as fh:
    fh.write("\n".join(lines))

print(f"copied {len(copies)} file(s); {len(missing)} missing; wrote chapter3_captions.md -> {FIG}")
