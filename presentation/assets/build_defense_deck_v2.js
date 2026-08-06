// rebuilds the defense deck around the research questions rather than thesis chapters
// usage: node build_defense_deck_v2.js [figuresDir ...]

const pptxgen = require("pptxgenjs");
const fs = require("fs");
const path = require("path");

const SEARCH_DIRS = process.argv.slice(2).length
  ? process.argv.slice(2)
  : ["figs", "presentation/figures", "manuscript_formatting/figures", "figures", "."];

const INK = "1A1A1A";
const BODY = "333333";
const MUTED = "8A8A8A";
const Q1 = "1F6FB2";        // question one, representation
const Q1T = "E9F1F8";
const Q2 = "C05621";        // question two, telling maps apart
const Q2T = "FBEEE4";
const NEUT = "5A5A5A";
const NEUTT = "F2F2F2";
const FONT = "Arial";

function findFig(n) {
  if (!n) return null;
  for (const d of SEARCH_DIRS) {
    const p = path.join(d, n);
    if (fs.existsSync(p)) return p;
  }
  return null;
}

const pres = new pptxgen();
pres.layout = "LAYOUT_WIDE";
pres.author = "Mina Burns";
pres.title = "Satellite embeddings for landscape change attribution";

const missing = [];

function T(s, text) {
  if (!text) return;
  s.addText(text, {
    x: 0.55, y: 0.3, w: 12.2, h: 0.62,
    fontSize: 28, bold: true, color: INK, fontFace: FONT,
    margin: 0, valign: "middle",
  });
}

function fig(s, file, x, y, w, h) {
  const p = findFig(file);
  if (p) {
    s.addImage({ path: p, x, y, w, h, sizing: { type: "contain", w, h } });
  } else {
    if (file) missing.push(file);
    s.addShape(pres.ShapeType.rect, {
      x, y, w, h,
      fill: { color: "FFFFFF" },
      line: { color: "C8C8C8", width: 1, dashType: "dash" },
    });
    s.addText(file ? `[ ${file} ]` : "[ figure to come ]", {
      x, y: y + h / 2 - 0.3, w, h: 0.6,
      fontSize: 14, color: MUTED, fontFace: FONT,
      align: "center", valign: "middle", margin: 0,
    });
  }
}

function bul(s, items, x, y, w, h, size) {
  if (!items || !items.length) return;
  s.addText(
    items.map((t, i) => ({
      text: t,
      options: { bullet: true, breakLine: i !== items.length - 1 },
    })),
    { x, y, w, h, fontSize: size || 18, color: BODY, fontFace: FONT,
      margin: 0, paraSpaceAfter: 12, valign: "top" }
  );
}

// row of tinted concept boxes
function boxRow(s, boxes, y, h, opts) {
  const o = opts || {};
  const n = boxes.length;
  const gap = 0.3;
  const left = 0.6;
  const total = 13.33 - left * 2;
  const w = (total - gap * (n - 1)) / n;
  boxes.forEach((b, i) => {
    const x = left + i * (w + gap);
    s.addShape(pres.ShapeType.rect, {
      x, y, w, h,
      fill: { color: b.tint || NEUTT },
      line: { color: b.tint || NEUTT, width: 1 },
    });
    s.addText(b.head, {
      x: x + 0.22, y: y + 0.18, w: w - 0.44, h: 0.42,
      fontSize: o.headSize || 19, bold: true,
      color: b.color || NEUT, fontFace: FONT, margin: 0,
    });
    if (b.body) {
      s.addText(b.body, {
        x: x + 0.22, y: y + 0.68, w: w - 0.44, h: h - 0.88,
        fontSize: o.bodySize || 15, color: BODY, fontFace: FONT,
        margin: 0, valign: "top", lineSpacing: 20,
      });
    }
  });
}

// ---- slide builders ------------------------------------------------------

function sFigure(o) {
  const s = pres.addSlide();
  s.background = { color: "FFFFFF" };
  T(s, o.title);
  const top = o.title ? 1.15 : 0.5;
  fig(s, o.fig, 0.75, top, 11.83, 7.5 - top - 0.35);
  if (o.notes) s.addNotes(o.notes);
  return s;
}

function sSplit(o) {
  const s = pres.addSlide();
  s.background = { color: "FFFFFF" };
  T(s, o.title);
  fig(s, o.fig, 0.55, 1.15, 8.3, 5.85);
  bul(s, o.bullets, 9.2, 1.45, 3.6, 5.4, o.size || 17);
  if (o.notes) s.addNotes(o.notes);
  return s;
}

