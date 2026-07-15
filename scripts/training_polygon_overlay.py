#!/usr/bin/env python3
"""Do the largest Grass/Shrub<->Wetland disagreements come from conflicting training
labels, or from both RF models extrapolating into unlabeled ground?

For each cell holding one of the 10 largest GS<->Wetland disagreement patches, this loads
both reviewers' interpreter training data (the `samples_generated` point sidecars: dense
pixels sampled from the drawn training polygons, with a `class`/`labelId` and `polygon_id`),
reprojects them to the raster CRS (EPSG:5070), reconstructs the disagreement patch as a
polygon, and asks per patch:

  (a) conflict     -- both reviewers have training in/near the zone but assign different
                      classes (e.g. reviewer A = Grass/Shrub, reviewer B = Wetland)
  (b) extrapolation -- neither reviewer placed training in the zone -> both RFs extrapolate
  (c) one-sided    -- only one reviewer trained in the zone

Quantifies, per patch: distance (m) from the patch to the nearest training point of each
reviewer, the training classes each reviewer placed inside the zone, and whether they
conflict where they co-occur. Renders both reviewers' training points over the side-by-side
maps with the patch outlined.

Outputs (reports/interpreter_agreement/geometry/):
  - gs_wetland_training_overlay.csv
  - gs_wetland_training_overlay.png

Requires: rasterio, numpy, pandas, geopandas, shapely, scipy, matplotlib
"""

import glob
import os
import sys

import numpy as np
import pandas as pd
import geopandas as gpd
import rasterio
from rasterio import features
from scipy import ndimage
from shapely.geometry import shape as shp_shape
from shapely.ops import unary_union

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import compare_interpreters as CI
import disagreement_geometry as DG

OUT = DG.OUT
GS, WET = 2, 5
NEAR_M = 20.0          # "in/near the zone" buffer (2 pixels)
COOCCUR = "labels co-occur in zone"
SAMP_DIR = "data/raw/samples_generated"


def samples_path(rev, grid, samp, tgt):
    hits = glob.glob(os.path.join(SAMP_DIR, f"CKIT_RF_{rev}_grid_s2_{grid}",
                                  f"samples_generated_reviewer_{rev}_grid_{grid}_sample_{samp}_*target_{tgt}_*.shp"))
    return hits[0] if hits else None


def load_pts(path, dst_crs):
    g = gpd.read_file(path)[["labelId", "class", "geometry"]]
    return g.to_crs(dst_crs)


def zone_stats(pts, patch_poly, near):
    """Points within `near` m of the patch, with class breakdown and nearest distance."""
    if pts is None or len(pts) == 0:
        return dict(n_in=0, dist_m=np.nan, classes={})
    d = pts.geometry.distance(patch_poly)                       # meters (EPSG:5070)
    inzone = pts[d <= near]
    cls = inzone["class"].value_counts().to_dict()
    return dict(n_in=len(inzone), dist_m=float(d.min()), classes=cls)


def dominant(classes):
    return max(classes, key=classes.get) if classes else None


