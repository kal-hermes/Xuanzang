#!/usr/bin/env python3
"""Strait of Magellan centreline via raster skeletonisation.

The strait's channel is locally ~2 km wide — far below any sane A*
grid. Instead: rasterise the water mask inside the strait bbox at
0.01 deg, skeletonise (medial axis), walk the skeleton graph from the
Atlantic entry to the Pacific exit, output the centreline waypoints.
"""
import json
import sys
from pathlib import Path

import numpy as np
from shapely.geometry import Point, box

sys.path.insert(0, str(Path(__file__).resolve().parent))
from astar_searoute import load_land  # noqa: E402

from skimage.morphology import medial_axis  # noqa: E402

land = load_land()

# strait bbox (lon, lat)
LON0, LON1 = -75.5, -64.5
LAT0, LAT1 = -54.5, -45.5
RES = 0.01

nx = int((LON1 - LON0) / RES)
ny = int((LAT1 - LAT0) / RES)

# use vectorised contains via prepared geometry
from shapely.prepared import prep  # noqa: E402

prep_land = prep(land)

# rasterise: water=1
import numpy as np

gx = LON0 + (np.arange(nx) + 0.5) * RES
gy = LAT0 + (np.arange(ny) + 0.5) * RES
# contains_xy on shapely 2.x
water = np.zeros((ny, nx), dtype=bool)
# test in row chunks for speed
from shapely import contains_xy  # noqa: E402

XX, YY = np.meshgrid(gx, gy)
water = ~contains_xy(land, XX, YY)

print("water cells:", water.sum(), "of", water.size)

# medial axis of the water, restricted to the largest connected
# component containing the strait entry
skel, dist = medial_axis(water, return_distance=True)

# entry (Atlantic, near [-65.3, -46.6]) and exit (Pacific [-75.2, -50.5])
def to_cell(lon, lat):
    return (int((lat - LAT0) / RES), int((lon - LON0) / RES))

def to_ll(j, i):
    return (round(LON0 + (i + 0.5) * RES, 4), round(LAT0 + (j + 0.5) * RES, 4))

# BFS over skeleton from entry cell to exit cell (8-connected)
from collections import deque

def nearest_skel(lon, lat):
    j0, i0 = to_cell(lon, lat)
    best = None
    bd = 1e18
    for j in range(max(0, j0 - 60), min(ny, j0 + 61)):
        for i in range(max(0, i0 - 60), min(nx, i0 + 61)):
            if skel[j, i]:
                d = (j - j0) ** 2 + (i - i0) ** 2
                if d < bd:
                    bd, best = d, (j, i)
    return best

start = nearest_skel(-65.0, -46.2)
goal = nearest_skel(-75.3, -50.6)
print("start cell:", start, to_ll(*start), "goal:", goal, to_ll(*goal))

prev = {start: None}
q = deque([start])
while q:
    cur = q.popleft()
    if cur == goal:
        break
    cj, ci = cur
    for dj in (-1, 0, 1):
        for di in (-1, 0, 1):
            if di == 0 and dj == 0:
                continue
            nxt = (cj + dj, ci + di)
            if not (0 <= nxt[0] < ny and 0 <= nxt[1] < nx):
                continue
            if not skel[nxt]:
                continue
            if nxt in prev:
                continue
            prev[nxt] = cur
            q.append(nxt)

if goal not in prev:
    print("FAIL: skeleton BFS did not reach goal")
    sys.exit(1)

path = [goal]
while path[-1] != start:
    path.append(prev[path[-1]])
path.reverse()
print("skeleton path length:", len(path))

pts = [to_ll(j, i) for j, i in path]

# simplify with land validation (reuse astar simplify)
from astar_searoute import simplify  # noqa: E402

buf = land.buffer(0.3 / 111.0)
simp = simplify(pts, tol_km=1.5, land_buf=buf)
simp = [p for p in simp if not buf.contains(Point(p[0], p[1]))]

Path("tools/astar_strait.json").write_text(json.dumps(simp, indent=1))
print(f"simplified to {len(simp)} pts; saved tools/astar_strait.json")