function sText(o) {
  const s = pres.addSlide();
  s.background = { color: "FFFFFF" };
  T(s, o.title);
  bul(s, o.bullets, 0.85, 1.6, 11.6, 5.2, o.size || 22);
  if (o.notes) s.addNotes(o.notes);
  return s;
}

function sBoxes(o) {
  const s = pres.addSlide();
  s.background = { color: "FFFFFF" };
  T(s, o.title);
  let y = 1.5;
  if (o.lead) {
    s.addText(o.lead, {
      x: 0.6, y: 1.15, w: 12.1, h: 0.5,
      fontSize: 19, color: BODY, fontFace: FONT, margin: 0,
    });
    y = 2.0;
  }
  boxRow(s, o.boxes, y, o.h || 3.5, o);
  if (o.figBelow) fig(s, o.figBelow, 0.75, y + (o.h || 3.5) + 0.3, 11.83, 7.2 - (y + (o.h || 3.5) + 0.3));
  if (o.notes) s.addNotes(o.notes);
  return s;
}

function sFigBoxes(o) {
  const s = pres.addSlide();
  s.background = { color: "FFFFFF" };
  T(s, o.title);
  fig(s, o.fig, 0.75, 1.15, 11.83, 4.0);
  boxRow(s, o.boxes, 5.35, 1.75, { headSize: 16, bodySize: 13 });
  if (o.notes) s.addNotes(o.notes);
  return s;
}

function sBig(o) {
  const s = pres.addSlide();
  s.background = { color: "FFFFFF" };
  s.addText(o.text, {
    x: 1.1, y: 2.5, w: 11.1, h: 2.5,
    fontSize: o.size || 40, bold: true, color: o.color || INK,
    fontFace: FONT, margin: 0, valign: "middle",
  });
  if (o.sub) {
    s.addText(o.sub, {
      x: 1.1, y: 5.05, w: 11.1, h: 0.8,
      fontSize: 19, color: BODY, fontFace: FONT, margin: 0,
    });
  }
  if (o.notes) s.addNotes(o.notes);
  return s;
}

function sSection(o) {
  const s = pres.addSlide();
  s.background = { color: "FFFFFF" };
  s.addText(o.kicker, {
    x: 0.9, y: 2.95, w: 11.5, h: 0.4,
    fontSize: 16, color: MUTED, fontFace: FONT, margin: 0,
  });
  s.addText(o.title, {
    x: 0.9, y: 3.4, w: 11.5, h: 1.1,
    fontSize: 32, bold: true, color: INK, fontFace: FONT, margin: 0,
  });
  if (o.notes) s.addNotes(o.notes);
  return s;
}

// =========================================================================
// TITLE
// =========================================================================

(function () {
  const s = pres.addSlide();
  s.background = { color: "FFFFFF" };
  s.addText("Structuring satellite embeddings for multi-class landscape change attribution", {
    x: 0.9, y: 1.7, w: 11.5, h: 1.9,
    fontSize: 34, bold: true, color: INK, fontFace: FONT, margin: 0,
  });
  s.addText(
    "Mina Burns\nM.S. defense, 7 August 2026\neMapR Lab, Oregon State University\n\nCommittee: Robert Kennedy (advisor), Jamon Van Den Hoek, Mark Raleigh, Hamed Alemohammad",
    { x: 0.9, y: 3.7, w: 11.5, h: 2.0, fontSize: 16, color: BODY,
      fontFace: FONT, margin: 0, lineSpacing: 25 }
  );
  s.addNotes("You are replacing this slide. Committee names carried over from the previous draft, verify spelling and roles.");
})();

// =========================================================================
// I. MOTIVATION
// =========================================================================

sSplit({
  title: "The western Great Lakes",
  fig: "fig_2_1_study_area.png",
  bullets: [
    "Mixed northern hardwood and conifer forest, wetland, and agriculture",
    "Timber harvest is an economic mainstay",
    "Beaver reshape hydrology across whole watersheds",
    "Insect and disease mortality and exurban development are both expanding",
  ],
  size: 17,
  notes:
    "Landscape character: heterogeneous forest, extensive wetland, agriculture, low-density development.\nWhy change here matters: harvest drives regional forest economy; beaver flowage alters hydrology and habitat; insect and disease mortality threatens species composition, including black ash.\nGrid: continuous fishnet over terrestrial MN, WI, and Michigan UP, US only, Great Lakes water excluded, roughly 21,561 cells.\nBlack boxes are the 180 interpreted cells, spread across the whole grid.\nSeven of nine GLKN park units fall inside the grid, and they supply the change training polygons only.",
});

