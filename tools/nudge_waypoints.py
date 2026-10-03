#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Nudge offshore the route waypoints that fall inside 10m land
polygons, IN THE BROWSER, using the app's own isPointInFill test;
then dump the fixed waypoints as Python source."""
import json
import re
from pathlib import Path

from playwright.sync_api import sync_playwright

URL = Path("/workspace/projects/history-geography-learning-app/index.html").resolve().as_uri() + "?v=186"

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

    def fix(route_name, source):
        route = [list(p) for p in source]
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
    # source of truth: the Albo-derived ROUTE in the python module
    import sys
    sys.path.insert(0, str(Path(__file__).resolve().parent))
    from magellan_route_albo import ROUTE_OUT as SRC_OUT, ROUTE_BACK as SRC_BACK

    for rn, src in [("out", SRC_OUT), ("back", SRC_BACK)]:
        n, r = fix(rn, src)
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
    })""")
    print("remaining land waypoints:", bad)

    # PIN every stop into route_out: insert the stop's exact coords at
    # the nearest-waypoint gap; if the stop coord is inside a land
    # polygon (harbour towns), nudge the PIN to nearby water (<= 0.35
    # deg) so the line touches the dot's edge instead of cutting
    # through the town. The displayed dot stays at the true coords.
    pins = pg.evaluate("""(() => {
      return window.ATLAS_LESSONS['lessons/magellan/voyage.json'].stops
        .map((s) => s.coords.slice());
    })()""")
    pinned = pg.evaluate("""((payload) => {
      const routes = JSON.parse(payload.routesJson);
      const pins = JSON.parse(payload.pinsJson);
      function landLL(lo, la) {
        const c = window.__P([lo, la]);
        if (!c) return false;
        window.__pt.x = c[0]; window.__pt.y = c[1];
        for (const ct of window.__ct) if (ct.isPointInFill(window.__pt)) return true;
        return false;
      }
      const pts = routes.out.map((p) => p.slice());
      let inserted = 0;
      for (const pin of pins) {
        let [px, py] = pin;
        if (landLL(px, py)) {
          // find nearest water in 16 directions, small radius only
          let best = null;
          for (let t = 0; t < 16; t++) {
            const th = t * Math.PI / 8;
            for (const d of [0.08, 0.15, 0.22, 0.3, 0.35]) {
              const lo2 = px + Math.sin(th) * d / Math.max(Math.cos(py * Math.PI / 180), 0.3);
              const la2 = py + Math.cos(th) * d;
              if (!landLL(lo2, la2)) {
                if (!best || d < best[0]) best = [d, lo2, la2];
                break;
              }
            }
          }
          if (best) [px, py] = [best[1], best[2]];
        }
        if (pts.some((p) => Math.abs(p[0] - px) < 0.05 && Math.abs(p[1] - py) < 0.05)) continue;
        // nearest waypoint, insert between it and its closer neighbour.
        // GATE: only insert if the stop is within 8 deg of some route
        // waypoint — otherwise it belongs to the OTHER leg (e.g. the
        // return-leg Cape of Good Hope stop must never be pinned into
        // the outbound Atlantic track) and pinning it would splice a
        // stray line across the map.
        {
          let nearest = 1e18;
          for (const p of pts) {
            const dd = (p[0] - px) ** 2 + (p[1] - py) ** 2;
            if (dd < nearest) nearest = dd;
          }
          if (nearest > 64) continue; // > 8 deg away: wrong leg
        }
        let bi = 0, bd = 1e18;
        for (let i = 0; i < pts.length; i++) {
          const d = (pts[i][0] - px) ** 2 + (pts[i][1] - py) ** 2;
          if (d < bd) { bd = d; bi = i; }
        }
        const seg = (a, b) => (Math.abs(pts[a][0] - pts[b][0]) > 180) ? 1e18 :
          (pts[a][0] - px) ** 2 + (pts[a][1] - py) ** 2 + (pts[b][0] - px) ** 2 + (pts[b][1] - py) ** 2;
        const left = bi > 0 ? seg(bi - 1, bi) : 1e18;
        const right = bi < pts.length - 1 ? seg(bi, bi + 1) : 1e18;
        pts.splice(left <= right ? bi : bi + 1, 0, [px, py]);
        inserted++;
      }
      return { out: pts.map((p) => p.map((v) => Math.round(v * 10000) / 10000)), inserted };
    })""", {"routesJson": json.dumps(routes), "pinsJson": json.dumps(pins)})
    routes["out"] = pinned["out"]
    print(f"pinned {pinned['inserted']} stops into route_out")

    Path("tools/albo_route_fixed.json").write_text(json.dumps(routes))
    print("saved tools/albo_route_fixed.json")
    b.close()
