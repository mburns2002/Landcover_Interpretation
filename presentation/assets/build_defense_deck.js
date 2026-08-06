// builds the defense slide deck
// usage: node build_defense_deck.js [figuresDir ...]
// any directory passed is searched for figure filenames; missing figures become labeled placeholders

const pptxgen = require("pptxgenjs");
const fs = require("fs");
const path = require("path");

// search these directories in order for each figure filename
const SEARCH_DIRS = process.argv.slice(2).length
  ? process.argv.slice(2)
  : [
      "presentation/figures",
      "manuscript_formatting/figures",
      "figures",
      ".",
    ];

const INK = "1A1A1A";
const BODY = "333333";
const MUTED = "8A8A8A";
const FONT = "Arial";

// resolve a figure filename against the search directories
function findFig(name) {
  if (!name) return null;
  for (const d of SEARCH_DIRS) {
    const p = path.join(d, name);
    if (fs.existsSync(p)) return p;
  }
  return null;
}

const pres = new pptxgen();
pres.layout = "LAYOUT_WIDE"; // 13.33 x 7.5
pres.author = "Mina Burns";
pres.title = "Satellite embeddings for multi-class landscape change attribution";

const missing = [];

function titleText(slide, text) {
  if (!text) return;
  slide.addText(text, {
    x: 0.55,
    y: 0.3,
    w: 12.2,
    h: 0.62,
    fontSize: 26,
    bold: true,
    color: INK,
    fontFace: FONT,
    margin: 0,
    valign: "middle",
  });
}

// draws either the image or a labeled placeholder frame
function figureAt(slide, file, x, y, w, h) {
  const p = findFig(file);
  if (p) {
    slide.addImage({ path: p, x, y, w, h, sizing: { type: "contain", w, h } });
  } else {
    if (file) missing.push(file);
    slide.addShape(pres.ShapeType.rect, {
      x,
      y,
      w,
      h,
      fill: { color: "FFFFFF" },
      line: { color: "C8C8C8", width: 1, dashType: "dash" },
    });
    slide.addText(file ? `[ ${file} ]` : "[ figure to come ]", {
      x,
      y: y + h / 2 - 0.3,
      w,
      h: 0.6,
      fontSize: 14,
      color: MUTED,
      fontFace: FONT,
      align: "center",
      valign: "middle",
      margin: 0,
    });
  }
}

function bulletsAt(slide, items, x, y, w, h, size) {
  if (!items || !items.length) return;
  slide.addText(
    items.map((t, i) => ({
      text: t,
      options: { bullet: true, breakLine: i !== items.length - 1 },
    })),
    {
      x,
      y,
      w,
      h,
      fontSize: size || 15,
      color: BODY,
      fontFace: FONT,
      margin: 0,
      paraSpaceAfter: 10,
      valign: "top",
    }
  );
}

// slide constructors -------------------------------------------------------

function addTitleSlide(o) {
  const s = pres.addSlide();
  s.background = { color: "FFFFFF" };
  s.addText(o.title, {
    x: 0.9,
    y: 1.9,
    w: 11.5,
    h: 1.9,
    fontSize: 34,
    bold: true,
    color: INK,
    fontFace: FONT,
    margin: 0,
  });
  s.addText(o.sub, {
    x: 0.9,
    y: 3.9,
    w: 11.5,
    h: 1.4,
    fontSize: 17,
    color: BODY,
    fontFace: FONT,
    margin: 0,
    lineSpacing: 26,
  });
  if (o.notes) s.addNotes(o.notes);
  return s;
}

// title + full width figure
function addFigureSlide(o) {
  const s = pres.addSlide();
  s.background = { color: "FFFFFF" };
  titleText(s, o.title);
  const top = o.title ? 1.12 : 0.5;
  const bottomPad = o.caption ? 0.62 : 0.35;
  figureAt(s, o.fig, 0.75, top, 11.83, 7.5 - top - bottomPad);
  if (o.caption) {
    s.addText(o.caption, {
      x: 0.75,
      y: 7.5 - 0.6,
      w: 11.83,
      h: 0.42,
      fontSize: 12,
      color: MUTED,
      fontFace: FONT,
      margin: 0,
    });
  }
  if (o.notes) s.addNotes(o.notes);
  return s;
}

// title + figure left + bullets right
function addSplitSlide(o) {
  const s = pres.addSlide();
  s.background = { color: "FFFFFF" };
  titleText(s, o.title);
  figureAt(s, o.fig, 0.55, 1.12, 8.35, 5.9);
  bulletsAt(s, o.bullets, 9.25, 1.35, 3.5, 5.5, 15);
  if (o.notes) s.addNotes(o.notes);
  return s;
}