sFigBoxes({
  title: "Four agents of change",
  fig: "pres_01_agents_naip.png",
  boxes: [
    { head: "Harvest", body: "Abrupt, geometric, economically central" },
    { head: "Development", body: "Gradual conversion at the exurban fringe" },
    { head: "Beaver", body: "Flooding, diffuse edges, spectrally subtle" },
    { head: "Insect / disease", body: "Partial canopy loss, no clear boundary" },
  ],
  notes:
    "Harvest: clear boundaries, high contrast, the easiest case. Regionally the dominant disturbance by area.\nDevelopment: slow, small, often below the patch size that change detection is tuned for.\nBeaver: ecologically interesting and spectrally hard. Flooded forest can look like wetland, water, or dead canopy depending on stage.\nInsect and disease: mortality without removal, so canopy structure changes and the spectral signal is weak.\nA human interpreter can usually name the agent from NAIP. That is what makes this attribution, not just detection.",
});

sSplit({
  title: "How change is mapped now",
  fig: "pres_12_olofsson_standard.png",
  bullets: [
    "Detect change first",
    "Label the cause second",
    "Errors from step one carry into step two",
  ],
  size: 19,
  notes:
    "Standard practice: detect-then-attribute. Olofsson et al. 2014 is the reference for good practice on accuracy and area estimation.\nThe two-stage structure means a missed detection can never be attributed, and a false detection gets a cause assigned to it.\nAttribution errors are therefore not independent of detection errors, they compound.\nOur alternative: attribute directly from a single classification, no detection step.",
});

sSplit({
  title: "And how do we know a map is good?",
  fig: "pres_05_census_vs_points.png",
  bullets: [
    "The standard is a sample of points",
    "Cheap, unbiased, and well understood",
    "But can it tell two similar maps apart?",
  ],
  size: 19,
  notes:
    "Design-based accuracy assessment from a probability sample is the accepted standard, Olofsson et al. 2014, Stehman 2014.\nIt supports unbiased estimates of accuracy and area with quantified uncertainty.\nOur question is different: not how accurate is this map, but which of these two maps is better.\nThat is the comparison anyone selecting a sensor, feature set, or algorithm actually has to make.",
});

sSplit({
  title: "We tested that with simulated landscapes",
  fig: "pres_09_simulation_f1.png",
  bullets: [
    "Truth known by construction",
    "Four maps, from near-perfect to badly degraded",
    "Full-map F1 separates them cleanly",
    "Sampled F1 does not",
  ],
  size: 17,
  notes:
    "Joint work with Rob Kennedy. Simulated 6 by 6 km landscapes, patch structure from real imagery, stochastic disturbance at a target rate.\nFour renditions of truth with increasing omission, commission, spatial misalignment, and edge effects.\nSample is stratified random, n = 50, corrected following Olofsson et al. 2014, so this is the recommended estimator, not a naive one.\nTwo findings: the sampled estimate scatters widely, and for the degraded maps it sits above the one-to-one line, so the sample paints a rosier picture than the map deserves.\nBinary two-class problem, the easiest case. Ten classes should be worse.\nConsequence: to compare maps we need reference labels everywhere, not at scattered points.",
});

// =========================================================================
// II. THE PROMISE
// =========================================================================

sBig({
  text: "Foundation models learn a general representation of a place, once, that many tasks can reuse.",
  size: 32,
  sub: "The question is whether that representation carries change.",
  notes:
    "Trained on large unlabeled archives, then applied to downstream tasks with little labeled data.\nIn remote sensing this matters because labels are scarce and expensive, which is exactly our situation.\nInstead of hand-designing indices for each task, you get a learned feature vector per pixel.\nThe promise is that sparse labels go further. The open question is what the representation actually encodes.",
});

