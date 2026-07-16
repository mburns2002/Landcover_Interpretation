#!/usr/bin/env python3
"""Embed a structured explanation into each report figure's PNG metadata.

Writes a `Title` and `Description` tEXt chunk (axes, metric definition, why the figure
exists, how to interpret) into every PNG under reports/. The text travels inside the file;
read it back with `exiftool <file>`, ImageMagick `identify -verbose`, or PIL
(`Image.open(p).text`). Re-runnable — apply again after regenerating any figure.

Usage:
    python scripts/annotate_figures.py            # annotate all
    python scripts/annotate_figures.py --check     # print embedded text, don't write

Requires: pillow
"""

import argparse
import glob
import os
import re

from PIL import Image, PngImagePlugin

REPORTS = "reports"

# ---- exact-basename descriptions (unique figures) -------------------------------------
DESC = {
"global_confusion_matrix.png": (
 "Inter-interpreter agreement confusion matrix",
 "Row-normalized confusion matrix of inter-interpreter agreement, pooled over all "
 "double-interpreted pairs.\n"
 "Axes: rows = Reviewer A's class, columns = Reviewer B's class (reviewers ordered "
 "alphabetically within each cell). Cell value = P(B assigns column | A assigns row); the "
 "diagonal is the agreement rate for that class.\n"
 "Why: shows which classes two independent interpreters concur on and which they confuse.\n"
 "Interpret: bright diagonal = reliable class (Water, Forest, Agriculture); off-diagonal "
 "mass = systematic confusion (Grass/Shrub spreads into Agriculture/Forest/Wetland; "
 "Insect/Disease -> Forest)."),

"class_disagreement_top.png": (
 "Class boundaries driving inter-interpreter disagreement",
 "Class boundaries ranked by their share of total inter-interpreter disagreement.\n"
 "Axes: x = percent of all disagreeing pixels contributed by that boundary; y = unordered "
 "class pair (A <-> B).\n"
 "Why: localizes where disagreement concentrates across the legend.\n"
 "Interpret: four boundaries (Forest<->Wetland, Agriculture<->Grass/Shrub, "
 "Grass/Shrub<->Forest, Grass/Shrub<->Wetland) account for ~68% of all disagreement."),

"per_class_agreement_forest.png": (
 "Per-class inter-interpreter F1 with bootstrap CIs",
 "Forest plot of per-class inter-interpreter agreement F1 with 95% cluster (pair) bootstrap "
 "confidence intervals.\n"
 "Axes: x = F1 (0-1); y = class (with number of pairs the class occurs in). F1 = "
 "2*TP/(row+col) = the balanced probability the two interpreters concur given one assigned "
 "the class. Dashed lines mark the tiers Low (<0.50), Moderate (0.50-0.70), High (>=0.70).\n"
 "Why: the reference reliability per class, with honest uncertainty; the resampling unit is "
 "the pair (not the pixel) because pixels within a cell are spatially autocorrelated.\n"
 "Interpret: Water/Forest/Agriculture are reliable references; Grass/Shrub and Wetland fall "
 "in Low = the human reference itself is unreliable there; wide CIs on rare disturbance "
 "classes reflect thin samples."),

"reviewer_overassignment_heatmap.png": (
 "Reviewer x class over-assignment index",
 "Directional reviewer bias: does a reviewer systematically over-assign a class?\n"
 "Axes: rows = reviewer, columns = class. Cell = log2[(pixels where the reviewer claims "
 "class C but the partner does not, +1) / (the reverse, +1)], pooled over that reviewer's "
 "pairs, area-weighted (pixels, not patches). '*' = 95% cluster (pair) bootstrap CI "
 "excludes 0.\n"
 "Why: tests whether disagreement reflects reproducible reviewer class-definition leanings.\n"
 "Interpret: red (+) = over-assigns vs partners, blue (-) = under-assigns. mina +Agriculture/"
 "+Water; bekka +Insect-Disease/+Harvest/+Urban; ash +Water. Caveat: the index is relative "
 "to comparison partners and the pairing graph is unbalanced (bekka-mina dominate), so "
 "paired reviewers mirror each other; rare-class extremes are unstable."),

"spatial_tolerance_delta.png": (
 "Spatial-tolerance diagnostic (edge-driven vs conceptual)",
 "Per-class agreement RECOVERED under relaxed k x k neighborhood matching, above a "
 "heterogeneity null. Two panels: A->B (dilate reviewer B's map) and B->A (dilate A) — the "
 "relation is asymmetric and this is NOT a confusion matrix.\n"
 "Axes: x = class; y = (relaxed agreement - strict agreement) minus the same quantity "
 "computed against the other map translated 3-5 px (a chance/heterogeneity null); paired "
 "bars for k=3 and k=5; error bars = 95% cluster (pair) bootstrap.\n"
 "Why: separates disagreement that is one-pixel boundary MISREGISTRATION (recovers under "
 "tolerance) from CONCEPTUAL disagreement (does not). No relaxed overall accuracy is "
 "produced — this is a diagnostic, not a corrected accuracy.\n"
 "Interpret: only Urban/Development recover above null (edge-driven); Grass/Shrub and "
 "Wetland stay ~0 (conceptual); no class keeps rising from 3x3 to 5x5, so there is no "
 ">1-pixel misregistration."),

# ---- geometry/ ----
"area_ecdf_focus.png": (
 "Disagreement patch-area ECDF by directed class pair",
 "ECDF of disagreement-patch AREA per directed class pair, for the high-disagreement "
 "boundaries, against an agreement-area reference.\n"
 "Axes: x = patch area (hectares, log scale); y = cumulative fraction of patches. Solid and "
 "dashed lines are the two directions (A->B, B->A, direction kept not symmetrized); dotted "
 "grey = agreement patches of the same classes (the size of the features being mapped).\n"
 "Why: shows whether disagreement occurs in small slivers or in feature-sized patches.\n"
 "Interpret: the disagreement ECDF sitting left of the agreement reference means disagreement "
 "patches are smaller than the mapped features — a boundary/edge phenomenon."),

"shape_index_ecdf_focus.png": (
 "Disagreement patch shape-index ECDF by directed class pair",
 "ECDF of disagreement-patch SHAPE INDEX per directed class pair.\n"
 "Axes: x = shape index = P/(2*sqrt(pi*A)) (1 = circle; higher = more crenulated/elongated); "
 "y = cumulative fraction of patches.\n"
 "Why: characterizes patch form independent of size.\n"
 "Interpret: the pooled ~1.13 is dominated by single-pixel specks (a 1x1 patch has shape "
 "index 1.128); see the area-weighted version for the patches that actually hold the area."),

"shape_index_area_weighted_ecdf.png": (
 "Shape index: area-weighted vs count-weighted",
 "Shape-index ECDF weighted by AREA vs by patch COUNT, per focus boundary.\n"
 "Axes: x = shape index; y = cumulative fraction of disagreement AREA (solid) or of patch "
 "COUNT (dotted); dashed vertical = the 1x1-pixel value 1.128.\n"
 "Why: the count-weighted shape index is dominated by single-pixel specks; area-weighting "
 "reveals the geometry of the patches that hold most of the disagreement.\n"
 "Interpret: the count curve jumps at 1.128 (specks), but the area curve extends to shape "
 "index 3-6 — the area-dominant disagreement patches are large and crenulated, not specks."),

"width_ecdf.png": (
 "Disagreement patch pixel-width ECDF (resolution-limit check)",
 "ECDF of disagreement-patch pixel width (2*Area/Perimeter).\n"
 "Axes: x = effective width in pixels (10 m each); y = cumulative fraction of patches; "
 "dashed at 1 and 2 px. 'all' vs 'interior only' (edge-touching patches excluded).\n"
 "Why: a resolution-limit check — thin 1-2 px ribbons make the discrete perimeter and shape "
 "index unstable.\n"
 "Interpret: ~93% of disagreement patches are <=1 px wide, so by count the disagreement is "
 "largely pixel-edge speckle at the resolution limit; interior vs all barely differ."),

"gs_wetland_top10.png": (
 "10 largest Grass/Shrub<->Wetland disagreement patches",
 "The 10 largest Grass/Shrub<->Wetland disagreement patches, rendered per cell.\n"
 "Layout: rows = patches (largest first); the two columns are the two reviewers' interpreted "
 "maps with the disagreement patch outlined in red; classes use the RF legend. Each row is "
 "annotated with area (ha), width (px), shape index, and extent (area / bounding-box area).\n"
 "Why: to see whether the biggest disagreements are thin margin bands or solid interior "
 "blocks.\n"
 "Interpret: they are large (30-120 ha), crenulated (shape 6-12), moderately space-filling "
 "(extent ~0.3) mosaic zones where one reviewer mapped Grass/Shrub and the other Wetland "
 "across whole landscape units — systematic class-definition disagreement, not edges."),

"gs_wetland_training_overlay.png": (
 "Training-label check on the largest GS<->Wetland patches",
 "The 10 largest Grass/Shrub<->Wetland disagreement patches with each reviewer's TRAINING "
 "data overlaid (dense pixels sampled from the drawn training polygons, colored by trained "
 "class), the patch outlined in red, the classified map faded.\n"
 "Layout: rows = patches; columns = the two reviewers.\n"
 "Why: tests whether the biggest disagreements come from CONFLICTING TRAINING LABELS or from "
 "both Random Forests EXTRAPOLATING into unlabeled ground.\n"
 "Interpret: differently-colored training points inside the same red patch = a direct "
 "training conflict (6 of 10); a red patch bare of a reviewer's points = that reviewer's RF "
 "extrapolated. Confirms the disagreement is encoded in the training labels, not model noise."),

# ---- model_comparison/ ----
"v2_global_confusion_matrix.png": (
 "Interpreted vs model v2 confusion matrix (all years)",
 "Row-normalized confusion matrix, interpreted (reference) vs AlphaEarth model v2 (the "
 "best-agreeing version), all target years, de-duplicated to one interpretation per "
 "location.\n"
 "Axes: rows = interpreted class (reference/truth), columns = model class; cell = "
 "P(model = column | interpreted = row).\n"
 "Why: where the model agrees with and departs from the interpretations.\n"
 "Interpret: strong diagonal for the stable classes (Water/Forest/Agriculture); small "
 "disturbance classes get absorbed into the dominant stable classes by the model."),

"v2_target2019_confusion_matrix.png": (
 "Interpreted vs model v2 confusion matrix (date-aligned 2019)",
 "As the all-years v2 confusion matrix, but restricted to the 30 date-aligned cells "
 "(interpreted target year 2019, whose 2018-2020 optical window matches the model "
 "composite).\n"
 "Axes: rows = interpreted class, columns = model class; cell = P(model | interpreted).\n"
 "Why: a temporally fair comparison — comparing like dates.\n"
 "Interpret: agreement is higher than the all-years matrix once dates are matched, i.e. "
 "temporal mismatch was inflating disagreement."),

"model_speckle_bar.png": (
 "Model-map spatial speckle by version",
 "Full-raster spatial speckle (neighbor-change) per model version.\n"
 "Axes: x = model version; y = fraction of horizontally-adjacent, both-valid pixel pairs "
 "whose class differs, computed over the entire raster (~2.4 billion pairs each).\n"
 "Why: quantifies spatial smoothness vs per-pixel noise.\n"
 "Interpret: v2-v5 ~0.08-0.13 (spatially smooth, coherent patches); v6 ~0.78 (speckly — the "
 "per-pixel dot-product classifier)."),

"model_speckle_vs_accuracy.png": (
 "Speckle vs agreement with interpretations",
 "Full-raster speckle vs pooled overall accuracy against the interpretations, one point per "
 "model version.\n"
 "Axes: x = neighbor-change (speckle); y = pooled overall accuracy vs interpreted.\n"
 "Why: relates spatial smoothness to agreement.\n"
 "Interpret: inverse relation — smoother maps (v2/v3/v5, top-left) agree best; the speckly "
 "v6 (bottom-right) agrees worst, so v6's low accuracy is partly a per-pixel-format effect, "
 "not only classification error."),

"model_speckle_crops.png": (
 "Same location across model versions (smooth vs speckly)",
 "The same map location shown across model versions.\n"
 "Layout: one panel per version, identical crop, classes colored; each annotated with its "
 "local neighbor-change.\n"
 "Why: visualize smooth vs speckly output.\n"
 "Interpret: v2/v3/v5 are coherent patches, v4 grainier, v6 salt-and-pepper (the water body "
 "is barely discernible)."),

"dedup_sensitivity_box.png": (
 "Selection sensitivity of interpreted-vs-model metrics",
 "Sensitivity of the interpreted-vs-model metrics to WHICH reviewer's interpretation is kept "
 "at each double-labeled location.\n"
 "Layout: four panels (overall accuracy, macro-F1, mean IoU, Cohen's kappa). Axes: x = model "
 "version; each box = the distribution over 100 random 'keep one interpretation per location' "
 "selections (seeded).\n"
 "Why: a robustness check on the de-duplication choice.\n"
 "Interpret: the boxes are tiny relative to the gaps between versions (OA range ~0.01) and "
 "the version ranking never changes, so the arbitrary reviewer choice does not affect the "
 "conclusions."),

# ---- Case_D ----
"tightness_vs_W.png": (
 "Approach D: scatter tightness vs window size, per class",
 "How the per-class proportion scatter tightens onto the 1:1 line as window size grows "
 "(Approach D).\n"
 "Layout: one panel per class. Axes: x = window size W (3,5,7,9); y = RMSE of "
 "(prop_map - prop_ref) to the 1:1 line; one line per model version.\n"
 "Why: prop_map/prop_ref = the fraction of a window's jointly-valid pixels that are the "
 "class in the map / reference; RMSE to 1:1 measures how well the variant carries the right "
 "class abundance locally. No confusion matrix or overall accuracy is produced.\n"
 "Interpret: a falling line means the scatter tightens with W — the variant has the right "
 "class abundance but misplaces pixels locally (right amount, wrong pixel). v4 stays high for "
 "Water/Urban/Agriculture (wrong abundance). Note v6's low RMSE for rare classes is a "
 "uniform-speckle artifact (its Pearson correlation there is ~0)."),

# ---- spatial_structure/ ----
"patch_size_ecdf.png": (
 "Patch-size ECDF: model variants vs interpreted",
 "ECDF of land cover patch size (8-connected components) for the model variants vs the "
 "interpreted reference.\n"
 "Axes: x = patch size (hectares, log scale); y = cumulative fraction of patches; the "
 "interpreted reference is the bold black line (the reference scale).\n"
 "Why: compares the spatial grain of each map to the interpretations.\n"
 "Interpret: a curve left of interpreted = finer / more fragmented; right of interpreted = "
 "coarser / over-smoothed. Order by grain: v6 (speckle) < v4 < interpreted < v5 < v2 < v3."),

"patch_size_hist_smallmultiples.png": (
 "Per-variant patch-size distribution vs interpreted",
 "Per-variant patch-size histograms against the interpreted distribution.\n"
 "Layout: one panel per model variant. Axes: x = patch size (ha, log); y = density; the "
 "black step outline is the interpreted reference, the filled histogram is the variant.\n"
 "Why: shows over- vs under-smoothing per variant.\n"
 "Interpret: mass shifted right of the interpreted outline = over-smoothed (larger patches); "
 "shifted left = fragmented."),

"mean_patch_size_by_class.png": (
 "Mean patch size per class, by source",
 "Mean patch size per class, grouped by source.\n"
 "Axes: x = class; y = mean patch size (hectares); bars per source (interpreted + v2-v6).\n"
 "Why: per-class spatial grain relative to the interpretations.\n"
 "Interpret: v2/v3/v5 over-smooth the large classes (Water/Agriculture patches far larger "
 "than interpreted), v4 is fragmented, v6 ~0 everywhere (speckle)."),

"morans_i_by_source.png": (
 "Moran's I of the class raster, by source",
 "Spatial autocorrelation (Moran's I) of the class raster, per source.\n"
 "Axes: x = source; y = mean per-cell Moran's I with queen (8-neighbor) contiguity; dashed "
 "line = interpreted reference. NB: class codes are nominal, so read this as a spatial-"
 "smoothness diagnostic, not autocorrelation of a meaningful quantitative variable.\n"
 "Why: an alternative smoothness measure that complements patch size.\n"
 "Interpret: v2/v3/v5 ~0.82 (smooth, near the interpreted 0.75), v4 lower, v6 ~0.09 "
 "(speckle). It cleanly isolates v6 but does not separate v2/v3/v5 — patch size does that."),
}


