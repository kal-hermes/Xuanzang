#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Decisive test: are the residual 'land hits' caused by Natural Earth
10m itself, or by our own DP simplification? Test the same route
waypoints against the UNSIMPLIFIED countries-10m.json polygons using
shapely point-in-polygon."""
import json

import shapely
import shapely.geometry as sg

ROUTE = json.load(open("tools/albo_route_fixed.json"))
topo = json.load(open("geo/countries-10m.json"))
topo_simple = json.load(open("geo/countries-10m-simple.json"))


def to_geoms(t):
    # decode arcs (world-atlas transform encoding)
    scale, translate = t["transform"]["scale"], t["transform"]["translate"]
    arcs = []
    for arc in t["arcs"]:
        pts, x, y = [], 0, 0
        for dx, dy in arc:
            x += dx
            y += dy
            pts.append((x * scale[0] + translate[0], y * scale[1] + translate[1]))
        arcs.append(pts)

    geoms = []
    for feat in t["objects"]["countries"]["geometries"]:
        polys = []
        shape = feat.get("arcs", [])
        # dispatch on declared type: Polygon=[ring...], MultiPolygon=[poly...]
        if feat.get("type") == "Polygon":
            polygons = [shape]
        elif feat.get("type") == "MultiPolygon":
            polygons = shape
        else:
            polygons = []
        for rings in polygons:  # rings = polygon (list of rings)
            outer, holes = [], []
            for i, ring in enumerate(rings):
                pts = []
                for r in ring:  # a ring chains one or more arcs
                    seg = arcs[r] if r >= 0 else list(reversed(arcs[~r]))
                    pts.extend(seg if not pts else seg[1:])
                pts = [(round(x, 4), round(y, 4)) for x, y in pts]
                if i == 0:
                    outer = pts
                else:
                    holes.append(pts)
            try:
                p = sg.Polygon(outer, holes)
                if not p.is_valid:
                    p = p.buffer(0)
                if p.geom_type == "MultiPolygon":
                    polys.extend(list(p.geoms))  # buffer(0) may split it
                elif p.geom_type == "Polygon" and p.area > 1e-9:
                    polys.append(p)
            except Exception:
                pass
        if polys:
            g = polys[0] if len(polys) == 1 else sg.MultiPolygon(polys)
            geoms.append((feat.get("properties", {}).get("name", "?"), g))
    return geoms


print("building full-res geometry index...")
geoms_full = to_geoms(topo)
spatial_full = shapely.STRtree([g for _, g in geoms_full])
print(f"  {len(geoms_full)} country features (full 10m)")

# test the waypoints that the browser flagged as land under the
# simplified data + ALL waypoints, both datasets
for label, t in [("SIMPLE (602KB, in use)", topo_simple), ("FULL 10m (3.6MB)", topo)]:
    geoms = to_geoms(t)
    tree = shapely.STRtree([g for _, g in geoms])
    nland = 0
    hits = []
    for rn in ["out", "back"]:
        for lon, lat in ROUTE[rn]:
            pt = sg.Point(lon, lat)
            for i in tree.query(pt):
                if geoms[i][1].intersects(pt):
                    nland += 1
                    hits.append((rn, round(lon, 1), round(lat, 1), geoms[i][0]))
                    break
    print(f"{label}: {nland} waypoints on land")
    for h in hits[:15]:
        print("   ", h)