sSplit({
  title: "AlphaEarth Foundations",
  fig: "pres_03_aef_schematic.png",
  bullets: [
    "64 numbers per 10 m pixel, per year",
    "Only three sensors needed at inference",
    "Eleven sources used as training targets",
    "1.28 km of spatial context per pixel",
  ],
  size: 17,
  notes:
    "Inputs at inference: Sentinel-2, Landsat 8 and 9, Sentinel-1. Everything else is training-time only.\nTraining targets also include ALOS PALSAR, Copernicus DEM, GEDI, ERA5-Land, GRACE, NLCD, and text embeddings from Wikipedia and GBIF.\nSpatial context is 1.28 km, 128 by 128 pixels at 10 m, so each pixel's embedding is informed by its neighborhood.\nSupport period is the window input imagery is drawn from; valid period is the window summarized. They need not coincide.\nNLCD was a training target. Our stable classes map closely onto NLCD classes, which may help stable-class performance and does nothing for change.",
});

sBig({
  text: "AlphaEarth was designed to describe what is there.",
  size: 36,
  sub: "We need to know what changed. Those are not the same task.",
  notes:
    "Each embedding summarizes a year, so change is not represented natively, it has to be constructed from two years.\nThe AEF authors suggest the dot product between two years as a similarity measure, which gives a magnitude of change.\nA magnitude says how much changed, not what happened. Attribution needs the latter.\nThat gap is the opening for this thesis.",
});

sBig({
  text: "Do AlphaEarth embeddings work for change attribution?",
  size: 40,
  color: INK,
  notes:
    "State it plainly and let it sit.\nThis is the question the whole talk answers, and the answer is qualified rather than yes or no.",
});

sBoxes({
  title: "Two questions",
  boxes: [
    {
      head: "1. How do we structure them?",
      body: "An embedding describes one year. Change has to be built from two. Which construction preserves what we need?",
      color: Q1, tint: Q1T,
    },
    {
      head: "2. How do we tell the maps apart?",
      body: "If several configurations score about the same, how do we decide which one is actually better?",
      color: Q2, tint: Q2T,
    },
  ],
  h: 3.2,
  headSize: 22,
  bodySize: 17,
  notes:
    "Question one is a representation problem, question two is a measurement problem.\nColors return in the results section so the audience can track which question each result answers.\nThe two turn out to be linked, which is the closing argument.",
});

// =========================================================================
// III. HOW WE TESTED
// =========================================================================

sSection({ kicker: "Testing it", title: "What the test requires" });

sBig({
  text: "To answer this we need a lot of labeled change.",
  size: 36,
  sub: "The National Park Service Great Lakes Network has been mapping it for over a decade.",
  notes:
    "GLKN change polygons: attributed by agent, 2010 to 2020, across seven park units inside the grid.\nHundreds of thousands of labeled change pixels, already attributed to cause.\nThis is what makes a ten-class attribution scheme trainable at all.\nWe add our own wall-to-wall interpreted cells on top, for validation.",
});

sFigure({
  title: "Workflow",
  fig: "pres_11_workflow_simple.png",
  notes:
    "Reference: GLKN polygons plus NAIP at two dates, interpreted wall to wall.\nFeatures: two parallel tracks, AlphaEarth embeddings and spectral composites, from the same three sensors.\nClassifier: Random Forest, 300 trees, identical across every configuration. That is the control that makes the comparison valid.\nEvaluation: accuracy plus spatial structure.",
});

sSplit({
  title: "How we built the reference",
  fig: "pres_04_ckit_interface.png",
  bullets: [
    "Interpreter views NAIP at both dates",
    "Places labeled points inside the cell",
    "A within-cell model labels every pixel",
    "180 cells, 72 done twice",
  ],
  size: 17,
  notes:
    "CKIT-RF, built for this project. Interpreter-driven Random Forest inside a single cell.\nOutput is a fully labeled cell, not a set of points, which is what lets us compare maps rather than just score them.\nFive interpreters. Cells drawn randomly across the grid, stratified by NAIP acquisition bracket.\n72 cells interpreted independently by two people. That overlap is what makes the reliability analysis possible.\nIf asked about cell distribution: brackets follow state NAIP acquisition cadence, so spatial spread partly tracks acquisition years.",
});

sSplit({
  title: "Change is rare",
  fig: "pres_02_rarity.png",
  bullets: [
    "Change is about 1.6% of interpreted pixels",
    "Harvest dominates what change there is",
    "Beaver and insect or disease are a rounding error",
  ],
  size: 17,
  notes:
    "Now that the audience knows what the reference is, this figure means something.\nAbout 1.6 percent of reference pixels are change. That number returns later as the trivial-baseline problem.\nThe four agents differ from each other by orders of magnitude, not just from stable classes.\nRarity constrains three separate things: what the classifier can learn, whether a sample sees the class at all, and how well interpreters agree.",
});

