# rf_class_maps

Colored renders of the **interpreted reference** rasters under `data/raw/rf_class_maps/` (that raw raster
tree is gitignored, so these PNGs are the only version visible on GitHub).

Despite the `rf_class_*Sentinel-2*` file naming, these are the adjudicated "Interpreted (RF)" reference
(the RF-assisted human interpretation used as ground truth), NOT a Random Forest classification of the
imagery. The spectral-baseline classification (`spec_all`) is a separate raster tree under
`data/raw/spectral_transferability_10class_percell/`. See `scripts/compare_interpreted_vs_model.py`.

## Files
`rf_class_04363_sample101_s2_2018.png` — grid cell 04363, sample_101, Sentinel-2, target 2018 (optical
window 2017-2019). Source:
`data/raw/rf_class_maps/CKIT_RF_mina_grid_s2_04363/rf_class_reviewer_mina_grid_04363_sample_101_sensor_Sentinel-2_target_2018_opt_2017_2019.tif`

`rf_class_31320_sample27_s2_2019.png` — grid cell 31320, sample_27, Sentinel-2, target 2019 (optical
window 2018-2020). Source:
`data/raw/rf_class_maps/CKIT_RF_bekka_grid_s2_31320/rf_class_reviewer_bekka_grid_31320_sample_27_sensor_Sentinel-2_target_2019_opt_2018_2020.tif`

Each source is a single-band int32 GeoTIFF (337x337 at 10 m, EPSG:5070) of the interpreted reference,
pixel values are CKIT class ids. Recolored with the canonical model legend
(`compare_interpreted_vs_model.load_mappings`); the CKIT-id to model-class crosswalk is in
`scripts/build_class_schema_figure.py`.
