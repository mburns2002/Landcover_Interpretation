#!/usr/bin/env python3
"""Fetch the per-cell temporal-transferability prediction rasters from Google Drive.

The GEE export wrote one folder per NAIP bracket at the Drive root, named
`transferability_10class_percell/<bracket>`. Drive renders the export path slash as a fullwidth
slash (U+FF0F), so each bracket is a separate top-level folder. Each holds 36 rasters named
`pred_<bracket>_cell<id>.tif`, 5 bands (band1=v2 ... band5=v6), values 1 to 10.

This copies them into `data/raw/transfer_predictions/<bracket>/` (git-ignored) via the authenticated
rclone remote. Run rclone config first if the `gdrive:` remote is not set up.

Usage: python scripts/fetch_transfer_predictions.py [--remote gdrive]
"""

import argparse
import os
import subprocess

BRACKETS = ["2017_2019", "2018_2020", "2019_2021", "2020_2022", "2021_2023"]
DRIVE_PREFIX = "transferability_10class_percell／"   # fullwidth slash from the export path
DEST = "data/raw/transfer_predictions"


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--remote", default="gdrive", help="rclone remote name (default: gdrive)")
    args = ap.parse_args()
    for bracket in BRACKETS:
        src = f"{args.remote}:{DRIVE_PREFIX}{bracket}"
        dst = os.path.join(DEST, bracket)
        os.makedirs(dst, exist_ok=True)
        print(f"copying {src} -> {dst}")
        subprocess.run(["rclone", "copy", src, dst, "--transfers", "8"], check=True)
    for bracket in BRACKETS:
        n = len([f for f in os.listdir(os.path.join(DEST, bracket)) if f.endswith(".tif")])
        print(f"  {bracket}: {n} rasters")


if __name__ == "__main__":
    main()