sBoxes({
  title: "Why this is hard",
  boxes: [
    { head: "Rare", body: "1.6% of pixels, and the agents differ by orders of magnitude" },
    { head: "Spatially clustered", body: "Change happens in patches, so nearby pixels repeat information" },
    { head: "Conceptually ambiguous", body: "Trained interpreters looking at the same ground disagree" },
  ],
  h: 3.0,
  headSize: 21,
  bodySize: 16,
  notes:
    "Three properties, each of which produces a separate result later.\nRare drives class absence in samples and thin training pools.\nClustered drives the design effect, meaning fewer independent observations than pixel counts suggest.\nAmbiguous drives the reference ceiling, which is the reason the change classes cannot be fixed by a better classifier alone.",
});

sFigure({
  title: "Building change from two years",
  fig: "pres_15_embedding_ops.png",
  notes:
    "Two embeddings, 2018 and 2020, 64 dimensions each.\nDelta: element-wise difference, direction of change in embedding space.\nDot product: similarity between the two years, collapses to a single magnitude.\nThese are the two operations available. The design question is what to combine them with.\nOn year choice: 2018 and 2020 bracket the interpretation dates; happy to say more if asked.",
});

sFigure({
  title: "Five configurations",
  fig: "fig_2_3_embedding_configs.png",
  notes:
    "v2 and v3 keep a full baseline embedding alongside change.\nv4 is delta only, no baseline.\nv5 is baseline plus dot product.\nv6 is dot product only, the AEF authors' suggested similarity measure on its own.\nThe design variable is whether a baseline embedding survives into the feature vector.",
});

sSplit({
  title: "The benchmark: spectral composites",
  fig: "pres_16_spectral_baseline.png",
  bullets: [
    "Sentinel-2, Landsat 8, Sentinel-1",
    "Roughly 50 bands",
    "Exactly the sensors AlphaEarth uses at inference",
    "Same information, different representation",
  ],
  size: 17,
  notes:
    "This is the null hypothesis. Without it, a good embedding score means nothing.\nCritically, these are the same three sensors AEF requires at inference, so the comparison holds input information constant and varies only representation.\nThat is a cleaner control than most embedding versus spectral comparisons, which use whatever baseline was convenient.\nIf embeddings do not beat this, the representation is not adding anything for this task.",
});

sBoxes({
  title: "Reporting on five classes",
  lead: "We care which agent caused the change, not which stable class was confused for another.",
  boxes: [
    { head: "Stable", body: "All six stable classes collapsed into one" },
    { head: "Harvest", body: "", color: Q2, tint: Q2T },
    { head: "Development", body: "", color: Q2, tint: Q2T },
    { head: "Beaver", body: "", color: Q2, tint: Q2T },
    { head: "Insect / disease", body: "", color: Q2, tint: Q2T },
  ],
  h: 1.15,
  headSize: 16,
  bodySize: 13,
  notes:
    "Ten classes were used for training. Reporting collapses the six stable classes into one.\nRationale: forest confused with wetland is not the error we care about. Missing a harvest is.\nCollapse is defined once and applied identically to every configuration.\nTen-class results exist and are in the supplement.",
});

// =========================================================================
// IV. RESULTS
// =========================================================================

sBoxes({
  title: "Results",
  boxes: [
    { head: "1. How do we structure them?", body: "Which construction of change from two embeddings works?", color: Q1, tint: Q1T },
    { head: "2. How do we tell the maps apart?", body: "Which configuration actually produces a better map?", color: Q2, tint: Q2T },
  ],
  h: 2.6,
  headSize: 22,
  bodySize: 17,
  notes:
    "Restate before results so the audience knows what each number is for.\nFirst three result slides answer question one, the rest answer question two.",
});

sFigure({
  title: "Change-class F1",
  fig: "pres_14_changeclass_f1_5class.png",
  notes:
    "Five-class collapse, four change classes, every configuration plus the spectral baseline.\nHigher is better. F1 balances missing real change against calling change where there is none.\nHarvest is the only class any configuration handles at all.\nDevelopment, beaver, and insect or disease are near zero everywhere, including spectral.\nThe uniformity is the informative part: if representation were the binding constraint, configurations would differ.",
});

