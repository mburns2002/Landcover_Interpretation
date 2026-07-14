#!/usr/bin/env python3
"""Pull Random Forest classified rasters from a shared Google Drive folder.

Lists every file in the Drive folder, keeps only the classified maps
(filenames starting with ``rf_class``), and downloads them into
``data/raw/rf_class_maps/`` while preserving the per-grid subfolder layout.

The script is safe to re-run: files already present on disk are skipped, so if
Google rate-limits you partway through, just run it again to pick up the rest.

Usage:
    python scripts/fetch_rf_class_maps.py
    python scripts/fetch_rf_class_maps.py --url <drive_folder_url>
    python scripts/fetch_rf_class_maps.py --prefix rf_class --dest data/raw/rf_class_maps

Requires:
    pip install gdown
"""

import argparse
import json
import os
import subprocess
import sys
import time

# default shared folder (SENTINEL_ALPHAEARTH_outputs)
DEFAULT_URL = "https://drive.google.com/drive/folders/1Wleu8hJ4pwc32A_UkFXwzcHs4qYqYTfJ"


def ensure_gdown():
    try:
        import gdown  # noqa: F401
    except ImportError:
        print("gdown not found. install it with:  pip install gdown", file=sys.stderr)
        sys.exit(1)


def list_folder(url):
    """Return the folder listing as a list of {url, path} dicts via `gdown --json`."""
    print(f"listing folder: {url}")
    result = subprocess.run(
        ["gdown", "--folder", "--json", url],
        capture_output=True,
        text=True,
    )
    if result.returncode != 0 or not result.stdout.strip():
        print("failed to list folder. stderr:", file=sys.stderr)
        print(result.stderr, file=sys.stderr)
        sys.exit(1)
    return json.loads(result.stdout)


def download_one(url, out, retries=4):
    """Download a single file with exponential backoff. Returns True on success."""
    import gdown

    for attempt in range(1, retries + 1):
        try:
            gdown.download(url, out, quiet=True)
            if os.path.exists(out) and os.path.getsize(out) > 0:
                return True
        except Exception as exc:  # noqa: BLE001 - report and retry
            print(f"    attempt {attempt} error: {exc}")
        # remove any empty/partial file before retrying
        if os.path.exists(out) and os.path.getsize(out) == 0:
            os.remove(out)
        if attempt < retries:
            wait = 2 ** attempt  # 2, 4, 8, ... seconds
            print(f"    retry in {wait}s (rate limit?)")
            time.sleep(wait)
    return False


def main():
    parser = argparse.ArgumentParser(description=__doc__,
                                     formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--url", default=DEFAULT_URL, help="Google Drive folder URL")
    parser.add_argument("--prefix", default="rf_class",
                        help="only download files whose name starts with this (default: rf_class)")
    parser.add_argument("--dest", default="data/raw/rf_class_maps",
                        help="destination directory (default: data/raw/rf_class_maps)")
    parser.add_argument("--pause", type=float, default=0.5,
                        help="seconds to pause between downloads to avoid rate limits")
    args = parser.parse_args()

    ensure_gdown()

    listing = list_folder(args.url)
    targets = [d for d in listing
               if os.path.basename(d["path"]).startswith(args.prefix)]

    print(f"total files in folder: {len(listing)}")
    print(f"matching '{args.prefix}*': {len(targets)}")
    os.makedirs(args.dest, exist_ok=True)

    ok = skipped = failed = 0
    failures = []
    for i, d in enumerate(targets, 1):
        out = os.path.join(args.dest, d["path"])
        os.makedirs(os.path.dirname(out), exist_ok=True)

        if os.path.exists(out) and os.path.getsize(out) > 0:
            skipped += 1
            continue

        print(f"[{i}/{len(targets)}] {os.path.basename(d['path'])}")
        if download_one(d["url"], out):
            ok += 1
        else:
            failed += 1
            failures.append(d["path"])
        time.sleep(args.pause)

    print("\n" + "=" * 50)
    print(f"downloaded: {ok}   already present: {skipped}   failed: {failed}")
    if failures:
        print("\nfailed files (re-run the script to retry these):")
        for f in failures:
            print(" ", f)
        sys.exit(1)


if __name__ == "__main__":
    main()


