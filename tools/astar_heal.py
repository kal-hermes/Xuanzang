#!/usr/bin/env python3
"""Final heal pass: for each segment still touching land, densify it
with intermediate points from a fine local A* (res 0.05) and splice.
Runs until validate-clean or 8 rounds."""
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from astar_searoute import load_land, plan_leg  # noqa: E402

from shapely.geometry import Point  # noqa: E402

land = load_land()
buf = land.buffer(2 / 111.0)


def seg_hits(a, b):
    if abs(b[0] - a[0]) > 180:
        return False
    for t in (0.15, 0.3, 0.45, 0.6, 0.75, 0.9):
        p = (a[0] + (b[0] - a[0]) * t, a[1] + (b[1] - a[1]) * t)
        if buf.contains(Point(p[0], p[1])):
            return True
    return False


path = sys.argv[1]
pts = json.loads(Path(path).read_text())
for rnd in range(8):
    out = [pts[0]]
    changed = False
    for a, b in zip(pts, pts[1:]):
        if seg_hits(a, b):
            seg = plan_leg(a, b, land, buf, 0.05, 0.3)
            if seg and len(seg) > 2:
                out.extend(seg[1:-1])
                changed = True
        out.append(b)
    pts = out
    if not changed:
        break
Path(path).write_text(json.dumps(pts))
print(f"{path}: {len(pts)} pts after {rnd + 1} rounds")