sSplit({
  title: "Is it just the training data?",
  fig: "fig_2_10_changecap.png",
  bullets: [
    "Vary change-class training points: 50, 100, 150, 200",
    "Producer's accuracy moves",
    "User's accuracy stays near zero",
    "More training points is not the fix",
  ],
  size: 17,
  notes:
    "The obvious first objection, so answer it directly.\nBeaver has a training pool of only about 502 pixels, so the cap is a large share of what exists.\nPushing the classifier to find more beaver only makes it predict beaver far more often than beaver occurs.\nThat is a precision problem, and a training budget cannot solve it.",
});

sSplit({
  title: "Embeddings perform like spectral",
  fig: "fig_2_5_percell_f1.png",
  bullets: [
    "One point per cell, identical footprints",
    "Distributions overlap heavily",
    "No configuration is clearly ahead",
  ],
  size: 18,
  notes:
    "Per-cell macro-F1 on the common 168-cell set, so this is a like-for-like comparison.\nThe baseline-preserving configurations and the spectral composite land in the same range.\nAnswer to question one, part one: keeping a baseline embedding matters, and embeddings do not beat a matched spectral composite on accuracy.\nSo the interesting difference between them is not statistical. Set up the next section.",
});

sBig({
  text: "Why are the change classes so bad?",
  size: 40,
  sub: "Every configuration fails on them, including the spectral baseline. That points somewhere other than the features.",
  notes:
    "Transition slide. The uniformity of the failure is the clue.\nIf features were the constraint, configurations would separate. They do not.\nWhat every configuration shares is the reference.",
});

sSplit({
  title: "Interpreters disagree, and not at random",
  fig: "fig_3_3_agreement_forest.png",
  bullets: [
    "Stable 0.99, Harvest 0.75",
    "Development 0.29",
    "Insect / disease 0.23",
    "Beaver 0.08",
  ],
  size: 18,
  notes:
    "72 double-interpreted cells, five interpreters, cluster bootstrap by pair.\nThe classes interpreters agree on least are the classes the classifiers fail on most.\nBeaver agreement is 0.077 with a confidence interval reaching zero. Two trained people essentially do not agree on beaver.\nInter-interpreter reliability is an established concern in reference data, see Stehman and Czaplewski 1998, Foody 2010, Pengra et al. 2020.\nEvidence that this is conceptual rather than geometric: contested zones are large and interior, both interpreters placed training points in them and assigned different classes, and relaxing spatial tolerance does not recover agreement for the transitional classes.",
});

sSplit({
  title: "Against the interpreter ceiling",
  fig: "fig_2_11_model_vs_interpreter.png",
  bullets: [
    "Grey diamonds: how well two humans agree",
    "Stable classes reach it",
    "Harvest does not",
    "Change classes sit below an already low ceiling",
  ],
  size: 17,
  notes:
    "The ceiling is what the reference can support, not what the classifier can do.\nStable classes approach it, so those are model-limited: better features should help.\nHarvest has a high ceiling, 0.75, and the model does not reach it. That gap is a genuine model shortfall.\nBeaver model F1 0.004 against a ceiling of 0.077; insect and disease 0.016 against 0.229. The ceiling explains why they are hard and does not close the gap.\nDefensible claim: a better classifier alone cannot fix these classes. Not that the classifier is already at the limit.",
});

sBig({
  text: "So every configuration scores about the same. Which one gives a better map?",
  size: 34,
  color: Q2,
  notes:
    "This is question two, and the point where aggregate metrics stop helping.\nAccuracy has told us what it can. The rest is spatial.",
});

sFigure({
  title: "The same ground",
  fig: "fig_2_9_speckle.png",
  notes:
    "Reference panel first, then each configuration on identical ground.\nSame classifier, same training data, same reference. Only the feature representation differs.\nBaseline-preserving configurations give contiguous patches. Delta-only is grainy. Dot-product-only is salt and pepper.\nAsk the audience which map they would give a park manager.",
});

sSplit({
  title: "Measuring it",
  fig: "fig_2_7_patch_ecdf.png",
  bullets: [
    "Area-weighted patch size",
    "Reference 239 ha, v2 110 ha, v6 near zero",
    "Moran's I and neighbor-change tell the same story",
  ],
  size: 18,
  notes:
    "One metric shown; we computed three and they agree, so the choice is not doing any work.\nReference median-by-area about 239 ha. v2 about 110, spec_all about 47, v6 essentially zero.\nNote the direction honestly: coherent configurations are smoother than the reference on Moran's I, 0.82 against 0.75, so the failure mode is over-smoothing rather than fragmentation.\nSpectral composite is more fragmented than the coherent embedding configurations.",
});

