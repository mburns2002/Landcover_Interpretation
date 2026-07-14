#!/usr/bin/env python3
"""Browse all inter-interpreter pair figures in VSCode.

Two ways to view the per-pair comparison figures produced by
``compare_interpreters.py`` (``outputs/interpreter_agreement/<grid>_<a>_vs_<b>.png``):

  contact sheet (default) -- stacks the pair figures into a few paginated overview
    PNGs (``montage_page_*.png``), sorted lowest-agreement first. Open a page in
    VSCode and scroll; great for a review pass over everything at once.

  interactive (--interactive) -- opens one matplotlib window; page with the Left/
    Right arrow keys (or 'q' to quit). Needs a GUI session (works on macOS).

Options let you view only the flagged (low-agreement) pairs.

Usage:
    python scripts/pairs_contact_sheet.py                 # all pairs -> montage pages
    python scripts/pairs_contact_sheet.py --per-page 8
    python scripts/pairs_contact_sheet.py --flagged-below 0.70
    python scripts/pairs_contact_sheet.py --interactive   # arrow-key browser

Requires: pillow, pandas (matplotlib only for --interactive)
"""

import argparse
import glob
import os
import re

import pandas as pd
from PIL import Image

DIR = "outputs/interpreter_agreement"
METRICS = os.path.join(DIR, "per_pair_metrics.csv")
PNG_RE = re.compile(r"(\d+)_([a-z]+)_vs_([a-z]+)\.png$", re.I)


def ordered_pairs(flagged_below=None):
    """Return [(png_path, agreement)] sorted by agreement ascending (worst first)."""
    pngs = [p for p in glob.glob(os.path.join(DIR, "*_vs_*.png")) if PNG_RE.search(os.path.basename(p))]
    agree = {}
    if os.path.exists(METRICS):
        m = pd.read_csv(METRICS)
        for r in m.itertuples():
            agree[(int(r.grid), str(r.revA), str(r.revB))] = float(r.overall_agreement)
    out = []
    for p in pngs:
        g, a, b = PNG_RE.search(os.path.basename(p)).groups()
        val = agree.get((int(g), a, b), 1.0)
        if flagged_below is None or val < flagged_below:
            out.append((p, val))
    return sorted(out, key=lambda z: z[1])


def build_contact_sheets(pairs, per_page, width, prefix="montage"):
    if not pairs:
        raise SystemExit("no pair figures found; run scripts/compare_interpreters.py first.")
    # clear any stale pages from a previous run of this prefix
    for old in glob.glob(os.path.join(DIR, f"{prefix}_page_*.png")):
        os.remove(old)
    pages = [pairs[i:i + per_page] for i in range(0, len(pairs), per_page)]
    written = []
    for pi, page in enumerate(pages, 1):
        imgs = []
        for path, _ in page:
            im = Image.open(path).convert("RGB")
            scale = width / im.width
            imgs.append(im.resize((width, int(im.height * scale))))
        gap = 12
        H = sum(im.height for im in imgs) + gap * (len(imgs) + 1)
        sheet = Image.new("RGB", (width, H), "white")
        y = gap
        for im in imgs:
            sheet.paste(im, (0, y)); y += im.height + gap
        out = os.path.join(DIR, f"{prefix}_page_{pi:02d}.png")
        sheet.save(out)
        written.append(out)
        print(f"  {out}  ({len(page)} pairs)")
    return written


def interactive(pairs):
    import matplotlib.pyplot as plt
    import matplotlib.image as mpimg
    if not pairs:
        raise SystemExit("no pair figures found; run scripts/compare_interpreters.py first.")
    idx = {"i": 0}
    fig, ax = plt.subplots(figsize=(15, 6))
    plt.subplots_adjust(left=0, right=1, top=0.95, bottom=0)

    def show():
        ax.clear(); ax.axis("off")
        path, val = pairs[idx["i"]]
        ax.imshow(mpimg.imread(path))
        ax.set_title(f"[{idx['i']+1}/{len(pairs)}]  {os.path.basename(path)}  "
                     f"(agreement {val:.2f})   ← / → to page, q to quit", fontsize=9)
        fig.canvas.draw_idle()

    def on_key(e):
        if e.key in ("right", "down", " "):
            idx["i"] = (idx["i"] + 1) % len(pairs); show()
        elif e.key in ("left", "up"):
            idx["i"] = (idx["i"] - 1) % len(pairs); show()
        elif e.key == "q":
            plt.close(fig)

    fig.canvas.mpl_connect("key_press_event", on_key)
    show()
    plt.show()


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--per-page", type=int, default=6, help="pairs per contact-sheet page (default: 6)")
    ap.add_argument("--width", type=int, default=1100, help="page width in px (default: 1100)")
    ap.add_argument("--flagged-below", type=float, default=None,
                    help="only include pairs with agreement below this value")
    ap.add_argument("--interactive", action="store_true", help="arrow-key browser instead of contact sheets")
    args = ap.parse_args()

    pairs = ordered_pairs(args.flagged_below)
    scope = f"agreement < {args.flagged_below}" if args.flagged_below else "all pairs"
    print(f"{len(pairs)} pair figures ({scope}), sorted lowest-agreement first")

    if args.interactive:
        interactive(pairs)
    else:
        prefix = "montage_flagged" if args.flagged_below else "montage"
        build_contact_sheets(pairs, args.per_page, args.width, prefix=prefix)
        print(f"\nopen the {prefix}_page_*.png in {DIR}/ in VSCode and scroll.")


if __name__ == "__main__":
    main()
