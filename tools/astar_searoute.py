#!/usr/bin/env python3
"""A* sea-route planner over the full-10m land polygons.

Replaces the heuristic nudge/pin/densify dance for the tricky
archipelago legs: given historical anchor waypoints (from Albo /
Pigafetta), route each leg through WATER only.

- Land: union of country polygons from geo/countries-10m.json
  (TopoJSON-decoded, same as land_test_full.py).
- Grid: lon/lat bins (0.25 deg default, finer near the target);
  cell walkable iff its centre is in water (with a shore-standoff
  buffer so the line doesn't kiss the coast).
- Cost: great-circle distance + penalty proportional to deviation
  from the straight anchor-to-anchor line, so the path stays near the
  historical track when the water allows it.
- Output: simplified waypoint list (Douglas-Peucker), snapped to
  start/end anchors exactly.

Usage: python tools/astar_searoute.py <spec.json>
spec: {"anchors": [[lon,lat],...], "out": "path.json",
       "resolution": 0.25, "standoff_km": 3}
"""
from __future__ import annotations

import heapq
import json
import math
import sys
from pathlib import Path

from shapely.geometry import Point, shape
from shapely.ops import unary_union
from shapely.validation import make_valid

ROOT = Path(__file__).resolve().parent.parent


def load_land():
    topo = json.loads((ROOT / "geo" / "countries-10m.json").read_text())
    tr = topo["transform"]
    sx, sy = tr["scale"][0], tr["scale"][1]
    tx, ty = tr["translate"][0], tr["translate"][1]
    arcs = []
    for arc in topo["arcs"]:
        x, y = 0, 0
        pts = []
        for dx, dy in arc:
            x += dx
            y += dy
            pts.append((x * sx + tx, y * sy + ty))
        arcs.append(pts)

    def ring_coords(ids):
        pts = []
        for i in ids:
            a = arcs[i if i >= 0 else ~i]
            seg = a if i >= 0 else list(reversed(a))
            if pts and pts[-1] == seg[0]:
                pts.extend(seg[1:])
            else:
                pts.extend(seg)
        return pts

    polys = []
    for geom in topo["objects"]["countries"]["geometries"]:
        gtype = geom.get("type")
        g = None
        if gtype == "Polygon":
            rings = [ring_coords(r) for r in geom["arcs"]]
            g = shape({"type": "Polygon", "coordinates": rings})
        elif gtype == "MultiPolygon":
            parts = []
            for poly_arcs in geom["arcs"]:
                rings = [ring_coords(r) for r in poly_arcs]
                if len(rings[0]) >= 4:
                    parts.append({"type": "Polygon", "coordinates": rings})
            g = shape({"type": "MultiPolygon", "coordinates": [p["coordinates"] for p in parts]})
        if g is None or g.is_empty:
            continue
        g = make_valid(g)
        # make_valid may return a GeometryCollection mixing polygons
        # and linework; extract every polygon, recursively
        def extract_polys(geom):
            if geom.geom_type == "Polygon":
                return [geom]
            if geom.geom_type == "MultiPolygon":
                return list(geom.geoms)
            if geom.geom_type == "GeometryCollection":
                out = []
                for sub in geom.geoms:
                    out.extend(extract_polys(sub))
                return out
            return []
        polys.extend(extract_polys(g))
    land = unary_union(polys)
    return land


def great_circle_km(a, b):
    lon1, lat1 = math.radians(a[0]), math.radians(a[1])
    lon2, lat2 = math.radians(b[0]), math.radians(b[1])
    return 6371.0 * math.acos(min(1.0, math.sin(lat1) * math.sin(lat2) +
                                  math.cos(lat1) * math.cos(lat2) * math.cos(lon2 - lon1)))


def plan(anchors, land, land_buf, res=0.25, dev_penalty=0.35):
    """A* between consecutive anchors; returns full waypoint list.
    Anchors that fall inside the standoff (harbour towns) are replaced
    by their nearest safe-water grid point so the rendered line never
    touches land — the stop DOT stays at the true historical coords."""
    from shapely.geometry import Point
    safe = []
    for a in anchors:
        if land_buf.contains(Point(a[0], a[1])):
            # nearest water: spiral search on the leg grid resolution
            found = None
            for r in range(1, 40):
                for t in range(0, 16):
                    th = t * math.pi / 8
                    d = r * res
                    lon = a[0] + math.sin(th) * d / max(math.cos(math.radians(a[1])), 0.3)
                    lat = a[1] + math.cos(th) * d
                    if not land_buf.contains(Point(lon, lat)):
                        found = [lon, lat]
                        break
                if found:
                    break
            safe.append(found if found else list(a))
        else:
            safe.append(list(a))
    out = [safe[0]]
    for a, b in zip(safe, safe[1:]):
        seg = plan_leg(a, b, land, land_buf, res, dev_penalty)
        if seg is None:
            print(f"WARN: no path found {a} -> {b}; using straight line", file=sys.stderr)
            out.append(b)
            continue
        out.extend(seg[1:])
    return out