def window_metrics_desc(path):
    parent = os.path.basename(os.path.dirname(path))
    if "Case_B" in parent:
        return ("Approach B window sampling: metrics vs window size",
 "Approach B (dominant pixel-pair per window): metrics vs window size W.\n"
 "Layout: overall accuracy, macro-F1, kappa (lines per model version) and windows-per-cell "
 "(log). Axes: x = W (1,3,5,7,9).\n"
 "Method: each cell is tiled exhaustively with non-overlapping WxW windows; per window the "
 "single most frequent (map,ref) pixel pair is that window's one contribution to the "
 "confusion matrix (ties: lowest map code then lowest ref code).\n"
 "Why/Interpret: metrics rise with W for the smooth versions because dominant-pair "
 "aggregation discards minority within-window disagreement; v6 saturates. Windows-per-cell "
 "falls ~1/W^2 so effective sample size drops sharply. This is a diagnostic of how within-"
 "window aggregation changes the assessment, NOT a corrected accuracy. W=1 reproduces the "
 "per-pixel confusion exactly.")
    return ("Approach C window sampling: metrics, majority share, B!=C vs window size",
 "Approach C (independent per-field plurality per window): metrics + diagnostics vs W.\n"
 "Layout (6 panels): overall accuracy, macro-F1, kappa (lines per version); 'plurality that "
 "is an actual majority' fraction (map per version + a single reference line); fraction of "
 "windows where Approach B != Approach C; windows-per-cell (log). Axes: x = W (1,3,5,7,9).\n"
 "Method: each field is labeled independently by PLURALITY (most frequent class), recorded "
 "as (plurality_map, plurality_ref) per window (a documented deviation from Robert's >50% "
 "majority rule, since 10 classes rarely yield a majority; ties: lowest class code).\n"
 "Interpret: the reference is almost always a true majority (~0.93 even at W=9), so plurality "
 "summarizes it well; but v6's map plurality collapses to ~0.04 (speckle -> the v6 label is "
 "weak, read its v6 metrics with care). B!=C rises with W (~7% smooth, ~15% v6), isolating "
 "windows where within-window heterogeneity drives the assessment. W=1 == B == per-pixel.")


