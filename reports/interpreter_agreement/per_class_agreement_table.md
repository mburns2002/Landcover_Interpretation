# Inter-interpreter per-class agreement (n = 72 double-interpreted cells)

Point estimates with 95% cluster (pair) bootstrap CIs (2000 replicates). F1 is the
balanced probability the two interpreters concur given one assigned the class.

| Class | Pairs | Support (px) | F1 (95% CI) | IoU (95% CI) | Reliability |
|-------|------:|-------------:|-------------|--------------|-------------|
| Water | 71 | 711,093 | 0.92 (0.86–0.95) | 0.85 (0.75–0.91) | High |
| Forest | 70 | 4,653,821 | 0.90 (0.88–0.92) | 0.82 (0.79–0.84) | High |
| Agriculture | 48 | 1,770,644 | 0.78 (0.72–0.82) | 0.64 (0.57–0.69) | High |
| Harvest | 35 | 124,714 | 0.75 (0.63–0.82) | 0.60 (0.46–0.70) | High |
| Urban | 72 | 269,340 | 0.61 (0.53–0.68) | 0.44 (0.36–0.51) | Moderate |
| Wetland | 61 | 1,302,064 | 0.47 (0.38–0.56) | 0.31 (0.24–0.39) | Low |
| Other | 16 | 29,888 | 0.45 (0.18–0.61) | 0.29 (0.10–0.43) | Low |
| Grass/Shrub | 69 | 1,079,543 | 0.29 (0.21–0.36) | 0.17 (0.12–0.22) | Low |
| Development | 27 | 9,734 | 0.28 (0.02–0.47) | 0.16 (0.01–0.30) | Low |
| Insect/Disease | 19 | 56,257 | 0.23 (0.00–0.47) | 0.13 (0.00–0.30) | Low |
| Beaver | 15 | 8,828 | 0.08 (0.00–0.21) | 0.04 (0.00–0.12) | Low |
| Unknown | 13 | 5,076 | 0.00 (0.00–0.00) | 0.00 (0.00–0.00) | Low |

**Overall** (95% CI):

- Overall agreement: 0.78 (0.75–0.80)
- Cohen's κ: 0.67 (0.62–0.71)
- Macro F1: 0.48 (0.43–0.51)
- Mean IoU: 0.37 (0.34–0.40)

Reliability tiers on F1: High ≥ 0.70, Moderate 0.50–0.70, Low < 0.50. Low/Moderate classes (e.g. Grass/Shrub, Wetland) indicate the human reference is itself unreliable there, so model scores on those classes are bounded by reference noise, not only model error.