sSplit({
  title: "The best-scoring configuration is one of the worst maps",
  fig: "pres_06b_speckle_vs_oa_5class.png",
  bullets: [
    "v4 tops five-class accuracy",
    "v4 is among the most fragmented",
    "Every configuration loses to predicting Stable everywhere",
  ],
  size: 17,
  notes:
    "This is the one thing to remember.\nv4 is delta-only: highest five-class overall accuracy at 0.894, among the most fragmented maps, and fourth of five on ten-class accuracy.\nThe dashed line is predicting Stable everywhere, 0.984, which beats every configuration. With change at 1.6 percent of the landscape, overall accuracy is uninformative.\nA conventional assessment, aggregate accuracy from a point sample, would have picked v4 or called them equivalent.\nOn rank correlation: five points describe five points, the informative feature is where v4 sits.",
});

// =========================================================================
// V. SYNTHESIS
// =========================================================================

sBoxes({
  title: "Back to the questions",
  boxes: [
    {
      head: "1. How do we structure them?",
      body: "Keep a full baseline embedding. Reducing change to a magnitude alone destroys the map, even when accuracy looks fine.",
      color: Q1, tint: Q1T,
    },
    {
      head: "2. How do we tell the maps apart?",
      body: "Not from accuracy, and not from a point sample. Spatial structure separates them, and it takes wall-to-wall reference to see it.",
      color: Q2, tint: Q2T,
    },
  ],
  h: 3.2,
  headSize: 22,
  bodySize: 17,
  notes:
    "Close the loop opened before the methods.\nQuestion one has a clean answer. Question two has a method answer rather than a number.\nThe link between them is the thesis: the property that distinguishes representations is the property conventional assessment cannot see.",
});

sText({
  title: "What we found",
  bullets: [
    "Embeddings match a matched spectral baseline. They do not beat it",
    "Keeping a baseline embedding is what matters most",
    "Aggregate accuracy is blind to spatial structure",
    "The change classes are limited by the reference, not the features",
  ],
  size: 21,
  notes:
    "Four claims, in the order the talk established them.\nFirst two answer question one, second two answer question two.\nThe fourth is the one that generalizes furthest: any rare, conceptually ambiguous class inherits it.",
});

sText({
  title: "Limitations",
  bullets: [
    "Change polygons come from park watersheds, a small part of the grid",
    "One region, one scheme, one classifier",
    "Reliability rests on 72 cells",
    "The reference is a consensus, not a truth",
  ],
  size: 21,
  notes:
    "First is the one most likely to be pressed: polygon frequencies describe surveyed watersheds, and classifiers extrapolate to a broader landscape.\n72 cells is enough for the transitional-class result and thin for the rarest agents.\nNext step: latent class models on the double-interpreted cells estimate interpreter sensitivity and specificity without a gold standard, turning the reliability bound into a correction.",
});

sText({
  title: "Thank you",
  bullets: [
    "Robert Kennedy",
    "Jamon Van Den Hoek, Mark Raleigh, Hamed Alemohammad",
    "Bekka, Peter, and Ash",
    "NPS Great Lakes Inventory and Monitoring Network",
    "eMapR Lab",
  ],
  size: 20,
  notes: "Verify committee names and roles against the title slide.",
});

// =========================================================================
// SUPPLEMENT
// =========================================================================

sSection({ kicker: "Backup", title: "Supplemental slides" });

