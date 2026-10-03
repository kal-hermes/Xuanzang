#!/usr/bin/env python3
"""De-zigzag pass: iteratively remove the middle waypoint of sharp
reversals (turn > 135 deg) UNLESS it is a stop pin or its removal puts
the new chord on land (checked in-browser). Then re-verify."""
import json
from pathlib import Path

from playwright.sync_api import sync_playwright

URL = Path("/workspace/projects/history-geography-learning-app/index.html").resolve().as_uri() + "?v=164"

with sync_playwright() as p:
    b = p.chromium.launch(headless=True)
    pg = b.new_page(viewport={"width": 1600, "height": 1000})
    pg.goto(URL, wait_until="load")
    pg.wait_for_timeout(4000)
    pg.select_option("#lesson-select", "lessons/magellan/voyage.json")
    pg.wait_for_timeout(5000)
    pg.evaluate("""(() => {
      window.__svg = document.querySelector('#map');
      window.__ct = [...window.__svg.querySelectorAll('#countries path')];
      window.__pt = window.__svg.createSVGPoint();
    })()""")

    data = pg.evaluate("""(() => ({
      out: window.ATLAS_LESSONS['lessons/magellan/voyage.json'].route_out.map((r) => r.slice()),
      back: window.ATLAS_LESSONS['lessons/magellan/voyage.json'].route_back.map((r) => r.slice()),
      pins: window.ATLAS_LESSONS['lessons/magellan/voyage.json'].stops.map((s) => s.coords.slice()),
    }))()""")
    routes = {"out": data["out"], "back": data["back"]}
    pins = data["pins"]

    def land(lonlat):
        return pg.evaluate("""(([lo, la]) => {
          const c = window.AtlasMap.project([lo, la]);
          if (!c) return true;
          window.__pt.x = c[0]; window.__pt.y = c[1];
          for (const ct of window.__ct) if (ct.isPointInFill(window.__pt)) return true;
          return false;
        })""", lonlat)

    for rn in ["out", "back"]:
        pts = routes[rn]
        removed = 0
        i = 1
        while i < len(pts) - 1:
            a, m, c = pts[i - 1], pts[i], pts[i + 1]
            if abs(c[0] - a[0]) > 180:
                i += 1
                continue
            ax, ay = m[0] - a[0], m[1] - a[1]
            bx, by = c[0] - m[0], c[1] - m[1]
            la, lb = (ax * ax + ay * ay) ** 0.5, (bx * bx + by * by) ** 0.5
            if la < 1e-9 or lb < 1e-9:
                i += 1
                continue
            dot = (ax * bx + ay * by) / (la * lb)
            isPin = any(abs(q[0] - m[0]) < 0.06 and abs(q[1] - m[1]) < 0.06 for q in pins)
            if dot < -0.7 and not isPin:  # > ~135 deg reversal
                # would removing m put the chord a->c on land? sample 5 pts
                bad = False
                for t in (0.2, 0.35, 0.5, 0.65, 0.8):
                    if land([a[0] + (c[0] - a[0]) * t, a[1] + (c[1] - a[1]) * t]):
                        bad = True
                        break
                if not bad:
                    pts.pop(i)
                    removed += 1
                    continue  # re-examine same i with new neighbours
            i += 1
        print(f"{rn}: removed {removed} zigzag points -> {len(pts)}")

    Path("tools/albo_route_fixed.json").write_text(json.dumps(routes))
    print("saved")
    b.close()
