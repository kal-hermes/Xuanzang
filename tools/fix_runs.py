#!/usr/bin/env python3
"""Targeted fix for visible land runs: coarse 2-unit sampling, insert
screen-space water points at run midpoints. Up to 5 rounds."""
import json
from pathlib import Path

from playwright.sync_api import sync_playwright

URL = Path("/workspace/projects/history-geography-learning-app/index.html").resolve().as_uri() + "?v=169"

JS_HELPERS = """(() => {
  window.__svg = document.querySelector('#map');
  window.__ct = [...window.__svg.querySelectorAll('#countries path')];
  window.__pt = window.__svg.createSVGPoint();
  window.__inv = ([x, y]) => [(x - 500) / 2.72222, (500 - y) / 2.72222];
  window.__landAt = (x, y) => {
    window.__pt.x = x; window.__pt.y = y;
    for (const c of window.__ct) if (c.isPointInFill(window.__pt)) return true;
    return false;
  };
})()"""

with sync_playwright() as p:
    b = p.chromium.launch(headless=True)
    pg = b.new_page(viewport={"width": 1600, "height": 1000})
    pg.goto(URL, wait_until="load")
    pg.wait_for_timeout(4000)
    pg.select_option("#lesson-select", "lessons/magellan/voyage.json")
    pg.wait_for_timeout(6000)
    pg.evaluate(JS_HELPERS)

    for rnd in range(5):
        runs = pg.evaluate("""(() => {
      const routes = [...window.__svg.querySelectorAll('path.searoute')];
      const out = [];
      routes.forEach((r, ri) => {
        const len = r.getTotalLength();
        let run = null;
        for (let d = 0; d <= len; d += 2) {
          const pt = r.getPointAtLength(d);
          if (window.__landAt(pt.x, pt.y)) {
            if (run) { run.len += 2; run.x2 = pt.x; run.y2 = pt.y; }
            else run = { ri, len: 2, x1: pt.x, y1: pt.y, x2: pt.x, y2: pt.y };
          } else if (run) {
            if (run.len >= 4) out.push(run);
            run = null;
          }
        }
        if (run && run.len >= 4) out.push(run);
      });
      return out;
    })""")
        if not runs:
            print(f"round {rnd}: no runs >= 4 units — done")
            break
        print(f"round {rnd}: {len(runs)} runs to fix")
        for run in runs:
            fix = pg.evaluate("""((run) => {
        const mx = (run.x1 + run.x2) / 2, my = (run.y1 + run.y2) / 2;
        for (let t = 0; t < 16; t++) {
          const th = t * Math.PI / 8;
          for (const d of [2, 3, 4, 6, 8, 11, 14]) {
            const x = mx + Math.sin(th) * d, y = my + Math.cos(th) * d;
            if (!window.__landAt(x, y)) return window.__inv([x, y]);
          }
        }
        return null;
      })""", run)
            if not fix:
                continue
            routes_data = pg.evaluate("""(() => ({
        out: window.ATLAS_LESSONS['lessons/magellan/voyage.json'].route_out,
        back: window.ATLAS_LESSONS['lessons/magellan/voyage.json'].route_back,
      }))()""")
            rn = "back" if run["ri"] else "out"
            pts = routes_data[rn]
            bi, bd = 0, 1e18
            for i, q in enumerate(pts):
                d2 = (q[0] - fix[0]) ** 2 + (q[1] - fix[1]) ** 2
                if d2 < bd:
                    bd, bi = d2, i
            def sd(i):
                return (pts[i][0] - fix[0]) ** 2 + (pts[i][1] - fix[1]) ** 2
            left = sd(bi - 1) if bi > 0 else 1e18
            right = sd(bi + 1) if bi < len(pts) - 1 else 1e18
            ni = bi - 1 if left <= right else bi + 1
            if abs(pts[ni][0] - pts[bi][0]) > 180:
                continue
            if not any(abs(q[0] - fix[0]) < 0.05 and abs(q[1] - fix[1]) < 0.05 for q in pts):
                pts.insert(max(bi, ni), [round(fix[0], 4), round(fix[1], 4)])
            pg.evaluate("""((payload) => {
          window.ATLAS_LESSONS['lessons/magellan/voyage.json'][payload.rn === 'out' ? 'route_out' : 'route_back'] = payload.pts;
        })""", {"rn": rn, "pts": pts})
        pg.evaluate("""(() => {
          const sel = document.querySelector('#journey-view-select');
          const v = sel.value;
          sel.value = v === 'step' ? 'explore' : 'step';
          sel.dispatchEvent(new Event('change'));
          sel.value = v;
          sel.dispatchEvent(new Event('change'));
        })""")
        pg.wait_for_timeout(2500)

    routes_data = pg.evaluate("""(() => ({
      out: window.ATLAS_LESSONS['lessons/magellan/voyage.json'].route_out,
      back: window.ATLAS_LESSONS['lessons/magellan/voyage.json'].route_back,
    }))()""")
    Path("tools/albo_route_fixed.json").write_text(json.dumps(routes_data))
    print("saved", {k: len(v) for k, v in routes_data.items()})
    b.close()