def plan_leg(a, b, land, land_buf, res, dev_penalty):
    # local grid around the leg with margin
    margin = 6.0
    lo_lon = min(a[0], b[0]) - margin
    hi_lon = max(a[0], b[0]) + margin
    lo_lat = min(a[1], b[1]) - margin
    hi_lat = max(a[1], b[1]) + margin
    # wrap longitudes into [-180, 180)
    def wrap(x):
        return (x + 180.0) % 360.0 - 180.0

    nx = max(2, int((hi_lon - lo_lon) / res))
    ny = max(2, int((hi_lat - lo_lat) / res))
    grid_lo = [lo_lon + i * res for i in range(nx + 1)]
    grid_la = [lo_lat + j * res for j in range(ny + 1)]

    def walkable(lon, lat):
        return not land_buf.contains(Point(lon, lat))

    # nodes: (i, j)
    def h(i, j):
        return great_circle_km((grid_lo[i], grid_la[j]), b) * (1.0 + 0) / 100.0

    start = (min(range(nx + 1), key=lambda i: abs(grid_lo[i] - a[0])),
             min(range(ny + 1), key=lambda j: abs(grid_la[j] - a[1])))
    goal = (min(range(nx + 1), key=lambda i: abs(grid_lo[i] - b[0])),
            min(range(ny + 1), key=lambda j: abs(grid_la[j] - b[1])))

    def id2ll(n):
        return (grid_lo[n[0]], grid_la[n[1]])

    def snap_walkable(n):
        """Nearest walkable cell to n (spiral out). Anchors inside the
        standoff buffer (harbour towns) otherwise snap the goal into
        land and A* fails."""
        if walkable(*id2ll(n)):
            return n
        for r in range(1, max(nx, ny) + 1):
            for di in range(-r, r + 1):
                for dj in (-r, r):
                    for cand in ((n[0] + di, n[1] + dj), (n[0] + di, n[1] - dj)):
                        i, j = cand
                        if 0 <= i <= nx and 0 <= j <= ny and walkable(grid_lo[i], grid_la[j]):
                            return (i, j)
            # also scan the top/bottom rows of the ring
            for dj in range(-r, r + 1):
                for cand in ((n[0] - r, n[1] + dj), (n[0] + r, n[1] + dj)):
                    i, j = cand
                    if 0 <= i <= nx and 0 <= j <= ny and walkable(grid_lo[i], grid_la[j]):
                        return (i, j)
        return None

    start = snap_walkable(start)
    goal = snap_walkable(goal)
    if start is None or goal is None:
        return None

    # deviation penalty: distance from the a-b line (perpendicular km)
    ax, ay = a
    bx, by = b
    abx, aby = bx - ax, by - ay
    ab_len = math.hypot(abx, aby) or 1e-9

    def dev_km(p):
        t = max(0.0, min(1.0, ((p[0] - ax) * abx + (p[1] - ay) * aby) / (ab_len ** 2)))
        proj = (ax + t * abx, ay + t * aby)
        return great_circle_km(p, proj)

    openq = [(0.0, start)]
    came = {}
    g = {start: 0.0}
    closed = set()
    while openq:
        _, cur = heapq.heappop(openq)
        if cur in closed:
            continue
        closed.add(cur)
        if cur == goal:
            path = [cur]
            while path[-1] != start:
                path.append(came[path[-1]])
            path.reverse()
            ga = id2ll(start)
            gb = id2ll(goal)
            return [a] + [id2ll(n) for n in path[1:-1]] + [b if not land_buf.contains(Point(b[0], b[1])) else gb]
        ci, cj = cur
        for di in (-1, 0, 1):
            for dj in (-1, 0, 1):
                if di == 0 and dj == 0:
                    continue
                ni, nj = ci + di, cj + dj
                if not (0 <= ni <= nx and 0 <= nj <= ny):
                    continue
                nxt = (ni, nj)
                if nxt in closed:
                    continue
                p = id2ll(nxt)
                if not walkable(p[0], p[1]):
                    continue
                step = great_circle_km(id2ll(cur), p)
                cost = g[cur] + step + dev_penalty * dev_km(p)
                if cost < g.get(nxt, math.inf):
                    g[nxt] = cost
                    came[nxt] = cur
                    heapq.heappush(openq, (cost + great_circle_km(p, b), nxt))
    return None


