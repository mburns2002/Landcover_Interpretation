# changeclass_f1_over_time

Five-class change-class F1 as a function of the temporal bracket (2017-2019 ... 2021-2023).

`changeclass_f1_over_time_5class.png` — small multiples, one panel per source (v2..v6, spec_all); the
four change classes (Harvest, Development, Beaver, Insect/Disease) are lines over the brackets. F1 is
recomputed on the common cell set by reusing pres_14's computation, so it matches Figure 14 / pres_18.
Harvest is the only change class detected at all; Beaver and Insect/Disease stay near the floor.

`changeclass_f1_over_time_5class_by_class.png` — the transpose: one panel per change class, the six
sources as lines colored by the model palette (v2..v6, spec_all brown). y-axes are scaled per panel
because the change classes differ by ~10x; shows which model leads each change type over time.

`changeclass_f1_over_time_5class.csv` — tidy values (source, bracket, class, f1); backs both figures.

Regenerate: `python scripts/changeclass_f1_over_time_5class.py`