// title + bullets only
function addTextSlide(o) {
  const s = pres.addSlide();
  s.background = { color: "FFFFFF" };
  titleText(s, o.title);
  bulletsAt(s, o.bullets, 0.85, 1.5, 11.6, 5.4, o.size || 20);
  if (o.notes) s.addNotes(o.notes);
  return s;
}

// title + native table
function addTableSlide(o) {
  const s = pres.addSlide();
  s.background = { color: "FFFFFF" };
  titleText(s, o.title);
  const head = o.rows[0].map((c) => ({
    text: String(c),
    options: { bold: true, color: INK, fill: { color: "FFFFFF" } },
  }));
  const body = o.rows.slice(1).map((r) =>
    r.map((c) => ({ text: String(c), options: { color: BODY } }))
  );
  s.addTable([head, ...body], {
    x: o.x || 1.0,
    y: 1.3,
    w: o.w || 11.3,
    fontSize: o.fontSize || 13,
    fontFace: FONT,
    border: { type: "solid", color: "DDDDDD", pt: 0.5 },
    align: "left",
    valign: "middle",
    autoPage: false,
    colW: o.colW,
  });
  if (o.note) {
    s.addText(o.note, {
      x: o.x || 1.0,
      y: 6.85,
      w: o.w || 11.3,
      h: 0.4,
      fontSize: 12,
      color: MUTED,
      fontFace: FONT,
      margin: 0,
    });
  }
  if (o.notes) s.addNotes(o.notes);
  return s;
}

// section divider
function addSectionSlide(o) {
  const s = pres.addSlide();
  s.background = { color: "FFFFFF" };
  s.addText(o.kicker, {
    x: 0.9,
    y: 2.9,
    w: 11.5,
    h: 0.4,
    fontSize: 15,
    color: MUTED,
    fontFace: FONT,
    margin: 0,
  });
  s.addText(o.title, {
    x: 0.9,
    y: 3.35,
    w: 11.5,
    h: 1.1,
    fontSize: 30,
    bold: true,
    color: INK,
    fontFace: FONT,
    margin: 0,
  });
  if (o.notes) s.addNotes(o.notes);
  return s;
}

// ==========================================================================
// ACT I. SETUP
// ==========================================================================

addTitleSlide({
  title:
    "Structuring satellite embeddings for multi-class landscape change attribution",
  sub:
    "Mina Burns\nPhD defense, 7 August 2026\neMapR Lab, Oregon State University\nAdvisor: Robert Kennedy",
  notes:
    "Thank the committee. One sentence of orientation: this thesis is about two things that turn out to be the same thing, how you represent satellite data for change attribution, and how you find out whether the resulting map is any good. Keep this to about 30 seconds.",
});

addFigureSlide({
  title: "Four agents of change in the western Great Lakes",
  fig: "pres_01_agents_naip.png",
  notes:
    "Set up the problem physically before any methods. Harvest and development are abrupt and geometric. Beaver flowage and insect and disease mortality are diffuse, irregular, and often partial canopy loss rather than removal. Point out that a human looking at NAIP can usually name the agent, which is what makes this an attribution problem rather than a detection problem. Do not linger, about 45 seconds.",
});

addFigureSlide({
  title: "Study area and reference watersheds",
  fig: "fig_2_1_study_area.png",
  bullets: [],
  notes:
    "Three states, Minnesota, Wisconsin, and the Michigan Upper Peninsula, terrestrial only, Great Lakes excluded. The study grid is a continuous frame of roughly 21,561 cells at 112 pixels, EPSG:5070. The seven GLKN park units shown are the source of the attributed change training polygons, and they occupy a small fraction of the grid. The 180 black squares are the interpreted validation cells, distributed across the full grid rather than confined to the parks. Be explicit about that distinction, since it is the single most common misreading of this design.",
});

addFigureSlide({
  title: "Change is rare",
  fig: "pres_02_rarity.png",
  notes:
    "The four change classes together are about 1.6 percent of interpreted reference pixels. That number is the complement of the all-Stable baseline accuracy that appears later, so plant it here and call back. Rarity is not a nuisance to be handled, it is the defining property of the problem and it drives three separate results in this talk: what the classifiers can learn, how many samples you need to see a class at all, and how much interpreters agree.",
});

addTextSlide({
  title: "Why change attribution is hard",
  bullets: [
    "Rare. Change is a small fraction of the landscape, and the agents differ in abundance by orders of magnitude",
    "Spatially clustered. Change occurs in patches, so nearby pixels carry redundant information",
    "Conceptually ambiguous. For some classes, trained interpreters looking at the same ground disagree on the label",
  ],
  size: 19,
  notes:
    "This is the thesis in one slide. Each adjective maps to one act of the talk. Rare drives the sampling results, clustered drives the design effect and the spatial coherence results, ambiguous drives the reference reliability results. Tell the audience that explicitly so they have a scaffold for the next 35 minutes.",
});

