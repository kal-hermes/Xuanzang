#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Nudge offshore the route waypoints that fall inside 10m land
polygons, IN THE BROWSER, using the app's own isPointInFill test;
then dump the fixed waypoints as Python source."""
import json
import re
from pathlib import Path

from playwright.sync_api import sync_playwright

URL = Path("/workspace/projects/history-geography-learning-app/index.html").resolve().as_uri() + "?v=126"

with sync_playwright() as p:
    b = p.chromium.launch(headless=True)
    pg = b.new_page(viewport={"width": 1600, "height": 1000})
    pg.goto(URL, wait_until="load")
    pg.wait_for_timeout(2500)
    pg.select_option("#lesson-select", "lessons/magellan/voyage.json")
    pg.wait_for_timeout(5000)

    # browser helpers
    pg.evaluate("""(() => {
      window.__svg = document.querySelector('#map');
      window.__ct = [...window.__svg.querySelectorAll('#countries path')];
      window.__pt = window.__svg.createSVGPoint();
      window.__P = window.AtlasMap.project;
    })()""")

    def fix(route_name):
        route = pg.evaluate(f"(() => {{ return window.ATLAS_LESSONS['lessons/magellan/voyage.json'].route_{route_name}; }})()")
        # densify: insert midpoints between consecutive waypoints (skip
        # antimeridian jumps) so the Bezier hugs the track tighter
        dense = [route[0]]
        for i in range(1, len(route)):
            a, bwp = route[i - 1], route[i]
            if abs(bwp[0] - a[0]) < 180:
                dense.append([(a[0] + bwp[0]) / 2, (a[1] + bwp[1]) / 2])
            dense.append(bwp)
        route = dense
        n = 0
        for i in range(len(route)):
            # test in browser whether waypoint i is on land; if so push
            # seaward (16 directions, increasing distance), keeping
            # history-true anchors by allowing only small nudges (<= 1.2 deg)
            newpt = pg.evaluate("""(([lon, lat]) => {
              function landLL(lo, la) {
                const c = window.__P([lo, la]);
                if (!c) return false;
                window.__pt.x = c[0]; window.__pt.y = c[1];
                for (const ct of window.__ct) if (ct.isPointInFill(window.__pt)) return true;
                return false;
              }
              if (!landLL(lon, lat)) return null;
              let best = null;
              for (let t = 0; t < 16; t++) {
                const th = t * Math.PI / 8;
                for (const d of [0.2, 0.4, 0.6, 0.8, 1.0, 1.2, 1.6, 2.0, 2.5, 3.0]) {
                  const lo2 = lon + Math.sin(th) * d / Math.max(Math.cos(lat * Math.PI / 180), 0.3);
                  const la2 = lat + Math.cos(th) * d;
                  // candidate must be water AND not skip a whole chord
                  // of land (cap nudge at 2.5 deg to stay history-true)
                  if (d > 2.5) continue;
                  if (!landLL(lo2, la2)) {
                    if (!best || d < best[0]) best = [d, lo2, la2];
                    break;
                  }
                }
              }
              return best ? [best[1], best[2]] : "DROP";
            })""", route[i])
            if newpt == "DROP":
                route[i] = None  # mark for deletion
                n += 1
            elif newpt:
                route[i] = [round(newpt[0], 2), round(newpt[1], 2)]
                n += 1
        route = [r for r in route if r is not None]
        pg.evaluate(f"""((r) => {{ window.ATLAS_LESSONS['lessons/magellan/voyage.json'].route_{route_name} = r; }})""", route)
        return n, route

    total = 0
    routes = {}
    for rn in ["out", "back"]:
        n, r = fix(rn)
        total += n
        routes[rn] = r
        print(f"{rn}: {n} waypoints nudged")

    # re-test
    bad = pg.evaluate("""(() => {
      const L = window.ATLAS_LESSONS['lessons/magellan/voyage.json'];
      let bad = 0;
      for (const rn of ['route_out', 'route_back']) {
        for (const [lon, lat] of L[rn]) {
          const c = window.__P([lon, lat]);
          if (!c) continue;
          window.__pt.x = c[0]; window.__pt.y = c[1];
          for (const ct of window.__ct) if (ct.isPointInFill(window.__pt)) { bad++; break; }
        }
      }
      return bad;
    })()""")
    print("remaining land waypoints:", bad)

    Path("tools/albo_route_fixed.json").write_text(json.dumps(routes))
    print("saved tools/albo_route_fixed.json")
    b.close()
