#!/usr/bin/env python3
"""Add a visible caption band (and embedded metadata) explaining each report figure.

Draws a caption under every PNG under reports/ — title, axes, metric definition, why the
figure exists, and how to interpret it — so the explanation is visible when viewing the
image normally. The same text is also written to the PNG's `Title`/`Description` metadata
(read with `exiftool`, `identify -verbose`, or PIL `Image.open(p).text`).

Idempotent: a `Captioned` flag in the metadata prevents stacking captions on re-runs.
Post-processes existing PNGs, so no plotting script needs to be re-run. If you regenerate a
figure (fresh, uncaptioned), just run this again to re-caption it.

Usage:
    python scripts/annotate_figures.py             # caption + embed metadata
    python scripts/annotate_figures.py --meta-only # embed metadata only, no caption band
    python scripts/annotate_figures.py --check      # print embedded text, don't write

Requires: pillow, matplotlib (for the bundled DejaVu font)
"""

import argparse
import glob
import os
import re

import matplotlib
from PIL import Image, ImageDraw, ImageFont, PngImagePlugin

REPORTS = "reports"
FONT_DIR = os.path.join(matplotlib.get_data_path(), "fonts", "ttf")

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

"variant_separation_scatter.png": (
 "How the embedding variants separate (single summary)",
 "One point per model variant, summarizing how the sampling diagnostics separate them.\n"
 "Axes: x = abundance-weighted Approach D proportion correlation to the reference (mean of "
 "per-class corr(prop_map, prop_ref) weighted by true class abundance; higher = tracks how "
 "much of each class is present); y = design effect at W=9 (higher = more spatially "
 "autocorrelated errors).\n"
 "Why: collapses the cross-variant story to two axes — abundance fidelity and spatial "
 "structure.\n"
 "Interpret: v2/v3/v5 cluster upper-right (coherent smooth classifiers that track abundance, "
 "x 0.61-0.69, deff 38-47); v4 is upper-middle (autocorrelated but weaker tracking, x 0.48); "
 "v6 is isolated bottom-left (dot-product: near-no abundance signal x 0.29, and low "
 "autocorrelation deff 10). Draws from designs, not accuracy estimates."),

"variant_comparison.png": (
 "Embedding classifier variants under the sampling strategies",
 "How the model variants (v2-v6, different classifiers over the same AlphaEarth embeddings; "
 "v6 = dot-product) differ on the design properties the sampling strategies expose.\n"
 "Panel 1: design effect vs W per variant — v6 is ~4x lower (its per-pixel dot-product "
 "classification gives spatially independent errors, so windows waste far less information; "
 "the smooth variants are highly autocorrelated). Panel 2: Approach D proportion correlation "
 "to the reference (class x variant heatmap) — v2/v3/v5 track abundance well (Water 0.97, "
 "Agriculture 0.87), v4 is intermediate (Water 0.56, Urban 0.18), and v6 is near zero "
 "everywhere (it carries almost no class-abundance signal). Panel 3: rare-class absence under "
 "simple random at n=20 — v6's speckle scatters every class per pixel, so rare classes are "
 "less often entirely absent (spurious presence, not signal); v4 is idiosyncratic (rarely "
 "predicts Beaver, over-predicts Urban).\n"
 "Why/Interpret: the sampling designs discriminate the variants. Design effect separates the "
 "dot-product v6 from the smooth v2-v5, and Approach D correlation orders their quality "
 "(v2≈v3≈v5 > v4 > v6). The stratification crossover (helps rare, hurts common) holds across "
 "all variants. Draws from designs, not accuracy estimates."),

"change_convergence.png": (
 "5-class collapse vs 10-class: change-class convergence",
 "Does merging the stable classes speed up convergence for the change classes?\n"
 "Layout: one panel per change class. Axes: x = n (log); y = stratified SD of that class's "
 "per-class F1 (v2, W=1, log); red dashed = 10-class scheme, blue = 5-class collapse.\n"
 "Why: the 5-class scheme gives each change stratum n/5 windows (vs n/10) — double the "
 "allocation — but it also collapses the six stable strata into one, so Stable is sampled "
 "n/5 instead of 6*n/10.\n"
 "Interpret: a CROSSOVER. 5-class converges faster at small n (the allocation benefit — SD "
 "lower for n<=~200), but for the rarest classes (Development, Beaver) the 10-class scheme "
 "catches up and passes at large n, because under-sampling Stable degrades change-class F1 "
 "PRECISION (false positives live in the stable background). Recall gain vs precision cost. "
 "Draws from a design, not accuracy estimates."),

