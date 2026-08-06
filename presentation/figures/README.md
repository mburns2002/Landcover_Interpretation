# Presentation figures — index

Quick, linked index of the defense-deck figures in this folder. Click a name to open the PNG. For a
visual gallery (all images inline, with alternate versions grouped), see [FIGURES.md](FIGURES.md).

All figures are PNG only at 300 dpi (Google Slides deck), titled in Title Case, no background gridlines.
Generators live in `presentation/scripts/` (same stem as the figure).

## Main figures

| Figure | What it shows |
|---|---|
| [pres_01_agents_naip](pres_01_agents_naip.png) | 2×2 before/after NAIP examples, one per change agent (Harvest, Development, Beaver, Insect/Disease). |
| [pres_02_rarity](pres_02_rarity.png) | Change is ~1.6% of reference pixels: full stacked bar plus a zoom of the change sliver by class. |
| [pres_02b_polygon_area](pres_02b_polygon_area.png) · [2018–2020](pres_02b_polygon_area_2018_2020.png) | Total change-polygon area by agent (2010–2020; and the 2018–2020 window). |
| [pres_02c_watershed_rarity](pres_02c_watershed_rarity.png) | Change polygons cover ~2.9% of the GLKN watersheds; zoom by change type. |
| [pres_03_aef_schematic](pres_03_aef_schematic.png) · [a](pres_03_aef_schematic_a.png) · [b](pres_03_aef_schematic_b.png) | AlphaEarth inputs / training-targets schematic (three style options). |
| [pres_04_ckit_interface](pres_04_ckit_interface.png) | Annotated CKIT-RF interface and the resulting interpreted cell. |
| [pres_05_census_vs_points](pres_05_census_vs_points.png) | Census versus 50 sample points. |
| [pres_06_speckle_vs_oa](pres_06_speckle_vs_oa.png) · [5-class](pres_06b_speckle_vs_oa_5class.png) | Map speckle (neighbor-change) versus overall accuracy (10-class pooled; 5-class design-based). |
| [pres_07_speckle_with_ref](pres_07_speckle_with_ref.png) | Speckle crop (cell 31320) with the interpreted reference added as the first panel. Three more locations in [pres_07_speckle_with_ref_locations/](pres_07_speckle_with_ref_locations/). |
| [pres_08_synthesis_loop](pres_08_synthesis_loop.png) | Two-box loop for the closing argument. |
| [pres_10class_legend](pres_10class_legend.png) | Standalone 10-class color legend (Stable / Change groups). |
| [pres_11_workflow_simple](pres_11_workflow_simple.png) · [colored](pres_11_workflow_simple_colored.png) · [colored v2](pres_11_workflow_simple_colored_v2.png) · [stage3](pres_11_workflow_simple_stage3.png) | Reference → Features → Classification → Evaluation workflow; v2 adds a classified land-cover map box. |
| [pres_14_changeclass_f1_5class](pres_14_changeclass_f1_5class.png) · [full](pres_14_changeclass_f1_5class_full.png) · [by bracket](pres_14b_changeclass_f1_by_bracket.png) | Five-class per-class change F1 by source (auto-zoom, full 0–1, and per-bracket facets). |
| [pres_15_embedding_ops](pres_15_embedding_ops.png) · [v2](pres_15_embedding_ops_version_2.png) · [v3](pres_15_embedding_ops_version_3.png) · [v4](pres_15_embedding_ops_version_4.png) · [v5](pres_15_embedding_ops_version_5.png) | Two operations on a pair of embeddings: Delta keeps 64 dims, Dot product collapses to one value. v5 is the smoothest. |
| [pres_16_spectral_baseline](pres_16_spectral_baseline.png) | How the spectral-composite baseline is built (sensors → composite → Random Forest → map). |
| [pres_17_model_metrics](pres_17_model_metrics.png) · [+spec](pres_17_model_metrics_with_spec.png) · [5-class](pres_17_model_metrics_5class.png) · [5-class +spec](pres_17_model_metrics_5class_with_spec.png) | Accuracy metrics (OA, F1, IoU, Kappa) by model, grouped by statistic. 10-class and 5-class, with/without spec_all. |
| [pres_18_changeagent_f1_5class](pres_18_changeagent_f1_5class.png) · [full](pres_18_changeagent_f1_5class_full.png) · [vs ceiling](pres_18_changeagent_f1_vs_ceiling.png) | Five-class change F1 grouped by change agent, colored by model; the ceiling version overlays the interpreter agreement. |
| [pres_19_interpreter_ceiling_5class](pres_19_interpreter_ceiling_5class.png) | Per-class inter-interpreter agreement F1 (95% CI): the human ceiling on classifier F1. |
| [pres_20_training_conflict_overlay](pres_20_training_conflict_overlay.png) | Conflicting training labels on shared ground: the top grass/shrub-vs-wetland contested patches where interpreters placed training points but assigned different classes (deck/Spectral version of manuscript Fig 3.5). |

## Supplemental figures

| Figure | What it shows |
|---|---|
| [tc_trajectory](tc_trajectory.png) | Tasseled Cap class-centroid trajectory. |
| [S_variant_composition_clipped](S_variant_composition_clipped.png) · [full](S_variant_composition_full_navy_diamond.png) | Variant-composition ablation (clipped y-axis; full continuous y-axis). |

_Alternate marker treatments for the variant-composition figure live in `marker_style_options/`._

## Analysis subfolders

- [changecap/](changecap/) — change-class training-cap sensitivity: same-location maps under each cap
  (the commission flood) plus curve figures (predicted pixels, precision/recall, kappa vs cap).
- [pres_07_speckle_with_ref_locations/](pres_07_speckle_with_ref_locations/) — pres_07 (reference +
  every classification) at three more locations.
