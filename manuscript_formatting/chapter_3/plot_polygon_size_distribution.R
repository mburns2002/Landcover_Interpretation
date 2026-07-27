#!/usr/bin/env Rscript
# distribution of GLKN change-agent polygon size, from the per-polygon histogram export.
# one facet per change agent, histogram of polygon area on a log10 hectare axis, free y since the
# per-agent polygon counts differ by two orders of magnitude.

suppressPackageStartupMessages({
  library(readr)
  library(dplyr)
  library(ggplot2)
})

# this script lives in manuscript_formatting/chapter_3/, so the repo root is two levels up
root <- normalizePath(file.path(dirname(sub("--file=", "", grep("--file=", commandArgs(FALSE), value = TRUE))), "..", ".."))
if (length(root) == 0 || is.na(root)) root <- normalizePath(".")
figdir <- file.path(root, "manuscript_formatting", "chapter_3")

cands <- list.files(root, pattern = "glkn_histograms_by_agent.*\\.csv$", recursive = TRUE, full.names = TRUE)
cands <- cands[!grepl("/\\.git/|/data/raw/", cands)]           # prefer the tracked reports copy
if (length(cands) == 0) stop("no histogram csv found")
csv <- cands[1]
message("input: ", csv)

# agent order by detectability, display labels, and the same colorblind-safe palette as the other
# chapter 3 figures (okabe-ito)
agent_levels <- c("harvest", "development", "beaver", "insect_disease_mort")
agent_labels <- c("Harvest", "Development", "Beaver", "Insect/Disease")
pal <- c("Harvest" = "#0072B2", "Development" = "#E69F00",
         "Beaver" = "#009E73", "Insect/Disease" = "#CC79A7")

d <- read_csv(csv, show_col_types = FALSE) %>%
  mutate(agent_f = factor(agent_labels[match(agent, agent_levels)], levels = agent_labels))

# facet labels carry the per-agent polygon count so the sample size is visible
labs <- d %>% count(agent_f) %>%
  mutate(lab = sprintf("%s (N = %s)", agent_f, formatC(n, big.mark = ",", format = "d")))
labeller_vec <- setNames(labs$lab, as.character(labs$agent_f))

p <- ggplot(d, aes(area_ha, fill = agent_f)) +
  geom_histogram(bins = 30, color = "white", linewidth = 0.15) +
  facet_wrap(~agent_f, ncol = 2, scales = "free_y", labeller = as_labeller(labeller_vec)) +
  scale_fill_manual(values = pal) +
  scale_x_log10() +
  guides(fill = "none") +
  labs(title = "GLKN Change-Agent Polygon Size Distribution",
       subtitle = "GLKN watersheds, 2010 to 2020",
       x = "polygon area (ha, log scale)", y = "number of polygons") +
  theme_classic(base_size = 13) +
  theme(plot.title = element_text(face = "bold", size = 15),
        plot.subtitle = element_text(size = 11, color = "grey25"),
        strip.text = element_text(face = "bold"),
        panel.grid = element_blank())

ggsave(file.path(figdir, "polygon_size_distribution_by_agent.pdf"), p, width = 8.5, height = 6)
ggsave(file.path(figdir, "polygon_size_distribution_by_agent.png"), p, width = 8.5, height = 6, dpi = 320)
message("wrote polygon_size_distribution_by_agent.{pdf,png} -> ", figdir)
