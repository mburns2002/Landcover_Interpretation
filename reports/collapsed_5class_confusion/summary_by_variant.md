# Collapsed 5-class census: per-variant summary

Census over 180 interpreted cells (adjudicated reference, temporally-matched per-bracket map field) from the 21,561-cell frame. OA is dominated by the ~98.5% Stable class; the all-Stable baseline is shown alongside. macro-F1 averages 5 classes here versus 10 in the 10-class matrices, so the two are not comparable as levels. CIs are 95% (ratio estimator with FPC; bootstrap in parentheses in the CSV).

| Variant | Valid px | All-Stable OA | OA (95% CI) | kappa (95% CI) | macro-F1 (95% CI) | mean IoU (95% CI) |
|---|---|---|---|---|---|---|
| v2 | 20,438,955 | 0.984 | 0.872 (0.848--0.896) | 0.043 (0.025--0.064) | 0.218 (0.207--0.230) | 0.192 (0.184--0.200) |
| v3 | 20,438,955 | 0.984 | 0.828 (0.802--0.854) | 0.021 (0.011--0.034) | 0.204 (0.193--0.215) | 0.178 (0.170--0.185) |
| v4 | 20,438,955 | 0.984 | 0.894 (0.879--0.910) | 0.074 (0.048--0.103) | 0.224 (0.211--0.235) | 0.198 (0.190--0.206) |
| v5 | 20,438,955 | 0.984 | 0.793 (0.762--0.825) | 0.014 (0.005--0.025) | 0.190 (0.183--0.197) | 0.165 (0.158--0.172) |
| v6 | 20,438,955 | 0.984 | 0.596 (0.572--0.620) | 0.005 (0.002--0.008) | 0.157 (0.152--0.161) | 0.123 (0.118--0.128) |
