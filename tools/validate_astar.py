#!/usr/bin/env python3
"""Validate an A* route against the land polygons: every point and
every segment midpoint must be in water (with standoff)."""
import json
import math
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from astar_searoute import load_land  # noqa: E402

from shapely.geometry import Point  # noqa: E402

route = json.loads(Path(sys.argv[1]).read_text())
land = load_land()
buf = land.buffer((float(sys.argv[2]) if len(sys.argv) > 2 else 3) / 111.0)

bad_pts = []
for lon, lat in route:
    if buf.contains(Point(lon, lat)):
        bad_pts.append([lon, lat])

bad_segs = []
for a, b in zip(route, route[1:]):
    if abs(b[0] - a[0]) > 180:
        continue  # antimeridian
    for t in (0.25, 0.5, 0.75):
        p = (a[0] + (b[0] - a[0]) * t, a[1] + (b[1] - a[1]) * t)
        if buf.contains(Point(p)):
            bad_segs.append([a, b])
            break

print(f"points: {len(route)}, on-land points: {len(bad_pts)}, segments crossing land: {len(bad_segs)}")
if bad_pts[:5]:
    print("sample bad points:", bad_pts[:5])
if bad_segs[:3]:
    print("sample bad segs:", bad_segs[:3])
sys.exit(1 if (bad_pts or bad_segs) else 0)