def prop_scatter_desc(path):
    v = re.search(r"prop_scatter_(v\d)\.png", os.path.basename(path)).group(1)
    return (f"Approach D per-class proportion scatter — model {v}",
 f"Approach D per class, model {v}: proportional-agreement density.\n"
 "Layout: rows = the 10 classes; columns = window size W (3,5,7,9). Each panel is a 2D "
 "density of prop_map (x) vs prop_ref (y) over windows, with the red 1:1 line; prop = the "
 "fraction of a window's jointly-valid pixels that are that class in the map / reference. "
 "Windows where BOTH proportions are 0 are dropped (rare classes are heavily zero-inflated); "
 "each panel is annotated with the retained window count and RMSE to 1:1.\n"
 "Why: a continuous view of whether the variant carries the right class abundance in the "
 "right area — no confusion matrix or overall accuracy.\n"
 "Interpret: density hugging the 1:1 line = right abundance; tightening from W=3 to W=9 "
 "(left to right) = right abundance with pixels locally misplaced; density biased off the "
 "1:1 line = a class-abundance bias.")


def pair_desc(path):
    m = re.search(r"(\d+)_([a-z]+)_vs_([a-z]+)\.png", os.path.basename(path), re.I)
    grid, a, b = m.group(1), m.group(2), m.group(3)
    flagged = "flagged_pairs" in path
    extra = (" This cell is in the flagged set (overall agreement < 0.70); the NN_ filename "
             "prefix orders the flagged pairs worst-agreement-first.") if flagged else ""
    return (f"Inter-interpreter comparison — grid {grid}: {a} vs {b}",
 f"Inter-interpreter comparison for grid {grid}: reviewer {a} vs reviewer {b}.\n"
 "Panels: Reviewer A's interpreted map | Reviewer B's interpreted map | agreement map "
 "(green = agree, red = disagree, grey = no data). Classes use the RF land cover legend; the "
 "title annotates overall agreement, macro-F1, mean IoU, and Cohen's kappa for this pair.\n"
 "Why: visually inspect where two independent interpretations of the same cell concur and "
 "differ.\n"
 "Interpret: red concentrated along class boundaries (especially wetland / grass-shrub / "
 "forest transitions) indicates conceptual boundary disagreement rather than whole-feature "
 "disagreement." + extra)


