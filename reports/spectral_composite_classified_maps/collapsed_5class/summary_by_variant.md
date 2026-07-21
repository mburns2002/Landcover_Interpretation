# Collapsed 5-class census: per-variant summary

Census over 168 interpreted cells (adjudicated reference, temporally-matched per-bracket map field) from the 21,561-cell frame. OA is dominated by the ~98.5% Stable class; the all-Stable baseline is shown alongside. macro-F1 averages 5 classes here versus 10 in the 10-class matrices, so the two are not comparable as levels. CIs are 95% (ratio estimator with FPC; bootstrap in parentheses in the CSV).

| Variant | Valid px | All-Stable OA | OA (95% CI) | kappa (95% CI) | macro-F1 (95% CI) | mean IoU (95% CI) |
|---|---|---|---|---|---|---|
| spec_all | 18,788,997 | 0.985 | 0.782 (0.758--0.806) | 0.031 (0.019--0.043) | 0.203 (0.192--0.215) | 0.171 (0.164--0.179) |