def main():
    codes, names, colors = CI.load_legend()
    pairs = CI.find_pairs()
    top = pd.read_csv(os.path.join(OUT, "gs_wetland_top10.csv"))

    rows = []
    render = []   # (rank, cell, patch_mask, a, b, transform, revA, ptsA, revB, ptsB, meta)
    for rank, r in enumerate(top.itertuples(), 1):
        gid, rest = r.cell_id.split("_s"); samp, tgt = rest.split("_t")
        (ra, fA), (rb, fB) = pairs[(gid, samp, tgt)][0], pairs[(gid, samp, tgt)][1]
        with rasterio.open(fA) as ds:
            a = ds.read(1); transform = ds.transform; crs = ds.crs
        with rasterio.open(fB) as ds:
            b = ds.read(1)
        # reconstruct the specific patch (deterministic labeling)
        mask = ((a == GS) & (b == WET)) | ((a == WET) & (b == GS))
        lab, _ = ndimage.label(mask, structure=DG.STRUCT)
        patch = lab == r.lid
        geoms = [shp_shape(g) for g, v in features.shapes(patch.astype(np.uint8), transform=transform) if v == 1]
        patch_poly = unary_union(geoms)

        pA = samples_path(ra, gid, samp, tgt); pB = samples_path(rb, gid, samp, tgt)
        ptsA = load_pts(pA, crs) if pA else None
        ptsB = load_pts(pB, crs) if pB else None
        zA = zone_stats(ptsA, patch_poly, NEAR_M)
        zB = zone_stats(ptsB, patch_poly, NEAR_M)

        # categorize
        if zA["n_in"] == 0 and zB["n_in"] == 0:
            cat = "extrapolation (neither trained in zone)"
        elif zA["n_in"] > 0 and zB["n_in"] > 0:
            da, db = dominant(zA["classes"]), dominant(zB["classes"])
            cat = f"conflict ({ra}:{da} vs {rb}:{db})" if da != db else f"agree-in-training ({da})"
        else:
            who = ra if zA["n_in"] > 0 else rb
            cat = f"one-sided (only {who} trained in zone)"

        rows.append(dict(
            rank=rank, cell_id=r.cell_id, area_ha=r.area_ha,
            reviewer_a=ra, a_pts_in_zone=zA["n_in"], a_dist_m=round(zA["dist_m"], 1),
            a_classes_in_zone=";".join(f"{k}:{v}" for k, v in zA["classes"].items()) or "-",
            reviewer_b=rb, b_pts_in_zone=zB["n_in"], b_dist_m=round(zB["dist_m"], 1),
            b_classes_in_zone=";".join(f"{k}:{v}" for k, v in zB["classes"].items()) or "-",
            category=cat))
        render.append((rank, r, a, b, patch, transform, ra, ptsA, rb, ptsB, colors, names))

    df = pd.DataFrame(rows)
    df.to_csv(os.path.join(OUT, "gs_wetland_training_overlay.csv"), index=False)
    with pd.option_context("display.max_colwidth", 40, "display.width", 200):
        print(df[["rank", "cell_id", "area_ha", "a_pts_in_zone", "a_dist_m",
                  "b_pts_in_zone", "b_dist_m", "category"]].to_string(index=False))

    make_render(render, os.path.join(OUT, "gs_wetland_training_overlay.png"))
    print(f"\noutputs -> {OUT}/gs_wetland_training_overlay.csv/png")


def make_render(render, path):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    from matplotlib.colors import ListedColormap, BoundaryNorm
    from matplotlib.patches import Patch

    _, names, colors = CI.load_legend()
    order = sorted(names)
    lut = {c: i + 1 for i, c in enumerate(order)}
    cmap = ListedColormap(["#ffffff"] + [colors[c] for c in order])
    norm = BoundaryNorm(np.arange(-0.5, len(order) + 1.5), cmap.N)

    def remap(arr):
        o = np.zeros_like(arr, np.int16)
        for c, i in lut.items():
            o[arr == c] = i
        return o

    def pts_xy(pts, transform):
        # world -> pixel (col,row) for plotting over imshow
        inv = ~transform
        cols, rows = inv * (pts.geometry.x.to_numpy(), pts.geometry.y.to_numpy())
        return cols, rows

    n = len(render)
    fig, axes = plt.subplots(n, 2, figsize=(7.6, 3.5 * n))
    for i, (rank, r, a, b, patch, transform, ra, ptsA, rb, ptsB, cols_, nm) in enumerate(render):
        for j, (arr, rev, pts) in enumerate([(a, ra, ptsA), (b, rb, ptsB)]):
            ax = axes[i, j]
            ax.imshow(remap(arr), cmap=cmap, norm=norm, interpolation="nearest", alpha=0.55)
            ax.contour(patch, levels=[0.5], colors="red", linewidths=1.6)
            if pts is not None and len(pts):
                cc, rr = pts_xy(pts, transform)
                pc = [colors.get(int(l), "#000000") for l in pts["labelId"]]
                ax.scatter(cc, rr, s=1.2, c=pc, edgecolors="k", linewidths=0.05)
            ax.set_xticks([]); ax.set_yticks([])
            ax.set_title(f"{rev} training" + (f"  [#{rank} {r.area_ha}ha {r.cell_id}]" if j == 0 else ""),
                         fontsize=8)
    handles = [Patch(facecolor=colors[c], edgecolor="k", label=names[c]) for c in (GS, WET)]
    handles += [Patch(facecolor="0.7", edgecolor="k", label="other classes (training pts)"),
                Patch(edgecolor="red", facecolor="none", label="disagreement patch")]
    fig.legend(handles=handles, loc="lower center", ncol=4, fontsize=8)
    fig.suptitle("Grass/Shrub <-> Wetland disagreement patches with each reviewer's training points\n"
                 "(map faded; points colored by trained class; patch outlined red)", fontsize=11)
    fig.tight_layout(rect=[0, 0.03, 1, 0.985])
    fig.savefig(path, dpi=130, bbox_inches="tight")
    plt.close(fig)


if __name__ == "__main__":
    main()
