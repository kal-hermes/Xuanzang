#!/usr/bin/env python3
"""Post-fix: any remaining segment that crosses land (between the
simplified A* points) gets a midpoint inserted from the safe spiral
search, iterated until validate-clean. Generic, no hardcoding."""
import json
import math
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from astar_searoute import load_land  # noqa: E402

from shapely.geometry import Point  # noqa: E402

land = load_land()
buf = land.buffer(4 / 111.0)


def seg_bad(a, b):
    if abs(b[0] - a[0]) > 180:
        return None
    for t in (0.2, 0.4, 0.6, 0.8):
        p = (a[0] + (b[0] - a[0]) * t, a[1] + (b[1] - a[1]) * t)
        if buf.contains(Point(p[0], p[1])):
            return p
    return None


def safe_near(a, p):
    # spiral from p constrained to be closer to a than p is (walk
    # toward water generally)
    for r in range(1, 60):
        for t in range(0, 16):
            th = t * math.pi / 8
            d = r * 0.06
            lon = p[0] + math.sin(th) * d / max(math.cos(math.radians(p[1])), 0.3)
            lat = p[1] + math.cos(th) * d
            if not buf.contains(Point(lon, lat)):
                return [lon, lat]
    return None


path = sys.argv[1]
pts = json.loads(Path(path).read_text())
for rnd in range(8):
    changed = False
    out = [pts[0]]
    for a, b in zip(pts, pts[1:]):
        hit = seg_bad(a, b)
        if hit:
            m = safe_near(a, hit)
            if m and not seg_bad(a, m) and not seg_bad(m, b):
                out.append(m)
                changed = True
        out.append(b)
    pts = out
    if not changed:
        break
Path(path).write_text(json.dumps(pts))
print(f"fixed {path}: {len(pts)} pts after {rnd + 1} rounds")
