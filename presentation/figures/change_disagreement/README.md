# change_disagreement — where interpreters disagreed about change (deck figures)

The dominant form of change-class disagreement is change-vs-stable: one interpreter called a pixel
change, the other stable. That is ~56% of all change-labeled pixels (1,103 ha across the 72
double-interpreted cells). Both interpreters calling change but disagreeing on the type is tiny by
comparison (~1.3%, 26 ha). Data: `reports/interpreter_agreement/change_stable_conflicts/`.

- `change_disagreement_summary.png` — the top contested change-vs-stable class pairs (symmetrized,
  hectares), colored by the change class in each pair. Forest-vs-Insect/Disease and Forest-vs-Harvest
  dominate.
- `change_disagreement_map_rank01..04_*.png` — the largest contested cells: the two reviewers'
  interpreted maps side by side, with the disagreed area (one called the stable class, the other the
  paired change class) outlined in black. Deck (Spectral) versions of the report examples.

Regenerate:
  `python presentation/scripts/pres_change_disagreement.py`       (summary)
  `python presentation/scripts/pres_change_disagreement_maps.py`  (maps)

Related (not deck-styled): `reports/interpreter_agreement/change_stable_conflicts/examples/` and
`.../change_change_conflicts/` (both-called-change, disagreed on type).
