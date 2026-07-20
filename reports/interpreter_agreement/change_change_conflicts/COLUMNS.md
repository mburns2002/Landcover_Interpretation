# change_change_conflicts data dictionary

These files flag pixels where two interpreters both called a pixel change but disagreed on which
change type. Change classes are Harvest (20), Development (30), Insect/Disease (50), Beaver (62). Unknown (10) is excluded, so an Unknown-vs-change pixel
is not a conflict; Fire (40) has zero pixels. See `summary.txt` for the headline totals and
`ordered_pairs.csv` for the directed and symmetrized class-pair totals.

## change_change_pixels_long.csv  (25 rows)

One row per (cell, reviewer pair, directed change-class pair). It depicts, for each double-
interpreted cell that has any conflict, how many pixels each ordered A-class -> B-class conflict
covers. A cell with two conflicting class pairs gets two rows. Reviewer A/B ordering is
alphabetical and therefore arbitrary, so a single directed pair carries no meaning on its own;
use the symmetrized totals in `ordered_pairs.csv` for reviewer-order-independent counts.

| column | meaning |
|---|---|
| grid | grid cell id (the physical cell) |
| sample | interpretation sample index for that cell |
| target | interpreted target year |
| revA | reviewer A (alphabetically first of the pair) |
| revB | reviewer B (alphabetically second) |
| A_class | the change class reviewer A assigned to these pixels |
| B_class | the change class reviewer B assigned to the same pixels |
| class_pair | `A_class->B_class`, the directed conflict label |
| pixels | number of conflict pixels of this class pair in this cell |
| area_ha | pixels x 0.01 ha (one 10 m pixel = 0.01 ha) |

## change_change_patches.csv  (748 rows)

One row per connected-component patch of the change/change conflict mask, labeled per cell with
8-connectivity. It depicts the spatial grouping of the conflicts: whether they are a handful of
large blobs or many scattered single pixels. A patch is a spatially contiguous run of conflict
pixels within one cell and reviewer pair, so patch counts and areas are what distinguish "a few
large disagreements" from "salt-and-pepper speckle."

| column | meaning |
|---|---|
| grid | grid cell id the patch is in |
| revA | reviewer A (alphabetically first) |
| revB | reviewer B (alphabetically second) |
| patch_id | patch label within this cell and reviewer pair (1-based) |
| pixels | number of conflict pixels in the patch |
| area_ha | pixels x 0.01 ha |