"recall_precision_convergence.png": (
 "5-class collapse vs 10-class: recall vs precision, shown not inferred",
 "Splits the change-class F1 crossover into its two components so the mechanism is visible "
 "rather than inferred from F1.\n"
 "Layout: 2 rows x 4 change classes. Top row = stratified SD of RECALL (producer's accuracy, "
 "TP/reference-total); bottom row = stratified SD of PRECISION (user's accuracy, TP/map-total). "
 "Axes: x = n (log); y = SD across 100 draws (v2, W=1, log). Blue solid = 5-class collapse, "
 "red dashed = 10-class.\n"
 "Why: recall depends on how well the design samples the reference change class; collapse "
 "doubles each change stratum's allocation (n/5 vs n/10), so recall should be estimated BETTER. "
 "Precision depends on the false-positive rate, whose denominator lives in the stable "
 "background; collapse samples Stable n/5 instead of 6*n/10, so precision should be estimated "
 "WORSE at large n.\n"
 "Interpret: exactly that split. Recall SD is lower under collapse at every n (ratio ~0.7-0.84). "
 "Precision SD crosses over — collapse is better at small n but WORSE at large n for the rarest "
 "classes (Development ~2x, Harvest ~1.6x the 10-class SD at n=5000). The F1 crossover is a "
 "recall gain traded against a precision loss, not a single effect. Draws from a design, not "
 "accuracy estimates."),

"collapse_summary.png": (
 "5-class collapse vs 10-class: OA, macro-F1, design effect",
 "Overall comparison of the two class schemes.\n"
 "Panels: OA SD vs n (W=1); macro-F1 SD vs n (W=1); design effect vs W. Solid = 5-class, "
 "dashed = 10-class; one line per variant.\n"
 "Interpret: OA SD is comparable between schemes (both fall ~1/sqrt(n)). macro-F1 SD is HIGHER "
 "and non-monotonic for the 5-class scheme — each of the four change classes carries 1/5 weight "
 "(vs 1/10), so their intermittent presence dominates the macro average; and macro-F1 is NOT "
 "comparable as a level across schemes (it averages 5 classes here, 10 there). Design effect is "
 "HIGHER under the collapse (the collapsed OA is dominated by the ~98% Stable class, which is "
 "highly spatially autocorrelated), lifting even the speckly v6 from ~10 to ~23 at W=9. Draws "
 "from a design, not accuracy estimates."),

"sd_vs_n_OA.png": (
 "Sampling experiment: precision vs sample size",
 "Approach A under simple random sampling: how precision improves with sample size.\n"
 "Layout: one panel per model version. Axes: x = n (windows drawn from the pooled frame, log, "
 "ticks at the actual n values); y = SD of overall accuracy across 100 draws (log). One line "
 "per window size W; dashed = a 1/sqrt(n) slope reference anchored at the W=1 line.\n"
 "Why: characterizes the sampling design's precision against the exhaustive-tiling census, and "
 "exposes the design effect.\n"
 "Interpret: every line is parallel to the dashed 1/sqrt(n) reference (n counts windows, each "
 "an independent draw, so SD ∝ 1/sqrt(n) at all W). Because larger W samples more pixels per "
 "window, at equal n it can sit BELOW W=1 — and the size of that gap is the design effect: "
 "small for the autocorrelated v2-v5 (the extra within-window pixels are largely redundant), "
 "large for the near-independent v6. Draws from a design, NOT accuracy estimates."),

"bias_vs_n_OA.png": (
 "Sampling experiment: weighted vs unweighted stratified bias",
 "Bias of sampled overall accuracy vs n (v2, W=3) for three estimators.\n"
 "Axes: x = n (log); y = mean sampled OA minus the census OA; dashed at 0. Lines: simple "
 "random (unweighted); stratified WEIGHTED (Horvitz-Thompson, window weight N_h/n_h, i.e. "
 "true center-class proportions); stratified UNWEIGHTED.\n"
 "Why: equal-allocation stratification oversamples rare classes on purpose, so the unweighted "
 "stratified mean does not target the census; weighting by the true proportions restores it.\n"
 "Interpret: simple and weighted-stratified converge to zero bias; unweighted stratified "
 "stays biased (~ -0.19) — the visible gap is the point."),

"class_absence.png": (
 "Sampling experiment: simple random fails for rare classes",
 "The documented failure of the simple-random arm for rare classes (v2, W=1).\n"
 "Axes: x = n (windows, log); y = fraction of 100 iterations in which the class is ENTIRELY "
 "absent (no sampled pixel labels it in reference or map); one line per class.\n"
 "Why: absence is a headline result, not a nuisance — when a class is absent its per-class "
 "metrics are undefined.\n"
 "Interpret: Development is absent in ~78% of iterations at n=20 and ~25% at n=200; the rare "
 "disturbance classes need large n before they appear reliably. This control motivates "
 "stratification."),

