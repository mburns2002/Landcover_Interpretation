# rf_class_maps

Colored renders of the Random Forest classified land-cover maps under `data/raw/rf_class_maps/` (that
raw raster tree is gitignored, so these PNGs are the only version visible on GitHub).

## Files
`rf_class_04363_sample101_s2_2018.png` — grid cell 04363, sample_101, Sentinel-2, target 2018 (optical
window 2017-2019). Source:
`data/raw/rf_class_maps/CKIT_RF_mina_grid_s2_04363/rf_class_reviewer_mina_grid_04363_sample_101_sensor_Sentinel-2_target_2018_opt_2017_2019.tif`

The source is a single-band int32 GeoTIFF (337x337 at 10 m, EPSG:5070) whose pixel values are CKIT class
ids. It is recolored with the canonical model legend (`compare_interpreted_vs_model.load_mappings`); the
CKIT-id to model-class crosswalk is in `scripts/build_class_schema_figure.py`.