addTextSlide({
  title: "Two questions",
  bullets: [
    "How should satellite embeddings be structured to represent both baseline condition and interannual change?",
    "How should the resulting maps be validated, given a reference that is itself produced by human interpretation?",
    "The two turn out to be linked. The property that distinguishes representations is the property conventional assessment is least able to see.",
  ],
  size: 19,
  notes:
    "Chapter 2 answers the first, Chapter 3 the second. Flag the third bullet as the punchline and say you will come back to it. Do not explain it yet.",
});

addTableSlide({
  title: "Ten-class scheme",
  rows: [
    ["Code", "Class", "Type"],
    ["1", "Harvest", "Change"],
    ["2", "Development", "Change"],
    ["3", "Forest", "Stable"],
    ["4", "Urban", "Stable"],
    ["5", "Water", "Stable"],
    ["6", "Agriculture", "Stable"],
    ["7", "Grass/Shrub", "Stable"],
    ["8", "Wetland", "Stable"],
    ["9", "Beaver", "Change"],
    ["10", "Insect/Disease Mortality", "Change"],
  ],
  x: 3.6,
  w: 6.1,
  fontSize: 14,
  note:
    "Five-class collapse: the six stable classes become Stable, the four change classes are retained, Unknown excluded.",
  notes:
    "Six stable classes, four change classes. Mention the five-class collapse now, since most results are reported both ways, and say that the collapse is defined once and applied identically everywhere. Roughly 40 seconds.",
});

// ==========================================================================
// ACT II. DATA AND METHODS
// ==========================================================================

addSectionSlide({
  kicker: "Part one",
  title: "How the data are represented",
  notes: "Brief pause. This is Chapter 2 territory.",
});

addFigureSlide({
  title: "AlphaEarth Foundations",
  fig: "pres_03_aef_schematic.png",
  notes:
    "Three points. First, only three sources are required at inference, Sentinel-2, Landsat 8 and 9, and Sentinel-1, while eleven sources were used as training targets, including GEDI, ERA5-Land, GRACE, and NLCD. Second, the spatial context is 1.28 km frames, 128 by 128 pixels at 10 m. Third, the support period is the range of input timestamps and the valid period is the window summarized, and they need not coincide. Flag NLCD as a training target yourself. Your stable classes map closely onto NLCD classes, which plausibly contributes to strong stable-class performance and explains nothing about the change classes. Raising it first is much better than answering it cold.",
});

addFigureSlide({
  title: "Five embedding configurations",
  fig: "fig_2_3_embedding_configs.png",
  notes:
    "The design variable is whether the representation retains a full baseline embedding or reduces change to a magnitude. v2 and v3 preserve the baseline, v5 adds the dot product to the baseline, v4 is delta only, v6 is dot product only. Everything downstream is held constant, same classifier, same training points, same reference. That control is what lets you attribute differences to representation.",
});

addTextSlide({
  title: "Spectral baseline",
  bullets: [
    "spec_all: Sentinel-2, Landsat 8, and Sentinel-1 composites, roughly 50 bands",
    "Those are exactly the three sources AlphaEarth requires at inference time",
    "So the comparison holds the input information constant and varies only the representation",
  ],
  size: 19,
  notes:
    "This is a stronger control than most embedding versus spectral comparisons in the literature, which compare against whatever baseline was convenient. Say so plainly. If asked, the AlphaEarth paper Table S1 lists these three as the only sources marked input, everything else is a training target only.",
});

addFigureSlide({
  title: "Workflow",
  fig: "fig_2_2_workflow.png",
  notes:
    "Move quickly. One line on the classifier: Random Forest, 300 trees, identical across every configuration. Do not explain Random Forest, the committee knows it and explaining it invites the question of why you are explaining it.",
});

addSplitSlide({
  title: "Choosing the assessment unit",
  fig: "fig_3_2_detection_rate_a.png",
  bullets: [
    "Detection rate rises with cell size for every agent",
    "Harvest and development are detected far more often than beaver and insect or disease at every scale",
    "112 px, 3,360 m, 11.29 km2 selected",
  ],
  notes:
    "At the selected 112 px cell, harvest appears in about 60 percent of complete cells, development in 31 percent, beaver in 9 percent, and insect and disease in 3 percent. That gradient is the rarity slide again, now expressed as a sampling constraint. The cell size is a compromise between detecting rare agents and keeping interpretation tractable.",
});

