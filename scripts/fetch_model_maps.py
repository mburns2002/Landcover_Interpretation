#!/usr/bin/env python3
"""Pull the AlphaEarth Foundations classified model maps from Google Drive.

These are the 10-class land cover maps exported from Google Earth Engine
(``classified_maps_10class_v2`` ... ``_v6``). GEE splits large exports into
multiple GeoTIFF tiles per version; this script downloads every tile into
``data/raw/model_maps/<version_folder>/`` so they can later be mosaicked and
compared against our interpreted (RF) results.

Uses authenticated rclone (see setup below); safe to re-run (skips files
already present, verified by size).

One-time setup (creates a reusable remote named ``gdrive``):
    brew install rclone            # or https://rclone.org/downloads/
    rclone config create gdrive drive scope drive.readonly
    # ^ browser sign-in; if interrupted finish with: rclone config reconnect gdrive:

Usage:
    python scripts/fetch_model_maps.py                    # all versions (v2-v6)
    python scripts/fetch_model_maps.py --versions v6      # just one
    python scripts/fetch_model_maps.py --versions v2 v3   # a subset
    python scripts/fetch_model_maps.py --list             # show sizes, download nothing
"""

import argparse
import json
import os
import subprocess
import sys

REMOTE = "gdrive"
FOLDER_TEMPLATE = "classified_maps_10class_{v}"
DEFAULT_VERSIONS = ["v2", "v3", "v4", "v5", "v6"]
DEST_ROOT = "data/raw/model_maps"


def run(cmd, **kw):
    return subprocess.run(cmd, capture_output=True, text=True, **kw)


def ensure_rclone(remote):
    if run(["which", "rclone"]).returncode != 0:
        sys.exit("rclone not found. install it (brew install rclone); see setup in this file's docstring.")
    if f"{remote}:" not in run(["rclone", "listremotes"]).stdout:
        sys.exit(f"rclone remote '{remote}:' not configured. see one-time setup in this file's docstring.")


def folder_listing(remote, folder):
    """Return list of {Name, Path, Size} for files in a Drive folder (recursive)."""
    r = run(["rclone", "lsjson", f"{remote}:{folder}", "-R", "--files-only"])
    if r.returncode != 0:
        return None
    return json.loads(r.stdout)


def human(nbytes):
    for unit in ("B", "KB", "MB", "GB", "TB"):
        if nbytes < 1024:
            return f"{nbytes:.1f} {unit}"
        nbytes /= 1024
    return f"{nbytes:.1f} PB"


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--versions", nargs="+", default=DEFAULT_VERSIONS,
                    help="version tags to fetch (default: v2 v3 v4 v5 v6)")
    ap.add_argument("--remote", default=REMOTE, help="rclone remote name (default: gdrive)")
    ap.add_argument("--dest", default=DEST_ROOT, help="destination root (default: data/raw/model_maps)")
    ap.add_argument("--list", action="store_true", help="show folder sizes and exit (no download)")
    args = ap.parse_args()

    ensure_rclone(args.remote)
    folders = [FOLDER_TEMPLATE.format(v=v) for v in args.versions]

    # summarize what we're about to fetch
    grand_files = grand_bytes = 0
    listings = {}
    print("planned download:")
    for folder in folders:
        entries = folder_listing(args.remote, folder)
        if entries is None:
            print(f"  {folder}: NOT FOUND (skipping)")
            continue
        listings[folder] = entries
        nbytes = sum(e["Size"] for e in entries)
        grand_files += len(entries)
        grand_bytes += nbytes
        print(f"  {folder}: {len(entries)} file(s), {human(nbytes)}")
    print(f"  TOTAL: {grand_files} file(s), {human(grand_bytes)}\n")

    if args.list:
        return
    if not listings:
        sys.exit("nothing to download.")

    # download each folder
    for folder, entries in listings.items():
        dest = os.path.join(args.dest, folder)
        os.makedirs(dest, exist_ok=True)
        print(f"==> {folder} -> {dest}")
        subprocess.run([
            "rclone", "copy", f"{args.remote}:{folder}", dest,
            "--transfers", "4", "--stats-one-line", "--stats", "15s",
        ])

    # verify
    print("\n" + "=" * 50)
    ok = True
    for folder, entries in listings.items():
        dest = os.path.join(args.dest, folder)
        for e in entries:
            p = os.path.join(dest, e["Path"])
            if not (os.path.exists(p) and os.path.getsize(p) == e["Size"]):
                print(f"  MISSING/SIZE MISMATCH: {folder}/{e['Path']}")
                ok = False
    print("all files present and sizes match." if ok else "some files missing (re-run to retry).")
    sys.exit(0 if ok else 1)


if __name__ == "__main__":
    main()
