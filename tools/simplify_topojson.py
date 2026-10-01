#!/usr/bin/env python3
"""Simplify a world-atlas TopoJSON by decimating its shared arcs.

Topology-safe: TopoJSON arcs are shared between features, so simplifying
each arc once keeps adjacent polygons glued (no slivers/gaps).

Method: Douglas-Peucker per arc with a tolerance in degrees, with a
minimum retained-point guard so tiny rings (microstates, islands)
survive. Closed arcs (first point == last point) are treated as rings.

Usage: simplify_topojson.py <in.json> <out.json> [tolerance_deg]
"""
import json
import sys
from pathlib import Path


def decode_arcs(topo):
    """delta-decoded arcs -> list of absolute point lists"""
    scale = topo["transform"]["scale"]
    translate = topo["transform"]["translate"]
    out = []
    for arc in topo["arcs"]:
        pts = []
        x, y = 0, 0
        for dx, dy in arc:
            x += dx
            y += dy
            pts.append((x * scale[0] + translate[0], y * scale[1] + translate[1]))
        out.append(pts)
    return out


def perp_dist(p, a, b):
    """distance from point p to line ab"""
    ax, ay = a
    bx, by = b
    px, py = p
    dx, dy = bx - ax, by - ay
    if dx == 0 and dy == 0:
        return ((px - ax) ** 2 + (py - ay) ** 2) ** 0.5
    t = ((px - ax) * dx + (py - ay) * dy) / (dx * dx + dy * dy)
    t = max(0.0, min(1.0, t))
    qx, qy = ax + t * dx, ay + t * dy
    return ((px - qx) ** 2 + (py - qy) ** 2) ** 0.5


def dp(points, tol):
    """iterative Douglas-Peucker"""
    n = len(points)
    if n < 3:
        return points
    keep = [False] * n
    keep[0] = keep[-1] = True
    stack = [(0, n - 1)]
    while stack:
        lo, hi = stack.pop()
        if hi <= lo + 1:
            continue
        dmax, idx = 0.0, -1
        for i in range(lo + 1, hi):
            d = perp_dist(points[i], points[lo], points[hi])
            if d > dmax:
                dmax, idx = d, i
        if dmax > tol:
            keep[idx] = True
            stack.append((lo, idx))
            stack.append((idx, hi))
    return [p for p, k in zip(points, keep) if k]


def simplify(points, tol, min_pts):
    if len(points) <= min_pts:
        return points
    out = dp(points, tol)
    # never collapse below the minimum guard
    if len(out) < min_pts:
        # keep evenly spaced subset
        step = max(1, (len(points) - 1) // (min_pts - 1))
        out = points[::step]
        out.append(points[-1])
    return out


def main():
    src, dst = sys.argv[1], sys.argv[2]
    tol = float(sys.argv[3]) if len(sys.argv) > 3 else 0.05

    topo = json.loads(Path(src).read_text())
    arcs_abs = decode_arcs(topo)
    total_before = sum(len(a) for a in arcs_abs)

    min_pts = 4  # microstate guard
    simplified = [simplify(a, tol, min_pts) for a in arcs_abs]
    total_after = sum(len(a) for a in simplified)

    # re-encode delta
    scale = topo["transform"]["scale"]
    translate = topo["transform"]["translate"]
    q = 1e4  # quantization for re-encoding (degrees)
    new_arcs = []
    for pts in simplified:
        # quantize first, then delta-encode
        qi = [(int(round((x - translate[0]) / scale[0])),
               int(round((y - translate[1]) / scale[1]))) for x, y in pts]
        enc = []
        px, py = 0, 0
        for x, y in qi:
            enc.append([x - px, y - py])
            px, py = x, y
        new_arcs.append(enc)
    topo["arcs"] = new_arcs

    Path(dst).write_text(json.dumps(topo, separators=(",", ":")))
    print(f"tol={tol}: {total_before} -> {total_after} points "
          f"({100 * total_after / total_before:.0f}%), "
          f"{len(new_arcs)} arcs")


if __name__ == "__main__":
    sys.exit(main())
