#!/usr/bin/env python3
"""Fetch the per-cell SPECTRAL transferability prediction rasters from Google Drive.

The GEE export wrote one folder per NAIP bracket at the Drive root, named
`spectral_transferability_10class_percell/<bracket>`. Drive renders the export path slash as a
fullwidth slash (U+FF0F), so each bracket is a separate top-level folder. Some brackets have
duplicate folders (re-export runs), so we copy every folder whose name matches the bracket and
let rclone merge by filename. Each file is `pred_specall_<bracket>_cell<id>.tif`, single band,
values 1 to 10.

This copies them into `data/raw/spectral_transferability_10class_percell/<bracket>/` (git-ignored)
via the authenticated rclone remote. Run rclone config first if the `gdrive:` remote is not set up.

Usage: python scripts/fetch_spectral_predictions.py [--remote gdrive]
"""

import argparse
import os
import re
import subprocess

BRACKETS = ["2017_2019", "2018_2020", "2019_2021", "2020_2022", "2021_2023"]
DRIVE_PREFIX = "spectral_transferability_10class_percell／"   # fullwidth slash from the export path
DEST = "data/raw/spectral_transferability_10class_percell"


def list_source_dirs(remote):
    # every top-level dir on the remote, so we can find duplicate bracket folders by exact name
    out = subprocess.run(["rclone", "lsf", f"{remote}:", "--dirs-only"],
                         capture_output=True, text=True, check=True).stdout
    return [d.rstrip("/") for d in out.splitlines()]


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--remote", default="gdrive", help="rclone remote name (default: gdrive)")
    args = ap.parse_args()

    all_dirs = list_source_dirs(args.remote)
    for bracket in BRACKETS:
        want = f"{DRIVE_PREFIX}{bracket}"
        matches = [d for d in all_dirs if d == want]
        dst = os.path.join(DEST, bracket)
        os.makedirs(dst, exist_ok=True)
        if not matches:
            print(f"MISSING: no Drive folder named {want}")
            continue
        # copy each duplicate folder into the same dest; rclone merges by filename
        for i, _ in enumerate(matches):
            src = f"{args.remote}:{want}"
            print(f"copying {src}  (match {i + 1}/{len(matches)}) -> {dst}")
            subprocess.run(["rclone", "copy", src, dst, "--transfers", "8"], check=True)

    # verify: recursive glob on the filename pattern, do not trust the folder tree
    print("\nverification (recursive glob on pred_specall_*.tif):")
    rx = re.compile(r"pred_specall_(\d{4}_\d{4})_cell(\d+)\.tif$")
    seen = {}
    for root, _, files in os.walk(DEST):
        for f in files:
            m = rx.search(f)
            if m:
                seen.setdefault(m.group(1), set()).add(m.group(2).zfill(5))
    total = 0
    for bracket in BRACKETS:
        n = len(seen.get(bracket, set()))
        total += n
        flag = "" if n >= 30 else "  <-- SHORT of ~36"
        print(f"  {bracket}: {n} unique cells{flag}")
    print(f"  total unique cells: {total}")


if __name__ == "__main__":
    main()
