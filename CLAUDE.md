# Project instructions

## Figures (matplotlib schematics and diagrams)

Text must NEVER overlap box borders, other boxes, or arrows. This is a hard requirement, not a
preference. Always verify a figure by reading the rendered PNG before committing it.

To guarantee it:

1. **Pin the axes to fill the figure so 1 data unit = 1 inch.** If you place boxes/arrows in data
   coordinates (limits set to the intended inches, e.g. 0..12 x 0..5) but set fonts in points, call
   `ax.set_position([0, 0, 1, 1])` (or `fig.subplots_adjust(0, 0, 1, 1)`) after `set_xlim`/`set_ylim`.
   Otherwise matplotlib's default axes margins inset the axes to ~78% of the canvas, shrinking the
   data-unit boxes while the point-sized fonts stay absolute, so labels render ~30% too large for their
   boxes and spill over the borders.

2. **Size every box to its text with real margin.** Measure text with the renderer
   (`text.get_window_extent(fig.canvas.get_renderer()).width / fig.dpi`) and confirm each line is
   narrower than the box interior (box width minus padding) and the stacked line block is shorter than
   the box interior height. If it does not fit, grow the box or wrap the text. Do not let a label touch
   or cross a border. Prefer a fit-check that prints a WARN when any line exceeds its box.

3. **Keep annotations clear of arrows and boxes.** Place a fork/branch annotation only in a gap that is
   wider than the measured text; never let it cross an arrow line or a box edge.

Other standing figure conventions (also in auto-memory): presentation figures under
`presentation/figures/` export PNG only at 300 dpi, never PDF (Google Slides deck); manuscript figures
under `manuscript_formatting/` keep their PDFs for Overleaf. Figure titles are Title Case.
