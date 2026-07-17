# Collapsed 5-class census: per-variant summary

Census over 180 interpreted cells (de-duplicated, seed 42) from the 21,561-cell frame. OA is dominated by the ~98.5% Stable class; the all-Stable baseline is shown alongside. macro-F1 averages 5 classes here versus 10 in the 10-class matrices, so the two are not comparable as levels. CIs are 95% (ratio estimator with FPC; bootstrap in parentheses in the CSV).

| Variant | Valid px | All-Stable OA | OA (95% CI) | kappa (95% CI) | macro-F1 (95% CI) | mean IoU (95% CI) |
|---|---|---|---|---|---|---|
| v2 | 20,437,331 | 0.985 | 0.884 (0.865--0.902) | 0.025 (0.013--0.038) | 0.211 (0.201--0.224) | 0.189 (0.182--0.197) |
| v3 | 20,437,331 | 0.985 | 0.807 (0.778--0.835) | 0.009 (0.003--0.016) | 0.193 (0.186--0.200) | 0.169 (0.162--0.176) |
| v4 | 20,437,331 | 0.985 | 0.941 (0.933--0.950) | 0.063 (0.038--0.090) | 0.217 (0.209--0.226) | 0.200 (0.196--0.206) |
| v5 | 20,437,331 | 0.985 | 0.767 (0.738--0.796) | 0.007 (0.002--0.013) | 0.187 (0.180--0.193) | 0.160 (0.153--0.167) |
| v6 | 20,437,331 | 0.985 | 0.750 (0.729--0.771) | 0.007 (0.002--0.012) | 0.178 (0.175--0.182) | 0.154 (0.149--0.158) |
