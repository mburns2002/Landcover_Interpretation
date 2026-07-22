# Inter-interpreter per-class agreement (n = 72 double-interpreted cells)

Point estimates with 95% cluster (pair) bootstrap CIs (2000 replicates). F1 is the
balanced probability the two interpreters concur given one assigned the class.

| Class | Pairs | Support (px) | F1 (95% CI) | IoU (95% CI) | Reliability |
|-------|------:|-------------:|-------------|--------------|-------------|
| Stable | 72 | 8,087,379 | 0.99 (0.99–1.00) | 0.99 (0.98–0.99) | High |
| Harvest | 35 | 124,641 | 0.75 (0.63–0.82) | 0.60 (0.46–0.70) | High |
| Development | 27 | 9,288 | 0.29 (0.03–0.47) | 0.17 (0.01–0.31) | Low |
| Insect/Disease | 19 | 56,257 | 0.23 (0.00–0.47) | 0.13 (0.00–0.30) | Low |
| Beaver | 15 | 8,828 | 0.08 (0.00–0.21) | 0.04 (0.00–0.12) | Low |

**Overall** (95% CI):

- Overall agreement: 0.99 (0.98–0.99)
- Cohen's κ: 0.60 (0.46–0.70)
- Macro F1: 0.47 (0.37–0.54)
- Mean IoU: 0.39 (0.33–0.44)

Reliability tiers on F1: High ≥ 0.70, Moderate 0.50–0.70, Low < 0.50. Low/Moderate classes (e.g. Grass/Shrub, Wetland) indicate the human reference is itself unreliable there, so model scores on those classes are bounded by reference noise, not only model error.