"strat_efficiency.png": (
 "Sampling experiment: stratification efficiency by class",
 "Whether stratifying on the center reference class reduces per-class variance (v2, W=1, "
 "n=5000).\n"
 "Axes: x = class (sorted); y = SD_stratified / SD_simple of the per-class F1, using the "
 "design-consistent (Horvitz-Thompson weighted) estimate for the stratified arm; dashed at 1. "
 "Green (<1) = stratification helps; red (>1) = hurts.\n"
 "Why: equal-allocation stratification trades common-class precision for rare-class "
 "precision.\n"
 "Interpret: it helps the rare classes enormously (Beaver ~0.14, an ~86% variance reduction) "
 "and hurts the common classes (Forest ~1.9), which equal allocation starves. The crossover "
 "(around Grass/Shrub-Water) is the design finding."),

"d_corr_vs_n.png": (
 "Sampling experiment: Approach D per-class correlation vs n",
 "Approach D under sampling: per-class proportion correlation vs sample size (v2, W=5, simple "
 "random).\n"
 "Axes: x = n (log); y = mean per-class Pearson corr(prop_map, prop_ref) across draws; one "
 "line per class.\n"
 "Why: correlation is the primary D tightness metric (RMSE rewards predicting near-zero for "
 "rare classes and produces artifacts); it should stabilize as n grows.\n"
 "Interpret: common classes reach a stable correlation quickly; rare classes are noisy at "
 "small n (few sampled windows contain them) and converge slowly. Correlation is undefined "
 "when a sample has no variance in a class (reported separately as frac_undefined)."),

"sd_vs_cost.png": (
 "Approach A design experiment: precision at equal cost",
 "Approach A (window-as-sampling-unit) precision vs sampling cost.\n"
 "Layout: one panel per model version. Axes: x = pixels sampled per cell (n*W^2, log); y = "
 "SD of overall accuracy across 200 random draws (log); one line per window size W.\n"
 "Method: within each cell, n non-overlapping WxW windows are placed at random (random "
 "sequential adsorption), all W^2 pixels enumerated and pooled into a confusion matrix.\n"
 "Why: at equal x, two designs interpret the same number of pixels — the lower curve "
 "extracts more information per pixel.\n"
 "Interpret: for the smooth versions (v2-v5), W=1 sits well below larger W at equal cost, so "
 "many small windows (or single pixels) buy far more precision per pixel interpreted than a "
 "few large windows — because pixels within a window are spatially autocorrelated. For the "
 "speckly v6 the curves nearly coincide (little autocorrelation to waste). These are draws "
 "from a design, NOT accuracy estimates."),

"design_effect_vs_W.png": (
 "Approach A design effect (cost of autocorrelation)",
 "How much within-window autocorrelation inflates sampling variance.\n"
 "Left panel: design effect = Var(sampled OA) / Var_binomial vs W, one line per version "
 "(Var_binomial = p(1-p)/N from the census OA p and the pooled pixel count N; a VARIANCE "
 "ratio, its square root is the SD ratio); dashed line at 1. Right panel: information "
 "retained per pixel = 1 / design effect vs W.\n"
 "Why: quantifies how far the effective sample size falls short of the nominal pixel count "
 "— 'how much autocorrelation costs you.'\n"
 "Interpret: at W=1 the design effect is ~0.8-0.95 (≈ independent pixels; slightly below 1 "
 "from cell stratification), rising steeply to ~28-32 at W=9 for the smooth versions — a 9x9 "
 "window's 81 pixels are worth only ~3 independent pixels. The speckly v6 stays low (~8 at "
 "W=9) because adjacent pixels are not autocorrelated. Effective sample size = N / deff."),

"bias_vs_W.png": (
 "Approach A unbiasedness check",
 "Does the sampling design recover the known census value?\n"
 "Axes: x = window size W; y = mean sampled overall accuracy (over 200 draws) minus the "
 "census OA; one line per version; dashed at 0.\n"
 "Why: a valid design should equal the census in expectation; the census is the truth here "
 "because we have every pixel.\n"
 "Interpret: bias is ~0 at all W (max |bias| ~0.005), so window aggregation under random "
 "placement is unbiased for the census — larger windows cost precision (see the design "
 "effect), not accuracy."),

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


DESIGN_EFFECT_ABCD = (
 "Sampling experiment: design effect vs W",
 "How much within-window spatial autocorrelation inflates sampling variance.\n"
 "Axes: x = window size W; y = design effect = Var(sampled OA) / Var_binomial, one line per "
 "model version; dashed at 1. Var_binomial = p(1-p)/(n*W^2) treats the sampled pixels as "
 "independent.\n"
 "Why: quantifies how far the effective sample size falls short of the nominal pixel count.\n"
 "Interpret: the design effect is ~1 at W=1 (verified — a per-pixel simple random sample "
 "behaves binomially), and rises steeply with W (~38-47 at W=9 for the smooth versions; ~10 "
 "for the speckly v6, whose adjacent pixels are not autocorrelated). Effective sample size = "
 "n*W^2 / design effect.")


