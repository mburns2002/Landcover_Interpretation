# Change detection rate vs grid cell area (caption)

**Figures:** `change_detection_rate_vs_cell_area_by_agent.{pdf,png}` (per-agent small multiples) and
`change_detection_rate_vs_cell_area_combined.{pdf,png}` (all agents on one set of axes).

Change detection rate against grid cell area for the four GLKN disturbance agents (harvest,
development, beaver, and insect and disease mortality), from the grid cell-size analysis of the GLKN
attributed change polygons within the seven-watershed area of interest (AOI). The by-agent figure
gives one panel per agent, and the combined figure overlays all four agents with a legend.

Detection rate, the y axis, is the number of complete cells intersecting at least one polygon of that
agent divided by the number of complete cells, that is `n_with_change / n_cells_complete`. It is a
per-cell proportion, the fraction of cells in which the agent is detected, and not an areal density.
The denominator is `n_cells_complete`, the cells fully contained in the AOI, so edge cells excluded by
the completeness filter are not counted; `n_cells_total` is not used. Cell area on the x axis is
`cell_side_m^2 / 1e6` in square kilometers, at the five grid sizes 0.18, 0.71, 2.82, 11.29, and 45.16
square kilometers (14, 28, 56, 112, and 224 pixels of 30 m). The x axis uses a base-10 log scale,
since the cell areas span a 256-fold range, and the top axis relabels the same positions in pixels.
The dashed vertical line marks the selected 112 pixel cell (11.29 square kilometers).

In the by-agent figure the y axis is free per panel, so the trend for the rare agents stays visible;
the panels are therefore not on a common y scale, and the combined figure gives the shared-scale
comparison. Detection rate rises with cell area for every agent, harvest is highest and insect and
disease is lowest, and beaver and insect and disease rest on few cells (for example, at the 112 pixel
size, 62 and 19 cells with change out of 664 complete cells), so their rates carry more sampling
noise. No aggregate "any change" line is drawn: the per-agent `n_with_change` counts cells, cells can
contain more than one agent, and a sum across agents would double-count, and the export has no
all-agent row.

The year window of the polygons is not recorded in this export (the file name and columns carry no
year field), so it is not asserted here.

Source: `reports/GLKN_change_agents/glkn_grid_proportions_per_agent_5070_4agent.csv` (EPSG:5070).
Script: `manuscript_formatting/chapter_3/plot_change_detection_rate.R`.