addFigureSlide({
  title: "Interpretation interface",
  fig: "pres_04_ckit_interface.png",
  notes:
    "CKIT-RF. An interpreter views NAIP for both dates, places labeled training points within the cell, and a within-cell Random Forest propagates those labels to every pixel. The output is a wall-to-wall labeled cell, not a set of points. Five interpreters, 180 cells, 72 of them interpreted independently by two people. That 72-cell overlap is what makes Chapter 3 possible.",
});

addSplitSlide({
  title: "A census within each cell, not scattered points",
  fig: "pres_05_census_vs_points.png",
  bullets: [
    "Every pixel in the cell carries a reference label",
    "A point sample of the same cell supports no statement about spatial structure",
    "This choice is what makes the Chapter 2 comparison possible",
  ],
  notes:
    "This is the design decision the whole talk turns on, so slow down here. The left panel is what we have, the right is what a conventional assessment would have. Tell them you will return to this in the final act and show, on simulated landscapes where truth is known, that the right panel cannot rank two maps that the left panel ranks cleanly. About one minute.",
});

// ==========================================================================
// ACT III. REPRESENTATION
// ==========================================================================

addSectionSlide({
  kicker: "Results, part one",
  title: "Representation determines spatial structure",
});

addTableSlide({
  title: "Aggregate accuracy, ten-class",
  rows: [
    ["Source", "OA", "Kappa", "Macro-F1", "Mean IoU", "Cells"],
    ["v2", "0.659", "0.536", "0.383", "0.301", "180"],
    ["v3", "0.635", "0.514", "0.381", "0.299", "180"],
    ["v4", "0.245", "0.123", "0.162", "0.096", "180"],
    ["v5", "0.593", "0.472", "0.365", "0.285", "180"],
    ["v6", "0.130", "0.040", "0.089", "0.049", "180"],
    ["spec_all", "0.588", "0.461", "0.362", "0.275", "168"],
  ],
  x: 2.6,
  w: 8.1,
  fontSize: 15,
  note: "Pooled across five NAIP brackets against the adjudicated reference.",
  notes:
    "The baseline-preserving configurations, v2, v3, and v5, sit between 0.59 and 0.66, and the spectral baseline at 0.588 is within that band. v4 and v6, the ones that discard the baseline, collapse. First conclusion: retaining a baseline embedding matters more than anything else in this comparison, and embeddings do not beat a matched spectral composite on aggregate accuracy.",
});

addTableSlide({
  title: "Every configuration loses to a trivial baseline",
  rows: [
    ["Source", "Five-class OA", "Kappa", "Macro-F1"],
    ["Predict Stable everywhere", "0.984", "0.000", "n/a"],
    ["v2", "0.872", "0.043", "0.218"],
    ["v3", "0.828", "0.021", "0.203"],
    ["v4", "0.894", "0.074", "0.224"],
    ["v5", "0.793", "0.014", "0.190"],
    ["v6", "0.596", "0.005", "0.157"],
  ],
  x: 3.1,
  w: 7.1,
  fontSize: 15,
  note: "Design-based five-class metrics.",
  notes:
    "Raise this yourself, do not wait to be asked. Predicting Stable everywhere gives 98.4 percent overall accuracy and every configuration falls below it. This is not a defect in the maps, it is a demonstration that overall accuracy is uninformative when the class of interest is 1.6 percent of the landscape. It is the strongest possible motivation for everything in Chapter 3. Note also that v4 is best on this metric and fourth of five on ten-class accuracy, which is the inversion the next slides explain.",
});

addFigureSlide({
  title: "Per-cell macro-F1",
  fig: "fig_2_5_percell_f1.png",
  notes:
    "One point per cell on the common 168-cell set, so the comparison is on identical footprints. The distributions overlap heavily for v2, v3, v5, and spec_all. Aggregate ranking is not stable across cells, which is a first hint that a single number is hiding structure.",
});