const supp = [
  ["Choosing the assessment unit", "fig_3_2_detection_rate_a.png",
    "Detection rate against cell size by agent. At 112 px (3,360 m) harvest appears in about 60% of complete cells, development 31%, beaver 9%, insect and disease 3%. Cell size trades detection of rare agents against interpretation effort."],
  ["Aggregate accuracy, ten-class", "fig_2_4_oa_by_bracket.png",
    "Per-bracket overall accuracy. Brackets use disjoint cell sets, so these are independent assessments rather than a transfer curve."],
  ["Per-cell change-class F1", "fig_2_6_change_f1.png",
    "One point per contributing cell. Contributing cell counts differ across sources."],
  ["Rare classes vanish from small samples", "fig_3_9_class_absence.png",
    "Fraction of Monte Carlo iterations in which a class is entirely absent from a simple random sample. For the rare change classes an accuracy estimate is undefined, not merely imprecise. A window is the block of contiguous pixels drawn at each sample location."],
  ["Coherent maps cost more to validate", "fig_3_8_design_effect.png",
    "Design effect, observed variance over binomial variance. Large for the coherent configurations, near one for the fragmented one. Spatial coherence inflates the variance of any estimate drawn from clustered units."],
  ["Stratify toward rare classes, then weight", "fig_S3_3_figure_S_bias_vs_n.png",
    "Simple random misses the change classes, stratified unweighted is biased, stratified with inclusion-probability weights recovers the census."],
  ["Sampling precision against sample size", "fig_3_7_sd_vs_n.png",
    "Precision improves as one over root n. Each spatial window contributes less than its pixel count owing to within-window autocorrelation."],
  ["Simulated landscapes and their renditions", "pres_10_simulation_landscapes.png",
    "Truth plus four renditions with increasing omission, commission, spatial misalignment, and edge effects."],
  ["Agreement under spatial tolerance", "fig_3_6_spatial_tolerance.png",
    "Allowing a match within 3 or 5 pixels recovers boundary-driven disagreement. Grass/shrub and wetland recover little, which is evidence the disagreement is conceptual."],
  ["Where interpreters disagree", "fig_3_4_disagreement_geometry.png",
    "Contested area is in large interior zones, not thin boundary strips. Dominant contested pairs are forest with wetland and grass/shrub with wetland."],
  ["Opposing labels on the same ground", "fig_3_5_training_conflict.png",
    "Both interpreters placed training points in the same contested zone and assigned different classes. Direct evidence of conceptual rather than geometric disagreement."],
  ["Ten-class interpreter agreement", "fig_S3_1_figure_S_agreement_forest_10class.png",
    "Wetland 0.475, grass/shrub 0.289. The transitional stable classes."],
  ["Moran's I by configuration", "fig_2_8_morans_i.png",
    "Reference 0.75, coherent configurations 0.82, v6 0.08. The coherent configurations are smoother than the reference."],
  ["Embeddings against spectral, by class", "fig_S2_3_spectral_vs_embedding_a.png",
    "Class-level comparison of the two feature families."],
  ["Combined embeddings and spectral", "S_variant_composition_full_navy_diamond.png",
    "Combining families gives at most a three-point gain over the better single family, not significant, with wider out-of-bag to validation gaps suggesting feature dilution."],
  ["Tasseled Cap class trajectories", "tc_trajectory.png",
    "Training points in Tasseled Cap change space. Use if asked whether the change classes are separable in a conventional spectral change space."],
  ["Tasseled Cap diagnostics", "fig_S2_5_tc_diagnostics_a.png",
    "Delta scatter, mean-delta signature, and linear discriminant projection."],
  ["Confusion matrix, v2", "fig_2_12_confusion_a.png",
    "Five-class collapse, counts colored by row proportion. Shows which classes absorb the change pixels."],
  ["Confusion matrix, spec_all", "fig_2_12_confusion_b.png",
    "The spectral baseline on 168 cells."],
  ["Change-polygon size by agent", "fig_3_1_polygon_size.png",
    "GLKN polygon area by agent, log hectares, 2010 to 2020. Median areas are similar; counts differ by orders of magnitude."],
  ["Total polygon area by agent", "pres_02b_polygon_area_2018_2020.png",
    "Restricted to the 2018 to 2020 classification window."],
  ["Stratification efficiency", "fig_S3_4_figure_S_strat_efficiency.png",
    "Ratio of stratified to simple-random standard deviation. Below one means stratification helps."],
  ["Approach D proportion correlation", "fig_S3_5_figure_S_d_corr_vs_n.png",
    "Per-class correlation of map against reference area proportions with sample size."],
  ["Dedup-selection sensitivity", "fig_S2_4_dedup_sensitivity.png",
    "Overall accuracy across 100 random pick-one-interpretation draws. Spread under one accuracy point."],
  ["Reviewer over-assignment", "fig_S2_6_reviewer_overassignment.png",
    "Log ratio of pixels a reviewer claims that the partner does not, against the reverse. Use if asked whether one interpreter drives the disagreement."],
];

supp.forEach(([t, f, n]) => sFigure({ title: t, fig: f, notes: n }));

pres.writeFile({ fileName: "/home/claude/Mina_Defense_v2.pptx" }).then(() => {
  const u = [...new Set(missing)];
  console.log(`slides: ${pres.slides.length}`);
  console.log(`\nmissing figures (${u.length}):`);
  u.forEach((m) => console.log("  " + m));
});
