#!/usr/bin/env Rscript
# change detection rate vs grid cell area, from the GLKN grid cell-size analysis.
# two figures: per-agent small multiples (free y) and a combined panel (shared y).
# detection rate = n_with_change / n_cells_complete (a per-cell proportion, not an areal density).

suppressPackageStartupMessages({
  library(readr)
  library(dplyr)
  library(ggplot2)
})

# this script lives in manuscript_formatting/chapter_3/, so the repo root is two levels up
root <- normalizePath(file.path(dirname(sub("--file=", "", grep("--file=", commandArgs(FALSE), value = TRUE))), "..", ".."))
if (length(root) == 0 || is.na(root)) root <- normalizePath(".")
figdir <- file.path(root, "manuscript_formatting", "chapter_3", "figures")
dir.create(figdir, showWarnings = FALSE, recursive = TRUE)

# glob for the grid cell-size csv (per-agent, 4-agent). prefer the tracked reports copy.
cands <- list.files(root, pattern = "grid_proportions_per_agent.*4agent.*\\.csv$",
                    recursive = TRUE, full.names = TRUE)
cands <- cands[!grepl("/\\.git/", cands)]
if (length(cands) == 0) stop("no grid cell-size csv found")
by_base <- split(cands, basename(cands))
if (length(by_base) > 1) {
  stop("multiple distinct grid cell-size csvs found, please disambiguate: ",
       paste(names(by_base), collapse = ", "))
}
reports_copy <- cands[grepl("/reports/", cands)]
csv <- if (length(reports_copy) > 0) reports_copy[1] else cands[1]
message("input: ", csv)

# agent order by detectability, display labels, and a colorblind-safe palette (okabe-ito)
agent_levels <- c("harvest", "development", "beaver", "insect_disease_mort")
agent_labels <- c("Harvest", "Development", "Beaver", "Insect/Disease")
pal <- c("Harvest" = "#0072B2", "Development" = "#E69F00",
         "Beaver" = "#009E73", "Insect/Disease" = "#CC79A7")

d <- read_csv(csv, show_col_types = FALSE) %>%
  mutate(
    area_km2 = (cell_side_m^2) / 1e6,                       # cell area in square km
    detection_rate = n_with_change / n_cells_complete,     # fraction of complete cells with change
    agent_f = factor(agent_labels[match(agent, agent_levels)], levels = agent_labels)
  ) %>%
  arrange(agent_f, area_km2)

# the five discrete cell sizes, for axis breaks (area) and the px secondary axis
sizes <- d %>% distinct(cell_side_px, cell_side_m, area_km2) %>% arrange(area_km2)
area_breaks <- sizes$area_km2
area_labs <- sprintf("%.2f", area_breaks)
px_labs <- as.character(sizes$cell_side_px)
sel_area <- sizes$area_km2[sizes$cell_side_px == 112]      # selected 112 px cell, 11.29 km2

base_theme <- theme_classic(base_size = 13) +
  theme(
    plot.title = element_text(face = "bold", size = 15),
    axis.title = element_text(size = 13),
    legend.position = "bottom",
    panel.grid = element_blank()                           # no background gridlines, keep axes
  )

# log axis (default, all ticks). linear axis: the narrow facets show only the endpoints and the
# selected cell (14, 112, 224 px); the wider combined panel can also show 56 px (2.82 km2)
x_log <- scale_x_log10(
  breaks = area_breaks, labels = area_labs,
  sec.axis = dup_axis(breaks = area_breaks, labels = px_labs, name = "grid cell side (px)")
)
x_lin <- function(px_keep) {                                 # linear scale labeling the given px sizes
  k <- sizes$cell_side_px %in% px_keep
  scale_x_continuous(
    breaks = area_breaks[k], labels = sprintf("%.2f", area_breaks[k]),
    sec.axis = dup_axis(breaks = area_breaks[k], labels = as.character(sizes$cell_side_px[k]),
                        name = "grid cell side (px)"))
}

# build and save both figures (per-agent facets and combined) for the given x scales and suffix
build_and_save <- function(x_facet, x_comb, xlab, suffix) {
  p_facet <- ggplot(d, aes(area_km2, detection_rate, color = agent_f)) +
    geom_vline(xintercept = sel_area, linetype = "dashed", color = "grey55", linewidth = 0.5) +
    geom_line(linewidth = 1) +
    geom_point(size = 2.4) +
    facet_wrap(~agent_f, ncol = 2, scales = "free_y") +
    scale_color_manual(values = pal) +
    x_facet +
    guides(color = "none") +
    labs(title = "GLKN Change Detection Rate vs Grid Cell Area, by Agent",
         x = xlab, y = "detection rate (fraction of complete cells with change)") +
    base_theme
  ggsave(file.path(figdir, paste0("change_detection_rate_vs_cell_area_by_agent", suffix, ".pdf")),
         p_facet, width = 8.5, height = 6.5)
  ggsave(file.path(figdir, paste0("change_detection_rate_vs_cell_area_by_agent", suffix, ".png")),
         p_facet, width = 8.5, height = 6.5, dpi = 320)

  p_comb <- ggplot(d, aes(area_km2, detection_rate, color = agent_f)) +
    geom_vline(xintercept = sel_area, linetype = "dashed", color = "grey55", linewidth = 0.5) +
    geom_line(linewidth = 1) +
    geom_point(size = 2.6) +
    scale_color_manual(values = pal, name = NULL) +
    x_comb +
    labs(title = "GLKN Change Detection Rate vs Grid Cell Area",
         x = xlab, y = "detection rate (fraction of complete cells with change)") +
    base_theme
  if (suffix == "") {                                          # the label overlaps a line on the linear x axis, keep it only on the log version
    p_comb <- p_comb + annotate("text", x = sel_area, y = max(d$detection_rate),
                                label = "selected: 112 px", angle = 90, vjust = -0.4, hjust = 1,
                                size = 3.3, color = "grey45")
  }
  ggsave(file.path(figdir, paste0("change_detection_rate_vs_cell_area_combined", suffix, ".pdf")),
         p_comb, width = 8, height = 5.6)
  ggsave(file.path(figdir, paste0("change_detection_rate_vs_cell_area_combined", suffix, ".png")),
         p_comb, width = 8, height = 5.6, dpi = 320)
}

# log: both panels label all ticks. linear: facets 14/112/224 px, combined also 56 px (2.82 km2)
build_and_save(x_log, x_log, expression("grid cell area (km"^2*", log scale)"), "")
build_and_save(x_lin(c(14, 112, 224)), x_lin(c(14, 56, 112, 224)),
               expression("grid cell area (km"^2*")"), "_linear")

message("wrote log and _linear versions of by_agent and combined (pdf+png) -> ", figdir)