addTableSlide({
  title: "Per-class F1, ten-class",
  rows: [
    ["Class", "v2", "v3", "v4", "v5", "v6", "spec_all"],
    ["Water", "0.938", "0.938", "0.300", "0.933", "0.150", "0.940"],
    ["Agriculture", "0.800", "0.806", "0.477", "0.797", "0.265", "0.620"],
    ["Forest", "0.793", "0.767", "0.351", "0.718", "0.188", "0.770"],
    ["Urban", "0.466", "0.497", "0.052", "0.481", "0.041", "0.453"],
    ["Wetland", "0.431", "0.409", "0.097", "0.405", "0.109", "0.373"],
    ["Grass/Shrub", "0.246", "0.280", "0.168", "0.256", "0.099", "0.332"],
    ["Harvest", "0.119", "0.083", "0.146", "0.041", "0.023", "0.102"],
    ["Development", "0.018", "0.007", "0.005", "0.006", "0.004", "0.007"],
    ["Insect/Disease", "0.016", "0.017", "0.008", "0.012", "0.006", "0.023"],
    ["Beaver", "0.004", "0.003", "0.012", "0.003", "0.001", "0.004"],
  ],
  x: 1.5,
  w: 10.3,
  fontSize: 12,
  note: "Sorted by v2 F1. The four change classes are at the bottom.",
  notes:
    "Do not soften this. The stable classes are respectable and the change classes are close to failures, uniformly across every configuration including the spectral baseline. Uniformity is the informative part: if representation were the binding constraint, the configurations would differ. They do not. That points at something the classifiers share, which is the reference, and that is Chapter 3. Expect the committee to press here, so state the honest position now and again at the ceiling slide.",
});

addFigureSlide({
  title: "The same ground, five configurations",
  fig: "fig_2_9_speckle.png",
  notes:
    "This is the central slide of Chapter 2. Same cell, same classifier, same training data, only the feature representation differs. v2, v3, and v5 give contiguous patches, v4 is grainy, v6 is salt and pepper with a neighbor-change value of 0.80. Let the audience look at it for a few seconds before you say anything. Then ask them which map they would hand to a park manager.",
});

addSplitSlide({
  title: "Accuracy and coherence come apart",
  fig: "pres_06b_speckle_vs_oa_5class.png",
  bullets: [
    "v4 has the highest five-class accuracy and is among the most fragmented",
    "The same configuration ranks fourth of five on ten-class accuracy",
    "Every configuration falls below the all-Stable baseline",
  ],
  notes:
    "The dissociation stated quantitatively. A configuration can top an aggregate metric while producing a map nobody would use. If asked about rank correlation, say that with five points a correlation coefficient describes those five points rather than supporting inference, and that the informative feature is the position of v4 rather than any trend.",
});

addSplitSlide({
  title: "Spatial structure, quantified",
  fig: "fig_2_8_morans_i.png",
  bullets: [
    "Reference Moran's I 0.75, coherent variants 0.82",
    "The maps are smoother than the reference, not just different",
    "v6 at 0.08 confirms the visual read",
  ],
  notes:
    "Be honest about the direction here. The coherent variants are more spatially autocorrelated than the interpreted reference, and their median-by-area patch size is smaller. So the failure mode is over-smoothing rather than fragmentation, and more coherent than truth is not automatically better. Expect a question on this and welcome it, since it is a genuinely interesting result.",
});

addFigureSlide({
  title: "Patch size distributions",
  fig: "fig_2_7_patch_ecdf.png",
  notes:
    "Area-weighted cumulative distribution of patch size within the interpreted footprints. The reference has a median-by-area of about 239 hectares, v2 about 110, spec_all about 47, v6 essentially zero. The spectral baseline is more fragmented than the coherent embedding configurations, which is the answer if anyone asks why spec_all is missing from the speckle scatter.",
});

addFigureSlide({
  title: "Training-cap sensitivity for the change classes",
  fig: "fig_2_10_changecap.png",
  notes:
    "Varying the change-class training cap over 50, 100, 150, and 200 points. Beaver has a training pool of only about 502 pixels, so the cap is a large fraction of what exists. Producer's accuracy moves and user's accuracy stays near zero, meaning the classifier can be pushed to find more beaver only by predicting far more beaver than exists. That is a precision problem the training budget cannot solve.",
});

addFigureSlide({
  title: "Embeddings against a matched spectral composite",
  fig: "fig_S2_3_spectral_vs_embedding_a.png",
  notes:
    "Same three sensors, different representation. The change classes are weak for both. Say the conclusion plainly: on this task, embeddings did not outperform a matched spectral composite on aggregate accuracy, and the interesting difference between them is spatial rather than statistical. Resisting the temptation to claim an embedding win is worth doing out loud.",
});

// ==========================================================================
// ACT IV. THE REFERENCE
// ==========================================================================

addSectionSlide({
  kicker: "Results, part two",
  title: "The reference is the binding constraint",
});

addSplitSlide({
  title: "Interpreters disagree, and not at random",
  fig: "fig_3_3_agreement_forest.png",
  bullets: [
    "Stable 0.99, Harvest 0.75",
    "Development 0.29, Insect/Disease 0.23, Beaver 0.08",
    "Same classes the classifiers fail on",
  ],
  notes:
    "Five interpreters, 72 double-interpreted cells, cluster bootstrap by pair. The classes with the lowest interpreter agreement are the same classes with the lowest classifier accuracy. Beaver agreement is 0.077, with a confidence interval reaching zero. Two trained people looking at the same imagery essentially do not agree on beaver.",
});

