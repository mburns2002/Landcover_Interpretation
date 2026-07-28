#!/usr/bin/env python3
"""Follow-ups to the adjudication-effect analysis (Chapter 3):
  1. ten-class contested share with and without Other (13), excluded pairwise like Unknown
  2. top contested class pairs (ten-class), to compare against the D1 disagreement ranking
  3. for Insect/Disease and Beaver: what the non-selected interpreter(s) assigned instead

Run: python scripts/adjudication_effect_followups.py
Requires: numpy, pandas, rasterio (imports helpers from adjudication_effect)
"""
import itertools
import os
import sys
from collections import defaultdict

import numpy as np
import pandas as pd

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import adjudication_effect as ae

ROOT, OUT, NAMES = ae.ROOT, ae.OUT, ae.NAMES

cells = ae.load_cells()
multiply = {k: v for k, v in cells.items() if len(v) >= 2}
truth = pd.read_csv(os.path.join(ROOT, "exports/truth_selections.csv"), dtype=str, keep_default_na=False)
choice = {(str(r.grid_id).zfill(5), str(r.sample_id)): r.reviewer.strip().lower() for r in truth.itertuples()}

valid_tot = contested_tot = 0
valid_noO = contested_noO = contested_with_other = 0
pair_ct = defaultdict(int)
pair_events_total = 0
alt = {50: defaultdict(int), 62: defaultdict(int)}       # adjudicated class -> {alternative class: count}
alt_total = {50: 0, 62: 0}

for key, revs in multiply.items():
    names_arms, stack, valid = ae.cell_arrays(revs)      # valid = pairwise non-Unknown
    k = len(names_arms)
    adj = stack[names_arms.index(choice[(key[0], key[1])])]
    any_other = (stack == 13).any(0)
    agree = np.ones(valid.shape, bool)
    for i in range(1, k):
        agree &= stack[i] == stack[0]
    contested = valid & ~agree

    # (1) with / without Other
    valid_tot += int(valid.sum()); contested_tot += int(contested.sum())
    valid_noO += int((valid & ~any_other).sum())
    contested_noO += int((contested & ~any_other).sum())
    contested_with_other += int((contested & any_other).sum())

    # (2) pairwise off-diagonal class-pair tally (non-Unknown), vectorized
    for i, j in itertools.combinations(range(k), 2):
        ai, aj = stack[i], stack[j]
        d = valid & (ai != aj)
        lo = np.minimum(ai[d], aj[d]).astype(np.int64)
        hi = np.maximum(ai[d], aj[d]).astype(np.int64)
        enc, cnt = np.unique(lo * 1000 + hi, return_counts=True)
        for e, c in zip(enc, cnt):
            pair_ct[(int(e // 1000), int(e % 1000))] += int(c)
        pair_events_total += int(d.sum())

    # (3) alternative class assigned by the non-selected arm(s), for Insect/Disease and Beaver
    for adjc in (50, 62):
        m = valid & (adj == adjc) & contested
        for i in range(k):
            if stack[i] is adj:                          # skip the chosen arm
                continue
            if np.shares_memory(stack[i], adj):
                continue
            other = stack[i]
            sel = m & (other != adjc)
            v, c = np.unique(other[sel], return_counts=True)
            for vv, cc in zip(v, c):
                alt[adjc][int(vv)] += int(cc)
            alt_total[adjc] += int(sel.sum())

# ---- 1. Other-churn report ----
print("=" * 78 + "\n[1] TEN-CLASS CONTESTED SHARE, WITH vs WITHOUT Other (13)\n" + "=" * 78)
print(f"  WITH Other:    contested {contested_tot:,} / valid {valid_tot:,} = "
      f"{100 * contested_tot / valid_tot:.4f}%")
print(f"  WITHOUT Other: contested {contested_noO:,} / valid {valid_noO:,} = "
      f"{100 * contested_noO / valid_noO:.4f}%   (Other dropped pairwise, like Unknown)")
print(f"  contested pixels involving Other (>=1 arm Other): {contested_with_other:,}"
      f"  ({100 * contested_with_other / contested_tot:.2f}% of the ten-class contested pixels)")
pd.DataFrame([
    dict(basis="with_other", contested=contested_tot, valid=valid_tot,
         percentage=round(100 * contested_tot / valid_tot, 4)),
    dict(basis="without_other", contested=contested_noO, valid=valid_noO,
         percentage=round(100 * contested_noO / valid_noO, 4)),
    dict(basis="contested_involving_other", contested=contested_with_other, valid=contested_tot,
         percentage=round(100 * contested_with_other / contested_tot, 4)),
]).to_csv(os.path.join(OUT, "other_churn_ten_class.csv"), index=False)

# ---- 2. top contested class pairs vs D1 ----
def pname(c):
    return NAMES.get(c, str(c))

rows = sorted(pair_ct.items(), key=lambda kv: -kv[1])
pr = pd.DataFrame([dict(**{"class_a": pname(a), "class_b": pname(b)}, pixels=n,
                        pct_of_pair_events=round(100 * n / pair_events_total, 3))
                   for (a, b), n in rows])
pr.to_csv(os.path.join(OUT, "contested_pairs_ten_class.csv"), index=False)
print("\n" + "=" * 78 + f"\n[2] TOP 15 CONTESTED CLASS PAIRS (ten-class; total pair-events {pair_events_total:,})\n" + "=" * 78)
print(pr.head(15).to_string(index=False))
d1 = os.path.join(ROOT, "reports/interpreter_agreement/class_disagreement_ranked.csv")
if os.path.exists(d1):
    print("\n  D1 (agreement analysis, class_disagreement_ranked.csv) top 5 for comparison:")
    print(pd.read_csv(d1).head(5).to_string(index=False))

# ---- 3. alternative class for Insect/Disease and Beaver ----
print("\n" + "=" * 78 + "\n[3] WHAT THE NON-SELECTED INTERPRETER(S) ASSIGNED INSTEAD (ten-class)\n" + "=" * 78)
rows3 = []
for adjc, nm in ((50, "Insect/Disease"), (62, "Beaver")):
    tot = alt_total[adjc]
    print(f"\n  adjudicated = {nm}: {tot:,} (pixel, other-arm) events among its contested pixels")
    for alt_c, n in sorted(alt[adjc].items(), key=lambda kv: -kv[1]):
        pct = 100 * n / tot if tot else 0
        print(f"      {pname(alt_c):16} {n:>8,}  {pct:6.2f}%")
        rows3.append(dict(adjudicated=nm, alternative_class=pname(alt_c), events=n,
                          denominator=tot, percentage=round(pct, 3)))
pd.DataFrame(rows3).to_csv(os.path.join(OUT, "alternative_class_insect_beaver.csv"), index=False)

print(f"\nwrote -> {OUT}/  (other_churn_ten_class, contested_pairs_ten_class, alternative_class_insect_beaver)")
