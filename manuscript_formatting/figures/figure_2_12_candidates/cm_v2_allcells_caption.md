# Caption: AlphaEarth Embedding v2 confusion matrix (Figure 2.12 candidate)

AlphaEarth Embedding v2, baseline + delta. Ten-class confusion matrix for the v2 embedding
configuration (the 2018 baseline field stacked with the 2018 to 2020 delta), pooled over all 180 grid
cells (the five per-bracket count matrices summed) against the adjudicated interpreted reference.
Reference classes are on the rows and predicted classes on the columns. Cells are raw pixel counts
colored by the row proportion, so the diagonal shade is the producer's accuracy for that class. The PA
column is producer's accuracy (recall) with the reference support n (row totals), the UA row is user's
accuracy (precision) with the predicted support n (column totals), and the corner gives overall
accuracy and Cohen's kappa. Overall accuracy is 66% and kappa is 0.54.

This replaces the earlier candidate that used only the single 2018 to 2020 in-sample control bracket
(36 cells); this version pools all 180 cells.

Source figure: `manuscript_formatting/figures/figure_2_12_candidates/cm_v2_allcells.png`.
