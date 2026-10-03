#!/usr/bin/env python3
"""Splice A*-planned segments (Philippines/Brunei + Strait) into
tools/albo_route_fixed.json, replacing the heuristic nudge output in
those regions. Idempotent: always starts from the CURRENT fixed.json
and replaces the lon-range windows."""
import json
from pathlib import Path

fx = json.loads(Path("tools/albo_route_fixed.json").read_text())
phl = json.loads(Path("tools/astar_philippines.json").read_text())
strait = json.loads(Path("tools/astar_strait.json").read_text())

out = fx["out"]

# --- Philippines window: first point with lon in [115..125] after the
# Cebu area to the route's Tidore end. Replace everything from the
# first waypoint east of 122E (Palawan approach) — keep Bohol/Cebu
# (123.8-124.4E) which the A* spec already includes at its head.
# Window = lon 118..129 (Palawan .. Tidore), lat 0..10
def in_phl(p):
    return 118.0 <= p[0] <= 129.5 and 0.0 <= p[1] <= 10.5

first = next(i for i, p in enumerate(out) if in_phl(p))
last = max(i for i, p in enumerate(out) if in_phl(p))
out = out[:first] + [list(p) for p in phl] + out[last + 1:]

# --- Strait window: lon -76..-64.5, lat -46..-55
def in_strait(p):
    return -76.5 <= p[0] <= -64.5 and -55.5 <= p[1] <= -45.8

first = next(i for i, p in enumerate(out) if in_strait(p))
last = max(i for i, p in enumerate(out) if in_strait(p))
out = out[:first] + [list(p) for p in strait] + out[last + 1:]

fx["out"] = out
Path("tools/albo_route_fixed.json").write_text(json.dumps(fx))
print("spliced: out =", len(out))