addSplitSlide({
  title: "Model accuracy against the interpreter ceiling",
  fig: "fig_2_11_model_vs_interpreter.png",
  bullets: [
    "Grey diamonds are the agreement ceiling",
    "Stable classes approach it",
    "Change classes fall below an already low ceiling",
  ],
  notes:
    "State the honest version. The ceiling explains why these classes are hard and it does not close the gap. Beaver model F1 is 0.004 against a ceiling of 0.077, insect and disease 0.016 against 0.229. So the reference bounds what is achievable and the classifier does not reach that bound. Someone will do this arithmetic, so do it first. The defensible claim is that raising the classifier alone cannot fix these classes, not that the classifier is already at the limit.",
});

addFigureSlide({
  title: "Is the disagreement about drawing or about defining?",
  fig: "fig_3_4_disagreement_geometry.png",
  notes:
    "If interpreters disagreed only on boundary placement, contested area would sit in thin strips along edges. It does not. The contested area is in large, geometrically complex zones, and the dominant contested pairs are forest with wetland and grass or shrub with wetland. That is a clue that the disagreement is about class identity.",
});

addFigureSlide({
  title: "Opposing labels on the same ground",
  fig: "fig_3_5_training_conflict.png",
  notes:
    "The direct evidence. In the largest contested zones both interpreters placed training points, and assigned them to different classes. One called it grass or shrub, the other wetland. This is not imprecision, it is disagreement about what the class means. Reviewers are anonymized.",
});

addSplitSlide({
  title: "Agreement does not recover under spatial tolerance",
  fig: "fig_3_6_spatial_tolerance.png",
  bullets: [
    "Allow a match within 3 or 5 pixels",
    "Boundary-driven disagreement recovers",
    "Grass/shrub and wetland recover little",
  ],
  notes:
    "The confirmatory test. If disagreement were about drawing, relaxing spatial precision would recover it. For the transitional classes it does not. Five convergent diagnostics all point the same way, which is why the chapter states the conclusion as strongly as it does.",
});

addTextSlide({
  title: "Hard to define, not hard to draw",
  bullets: [
    "For the transitional and rare classes, there is no single correct label for the ground",
    "The achievable accuracy on those classes is bounded by the reference, not by the classifier",
    "A reported accuracy without a companion reliability estimate cannot distinguish the two cases",
  ],
  size: 19,
  notes:
    "The verdict slide for Chapter 3's first half. Pause on the third bullet, which is the recommendation that follows. If asked what to do about it, the answer is latent class modeling on the double-interpreted cells, which is on the future work slide.",
});

// ==========================================================================
// ACT V. SAMPLING
// ==========================================================================

addSectionSlide({
  kicker: "Results, part three",
  title: "What a sample can and cannot tell you",
});

addSplitSlide({
  title: "Rare classes vanish from small samples",
  fig: "fig_3_9_class_absence.png",
  bullets: [
    "Fraction of iterations where a class is entirely absent",
    "Common classes always present",
    "Rare change classes missed outright at small n",
  ],
  notes:
    "Simple random sampling, Monte Carlo. For the rare change classes, an accuracy estimate is not merely imprecise at small sample size, it is undefined, since the class never appears. That is a qualitatively different failure from a wide confidence interval and it is easy to miss in practice.",
});

addSplitSlide({
  title: "Coherent maps cost more to validate",
  fig: "fig_3_8_design_effect.png",
  bullets: [
    "Design effect is observed variance over binomial variance",
    "Large for coherent variants",
    "Near one for the fragmented variant",
  ],
  notes:
    "This is where the two chapters lock together. Spatial coherence, the property that makes a map usable, is the property that inflates the variance of any estimate drawn from spatially clustered units. The fragmented map is cheap to validate and worthless. The good map is expensive to validate. Representation choice and validation design are therefore not separable decisions.",
});

addSplitSlide({
  title: "Stratify toward the rare classes, then weight",
  fig: "fig_S3_3_figure_S_bias_vs_n.png",
  bullets: [
    "Simple random misses the change classes",
    "Stratified unweighted is biased",
    "Stratified with inclusion-probability weights recovers the census",
  ],
  notes:
    "The practical recommendation. Stratification is necessary to see the rare classes at all, and it introduces bias unless the estimates are weighted by inclusion probability. Both steps are required. Then set up the next slide by asking whether that is sufficient.",
});

