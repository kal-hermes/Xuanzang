#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Surgical fix of the remaining 12 curve-touches: nudge the SPECIFIC
waypoints bracketing each hit, iterating in-browser until the rendered
CURVE (not just waypoints) is land-free at fine sampling."""
import json
from pathlib import Path

from playwright.sync_api import sync_playwright

URL = Path("/workspace/projects/history-geography-learning-app/index.html").resolve().as_uri() + "?v=125"

FIXES = {
    # (route, idx): [dlon, dlat] manual nudge — seaward direction
    ("out", 28): [0.35, 0.0],    # Rio bay: push E out of the bay polygon
    ("out", 29): [0.5, -0.15],
    ("out", 47): [-0.2, -0.35],  # Plata: S out of URY polygon
    ("out", 48): [-0.3, -0.4],
    ("out", 69): [-0.25, -0.4],  # Patagonia coast Golfo San Jorge
    ("out", 73): [0.3, -0.5],    # San Julian approach
    ("out", 76): [0.35, -0.3],   # coast south of San Julian
    ("out", 77): [0.4, -0.25],
    ("out", 84): [0.4, -0.5],    # strait S bend (Brunswick pen.)
    ("out", 85): [0.5, -0.4],
    ("out", 86): [0.6, -0.3],
    ("out", 87): [0.55, -0.35],
    ("out", 184): [-0.3, 0.45],  # Borneo N coast offshore
    ("out", 185): [-0.25, 0.5],
    ("out", 186): [0.6, 0.6],    # Borneo return leg offshore
    ("back", 7): [-0.35, 0.0],   # Ceram strait area
    ("back", 8): [-0.4, 0.1],
    ("back", 12): [0.15, -0.55], # Timor S coast offshore
    ("back", 13): [0.1, -0.6],
    ("back", 58): [-0.3, -0.5],  # Cape Verde: S of Santiago
}

with sync_playwright() as p:
    b = p.chromium.launch(headless=True)
    pg = b.new_page(viewport={"width": 1600, "height": 1000})
    pg.goto(URL, wait_until="load")
    pg.wait_for_timeout(2500)
    pg.select_option("#lesson-select", "lessons/magellan/voyage.json")
    pg.wait_for_timeout(5000)

    routes = pg.evaluate("""(() => ({
      out: window.ATLAS_LESSONS['lessons/magellan/voyage.json'].route_out.map(r => r.slice()),
      back: window.ATLAS_LESSONS['lessons/magellan/voyage.json'].route_back.map(r => r.slice()),
    }))()""")

    for (rn, idx), [dl, da] in FIXES.items():
        routes[rn][idx][0] = round(routes[rn][idx][0] + dl, 2)
        routes[rn][idx][1] = round(routes[rn][idx][1] + da, 2)

    pg.evaluate("""((rs) => {
      const L = window.ATLAS_LESSONS['lessons/magellan/voyage.json'];
      L.route_out = rs.out; L.route_back = rs.back;
    })""", routes)

    # rebuild the routes in the DOM as the app does, then test the curve
    for attempt in range(6):
        pg.evaluate("""(() => {
          // re-trigger the app's own route drawing via the real
          // journey-view dropdown (explore -> step -> explore)
          const sel = document.querySelector('#journey-view-select');
          if (!sel) return;
          const v = sel.value;
          sel.value = v === 'step' ? 'explore' : 'step';
          sel.dispatchEvent(new Event('change'));
          sel.value = v;
          sel.dispatchEvent(new Event('change'));
        })""")
        pg.wait_for_timeout(2500)
        hits = pg.evaluate("""(() => {
          const svg = document.querySelector('#map');
          const routes = [...svg.querySelectorAll('path.searoute')];
          const countries = [...svg.querySelectorAll('#countries path')];
          const svgPt = svg.createSVGPoint();
          const vb = svg.viewBox.baseVal;
          let land = 0, sea = 0;
          const out = [];
          routes.forEach((r, ri) => {
            const len = r.getTotalLength();
            for (let d = 0; d <= len; d += 3) {
              const pt = r.getPointAtLength(d);
              if (pt.x < vb.x || pt.x > vb.x + vb.width) continue;
              svgPt.x = pt.x; svgPt.y = pt.y;
              for (const c of countries) {
                if (c.isPointInFill(svgPt)) {
                  land++;
                  if (out.length < 12) out.push([ri ? 'back' : 'out',
                    Math.round(((pt.x - 10) / 980 * 360 - 180) * 10) / 10,
                    Math.round((90 - (pt.y - 255) / 490 * 180) * 10) / 10,
                    c.dataset.iso3]);
                  break;
                }
              }
              sea++;
            }
          });
          return {land, sea, out};
        })""")
        print(f"attempt {attempt}: land={hits['land']}/{hits['sea']}", hits["out"][:6])
        if hits["land"] == 0:
            break
        # nudge waypoints nearest each remaining hit
        for _, hl, ha, _iso in hits["out"]:
            rn = "out" if _ == "out" else "back" if _ == "back" else _
            best = None
            for i, (lo, la) in enumerate(routes[rn]):
                dd = (lo - hl) ** 2 + (la - ha) ** 2
                if best is None or dd < best[0]:
                    best = (dd, i)
            i = best[1]
            # push away from land: direction = away from the hit point
            import math
            dx = routes[rn][i][0] - hl
            dy = routes[rn][i][1] - ha
            m = math.hypot(dx, dy) or 1
            routes[rn][i][0] = round(routes[rn][i][0] + dx / m * 0.3, 2)
            routes[rn][i][1] = round(routes[rn][i][1] + dy / m * 0.3, 2)
        pg.evaluate("""((rs) => {
          const L = window.ATLAS_LESSONS['lessons/magellan/voyage.json'];
          L.route_out = rs.out; L.route_back = rs.back;
        })""", routes)

    Path("tools/albo_route_fixed.json").write_text(json.dumps(routes))
    print("saved")
    b.close()