def _five_class_wrap(result, path):
    """Shared experiment figures live in both the 10-class and 5-class folders under the same
    basename; flag the collapse version so its numbers aren't read as the 10-class ones."""
    if result and "Case_ABCD_sampling_5class" in path and \
            os.path.basename(path) not in ("change_convergence.png", "collapse_summary.png",
                                            "recall_precision_convergence.png"):
        title, body = result
        return ("[5-class collapse] " + title,
                "5-CLASS COLLAPSE version (Stable + Harvest/Development/Insect-Disease/Beaver; "
                "Unknown excluded). Class-specific numbers quoted below are from the 10-class run; "
                "the structure and interpretation carry over.\n" + body)
    return result


def describe(path):
    base = os.path.basename(path)
    if base == "design_effect_vs_W.png" and "Case_ABCD_sampling" in path:
        return _five_class_wrap(DESIGN_EFFECT_ABCD, path)
    if base in DESC:
        return _five_class_wrap(DESC[base], path)
    if base == "window_sampling_metrics.png":
        return window_metrics_desc(path)
    if base.startswith("prop_scatter_"):
        return prop_scatter_desc(path)
    if re.search(r"\d+_[a-z]+_vs_[a-z]+\.png", base, re.I):
        return pair_desc(path)
    return None


def _font(size, bold=False):
    return ImageFont.truetype(
        os.path.join(FONT_DIR, "DejaVuSans-Bold.ttf" if bold else "DejaVuSans.ttf"), size)


def _wrap(draw, text, font, max_w):
    """Word-wrap `text` to `max_w` pixels, preserving explicit newlines as paragraph breaks."""
    lines = []
    for para in text.split("\n"):
        if not para.strip():
            lines.append("")
            continue
        cur = ""
        for word in para.split(" "):
            trial = (cur + " " + word).strip()
            if not cur or draw.textlength(trial, font=font) <= max_w:
                cur = trial
            else:
                lines.append(cur)
                cur = word
        lines.append(cur)
    return lines


def render_caption(im, title, body):
    """Return a new image = `im` with a white caption band (title + body) drawn beneath it."""
    W = im.width
    margin = 20
    fs = max(13, min(20, W // 95))
    tf, bf = _font(fs + 2, bold=True), _font(fs)
    lh_t, lh_b = fs + 8, fs + 6
    scratch = ImageDraw.Draw(im)
    max_w = W - 2 * margin
    tlines = _wrap(scratch, title, tf, max_w)
    blines = _wrap(scratch, body, bf, max_w)
    cap_h = margin + len(tlines) * lh_t + 8 + len(blines) * lh_b + margin
    canvas = Image.new("RGB", (W, im.height + cap_h), "white")
    canvas.paste(im, (0, 0))
    d = ImageDraw.Draw(canvas)
    d.line([(0, im.height), (W, im.height)], fill=(150, 150, 150), width=2)
    y = im.height + margin
    for ln in tlines:
        d.text((margin, y), ln, fill=(0, 0, 0), font=tf); y += lh_t
    y += 8
    for ln in blines:
        d.text((margin, y), ln, fill=(45, 45, 45), font=bf); y += lh_b
    return canvas


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--check", action="store_true", help="print embedded text instead of writing")
    ap.add_argument("--meta-only", action="store_true", help="embed metadata but do not draw a caption")
    args = ap.parse_args()

    pngs = sorted(glob.glob(os.path.join(REPORTS, "**", "*.png"), recursive=True))
    captioned = embedded = missing = 0
    for p in pngs:
        if args.check:
            t = Image.open(p).text
            print(f"\n=== {p} ===  (captioned={t.get('Captioned','0')})")
            print("Title:", t.get("Title", "(none)"))
            print(t.get("Description", "(no Description)")[:300])
            continue
        d = describe(p)
        if d is None:
            missing += 1
            print(f"  NO DESCRIPTION: {p}")
            continue
        title, desc = d
        orig = Image.open(p)
        already = orig.text.get("Captioned") == "1"
        info = PngImagePlugin.PngInfo()
        info.add_text("Title", title)
        info.add_text("Description", desc)
        info.add_text("Source", "Landcover_Interpretation / scripts/annotate_figures.py")
        if args.meta_only or already:
            info.add_text("Captioned", "1" if already else "0")
            orig.save(p, pnginfo=info)
            embedded += 1
        else:
            info.add_text("Captioned", "1")
            render_caption(orig.convert("RGB"), title, desc).save(p, pnginfo=info)
            captioned += 1
    if not args.check:
        print(f"\ncaptioned {captioned}; metadata-only {embedded}; {missing} without a description")


if __name__ == "__main__":
    main()