addSplitSlide({
  title: "Can a point sample tell two maps apart?",
  fig: "pres_09_simulation_f1.png",
  bullets: [
    "Simulated landscapes, truth known by construction",
    "Pixel-level F1 separates the four maps cleanly",
    "Correctly weighted sampled F1 does not",
  ],
  notes:
    "The terminal escalation, and joint work with Rob. Four renditions of a known truth landscape, from near-exact to badly degraded. Pixel-level F1 puts them in non-overlapping bands. Sampled F1, stratified and Olofsson-weighted, the exact estimator recommended on the previous slide, overlaps heavily across renditions and sits above the one-to-one line for the degraded maps, so it is optimistic about bad maps. So unbiasedness is necessary and not sufficient. This is a binary two-class problem, the easiest discrimination task available, which means ten classes should be worse rather than better.",
});

// ==========================================================================
// ACT VI. SYNTHESIS
// ==========================================================================

addSectionSlide({
  kicker: "Part four",
  title: "What it means together",
});

addFigureSlide({
  title: "The loop",
  fig: "pres_08_synthesis_loop.png",
  notes:
    "Deliver the punchline promised on slide six. Chapter 2 found that spatial structure is the axis on which representations actually differ. Chapter 3 found that conventional assessment is least able to see that axis. So a study of these same configurations designed the usual way, comparing aggregate accuracy from a point sample, would have concluded that the configurations were equivalent. The wall-to-wall response design is what made the difference visible.",
});

addTextSlide({
  title: "Reference-limited or model-limited",
  bullets: [
    "Stable classes are model-limited. Better features and better classifiers should help",
    "Change classes are reference-limited. Every configuration fails on them equally, including the spectral baseline",
    "The two cases call for different responses, and an accuracy figure alone cannot tell them apart",
  ],
  size: 19,
  notes:
    "This is the claim neither chapter can make alone. Chapter 2 supplies the uniformity of the failure, Chapter 3 supplies the cause. Say explicitly that this is the synthesis, since a committee listens for whether the manuscripts are a thesis or two papers stapled together.",
});

addTextSlide({
  title: "Recommendations",
  bullets: [
    "Retain a baseline embedding. Do not reduce interannual change to a magnitude alone",
    "Report a spatial-structure diagnostic alongside accuracy",
    "Report per-class interpreter agreement alongside per-class accuracy",
    "Stratify toward the rare classes and weight the estimates by inclusion probability",
    "To rank maps whose accuracies are close, enumerate within assessment units rather than sampling points",
  ],
  size: 17,
  notes:
    "Keep this crisp, one sentence each. These five follow directly from the five results just presented, in the same order, and it is worth saying so.",
});

addTextSlide({
  title: "Limitations",
  bullets: [
    "Reference change polygons come from the GLKN watersheds, a small and possibly unrepresentative fraction of the grid",
    "One region, one class scheme, one classifier",
    "Reliability rests on 72 double-interpreted cells, thin for the rarest agents",
    "The adjudicated reference is a consensus, not an estimate of an unobserved true label",
    "Simulation perturbations are parameterized rather than calibrated to the observed error structure",
  ],
  size: 16,
  notes:
    "Own these plainly and do not over-hedge. The first is the one most likely to be pressed, so have the answer ready: the polygon frequencies characterize the surveyed watersheds rather than the region, and the classifiers extrapolate to a landscape whose change characteristics may differ.",
});

addTextSlide({
  title: "Contributions and next steps",
  bullets: [
    "A controlled comparison of embedding representations holding classifier, training data, and reference fixed",
    "Evidence that aggregate accuracy is dissociated from spatial coherence, and a diagnostic for the dissociation",
    "A reliability characterization of a multi-interpreter reference, with five convergent diagnostics locating the disagreement",
    "Next: latent class models on the double-interpreted cells, converting the reliability bound into an applied correction",
  ],
  size: 17,
  notes:
    "The latent class point is the strongest forward-looking answer available, so land it clearly. Those models estimate sensitivity and specificity of several imperfect classifications without a gold standard, and the 72 double-interpreted cells are structurally what such models require.",
});

addTextSlide({
  title: "Thank you",
  bullets: [
    "Robert Kennedy, advisor",
    "Committee members",
    "Jamon and the eMapR Lab",
    "Bekka, Peter, and Ash, interpretation",
    "NPS Great Lakes Inventory and Monitoring Network",
  ],
  size: 18,
  notes:
    "Name the interpreters, they did a large share of the labor. Then stop talking and take questions.",
});

// ==========================================================================
// SUPPLEMENTAL
// ==========================================================================

addSectionSlide({
  kicker: "Backup",
  title: "Supplemental slides",
});

