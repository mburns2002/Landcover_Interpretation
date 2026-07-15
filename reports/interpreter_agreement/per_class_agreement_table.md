# Inter-interpreter per-class agreement (n = 69 double-interpreted cells)

Point estimates with 95% cluster (pair) bootstrap CIs (2000 replicates). F1 is the
balanced probability the two interpreters concur given one assigned the class.

| Class | Pairs | Support (px) | F1 (95% CI) | IoU (95% CI) | Reliability |
|-------|------:|-------------:|-------------|--------------|-------------|
| Water | 68 | 707,099 | 0.92 (0.86–0.95) | 0.85 (0.75–0.91) | High |
| Forest | 67 | 4,462,932 | 0.90 (0.88–0.91) | 0.81 (0.78–0.84) | High |
| Agriculture | 47 | 1,668,792 | 0.78 (0.72–0.82) | 0.63 (0.56–0.69) | High |
| Harvest | 34 | 97,461 | 0.70 (0.60–0.76) | 0.53 (0.42–0.62) | Moderate |
| Urban | 69 | 263,149 | 0.60 (0.53–0.68) | 0.43 (0.36–0.51) | Moderate |
| Wetland | 59 | 1,267,358 | 0.47 (0.37–0.55) | 0.30 (0.23–0.38) | Low |
| Other | 16 | 29,888 | 0.45 (0.19–0.60) | 0.29 (0.10–0.43) | Low |
| Grass/Shrub | 66 | 1,050,926 | 0.30 (0.23–0.36) | 0.17 (0.13–0.22) | Low |
| Development | 26 | 9,606 | 0.28 (0.02–0.46) | 0.17 (0.01–0.30) | Low |
| Insect/Disease | 18 | 56,082 | 0.23 (0.01–0.49) | 0.13 (0.00–0.32) | Low |
| Beaver | 14 | 8,816 | 0.08 (0.00–0.21) | 0.04 (0.00–0.12) | Low |
| Unknown | 12 | 4,874 | 0.00 (0.00–0.00) | 0.00 (0.00–0.00) | Low |

**Overall** (95% CI):

- Overall agreement: 0.77 (0.74–0.80)
- Cohen's κ: 0.66 (0.62–0.70)
- Macro F1: 0.47 (0.43–0.51)
- Mean IoU: 0.36 (0.33–0.39)

Reliability tiers on F1: High ≥ 0.70, Moderate 0.50–0.70, Low < 0.50. Low/Moderate classes (e.g. Grass/Shrub, Wetland) indicate the human reference is itself unreliable there, so model scores on those classes are bounded by reference noise, not only model error.
