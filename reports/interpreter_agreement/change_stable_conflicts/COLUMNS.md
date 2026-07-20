# change_stable_conflicts data dictionary

These files flag pixels where one interpreter called a pixel an attributed change class and the
other called it a stable class (in either direction). Change classes are Harvest (20), Development (30), Insect/Disease (50), Beaver (62). Stable classes are
Urban (0), Agriculture (1), Grass/Shrub (2), Forest (3), Water (4), Wetland (5), Other (13). Unknown (10) is unattributed disturbance and is neither stable nor an attributed change
class, so Unknown-vs-stable is reported separately in `summary.txt`, not counted as a conflict;
Fire (40) has zero pixels. See `summary.txt` for the headline totals and `ordered_pairs.csv` for
the directed and symmetrized class-pair totals.

## change_stable_pixels_long.csv  (379 rows)

One row per (cell, reviewer pair, directed class pair). It depicts, for each double-interpreted
cell that has any change/stable conflict, how many pixels each ordered A-class -> B-class conflict
covers, where exactly one of the two classes is stable and the other is an attributed change
class. A cell with several conflicting class pairs gets several rows. Reviewer A/B ordering is
alphabetical and therefore arbitrary, so a single directed pair carries no meaning on its own; the
`stable_class` and `change_class` columns give the reviewer-order-independent view, and the
symmetrized totals are in `ordered_pairs.csv`.

| column | meaning |
|---|---|
| grid | grid cell id (the physical cell) |
| sample | interpretation sample index for that cell |
| target | interpreted target year |
| revA | reviewer A (alphabetically first of the pair) |
| revB | reviewer B (alphabetically second) |
| A_class | the class reviewer A assigned to these pixels (stable or change) |
| B_class | the class reviewer B assigned to the same pixels (the other kind) |
| class_pair | `A_class->B_class`, the directed conflict label |
| stable_class | the stable class of the pair, regardless of which reviewer assigned it |
| change_class | the attributed change class of the pair, regardless of reviewer |
| pixels | number of conflict pixels of this class pair in this cell |
| area_ha | pixels x 0.01 ha (one 10 m pixel = 0.01 ha) |

## change_stable_patches.csv  (16447 rows)

One row per connected-component patch of the change/stable conflict mask, labeled per cell with
8-connectivity. It depicts the spatial grouping of the conflicts: whether they are a handful of
large blobs or many scattered pixels. A patch is a spatially contiguous run of conflict pixels
within one cell and reviewer pair, so patch counts and areas distinguish "a few large disagreed
zones" from "boundary or salt-and-pepper speckle."

| column | meaning |
|---|---|
| grid | grid cell id the patch is in |
| revA | reviewer A (alphabetically first) |
| revB | reviewer B (alphabetically second) |
| patch_id | patch label within this cell and reviewer pair (1-based) |
| pixels | number of conflict pixels in the patch |
| area_ha | pixels x 0.01 ha |
