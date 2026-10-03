#!/usr/bin/env python3
"""Hand-fix the Strait of Magellan section of route_out: the nudge pass
scattered waypoints into a zigzag that the Bezier renderer amplifies
into a knotted tangle. Replace the -75..-66 deg section with a clean
channel-axis waypoint list (verified in-browser against the full-10m
polygons)."""
import json
from pathlib import Path

from playwright.sync_api import sync_playwright

URL = Path("/workspace/projects/history-geography-learning-app/index.html").resolve().as_uri() + "?v=172"

# channel-axis waypoints (Atlantic -> Pacific), spaced along the true
# fairway; each will be verified/adjusted to water in-browser
STRAIT = [
    [-65.4, -46.4],
    [-66.5, -48.0],
    [-67.4, -49.0],
    [-68.2, -50.2],
    [-68.9, -51.3],
    [-69.3, -51.9],
    [-69.6, -52.4],
    [-70.1, -52.6],
    [-70.6, -52.75],
    [-71.2, -52.95],
    [-71.8, -53.25],
    [-72.4, -53.4],
    [-73.0, -53.45],
    [-73.6, -53.3],
    [-74.2, -53.0],
    [-74.7, -52.7],
    [-75.3, -51.8],
    [-75.6, -50.85],
]

with sync_playwright() as p:
    b = p.chromium.launch(headless=True)
    pg = b.new_page(viewport={"width": 1600, "height": 1000})
    pg.goto(URL, wait_until="load")
    pg.wait_for_timeout(4000)
    pg.select_option("#lesson-select", "lessons/magellan/voyage.json")
    pg.wait_for_timeout(6000)
    pg.evaluate("""(() => {
      window.__svg = document.querySelector('#map');
      window.__ct = [...window.__svg.querySelectorAll('#countries path')];
      window.__pt = window.__svg.createSVGPoint();
    })()""")

    # verify each STRAIT waypoint is water; nudge small if not
    fixed = []
    for lo, la in STRAIT:
        r = pg.evaluate("""(([lo, la]) => {
      function landLL(x, y) {
        const c = window.AtlasMap.project([x, y]);
        window.__pt.x = c[0]; window.__pt.y = c[1];
        for (const ct of window.__ct) if (ct.isPointInFill(window.__pt)) return true;
        return false;
      }
      if (!landLL(lo, la)) return [lo, la];
      for (let t = 0; t < 16; t++) {
        const th = t * Math.PI / 8;
        for (const d of [0.08, 0.15, 0.25, 0.4, 0.6, 0.9]) {
          const lo2 = lo + Math.sin(th) * d / Math.max(Math.cos(la * Math.PI / 180), 0.3);
          const la2 = la + Math.cos(th) * d;
          if (!landLL(lo2, la2)) return [lo2, la2];
        }
      }
      return null;
    })""", [lo, la])
        if r:
            fixed.append([round(r[0], 4), round(r[1], 4)])
        else:
            print(f"WARN: no water near {lo},{la} — kept original")
            fixed.append([lo, la])

    route = json.loads(Path("tools/albo_route_fixed.json").read_text(encoding="utf-8"))
    out = route["out"]
    # replace the section between first point <= -63.9 (after plata) up
    # to and including [-75.6, -50.85]
    lo_idx = next(i for i, q in enumerate(out) if q[0] <= -65.0 and q[0] > -66.0)
    hi_idx = next(i for i, q in enumerate(out) if abs(q[0] + 75.6) < 0.2 and abs(q[1] + 50.85) < 0.2)
    print(f"replacing out[{lo_idx}:{hi_idx + 1}] ({hi_idx + 1 - lo_idx} pts) with {len(fixed)} channel pts")
    route["out"] = out[:lo_idx] + fixed + out[hi_idx + 1:]
    Path("tools/albo_route_fixed.json").write_text(json.dumps(route), encoding="utf-8")
    print("saved", {k: len(v) for k, v in route.items()})
    b.close()