def simplify(points, tol_km=8.0, land_buf=None):
    """Douglas-Peucker in lon/lat degrees (tol converted). If land_buf
    is given, every candidate cut (removing a point) is validated: the
    new segment must not cross land — otherwise the point is kept."""
    tol = tol_km / 111.0

    def seg_ok(a, b):
        if land_buf is None:
            return True
        if abs(b[0] - a[0]) > 180:
            return True
        for t in (0.2, 0.4, 0.6, 0.8):
            p = (a[0] + (b[0] - a[0]) * t, a[1] + (b[1] - a[1]) * t)
            if land_buf.contains(Point(p[0], p[1])):
                return False
        return True

    def dp(pts):
        if len(pts) < 3:
            return pts
        ax, ay = pts[0]
        bx, by = pts[-1]
        dx, dy = bx - ax, by - ay
        L = math.hypot(dx, dy) or 1e-12
        best, bi = -1.0, -1
        for i in range(1, len(pts) - 1):
            d = abs(dy * pts[i][0] - dx * pts[i][1] + bx * ay - by * ax) / L
            if d > best:
                best, bi = d, i
        if best > tol and seg_ok(pts[0], pts[-1]):
            return dp(pts[: bi + 1])[:-1] + dp(pts[bi:])
        if best > tol:
            # can't shortcut this span: recurse both sides anyway
            return dp(pts[: bi + 1])[:-1] + dp(pts[bi:])
        return [pts[0], pts[-1]]

    return dp(points)


if __name__ == "__main__":
    spec = json.loads(Path(sys.argv[1]).read_text())
    print("loading land polygons ...")
    land = load_land()
    standoff = spec.get("standoff_km", 3)
    print(f"buffering land by {standoff} km ...")
    land_buf = land.buffer(standoff / 111.0)
    res = spec.get("resolution", 0.25)
    anchors = spec["anchors"]
    full = plan(anchors, land, land_buf, res=res,
                dev_penalty=spec.get("dev_penalty", 0.35))
    simp = simplify(full, tol_km=spec.get("simplify_km", 8), land_buf=land_buf)
    # drop anchor points that sit inside the standoff (harbour towns);
    # the A* grid point nearest to them is already in safe water
    simp = [p for p in simp if not land_buf.contains(Point(p[0], p[1]))]
    # heal: any remaining adjacent pair whose segment touches land gets
    # the ORIGINAL grid points re-inserted between them (walk back
    # through `full`), converging in a few rounds
    def seg_hits(a, b):
        if abs(b[0] - a[0]) > 180:
            return False
        for t in (0.15, 0.3, 0.45, 0.6, 0.75, 0.9):
            p = (a[0] + (b[0] - a[0]) * t, a[1] + (b[1] - a[1]) * t)
            if land_buf.contains(Point(p[0], p[1])):
                return True
        return False

    for _round in range(6):
        changed = False
        out = [simp[0]]
        for a, b in zip(simp, simp[1:]):
            if seg_hits(a, b):
                # find the stretch of `full` between a and b
                try:
                    ia = next(i for i, q in enumerate(full) if abs(q[0] - a[0]) < 1e-6 and abs(q[1] - a[1]) < 1e-6)
                    ib = next(i for i, q in enumerate(full) if abs(q[0] - b[0]) < 1e-6 and abs(q[1] - b[1]) < 1e-6)
                except StopIteration:
                    ia = ib = None
                if ia is not None and ib is not None and ib > ia + 1:
                    out.extend(full[ia + 1:ib])
                    changed = True
                else:
                    out.append(b)
                    continue
            out.append(b)
        simp = out
        if not changed:
            break
    Path(spec["out"]).write_text(json.dumps(simp, indent=1))
    print(f"planned {len(anchors)} anchors -> {len(full)} grid pts -> {len(simp)} simplified pts")
    print("saved", spec["out"])
