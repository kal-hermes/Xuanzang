#!/usr/bin/env python3
"""Offline replication of the map.js worldQuick decimation to find why
the budget never lands."""
import json
import math

t = json.load(open("geo/countries-10m.json"))
scale = t["transform"]["scale"]
translate = t["transform"]["translate"]
arcs = []
for arc in t["arcs"]:
    pts, x, y = [], 0, 0
    for dx, dy in arc:
        x += dx
        y += dy
        pts.append([x * scale[0] + translate[0], y * scale[1] + translate[1]])
    arcs.append(pts)

# merge by iso3 like loadWorld does
byIso3 = {}
for feat in t["objects"]["countries"]["geometries"]:
    iso3 = feat.get("properties", {}).get("iso3")
    if not iso3:
        continue
    ty, a = feat.get("type"), feat.get("arcs")
    polys = []
    for poly in ([a] if ty == "Polygon" else a):
        for ring in poly:
            pts = []
            for r in ring:
                seg = arcs[r] if r >= 0 else list(reversed(arcs[~r]))
                pts.extend(seg if not pts else seg[1:])
            polys.append(pts)
    if iso3 in byIso3:
        byIso3[iso3].extend(polys)
    else:
        byIso3[iso3] = polys

ringPts = [r for rings in byIso3.values() for r in rings]
total = sum(len(r) for r in ringPts)
print(f"world rings: {len(ringPts)}, total pts: {total}")
sizes = sorted((len(r) for r in ringPts), reverse=True)
print("top 5 ring sizes:", sizes[:5])

BUDGET = 25000
wsum = sum(math.sqrt(len(r)) for r in ringPts)

def sim(shrink):
    t_ = 0
    for r in ringPts:
        keep = max(3, round(BUDGET * math.sqrt(len(r)) / wsum * shrink))
        t_ += min(len(r), keep + 1)
    return t_

shrink = 1.0
for _ in range(8):
    s = sim(shrink)
    if s <= BUDGET:
        break
    shrink *= 0.75
print(f"shrink={shrink:.3f}, simulated total={sim(shrink)}")

actual = 0
for r in ringPts:
    keep = max(3, round(BUDGET * math.sqrt(len(r)) / wsum * shrink))
    if keep >= len(r):
        actual += len(r)
    else:
        actual += keep + 1
print(f"ACTUAL total after decimation: {actual}")
