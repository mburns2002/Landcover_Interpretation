# Figure 2.9 caption (OSU thesis format, placed below the figure)

Figure 2.9. Classified-map coherence at one location (cell 31320, EPSG:5070): the spectral baseline
(spec_all) alongside each embedding configuration (v2 to v6), from the current 180-cell temporally-matched
classifications. Each panel is the same ground extent colored with the standard 10-class palette. The
spectral baseline and the baseline-preserving embedding configurations (v2, v3, v5) produce contiguous
patches, v4 is grainier, and the dot-product configuration v6 is salt-and-pepper. A 1 km scale bar is on
the spectral panel.

## Alt text (OSU requires alt text on figures)

Six classified-map panels of the same location: the spectral baseline and the five embedding
configurations. The spectral baseline and configurations v2, v3, and v5 show contiguous land-cover
patches, v4 is grainier, and v6 fragments into salt-and-pepper speckle.

Source figure: `manuscript_formatting/figures/figure_2_9_speckle_crops.png` (and `.pdf`).

## Variant with the interpreted reference

`figure_2_9_speckle_crops_with_ref.png` (and `.pdf`) prepends the adjudicated interpreted reference for
the same cell as the first panel, so the classifications can be judged against ground truth (panel order:
interpreted reference, spectral, v2 to v6). The reference is the "Interpreted (RF)" raster from
`data/raw/rf_class_maps` (CKIT ids remapped to the 10 model codes); it is a separate raster from the
spectral baseline (spec_all).
