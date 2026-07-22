#!/usr/bin/env python3
"""Collect the Chapter 2 data figures from reports/ into manuscript_formatting/figures/ under their
thesis 2.x filenames. This is a copy-and-rename pass; the reports/ originals are left in place and
unaltered, and image bytes are preserved (shutil.copy2, no re-encoding).

Run: python scripts/collect_chapter2_figures.py
"""

import hashlib
import os
import shutil

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FIG = os.path.join(ROOT, "manuscript_formatting", "figures")

# straight copies: source (repo-relative) -> destination filename
STRAIGHT = {
    "reports/transfer_confusion_adjudicated/oa_by_bracket.png": "figure_2_4.png",
    "reports/per_cell_f1_5class/f1_violin_common.png": "figure_2_5.png",
    "reports/per_cell_change_f1/change_f1_violins.png": "figure_2_6.png",
    "reports/spatial_structure/with_spec_all/patch_size_ecdf_area_weighted.png": "figure_2_7.png",
    "reports/spatial_structure/with_spec_all/morans_i_by_source.png": "figure_2_8.png",
    "reports/sensitivity_changecap/change_classes_ua_pa_vs_cap.png": "figure_2_10.png",
}
# figure 2.11: representative source panel plus the full per-source set
REP_2_11 = "reports/model_vs_interpreter_5class/forest_5class_v4.png"
ALL_2_11 = ["forest_5class_v2.png", "forest_5class_v3.png", "forest_5class_v4.png",
            "forest_5class_v5.png", "forest_5class_v6.png", "forest_5class_spec_all.png"]
# figure 2.12: unresolved; copy the draft-referenced confusion candidates only
CAND_2_12 = [
    "reports/transfer_confusion_adjudicated/cm_v2_2018_2020.png",     # 10-class v2 per-bracket
    "reports/spectral_composite_classified_maps/cm_specall_pooled.png",  # 10-class spec_all pooled
    "reports/collapsed_5class_confusion/confusion_v2.png",           # 5-class v2 pooled
    "reports/spectral_composite_classified_maps/collapsed_5class/confusion_specall.png",  # 5-class spec_all pooled
]
# figure 2.9: use the already-regenerated current-pipeline crop, not the stale snapshot
REGEN_2_9 = os.path.join(FIG, "figure_2_9_speckle_crops.png")


def md5(path):
    return hashlib.md5(open(path, "rb").read()).hexdigest()


def copy(src_abs, dst_abs, log):
    shutil.copy2(src_abs, dst_abs)                          # preserves bytes and metadata
    ok = os.path.getsize(src_abs) == os.path.getsize(dst_abs) and md5(src_abs) == md5(dst_abs)
    log.append((os.path.relpath(src_abs, ROOT), os.path.relpath(dst_abs, ROOT), "byte-identical" if ok else "MISMATCH"))


def main():
    os.makedirs(FIG, exist_ok=True)
    log = []

    # straight copies
    for src, dst in STRAIGHT.items():
        copy(os.path.join(ROOT, src), os.path.join(FIG, dst), log)

    # 2.9: regenerated current-pipeline crop -> clean name (stale snapshot is not promoted)
    if os.path.exists(REGEN_2_9):
        copy(REGEN_2_9, os.path.join(FIG, "figure_2_9.png"), log)
        note_2_9 = "regenerated current-pipeline crop present; copied to figure_2_9.png"
    else:
        note_2_9 = "regenerated crop MISSING; stale snapshot NOT promoted; needs regeneration"

    # 2.11: representative panel plus the full per-source set
    copy(os.path.join(ROOT, REP_2_11), os.path.join(FIG, "figure_2_11.png"), log)
    sub_11 = os.path.join(FIG, "figure_2_11_all_sources")
    os.makedirs(sub_11, exist_ok=True)
    for name in ALL_2_11:
        copy(os.path.join(ROOT, "reports/model_vs_interpreter_5class", name),
             os.path.join(sub_11, name), log)

    # 2.12: candidates only, no final figure assembled
    sub_12 = os.path.join(FIG, "figure_2_12_candidates")
    os.makedirs(sub_12, exist_ok=True)
    for src in CAND_2_12:
        copy(os.path.join(ROOT, src), os.path.join(sub_12, os.path.basename(src)), log)

    print(f"copies made: {len(log)}")
    for s, d, status in log:
        print(f"  {status:14} {s} -> {d}")
    print("\n2.9:", note_2_9)

    # present / missing / flagged status per figure number
    def present(n):
        return os.path.exists(os.path.join(FIG, f"figure_2_{n}.png"))
    print("\nclean figure_2_x.png present:",
          ", ".join(f"2.{n}" for n in list(range(4, 12)) if present(n)))


if __name__ == "__main__":
    main()