addTextSlide({
  title: "Supplemental contents",
  bullets: [
    "Tasseled Cap training-signal diagnostics",
    "Combined embedding and spectral configurations",
    "Overall accuracy by NAIP bracket",
    "Pooled confusion matrices",
    "Per-cell change-class F1",
    "Change-polygon size distributions",
    "Sampling precision against sample size",
    "Stratification efficiency and Approach D correlations",
    "Dedup-selection sensitivity",
    "Reviewer over-assignment",
    "Ten-class interpreter agreement",
  ],
  size: 15,
  notes:
    "Keep this slide's page number written on your hand. Jumping straight to the right backup slide during questions is worth more than any single result in the deck.",
});

const supp = [
  ["Tasseled Cap class-centroid trajectory", "tc_trajectory.png",
    "Training points in Tasseled Cap change space. Use if asked whether the change classes are separable in a conventional spectral change space at all."],
  ["Tasseled Cap diagnostics", "fig_S2_5_tc_diagnostics_a.png",
    "Delta scatter, mean-delta class signature, and linear discriminant projection of class separability."],
  ["Combined embeddings and spectral features", "S_variant_composition_full_navy_diamond.png",
    "Combining the two families gives at most a three-point gain over the better single family, not significant, with wider out-of-bag to validation gaps suggesting feature dilution."],
  ["Overall accuracy by NAIP bracket", "fig_2_4_oa_by_bracket.png",
    "Each bracket uses a disjoint cell set, so these are independent per-bracket assessments rather than a transfer curve. Do not pool across brackets for source comparisons."],
  ["Pooled confusion matrix, v2", "fig_2_12_confusion_a.png",
    "Five-class collapse, raw pixel counts colored by row proportion. Use for questions about which classes absorb the change pixels."],
  ["Pooled confusion matrix, spec_all", "fig_2_12_confusion_b.png",
    "The spectral baseline on 168 cells. Compare the change-class rows against v2."],
  ["Per-cell change-class F1", "fig_2_6_change_f1.png",
    "One point per contributing cell. Contributing cell counts differ across sources and are annotated."],
  ["Change-polygon size by agent", "fig_3_1_polygon_size.png",
    "GLKN polygon area by agent on a log hectare axis, 2010 through 2020. Median areas are similar across agents; the counts differ by orders of magnitude."],
  ["Total polygon area by agent", "pres_02b_polygon_area_2018_2020.png",
    "Restricted to the 2018 to 2020 classification window. The full 2010 to 2020 version exists as a separate file."],
  ["Sampling precision against sample size", "fig_3_7_sd_vs_n.png",
    "Precision improves as one over root n, and each spatial window contributes less than its pixel count owing to within-window autocorrelation."],
  ["Stratification efficiency by class", "fig_S3_4_figure_S_strat_efficiency.png",
    "Ratio of stratified to simple-random standard deviation. Below one means stratification helps for that class."],
  ["Approach D proportion correlation", "fig_S3_5_figure_S_d_corr_vs_n.png",
    "Per-class correlation of map against reference area proportions with sample size."],
  ["Dedup-selection sensitivity", "fig_S2_4_dedup_sensitivity.png",
    "Overall accuracy across 100 random pick-one-interpretation-per-location draws. The spread is under one accuracy point, so the choice of which interpretation to retain does not drive the results."],
  ["Reviewer over-assignment", "fig_S2_6_reviewer_overassignment.png",
    "Log ratio of pixels a reviewer claims for a class that the partner does not, against the reverse. Use if asked whether one interpreter drives the disagreement."],
  ["Ten-class interpreter agreement", "fig_S3_1_figure_S_agreement_forest_10class.png",
    "The ten-class version of the agreement figure. Wetland at 0.475 and grass or shrub at 0.289 are the transitional classes referenced in the talk."],
  ["Simulated landscape and its four renditions", "pres_10_simulation_landscapes.png",
    "Truth plus four renditions with increasing omission, commission, spatial misalignment, and edge effects. Show this if anyone questions whether the simulated maps are visibly different."],
];

supp.forEach(([t, f, n]) => addFigureSlide({ title: t, fig: f, notes: n }));

// ==========================================================================

pres.writeFile({ fileName: "/home/claude/Burns_defense_2026-08-07.pptx" }).then(() => {
  const uniq = [...new Set(missing)];
  console.log(`slides written: ${pres.slides.length}`);
  console.log(`figures found in: ${SEARCH_DIRS.join(", ")}`);
  console.log(`\nplaceholders (${uniq.length} figures not found):`);
  uniq.forEach((m) => console.log("  " + m));
});