def describe(path):
    base = os.path.basename(path)
    if base in DESC:
        return DESC[base]
    if base == "window_sampling_metrics.png":
        return window_metrics_desc(path)
    if base.startswith("prop_scatter_"):
        return prop_scatter_desc(path)
    if re.search(r"\d+_[a-z]+_vs_[a-z]+\.png", base, re.I):
        return pair_desc(path)
    return None


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--check", action="store_true", help="print embedded text instead of writing")
    args = ap.parse_args()

    pngs = sorted(glob.glob(os.path.join(REPORTS, "**", "*.png"), recursive=True))
    done = missing = 0
    for p in pngs:
        if args.check:
            t = Image.open(p).text
            print(f"\n=== {p} ===")
            print("Title:", t.get("Title", "(none)"))
            print(t.get("Description", "(no Description)")[:300])
            continue
        d = describe(p)
        if d is None:
            missing += 1
            print(f"  NO DESCRIPTION: {p}")
            continue
        title, desc = d
        im = Image.open(p)
        info = PngImagePlugin.PngInfo()
        info.add_text("Title", title)
        info.add_text("Description", desc)
        info.add_text("Source", "Landcover_Interpretation / scripts/annotate_figures.py")
        im.save(p, pnginfo=info)
        done += 1
    if not args.check:
        print(f"\nannotated {done} figures; {missing} without a description")


if __name__ == "__main__":
    main()
