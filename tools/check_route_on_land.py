#!/usr/bin/env python3
"""Assert the Xuanzang route polylines stay on land (no sea crossings).
Ray-casting point-in-polygon against the vendored countries-10m TopoJSON."""
import json, math, sys

topo = json.load(open("geo/countries-10m-simple.json", encoding="utf-8"))
arcs = topo["arcs"]

def decode_arcs(arcs, transform):
    scale, tr = transform["scale"], transform["translate"]
    out = []
    for arc in arcs:
        pts = []
        x = y = 0
        for i, (ix, iy) in enumerate(arc):
            x += ix; y += iy
            pts.append((x * scale[0] + tr[0], y * scale[1] + tr[1]))
        out.append(pts)
    return out

decoded = decode_arcs(arcs, topo["transform"])

def ring_coords(arc_idx_list):
    pts = []
    for ai in arc_idx_list:
        a = decoded[ai] if ai >= 0 else decoded[~ai][::-1]
        pts.extend(a if ai >= 0 else a)
    return pts

polys = []  # country -> list of PARTS; part = list of rings (outer first)
for geom in topo["objects"]["countries"]["geometries"]:
    t = geom.get("type")
    parts = []
    if t == "Polygon":
        parts.append([ring_coords(r) for r in geom["arcs"]])
    elif t == "MultiPolygon":
        for poly in geom["arcs"]:
            parts.append([ring_coords(ring) for ring in poly])
    if parts:
        polys.append(parts)

def inside_ring(pt, ring):
    x, y = pt
    n = len(ring)
    inside = False
    j = n - 1
    for i in range(n):
        xi, yi = ring[i]; xj, yj = ring[j]
        if (yi > y) != (yj > y) and x < (xj - xi) * (y - yi) / (yj - yi) + xi:
            inside = not inside
        j = i
    return inside

def on_land(pt):
    for parts in polys:
        for rings in parts:
            if inside_ring(pt, rings[0]):
                for hole in rings[1:]:
                    if inside_ring(pt, hole):
                        break
                else:
                    return True
    return False

def sample_route(route, step_deg=0.15):
    bad = []
    for (a, b) in zip(route, route[1:]):
        L = math.hypot(b[0]-a[0], b[1]-a[1])
        n = max(1, int(L / step_deg))
        for i in range(n + 1):
            p = (a[0] + (b[0]-a[0]) * i / n, a[1] + (b[1]-a[1]) * i / n)
            if not on_land(p):
                bad.append((round(p[0], 2), round(p[1], 2)))
    return bad

sys.path.insert(0, "tools")
from xuanzang_route_pts import ROUTE_OUT_CURVED, ROUTE_BACK_CURVED
for name, route in (("out", ROUTE_OUT_CURVED), ("back", ROUTE_BACK_CURVED)):
    bad = sample_route(route)
    print(f"{name}: {'ALL ON LAND' if not bad else f'{len(bad)} SEA samples: {bad[:12]}'}")
