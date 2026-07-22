# Figure 2.3 caption (OSU thesis format, placed below the figure)

Figure 2.3. Construction of the five embedding feature configurations from the 2018 and 2020
AlphaEarth embedding fields. Baseline-preserving configurations (v2, v3, v5) retain a full embedding
field, whereas change-only configurations (v4, v6) retain only a difference (delta) or similarity
(dot product) summary. Band counts are shown at right.

## Alt text (OSU requires alt text on figures)

A schematic showing two 64-dimensional annual embedding fields, 2018 and 2020, the delta and
dot-product operations derived from them, and five rows (v2 to v6) that stack baseline and change
blocks into classifier inputs of 128, 128, 64, 65, and 1 bands.

## Tone note (for Figure 2.2 to match)

No Figure 2.2 workflow diagram was found in the repository, so the baseline and change tones were
chosen here as the reference. Baseline (full embedding field) is Okabe-Ito blue (#0072B2) and change
(delta or dot) is Okabe-Ito orange (#E69F00). The two tones differ in hue and lightness, so they read
in grayscale, and the change blocks also carry a diagonal hatch, so the encoding does not rely on
color alone. Figure 2.2 should reuse these two tones for the baseline versus change distinction.

Source figure: `manuscript_formatting/figures/figure_embedding_configs/figure_2_3_embedding_configs.png`
(and `.pdf`).
