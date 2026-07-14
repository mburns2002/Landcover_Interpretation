#!/usr/bin/env python3
"""Pull Random Forest classified rasters from Google Drive using rclone (authenticated).

This is the reliable path when the public share link hits Google's download quota
("too many accesses"). It authenticates with your Google account via an rclone
remote, so it is not subject to the anonymous per-link quota.

What it does:
  1. bulk-copies every ``rf_class*.tif`` from the Drive folder into
     ``data/raw/rf_class_maps/`` (rclone skips files already present)
  2. reconciles against a full recursive listing and grabs, by file ID, any files
     that rclone's directory walk missed because Google Drive stored them under
     DUPLICATE-NAMED folders (rclone silently ignores duplicate directories)

One-time setup (creates a reusable remote named ``gdrive``):
    brew install rclone            # or: https://rclone.org/downloads/
    rclone config create gdrive drive scope drive.readonly
    # ^ opens a browser: sign in with the Google account that has the folder,
    #   click Allow, wait for "Success!". If interrupted, finish with:
    #   rclone config reconnect gdrive:

Usage:
    python scripts/fetch_rf_class_maps_rclone.py
    python scripts/fetch_rf_class_maps_rclone.py --remote gdrive --folder-id <id>
    python scripts/fetch_rf_class_maps_rclone.py --prefix rf_class --dest data/raw/rf_class_maps
"""

import argparse
import json
import os
import subprocess
import sys

# shared folder (SENTINEL_ALPHAEARTH_outputs) and the remote created during setup
DEFAULT_FOLDER_ID = "1Wleu8hJ4pwc32A_UkFXwzcHs4qYqYTfJ"
DEFAULT_REMOTE = "gdrive"


def run(cmd):
    """Run a command, returning (returncode, stdout, stderr)."""
    p = subprocess.run(cmd, capture_output=True, text=True)
    return p.returncode, p.stdout, p.stderr


def ensure_rclone(remote):
    if not subprocess.run(["which", "rclone"], capture_output=True).returncode == 0:
        sys.exit("rclone not found. install it (brew install rclone) and see setup in this file's docstring.")
    rc, out, _ = run(["rclone", "listremotes"])
    if f"{remote}:" not in out:
        sys.exit(f"rclone remote '{remote}:' not configured. see one-time setup in this file's docstring.")


def bulk_copy(remote, folder_id, prefix, dest):
    """rclone copy of every prefix*.tif; skips files already on disk."""
    print(f"bulk-copying {prefix}*.tif from {remote}: (folder {folder_id}) ...")
    cmd = [
        "rclone", "copy", f"{remote}:", dest,
        "--drive-root-folder-id", folder_id,
        "--include", f"**{prefix}*.tif",
        "--transfers", "8",
        "--stats-one-line", "--stats", "10s",
    ]
    # stream progress straight to the terminal
    subprocess.run(cmd)


def list_all_ids(remote, folder_id, prefix):
    """Recursive listing with file IDs. Returns {basename: (id, relpath)}.

    Uses rclone lsjson -R so we can recover files hidden inside duplicate-named
    directories that a normal copy walk skips.
    """
    rc, out, err = run([
        "rclone", "lsjson", f"{remote}:", "-R", "--files-only",
        "--drive-root-folder-id", folder_id,
    ])
    if rc != 0:
        sys.exit(f"rclone lsjson failed:\n{err}")
    entries = json.loads(out)
    result = {}
    for e in entries:
        name = e.get("Name", "")
        if name.startswith(prefix) and name.endswith(".tif"):
            # keep the first ID seen for a given basename (duplicates are identical files)
            result.setdefault(name, (e.get("ID"), e.get("Path")))
    return result


def files_on_disk(dest, prefix):
    found = set()
    for root, _, files in os.walk(dest):
        for f in files:
            if f.startswith(prefix) and f.endswith(".tif"):
                found.add(f)
    return found


def fetch_by_id(remote, file_id, out_path):
    os.makedirs(os.path.dirname(out_path), exist_ok=True)
    rc, _, err = run(["rclone", "backend", "copyid", f"{remote}:", file_id, out_path])
    ok = rc == 0 and os.path.exists(out_path) and os.path.getsize(out_path) > 0
    if not ok:
        print(f"    copyid failed for {os.path.basename(out_path)}: {err.strip()}")
    return ok


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--remote", default=DEFAULT_REMOTE, help="rclone remote name (default: gdrive)")
    ap.add_argument("--folder-id", default=DEFAULT_FOLDER_ID, help="Drive folder ID")
    ap.add_argument("--prefix", default="rf_class", help="filename prefix to fetch (default: rf_class)")
    ap.add_argument("--dest", default="data/raw/rf_class_maps", help="destination directory")
    args = ap.parse_args()

    ensure_rclone(args.remote)
    os.makedirs(args.dest, exist_ok=True)

    # 1. bulk copy
    bulk_copy(args.remote, args.folder_id, args.prefix, args.dest)

    # 2. reconcile against the full listing and recover anything missed
    print("\nreconciling against full recursive listing ...")
    expected = list_all_ids(args.remote, args.folder_id, args.prefix)
    on_disk = files_on_disk(args.dest, args.prefix)
    missing = {name: meta for name, meta in expected.items() if name not in on_disk}

    print(f"expected unique {args.prefix}*.tif: {len(expected)}")
    print(f"on disk:                           {len(on_disk)}")
    print(f"missing (fetching by file ID):     {len(missing)}")

    recovered = 0
    for name, (file_id, relpath) in sorted(missing.items()):
        out_path = os.path.join(args.dest, relpath)
        print(f"  copyid {name}")
        if fetch_by_id(args.remote, file_id, out_path):
            recovered += 1

    final = len(files_on_disk(args.dest, args.prefix))
    print("\n" + "=" * 50)
    print(f"recovered by ID: {recovered}   total on disk: {final} / {len(expected)}")
    if final < len(expected):
        sys.exit(1)


if __name__ == "__main__":
    main()
