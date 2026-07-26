# Case_ABCD_sampling_5class

The **5-class collapse** of the sampling-design experiment. Same setup, designs, and approaches as the
10-class run; see [`../Case_ABCD_sampling/README.md`](../Case_ABCD_sampling/README.md) for the full
description of the population, the two designs (simple random, stratified HT), the four approaches
(A/B/C/D), and the table and plot definitions.

## What differs here
- **Classes:** Stable (urban, agriculture, grass/shrub, forest, water, wetland, and other), with
  Harvest, Development, Insect/Disease, and Beaver kept distinct.
- **Unknown is excluded** (unattributed change with no model equivalent). See `exclusion.txt` for the
  excluded-pixel count and its share of the frame.
- **Extra outputs** (from `scripts/sampling_collapse_comparison.py`): `collapse_vs_10class.csv`,
  `collapsed_kappa.csv`, `change_convergence.png`, `collapse_summary.png`, and
  `recall_precision_convergence.png`.

## Regenerate
```bash
python scripts/sampling_experiment_ABCD.py --collapse \
  --truth exports/truth_selections.csv --preds data/raw/transfer_predictions
python scripts/sampling_collapse_comparison.py     # the collapse comparison outputs
```
