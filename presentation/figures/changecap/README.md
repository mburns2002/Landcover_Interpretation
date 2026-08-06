# changecap — change-class training-cap sensitivity (deck figures)

Spectral-styled figures for the change-class training-cap analysis: a v2 embedding classifier is trained
with the four change classes capped at 50, 100, 150, and 200 training points (stable classes held at
200), scored on the common 180-cell set. Data: `reports/sensitivity_changecap_5class/`. The story is
that raising the cap floods the map with (mostly false) change.

## Maps (spatial comparison)

Same location classified under each cap, with the interpreted reference; each panel annotated with the
share of pixels it labels as change:

- `changecap_maps_cell04602_2017_2019.png` — cell 04602 (all four change classes)
- `changecap_maps_cell50721_2020_2022.png` — cell 50721 (Beaver, Development, Harvest)

Watch the Beaver (orange) commission grow along the wetland corridor as the cap rises.

## Curves (from sensitivity_metrics_long_5class.csv)

- `changecap_predicted_pixels_vs_cap.png` — predicted change pixels vs cap, one panel per change class,
  with the interpreted-reference count (dashed). Predictions climb far above truth, especially Beaver
  and Development.
- `changecap_precision_recall_vs_cap.png` — precision (UA) and recall (PA) vs cap. Recall rises only
  modestly while precision stays near zero: the extra change predictions are almost all false positives.
- `changecap_kappa_vs_cap.png` — overall kappa and macro-F1 vs cap; both fall as the cap rises.

Regenerate: `python presentation/scripts/pres_changecap_maps.py` and
`python presentation/scripts/pres_changecap_curves.py`.

## Related (not deck-styled)

Existing analysis outputs live under `reports/sensitivity_changecap/` (10-class) and
`reports/sensitivity_changecap_5class/` (5-class), including per-cap confusion matrices and the
`cap_vs_embedding_maps/` and `top_disagreement_maps/` map sets. Manuscript Figure 2.10
(`manuscript_formatting/figures/figure_2_10.png`) is the training-cap UA/PA figure.
